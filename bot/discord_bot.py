# --- 必要なライブラリのインポート ---
import discord
import datetime
import firebase_admin # Firestoreを使うために必要
from firebase_admin import credentials # Firestoreを使うために必要
from firebase_admin import firestore   # Firestoreを使うために必要
import asyncio # 非同期処理のため (Botの他の処理を止めないように)
import os # 環境変数からファイルパスを読み込むため
import json # JSON設定ファイル読み込み用
from dotenv import load_dotenv # .envファイル読み込み用

# .envファイルから環境変数を読み込み
load_dotenv()

# --- Discord Bot の設定 ---
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.reactions = True
intents.guild_scheduled_events = True  # スケジュールイベント権限を追加
bot = discord.Client(intents=intents)

# --- Firebase Firestore の設定 ---
# 環境変数またはサービスアカウントファイルから設定を読み込み
FIREBASE_SERVICE_ACCOUNT_KEY_PATH = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH', 
                                             './nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json')

db = None # Firestoreクライアントをグローバル変数として定義

def initialize_firebase():
    """Firebase Firestoreを初期化する関数"""
    global db
    try:
        if not firebase_admin._apps: # まだ初期化されていなければ初期化
            # まずファイルパスから読み込みを試行
            if os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH') and os.path.exists(os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH')):
                key_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH')
                print(f"🔑 Firebaseサービスアカウントキーファイルを読み込み中: {key_path}")
                cred = credentials.Certificate(key_path)
            elif os.path.exists(FIREBASE_SERVICE_ACCOUNT_KEY_PATH):
                print(f"🔑 デフォルトのFirebaseサービスアカウントキーファイルを読み込み中: {FIREBASE_SERVICE_ACCOUNT_KEY_PATH}")
                cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_KEY_PATH)
            elif os.getenv('FIREBASE_SERVICE_ACCOUNT'):
                print("🔑 環境変数からFirebaseサービスアカウント情報を読み込み中...")
                service_account_info = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT'))
                cred = credentials.Certificate(service_account_info)
            else:
                raise FileNotFoundError("Firebaseサービスアカウントキーが見つかりません")
            
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
                    'MEMBER_JOIN': 5,
                    'EVENT_JOIN': 2  # イベント参加でスコア+2
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

# --- イベント情報をFirestoreに保存/更新する関数 ---
async def save_event_to_firestore(event_data: dict):
    """イベント情報をFirestoreの'events'コレクションに保存/更新する"""
    if db is None:
        print("⚠️ Firebase Firestoreが初期化されていません。イベント保存をスキップしました。")
        return

    try:
        event_id = event_data.get('eventId')
        if not event_id:
            print("❌ イベントIDが見つかりません")
            return
        
        event_ref = db.collection('events').document(event_id)
        event_data['updatedAt'] = firestore.SERVER_TIMESTAMP
        
        await asyncio.to_thread(event_ref.set, event_data, merge=True)
        print(f"📅 イベント情報をFirestoreに保存: {event_data.get('name', 'Unknown Event')}")
        
    except Exception as e:
        print(f'❌ イベント保存エラー: {e}')
        print(f'❌ 保存しようとしたデータ: {event_data}')

async def delete_event_from_firestore(event_id: str):
    """イベント情報をFirestoreから削除する"""
    if db is None:
        return

    try:
        event_ref = db.collection('events').document(event_id)
        await asyncio.to_thread(event_ref.delete)
        print(f"🗑️ イベントをFirestoreから削除: {event_id}")
        
    except Exception as e:
        print(f'❌ イベント削除エラー: {e}')

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

    # ボットがメンションされた場合の応答処理
    if bot.user in message.mentions:
        await handle_mention_response(message)

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
            'reactionCount': len(message.reactions) if message.reactions else 0,
            'isMention': bot.user in message.mentions
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

# --- スケジュールイベント関連のリスナー ---

