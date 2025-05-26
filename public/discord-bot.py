# --- 必要なライブラリのインポート ---
import discord
import datetime
import firebase_admin # Firestoreを使うために必要
from firebase_admin import credentials # Firestoreを使うために必要
from firebase_admin import firestore   # Firestoreを使うために必要
import asyncio # 非同期処理のため (Botの他の処理を止めないように)
import os # 環境変数からファイルパスを読み込むため
import json # JSON設定ファイル読み込み用

# --- Discord Bot の設定 ---
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.reactions = True
bot = discord.Client(intents=intents)

# --- Firebase Firestore の設定 ---
# 環境変数またはサービスアカウントファイルから設定を読み込み
FIREBASE_SERVICE_ACCOUNT_KEY_PATH = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH', 
                                             '/home/mitz_matsuoka/bot_files/citric-goal-325101-5e32397a8375.json')

db = None # Firestoreクライアントをグローバル変数として定義

def initialize_firebase():
    """Firebase Firestoreを初期化する関数"""
    global db
    try:
        if not firebase_admin._apps: # まだ初期化されていなければ初期化
            # 環境変数からサービスアカウント情報を取得
            if os.getenv('FIREBASE_SERVICE_ACCOUNT'):
                service_account_info = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT'))
                cred = credentials.Certificate(service_account_info)
            else:
                # ファイルパスから読み込み
                cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_KEY_PATH)
            
            firebase_admin.initialize_app(cred)
        
        db = firestore.client() # Firestoreデータベースへの参照を取得
        print("✅ Firebase Firestoreへの接続準備ができました。")
        return True
    except FileNotFoundError:
        print(f"❌ 致命的エラー: Firebaseサービスアカウントキーファイルが見つかりません。")
        print(f"指定されたパス: {FIREBASE_SERVICE_ACCOUNT_KEY_PATH}")
        print("パスが正しいか、ファイルがサーバーのその場所に存在するか確認してください。")
        return False
    except Exception as e:
        print(f"❌ 致命的エラー: Firebase Firestoreの初期化に失敗しました: {e}")
        print("サービスアカウントキーの内容や権限、ネットワーク接続を確認してください。")
        return False

# Firebase初期化
firebase_initialized = initialize_firebase()

# --- ユーザー情報をFirestoreに保存/更新する関数 ---
async def update_user_info(user_id: str, guild_id: str, username: str, action_type: str = None):
    """ユーザー情報をFirestoreのusersコレクションに保存/更新する"""
    if db is None:
        return
    
    try:
        user_ref = db.collection('users').document(user_id)
        user_doc = await asyncio.to_thread(user_ref.get)
        
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
        if user_doc.exists:
            # 既存ユーザーの更新
            update_data = {
                'lastActive': current_time,
                'username': username,
                'guildId': guild_id,
                'isActive': True
            }
            
            # エンゲージメントスコアの更新
            if action_type:
                current_data = user_doc.to_dict()
                current_score = current_data.get('engagementScore', 0)
                
                # アクションタイプに応じてスコアを加算
                score_increment = {
                    'MESSAGE_CREATE': 1,
                    'MESSAGE_EDIT': 0.5,
                    'REACTION_ADD': 0.3,
                    'MEMBER_JOIN': 5
                }.get(action_type, 0)
                
                update_data['engagementScore'] = current_score + score_increment
            
            await asyncio.to_thread(user_ref.update, update_data)
        else:
            # 新規ユーザーの作成
            user_data = {
                'id': user_id,
                'username': username,
                'guildId': guild_id,
                'joinedAt': current_time,
                'lastActive': current_time,
                'interests': [],
                'engagementScore': 5 if action_type == 'MEMBER_JOIN' else 1,
                'isActive': True,
                'preferences': {
                    'podcastNotifications': True,
                    'matchingNotifications': True,
                    'dmNotifications': True,
                    'language': 'ja'
                }
            }
            await asyncio.to_thread(user_ref.set, user_data)
            
    except Exception as e:
        print(f'❌ ユーザー情報更新エラー: {e}')