# スケジュールイベントが作成されたとき
@bot.event
async def on_scheduled_event_create(event: discord.ScheduledEvent):
    guild_id = str(event.guild.id)
    guild_name = event.guild.name
    creator_id = str(event.creator.id) if event.creator else None
    creator_name = event.creator.display_name if event.creator else 'Unknown User'

    # イベントデータの作成
    event_data = {
        'eventId': str(event.id),
        'name': event.name,
        'description': event.description or '',
        'guildId': guild_id,
        'guildName': guild_name,
        'creatorId': creator_id,
        'creatorName': creator_name,
        'startTime': event.start_time.isoformat() if event.start_time else None,
        'endTime': event.end_time.isoformat() if event.end_time else None,
        'location': event.location or '',
        'status': event.status.name if event.status else 'unknown',
        'entityType': event.entity_type.name if event.entity_type else 'unknown',
        'privacyLevel': event.privacy_level.name if event.privacy_level else 'unknown',
        'userCount': event.user_count or 0,
        'createdAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'keywords': extract_keywords(f"{event.name} {event.description or ''}"),
        'isActive': True
    }

    # Firestoreに保存
    await save_event_to_firestore(event_data)

    # インタラクションとしても記録
    interaction_data = {
        'type': 'scheduled_event_create',
        'userId': creator_id,
        'username': creator_name,
        'guildId': guild_id,
        'guildName': guild_name,
        'eventId': str(event.id),
        'eventName': event.name,
        'keywords': ['イベント作成', 'スケジュール'] + extract_keywords(event.name),
        'metadata': {
            'eventDescription': event.description or '',
            'startTime': event.start_time.isoformat() if event.start_time else None,
            'endTime': event.end_time.isoformat() if event.end_time else None,
            'location': event.location or '',
            'entityType': event.entity_type.name if event.entity_type else 'unknown'
        }
    }

    asyncio.create_task(log_interaction_to_firestore(interaction_data))
    print(f"📅 新しいイベントが作成されました: {event.name}")

# スケジュールイベントが更新されたとき
@bot.event
async def on_scheduled_event_update(before: discord.ScheduledEvent, after: discord.ScheduledEvent):
    guild_id = str(after.guild.id)
    guild_name = after.guild.name
    creator_id = str(after.creator.id) if after.creator else None
    creator_name = after.creator.display_name if after.creator else 'Unknown User'

    # 更新されたイベントデータ
    event_data = {
        'eventId': str(after.id),
        'name': after.name,
        'description': after.description or '',
        'guildId': guild_id,
        'guildName': guild_name,
        'creatorId': creator_id,
        'creatorName': creator_name,
        'startTime': after.start_time.isoformat() if after.start_time else None,
        'endTime': after.end_time.isoformat() if after.end_time else None,
        'location': after.location or '',
        'status': after.status.name if after.status else 'unknown',
        'entityType': after.entity_type.name if after.entity_type else 'unknown',
        'privacyLevel': after.privacy_level.name if after.privacy_level else 'unknown',
        'userCount': after.user_count or 0,
        'createdAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'keywords': extract_keywords(f"{after.name} {after.description or ''}"),
        'isActive': True
    }

    # Firestoreに更新保存
    await save_event_to_firestore(event_data)

    # 変更内容を記録
    changes = []
    if before.name != after.name:
        changes.append(f"名前: {before.name} → {after.name}")
    if before.description != after.description:
        changes.append(f"説明: {before.description or '(なし)'} → {after.description or '(なし)'}")
    if before.start_time != after.start_time:
        changes.append(f"開始時間: {before.start_time} → {after.start_time}")
    if before.status != after.status:
        changes.append(f"ステータス: {before.status.name if before.status else 'unknown'} → {after.status.name if after.status else 'unknown'}")

    # インタラクションとしても記録
    interaction_data = {
        'type': 'scheduled_event_update',
        'userId': creator_id,
        'username': creator_name,
        'guildId': guild_id,
        'guildName': guild_name,
        'eventId': str(after.id),
        'eventName': after.name,
        'keywords': ['イベント更新', 'スケジュール変更'] + extract_keywords(after.name),
        'metadata': {
            'changes': changes,
            'beforeStatus': before.status.name if before.status else 'unknown',
            'afterStatus': after.status.name if after.status else 'unknown',
            'eventDescription': after.description or '',
            'startTime': after.start_time.isoformat() if after.start_time else None,
            'endTime': after.end_time.isoformat() if after.end_time else None
        }
    }

    asyncio.create_task(log_interaction_to_firestore(interaction_data))
    print(f"📅 イベントが更新されました: {after.name} ({len(changes)}件の変更)")

# スケジュールイベントが削除されたとき
@bot.event
async def on_scheduled_event_delete(event: discord.ScheduledEvent):
    guild_id = str(event.guild.id)
    guild_name = event.guild.name
    creator_id = str(event.creator.id) if event.creator else None
    creator_name = event.creator.display_name if event.creator else 'Unknown User'

    # Firestoreから削除
    await delete_event_from_firestore(str(event.id))

    # インタラクションとして記録
    interaction_data = {
        'type': 'scheduled_event_delete',
        'userId': creator_id,
        'username': creator_name,
        'guildId': guild_id,
        'guildName': guild_name,
        'eventId': str(event.id),
        'eventName': event.name,
        'keywords': ['イベント削除', 'スケジュール削除'] + extract_keywords(event.name),
        'metadata': {
            'eventDescription': event.description or '',
            'startTime': event.start_time.isoformat() if event.start_time else None,
            'endTime': event.end_time.isoformat() if event.end_time else None,
            'location': event.location or '',
            'finalStatus': event.status.name if event.status else 'unknown',
            'userCount': event.user_count or 0
        }
    }

    asyncio.create_task(log_interaction_to_firestore(interaction_data))
    print(f"🗑️ イベントが削除されました: {event.name}")

# ユーザーがスケジュールイベントに参加したとき
@bot.event
async def on_scheduled_event_user_add(event: discord.ScheduledEvent, user: discord.User):
    guild_id = str(event.guild.id)
    guild_name = event.guild.name
    user_id = str(user.id)
    user_name = user.display_name or user.name

    # ユーザー情報の更新（イベント参加でエンゲージメントスコア+2）
    await update_user_info(user_id, guild_id, user_name, 'EVENT_JOIN')

    # インタラクションとして記録
    interaction_data = {
        'type': 'scheduled_event_user_add',
        'userId': user_id,
        'username': user_name,
        'guildId': guild_id,
        'guildName': guild_name,
        'eventId': str(event.id),
        'eventName': event.name,
        'keywords': ['イベント参加', 'スケジュール参加'] + extract_keywords(event.name),
        'metadata': {
            'eventDescription': event.description or '',
            'startTime': event.start_time.isoformat() if event.start_time else None,
            'eventStatus': event.status.name if event.status else 'unknown',
            'currentUserCount': event.user_count or 0
        }
    }

    asyncio.create_task(log_interaction_to_firestore(interaction_data))
    print(f"👥 {user_name} がイベント '{event.name}' に参加しました")

# ユーザーがスケジュールイベントから退出したとき
@bot.event
async def on_scheduled_event_user_remove(event: discord.ScheduledEvent, user: discord.User):
    guild_id = str(event.guild.id)
    guild_name = event.guild.name
    user_id = str(user.id)
    user_name = user.display_name or user.name

    # インタラクションとして記録
    interaction_data = {
        'type': 'scheduled_event_user_remove',
        'userId': user_id,
        'username': user_name,
        'guildId': guild_id,
        'guildName': guild_name,
        'eventId': str(event.id),
        'eventName': event.name,
        'keywords': ['イベント退出', 'スケジュール退出'] + extract_keywords(event.name),
        'metadata': {
            'eventDescription': event.description or '',
            'startTime': event.start_time.isoformat() if event.start_time else None,
            'eventStatus': event.status.name if event.status else 'unknown',
            'currentUserCount': event.user_count or 0
        }
    }

    asyncio.create_task(log_interaction_to_firestore(interaction_data))
    print(f"👋 {user_name} がイベント '{event.name}' から退出しました")