# --- インタラクションをFirestoreに記録する非同期関数 ---
async def log_interaction_to_firestore(interaction_data: dict):
    """指定されたデータをFirestoreの'interactions'コレクションに新しいドキュメントとして追記する非同期関数"""
    if db is None:
        print("⚠️ Firebase Firestoreが初期化されていません。ログをスキップしました。")
        return

    try:
        # サーバー側のタイムスタンプを追加
        interaction_data['timestamp'] = firestore.SERVER_TIMESTAMP
        
        # Firestoreへの書き込み
        await asyncio.to_thread(db.collection('interactions').add, interaction_data)
        
        # デバッグ用（必要に応じてコメントアウト）
        # print(f"📝 インタラクションをFirestoreに記録: {interaction_data.get('type')}")
        
    except Exception as e:
        print(f'❌ Firestoreへの書き込みエラー: {e}')
        print(f'❌ 書き込もうとしたデータ: {interaction_data}')

# --- Discordイベントを待ち受けるコード ---
@bot.event
async def on_ready():
    print(f'🚀 ログインしました！ Bot名: {bot.user}')
    if db is None:
        print("⚠️ Firebase Firestoreが初期化されていないため、ログ機能は動作しません。")
    else:
        print("📝 ログ記録の準備ができました (Firestore)。")
    print('------')

# --- 各種イベントリスナー関数 ---

# メッセージが送信されたとき
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    
    # DMの場合はguild_idをNoneに設定
    guild_id = str(message.guild.id) if message.guild else None
    guild_name = message.guild.name if message.guild else 'DM'
    
    # チャンネル名の取得
    channel_name = 'Unknown Channel'
    if isinstance(message.channel, discord.TextChannel) or \
       isinstance(message.channel, discord.VoiceChannel) or \
       isinstance(message.channel, discord.Thread):
        channel_name = message.channel.name
    elif isinstance(message.channel, discord.DMChannel):
        channel_name = f'DM with {message.channel.recipient.name if message.channel.recipient else "Unknown User"}'

    user_name = message.author.display_name or message.author.name
    user_id = str(message.author.id)
    message_id = str(message.id)
    content = message.clean_content

    # ユーザー情報の更新
    if guild_id:
        await update_user_info(user_id, guild_id, user_name, 'MESSAGE_CREATE')

    # インタラクションデータの作成
    interaction_data = {
        'type': 'message',
        'userId': user_id,
        'username': user_name,
        'guildId': guild_id,
        'guildName': guild_name,
        'channelId': str(message.channel.id),
        'channelName': channel_name,
        'messageId': message_id,
        'content': content,
        'keywords': extract_keywords(content),  # キーワード抽出
        'metadata': {
            'hasAttachments': len(message.attachments) > 0,
            'hasEmbeds': len(message.embeds) > 0,
            'mentionCount': len(message.mentions),
            'reactionCount': len(message.reactions) if message.reactions else 0
        }
    }
    
    asyncio.create_task(log_interaction_to_firestore(interaction_data))

# メッセージが編集されたとき
@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if after.author.bot:
        return
    if before.content == after.content:
        return

    guild_id = str(after.guild.id) if after.guild else None
    guild_name = after.guild.name if after.guild else 'DM'
    
    channel_name = 'Unknown Channel'
    if isinstance(after.channel, discord.TextChannel) or \
       isinstance(after.channel, discord.VoiceChannel) or \
       isinstance(after.channel, discord.Thread):
        channel_name = after.channel.name
    elif isinstance(after.channel, discord.DMChannel):
        channel_name = f'DM with {after.channel.recipient.name if after.channel.recipient else "Unknown User"}'

    user_name = after.author.display_name or after.author.name
    user_id = str(after.author.id)

    # ユーザー情報の更新
    if guild_id:
        await update_user_info(user_id, guild_id, user_name, 'MESSAGE_EDIT')

    interaction_data = {
        'type': 'message_edit',
        'userId': user_id,
        'username': user_name,
        'guildId': guild_id,
        'guildName': guild_name,
        'channelId': str(after.channel.id),
        'channelName': channel_name,
        'messageId': str(after.id),
        'content': after.clean_content,
        'keywords': extract_keywords(after.clean_content),
        'metadata': {
            'contentBefore': before.clean_content,
            'contentAfter': after.clean_content
        }
    }
    
    asyncio.create_task(log_interaction_to_firestore(interaction_data))