# --- ユーティリティ関数 ---
def extract_keywords(content: str) -> list:
    """メッセージからキーワードを抽出する関数"""
    import re
    
    # 日本語の助詞・助動詞・記号を除外するパターン
    stop_words = {
        'は', 'が', 'を', 'に', 'で', 'と', 'の', 'も', 'から', 'まで', 'より', 'へ', 'や', 'か', 'だ', 'である', 'です', 'ます', 'した', 'する', 'される', 'れる', 'られる', 'せる', 'させる', 'ない', 'ぬ', 'ん', 'た', 'て', 'で', 'ば', 'なら', 'ても', 'でも', 'けれど', 'けれども', 'しかし', 'だが', 'でも', 'それで', 'そして', 'また', 'さらに', 'ただし', 'なお', 'ちなみに', 'つまり', 'すなわち', 'いわゆる', 'たとえば', 'など', 'なんか', 'みたい', 'ような', 'らしい', 'っぽい', 'という', 'といった', 'とか', 'とは', 'って', 'っていう', 'ていう', 'である', 'だった', 'でした', 'でしょう', 'だろう', 'かもしれない', 'かも', 'はず', 'べき', 'べきだ', 'べきである', 'ところ', 'わけ', 'こと', 'もの', 'の', 'ん', 'よ', 'ね', 'な', 'さ', 'ぞ', 'ぜ', 'わ', 'かな', 'かしら', 'っけ', 'たっけ', 'だっけ'
    }
    
    # URLやメンションを除去
    content = re.sub(r'https?://\S+', '', content)
    content = re.sub(r'<@!?\d+>', '', content)
    content = re.sub(r'<#\d+>', '', content)
    content = re.sub(r'<:\w+:\d+>', '', content)
    
    # 記号や数字を除去し、単語に分割
    words = re.findall(r'[ぁ-んァ-ヶ一-龯a-zA-Z]+', content)
    
    # 2文字以上の単語のみを抽出し、ストップワードを除外
    keywords = []
    for word in words:
        if len(word) >= 2 and word.lower() not in stop_words:
            keywords.append(word.lower())
    
    # 重複を除去し、出現頻度でソート
    from collections import Counter
    word_counts = Counter(keywords)
    keywords = [word for word, count in word_counts.most_common()]
    
    # 最大10個のキーワードに制限
    return keywords[:10]

# --- データ取得機能 ---

async def get_all_users(guild_id: str = None):
    """usersコレクションから全ユーザーデータを取得"""
    if db is None:
        print("⚠️ Firebase Firestoreが初期化されていません。")
        return []
    
    try:
        users_ref = db.collection('users')
        if guild_id:
            users_ref = users_ref.where('guildId', '==', guild_id)
        
        docs = await asyncio.to_thread(users_ref.get)
        users = []
        for doc in docs:
            user_data = doc.to_dict()
            user_data['id'] = doc.id
            users.append(user_data)
        
        print(f"📊 ユーザーデータを取得: {len(users)}件")
        return users
    except Exception as e:
        print(f"❌ ユーザーデータ取得エラー: {e}")
        return []

async def get_all_guilds():
    """guildsコレクションから全サーバーデータを取得"""
    if db is None:
        print("⚠️ Firebase Firestoreが初期化されていません。")
        return []
    
    try:
        docs = await asyncio.to_thread(db.collection('guilds').get)
        guilds = []
        for doc in docs:
            guild_data = doc.to_dict()
            guild_data['id'] = doc.id
            guilds.append(guild_data)
        
        print(f"📊 サーバーデータを取得: {len(guilds)}件")
        return guilds
    except Exception as e:
        print(f"❌ サーバーデータ取得エラー: {e}")
        return []

async def get_all_interactions(guild_id: str = None, limit: int = None):
    """interactionsコレクションから全インタラクションデータを取得"""
    if db is None:
        print("⚠️ Firebase Firestoreが初期化されていません。")
        return []
    
    try:
        interactions_ref = db.collection('interactions')
        if guild_id:
            interactions_ref = interactions_ref.where('guildId', '==', guild_id)
        
        interactions_ref = interactions_ref.order_by('timestamp', direction=firestore.Query.DESCENDING)
        
        if limit:
            interactions_ref = interactions_ref.limit(limit)
        
        docs = await asyncio.to_thread(interactions_ref.get)
        interactions = []
        for doc in docs:
            interaction_data = doc.to_dict()
            interaction_data['id'] = doc.id
            interactions.append(interaction_data)
        
        print(f"📊 インタラクションデータを取得: {len(interactions)}件")
        return interactions
    except Exception as e:
        print(f"❌ インタラクションデータ取得エラー: {e}")
        return []

async def get_all_topics(guild_id: str = None):
    """topicsコレクションから全トピックデータを取得"""
    if db is None:
        print("⚠️ Firebase Firestoreが初期化されていません。")
        return []
    
    try:
        topics_ref = db.collection('topics')
        if guild_id:
            topics_ref = topics_ref.where('guildId', '==', guild_id)
        
        topics_ref = topics_ref.order_by('popularity', direction=firestore.Query.DESCENDING)
        
        docs = await asyncio.to_thread(topics_ref.get)
        topics = []
        for doc in docs:
            topic_data = doc.to_dict()
            topic_data['id'] = doc.id
            topics.append(topic_data)
        
        print(f"📊 トピックデータを取得: {len(topics)}件")
        return topics
    except Exception as e:
        print(f"❌ トピックデータ取得エラー: {e}")
        return []

async def get_all_podcasts(guild_id: str = None):
    """podcastsコレクションから全ポッドキャストデータを取得"""
    if db is None:
        print("⚠️ Firebase Firestoreが初期化されていません。")
        return []
    
    try:
        podcasts_ref = db.collection('podcasts')
        if guild_id:
            podcasts_ref = podcasts_ref.where('guildId', '==', guild_id)
        
        podcasts_ref = podcasts_ref.order_by('publishedAt', direction=firestore.Query.DESCENDING)
        
        docs = await asyncio.to_thread(podcasts_ref.get)
        podcasts = []
        for doc in docs:
            podcast_data = doc.to_dict()
            podcast_data['id'] = doc.id
            podcasts.append(podcast_data)
        
        print(f"📊 ポッドキャストデータを取得: {len(podcasts)}件")
        return podcasts
    except Exception as e:
        print(f"❌ ポッドキャストデータ取得エラー: {e}")
        return []

async def get_all_user_matches(guild_id: str = None):
    """user_matchesコレクションから全マッチングデータを取得"""
    if db is None:
        print("⚠️ Firebase Firestoreが初期化されていません。")
        return []
    
    try:
        matches_ref = db.collection('user_matches')
        if guild_id:
            matches_ref = matches_ref.where('guildId', '==', guild_id)
        
        matches_ref = matches_ref.order_by('createdAt', direction=firestore.Query.DESCENDING)
        
        docs = await asyncio.to_thread(matches_ref.get)
        matches = []
        for doc in docs:
            match_data = doc.to_dict()
            match_data['id'] = doc.id
            matches.append(match_data)
        
        print(f"📊 マッチングデータを取得: {len(matches)}件")
        return matches
    except Exception as e:
        print(f"❌ マッチングデータ取得エラー: {e}")
        return []