# メッセージが削除されたとき
@bot.event
async def on_message_delete(message: discord.Message):
    if message.author.bot:
        return

    guild_id = str(message.guild.id) if message.guild else None
    guild_name = message.guild.name if message.guild else 'DM'
    
    channel_name = 'Unknown Channel'
    if isinstance(message.channel, discord.TextChannel) or \
       isinstance(message.channel, discord.VoiceChannel) or \
       isinstance(message.channel, discord.Thread):
        channel_name = message.channel.name
    elif isinstance(message.channel, discord.DMChannel):
        channel_name = f'DM with {message.channel.recipient.name if message.channel.recipient else "Unknown User"}'

    user_name = message.author.display_name or message.author.name
    user_id = str(message.author.id)
    content = message.clean_content if message.clean_content else "(Content not available)"

    interaction_data = {
        'type': 'message_delete',
        'userId': user_id,
        'username': user_name,
        'guildId': guild_id,
        'guildName': guild_name,
        'channelId': str(message.channel.id),
        'channelName': channel_name,
        'messageId': str(message.id),
        'content': content,
        'keywords': extract_keywords(content) if content != "(Content not available)" else [],
        'metadata': {
            'deletedContent': content
        }
    }
    
    asyncio.create_task(log_interaction_to_firestore(interaction_data))

# メンバーがサーバーに参加したとき
@bot.event
async def on_member_join(member: discord.Member):
    guild_id = str(member.guild.id)
    user_name = member.display_name or member.name
    user_id = str(member.id)

    # ユーザー情報の作成
    await update_user_info(user_id, guild_id, user_name, 'MEMBER_JOIN')

    interaction_data = {
        'type': 'member_join',
        'userId': user_id,
        'username': user_name,
        'guildId': guild_id,
        'guildName': member.guild.name,
        'keywords': ['新規参加', 'ウェルカム'],
        'metadata': {
            'accountCreated': member.created_at.isoformat(),
            'isBot': member.bot,
            'roles': [role.name for role in member.roles if role.name != '@everyone']
        }
    }
    
    asyncio.create_task(log_interaction_to_firestore(interaction_data))

# メンバーがサーバーから退出したとき
@bot.event
async def on_member_remove(member: discord.Member):
    guild_id = str(member.guild.id)
    user_name = member.display_name or member.name
    user_id = str(member.id)

    # ユーザーを非アクティブに設定
    if db:
        try:
            user_ref = db.collection('users').document(user_id)
            await asyncio.to_thread(user_ref.update, {
                'isActive': False,
                'leftAt': datetime.datetime.now(datetime.timezone.utc)
            })
        except Exception as e:
            print(f'❌ ユーザー退出処理エラー: {e}')

    interaction_data = {
        'type': 'member_leave',
        'userId': user_id,
        'username': user_name,
        'guildId': guild_id,
        'guildName': member.guild.name,
        'keywords': ['退出', 'さようなら'],
        'metadata': {
            'roles': [role.name for role in member.roles if role.name != '@everyone']
        }
    }
    
    asyncio.create_task(log_interaction_to_firestore(interaction_data))