async def get_all_events(guild_id: str = None):
    """eventsコレクションから全イベントデータを取得"""
    if db is None:
        print("⚠️ Firebase Firestoreが初期化されていません。")
        return []
    
    try:
        events_ref = db.collection('events')
        if guild_id:
            events_ref = events_ref.where('guildId', '==', guild_id)
        
        events_ref = events_ref.order_by('updatedAt', direction=firestore.Query.DESCENDING)
        
        docs = await asyncio.to_thread(events_ref.get)
        events = []
        for doc in docs:
            event_data = doc.to_dict()
            event_data['id'] = doc.id
            events.append(event_data)
        
        print(f"📊 イベントデータを取得: {len(events)}件")
        return events
    except Exception as e:
        print(f"❌ イベントデータ取得エラー: {e}")
        return []

async def get_all_analytics_sessions(guild_id: str = None):
    """analytics_sessionsコレクションから全分析データを取得"""
    if db is None:
        print("⚠️ Firebase Firestoreが初期化されていません。")
        return []
    
    try:
        analytics_ref = db.collection('analytics_sessions')
        if guild_id:
            analytics_ref = analytics_ref.where('guildId', '==', guild_id)
        
        analytics_ref = analytics_ref.order_by('date', direction=firestore.Query.DESCENDING)
        
        docs = await asyncio.to_thread(analytics_ref.get)
        analytics = []
        for doc in docs:
            analytics_data = doc.to_dict()
            analytics_data['id'] = doc.id
            analytics.append(analytics_data)
        
        print(f"📊 分析データを取得: {len(analytics)}件")
        return analytics
    except Exception as e:
        print(f"❌ 分析データ取得エラー: {e}")
        return []

async def get_all_bot_actions(guild_id: str = None, limit: int = None):
    """bot_actionsコレクションから全ボットアクションデータを取得"""
    if db is None:
        print("⚠️ Firebase Firestoreが初期化されていません。")
        return []
    
    try:
        actions_ref = db.collection('bot_actions')
        if guild_id:
            actions_ref = actions_ref.where('guildId', '==', guild_id)
        
        actions_ref = actions_ref.order_by('timestamp', direction=firestore.Query.DESCENDING)
        
        if limit:
            actions_ref = actions_ref.limit(limit)
        
        docs = await asyncio.to_thread(actions_ref.get)
        actions = []
        for doc in docs:
            action_data = doc.to_dict()
            action_data['id'] = doc.id
            actions.append(action_data)
        
        print(f"📊 ボットアクションデータを取得: {len(actions)}件")
        return actions
    except Exception as e:
        print(f"❌ ボットアクションデータ取得エラー: {e}")
        return []

async def get_all_data(guild_id: str = None):
    """全コレクションからデータを取得してまとめて返す"""
    if db is None:
        print("⚠️ Firebase Firestoreが初期化されていません。")
        return {}
    
    print(f"📊 全データ取得を開始... (Guild ID: {guild_id or 'All'})")
    
    try:
        # 並行してデータを取得
        results = await asyncio.gather(
            get_all_users(guild_id),
            get_all_guilds() if not guild_id else asyncio.coroutine(lambda: [])(),
            get_all_interactions(guild_id, limit=1000),  # 最新1000件に制限
            get_all_topics(guild_id),
            get_all_podcasts(guild_id),
            get_all_user_matches(guild_id),
            get_all_events(guild_id),
            get_all_analytics_sessions(guild_id),
            get_all_bot_actions(guild_id, limit=500),  # 最新500件に制限
            return_exceptions=True
        )
        
        all_data = {
            'users': results[0] if not isinstance(results[0], Exception) else [],
            'guilds': results[1] if not isinstance(results[1], Exception) else [],
            'interactions': results[2] if not isinstance(results[2], Exception) else [],
            'topics': results[3] if not isinstance(results[3], Exception) else [],
            'podcasts': results[4] if not isinstance(results[4], Exception) else [],
            'user_matches': results[5] if not isinstance(results[5], Exception) else [],
            'events': results[6] if not isinstance(results[6], Exception) else [],
            'analytics_sessions': results[7] if not isinstance(results[7], Exception) else [],
            'bot_actions': results[8] if not isinstance(results[8], Exception) else [],
        }
        
        # 統計情報を表示
        total_records = sum(len(data) for data in all_data.values())
        print(f"✅ 全データ取得完了: 合計 {total_records} 件")
        print("📋 コレクション別件数:")
        for collection_name, data in all_data.items():
            print(f"   - {collection_name}: {len(data)}件")
        
        return all_data
        
    except Exception as e:
        print(f"❌ 全データ取得エラー: {e}")
        return {}