# リアクションが追加されたとき
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id) if payload.guild_id else None
    guild_id = str(payload.guild_id) if payload.guild_id else None
    guild_name = guild.name if guild else 'DM'

    channel = bot.get_channel(payload.channel_id)
    channel_name = 'Unknown Channel'
    if isinstance(channel, discord.TextChannel) or \
       isinstance(channel, discord.VoiceChannel) or \
       isinstance(channel, discord.Thread):
        channel_name = channel.name
    elif isinstance(channel, discord.DMChannel):
        channel_name = 'DM'

    user = bot.get_user(payload.user_id)
    user_name = user.display_name if user else 'Unknown User'
    user_id = str(payload.user_id)

    # ユーザー情報の更新
    if guild_id and user:
        await update_user_info(user_id, guild_id, user_name, 'REACTION_ADD')

    interaction_data = {
        'type': 'reaction_add',
        'userId': user_id,
        'username': user_name,
        'guildId': guild_id,
        'guildName': guild_name,
        'channelId': str(payload.channel_id),
        'channelName': channel_name,
        'messageId': str(payload.message_id),
        'keywords': ['リアクション', payload.emoji.name],
        'metadata': {
            'emojiName': payload.emoji.name,
            'emojiId': str(payload.emoji.id) if payload.emoji.is_custom_emoji() else None,
            'isCustomEmoji': payload.emoji.is_custom_emoji()
        }
    }
    
    asyncio.create_task(log_interaction_to_firestore(interaction_data))

# リアクションが削除されたとき
@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id) if payload.guild_id else None
    guild_id = str(payload.guild_id) if payload.guild_id else None
    guild_name = guild.name if guild else 'DM'

    channel = bot.get_channel(payload.channel_id)
    channel_name = 'Unknown Channel'
    if isinstance(channel, discord.TextChannel) or \
       isinstance(channel, discord.VoiceChannel) or \
       isinstance(channel, discord.Thread):
        channel_name = channel.name
    elif isinstance(channel, discord.DMChannel):
        channel_name = 'DM'

    user = bot.get_user(payload.user_id)
    user_name = user.display_name if user else 'Unknown User'
    user_id = str(payload.user_id)

    interaction_data = {
        'type': 'reaction_remove',
        'userId': user_id,
        'username': user_name,
        'guildId': guild_id,
        'guildName': guild_name,
        'channelId': str(payload.channel_id),
        'channelName': channel_name,
        'messageId': str(payload.message_id),
        'keywords': ['リアクション削除', payload.emoji.name],
        'metadata': {
            'emojiName': payload.emoji.name,
            'emojiId': str(payload.emoji.id) if payload.emoji.is_custom_emoji() else None,
            'isCustomEmoji': payload.emoji.is_custom_emoji()
        }
    }
    
    asyncio.create_task(log_interaction_to_firestore(interaction_data))

# --- ユーティリティ関数 ---
def extract_keywords(content: str) -> list:
    """メッセージからキーワードを抽出する簡単な関数"""
    if not content:
        return []
    
    # 簡単なキーワード抽出（実際の実装ではより高度な自然言語処理を使用）
    import re
    
    # 日本語と英語の単語を抽出
    words = re.findall(r'[ぁ-んァ-ヶー一-龠a-zA-Z]+', content.lower())
    
    # 3文字以上の単語のみを抽出し、重複を除去
    keywords = list(set([word for word in words if len(word) >= 3]))
    
    # 最大10個のキーワードに制限
    return keywords[:10]

# --- Discordボットの実行 ---
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', '')

if __name__ == '__main__':
    if not DISCORD_BOT_TOKEN:
        print("❌ 致命的エラー: Discord Botトークンが設定されていません。")
        print("環境変数 DISCORD_BOT_TOKEN を設定してください。")
    elif not firebase_initialized:
        print("❌ 致命的エラー: Firestoreが初期化されていないため、Botを起動できません。")
    else:
        print("🚀 ボットを起動します...")
        try:
            bot.run(DISCORD_BOT_TOKEN)
        except discord.LoginFailure:
            print("❌ 致命的エラー: Discord Botトークンが不正です。正しいトークンを設定してください。")
        except Exception as e:
            print(f"❌ ボットの起動中に予期せぬエラーが発生しました: {e}")

print("🔚 ボットが終了しました。")