async def export_data_to_json(guild_id: str = None, filename: str = None):
    """全データをJSONファイルにエクスポート"""
    if not filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        guild_suffix = f"_guild_{guild_id}" if guild_id else "_all_guilds"
        filename = f"firestore_export{guild_suffix}_{timestamp}.json"
    
    print(f"📤 データエクスポートを開始: {filename}")
    
    try:
        all_data = await get_all_data(guild_id)
        
        # タイムスタンプとメタデータを追加
        export_data = {
            'metadata': {
                'exportedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'guildId': guild_id,
                'totalRecords': sum(len(data) for data in all_data.values()),
                'collections': list(all_data.keys())
            },
            'data': all_data
        }
        
        # JSONファイルに保存
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ データエクスポート完了: {filename}")
        print(f"📊 エクスポートされたレコード数: {export_data['metadata']['totalRecords']}件")
        return filename
        
    except Exception as e:
        print(f"❌ データエクスポートエラー: {e}")
        return None

# --- ボット起動処理 ---
# 注意: ボットの起動は run_bot.py から行います
# このファイルを直接実行する場合のみ以下のコードが実行されます
if __name__ == "__main__":
    print("⚠️ 警告: このファイルは直接実行せず、run_bot.py を使用してください")
    print("   python3 run_bot.py")
    exit(1)

# --- メンション応答処理関数 ---
async def handle_mention_response(message: discord.Message):
    """ボットがメンションされた時の応答処理"""
    try:
        # メンションを除いたメッセージ内容を取得
        content = message.content
        for mention in message.mentions:
            content = content.replace(f'<@{mention.id}>', '').replace(f'<@!{mention.id}>', '')
        content = content.strip()
        
        # ユーザー名を取得
        user_name = message.author.display_name or message.author.name
        
        # キーワードベースの応答選択
        response = await generate_response(content, user_name, message)
        
        # 応答を送信
        if response:
            await message.reply(response)
            
            # ボットアクションをFirestoreに記録
            await log_bot_action(message, response, 'mention_response')
            
    except Exception as e:
        print(f'❌ メンション応答エラー: {e}')
        # エラー時のフォールバック応答
        await message.reply("にゃーん？ちょっと調子が悪いみたいだにゃ... 🐱💦")

async def generate_response(content: str, user_name: str, message: discord.Message) -> str:
    """メッセージ内容に基づいて適切な応答を生成"""
    content_lower = content.lower()
    
    # 挨拶系
    if any(word in content_lower for word in ['こんにちは', 'おはよう', 'こんばんは', 'はじめまして', 'よろしく']):
        responses = [
            f"にゃーん！{user_name}さん、こんにちはだにゃ！ 🐱✨\n**トラにゃん**: 新しいお友達かにゃ？よろしくお願いしますにゃ！",
            f"こんにちはにゃ〜！{user_name}さん！ 🐱💫\n**クロにゃん**: みんなでお話しできて嬉しいにゃ〜！",
            f"にゃにゃ！{user_name}さん、ようこそにゃ！ 🐱🎉\n**トラにゃん**: このサーバーは楽しいことがいっぱいだにゃ！"
        ]
        return responses[hash(user_name) % len(responses)]
    
    # 質問・ヘルプ系
    elif any(word in content_lower for word in ['質問', '教えて', 'ヘルプ', 'help', '分からない', 'わからない']):
        responses = [
            f"にゃにゃ？{user_name}さん、何か困ったことがあるのかにゃ？ 🐱❓\n**クロにゃん**: みんなで助け合うのが一番だにゃ〜！",
            f"質問があるのかにゃ？{user_name}さん！ 🐱💭\n**トラにゃん**: 分からないことは恥ずかしくないにゃ！みんなで解決するにゃ！",
            f"にゃーん！{user_name}さん、どんなことで困ってるのかにゃ？ 🐱🤔\n**クロにゃん**: 詳しく教えてくれたら、みんなで考えるにゃ〜！"
        ]
        return responses[hash(content) % len(responses)]
    
    # 感謝系
    elif any(word in content_lower for word in ['ありがとう', 'ありがと', 'サンキュー', 'thanks']):
        responses = [
            f"にゃーん！{user_name}さん、どういたしましてにゃ！ 🐱💕\n**トラにゃん**: お役に立てて嬉しいにゃ〜！",
            f"にゃにゃ〜！{user_name}さんの笑顔が一番の報酬だにゃ！ 🐱😊\n**クロにゃん**: また何かあったら声をかけてにゃ〜！",
            f"にゃーん！{user_name}さん、こちらこそありがとうにゃ！ 🐱✨\n**トラにゃん**: みんなで支え合うのが大切だにゃ！"
        ]
        return responses[hash(user_name + content) % len(responses)]
    
    # イベント・活動系
    elif any(word in content_lower for word in ['イベント', 'event', '活動', '参加', '企画']):
        responses = [
            f"にゃにゃ！{user_name}さん、イベントに興味があるのかにゃ？ 🐱🎪\n**トラにゃん**: みんなで楽しいことをするのは最高だにゃ！",
            f"イベントの話かにゃ〜？{user_name}さん！ 🐱🎉\n**クロにゃん**: 新しい企画があったら教えてほしいにゃ〜！",
            f"にゃーん！{user_name}さん、一緒に楽しいことをするにゃ！ 🐱🌟\n**トラにゃん**: みんなの参加を待ってるにゃ〜！"
        ]
        return responses[hash(content + user_name) % len(responses)]
    
    # 一般的な応答
    else:
        responses = [
            f"にゃーん！{user_name}さん、お話ししてくれてありがとうにゃ！ 🐱💬\n**トラにゃん**: もっと詳しく聞かせてほしいにゃ〜！",
            f"にゃにゃ〜！{user_name}さんのお話、興味深いにゃ！ 🐱✨\n**クロにゃん**: みんなでお話しするの楽しいにゃ〜！",
            f"にゃーん！{user_name}さん、どんなことでも気軽に話しかけてにゃ！ 🐱😸\n**トラにゃん**: このコミュニティはみんな優しいにゃ！",
            f"にゃにゃ！{user_name}さん、今日はどんな一日だったかにゃ？ 🐱🌅\n**クロにゃん**: みんなの日常も聞いてみたいにゃ〜！"
        ]
        return responses[hash(content + user_name + str(message.created_at.hour)) % len(responses)]

async def log_bot_action(message: discord.Message, response: str, action_type: str):
    """ボットのアクションをFirestoreに記録"""
    if db is None:
        return
    
    try:
        guild_id = str(message.guild.id) if message.guild else None
        
        action_data = {
            'type': 'bot_action',
            'actionType': action_type,
            'userId': str(message.author.id),
            'username': message.author.display_name or message.author.name,
            'guildId': guild_id,
            'guildName': message.guild.name if message.guild else 'DM',
            'channelId': str(message.channel.id),
            'channelName': message.channel.name if hasattr(message.channel, 'name') else 'DM',
            'originalMessage': message.content,
            'botResponse': response,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'metadata': {
                'messageId': str(message.id),
                'responseLength': len(response)
            }
        }
        
        await asyncio.to_thread(db.collection('bot_actions').add, action_data)
        print(f"🤖 ボットアクションを記録: {action_type}")
        
    except Exception as e:
        print(f'❌ ボットアクション記録エラー: {e}')