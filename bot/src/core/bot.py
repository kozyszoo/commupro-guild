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
# 現在のスクリプトのディレクトリを基準にした絶対パスを設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_KEY_PATH = os.path.join(SCRIPT_DIR, 'nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json')
FIREBASE_SERVICE_ACCOUNT_KEY_PATH = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH', DEFAULT_KEY_PATH)

db = None # Firestoreクライアントをグローバル変数として定義

async def initialize_firebase():
    """Firebase Firestoreを初期化する関数"""
    global db
    print("🔧 Firebase初期化を開始...")
    
    try:
        if not firebase_admin._apps: # まだ初期化されていなければ初期化
            cred = None
            
            # 1. 環境変数のFIREBASE_SERVICE_ACCOUNT_KEY_PATHから読み込み
            env_key_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH')
            if env_key_path and os.path.exists(env_key_path):
                print(f"🔑 環境変数からFirebaseサービスアカウントキーファイルを読み込み中: {env_key_path}")
                cred = credentials.Certificate(env_key_path)
            
            # 2. デフォルトパスから読み込み
            elif os.path.exists(FIREBASE_SERVICE_ACCOUNT_KEY_PATH):
                print(f"🔑 デフォルトのFirebaseサービスアカウントキーファイルを読み込み中: {FIREBASE_SERVICE_ACCOUNT_KEY_PATH}")
                cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_KEY_PATH)
            
            # 3. 環境変数のFIREBASE_SERVICE_ACCOUNTから読み込み
            elif os.getenv('FIREBASE_SERVICE_ACCOUNT'):
                print("🔑 環境変数からFirebaseサービスアカウント情報を読み込み中...")
                service_account_info = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT'))
                cred = credentials.Certificate(service_account_info)
            
            # 4. 他の可能なパスを試行
            else:
                possible_paths = [
                    './nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json',
                    '../nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json',
                    os.path.join(os.getcwd(), 'nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json'),
                    os.path.join(os.getcwd(), 'bot', 'nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json')
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        print(f"🔑 代替パスからFirebaseサービスアカウントキーファイルを読み込み中: {path}")
                        cred = credentials.Certificate(path)
                        break
                
                if cred is None:
                    print("❌ デバッグ情報:")
                    print(f"   現在の作業ディレクトリ: {os.getcwd()}")
                    print(f"   スクリプトディレクトリ: {SCRIPT_DIR}")
                    print(f"   デフォルトキーパス: {FIREBASE_SERVICE_ACCOUNT_KEY_PATH}")
                    print(f"   環境変数FIREBASE_SERVICE_ACCOUNT_KEY_PATH: {env_key_path}")
                    print("   試行したパス:")
                    for path in possible_paths:
                        exists = "✅" if os.path.exists(path) else "❌"
                        print(f"     {exists} {path}")
                    raise FileNotFoundError("Firebaseサービスアカウントキーが見つかりません")
            
            firebase_admin.initialize_app(cred)
            print("✅ Firebase Admin SDKの初期化が完了しました")
        
        db = firestore.client() # Firestoreデータベースへの参照を取得
        print("✅ Firebase Firestoreへの接続準備ができました。")
        
        # 接続テストを実行
        try:
            test_ref = db.collection('_test').document('connection_test')
            await asyncio.to_thread(test_ref.set, {
                'timestamp': datetime.datetime.now(datetime.timezone.utc),
                'status': 'connected'
            })
            print("✅ Firestore接続テストが成功しました")
            # テストドキュメントを削除
            await asyncio.to_thread(test_ref.delete)
        except Exception as test_error:
            print(f"⚠️ Firestore接続テストに失敗しました: {test_error}")
        
        return True
        
    except FileNotFoundError as e:
        print(f"❌ 致命的エラー: Firebaseサービスアカウントキーファイルが見つかりません。")
        print(f"エラー詳細: {e}")
        return False
    except Exception as e:
        print(f"❌ 致命的エラー: Firebase Firestoreの初期化に失敗しました: {e}")
        print("サービスアカウントキーの内容や権限、ネットワーク接続を確認してください。")
        return False

# Firebase初期化（非同期で実行）
firebase_initialized = False

async def init_firebase_async():
    """Firebase初期化を非同期で実行"""
    global firebase_initialized
    firebase_initialized = await initialize_firebase()
    return firebase_initialized

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
        print(f"   スキップされたログタイプ: {interaction_data.get('type', 'unknown')}")
        return

    try:
        # サーバー側のタイムスタンプを追加




        
        interaction_data['timestamp'] = firestore.SERVER_TIMESTAMP
        
        # Firestoreへの書き込み
        doc_ref = await asyncio.to_thread(db.collection('interactions').add, interaction_data)
        
        # 成功ログ（デバッグ用）
        print(f"📝 インタラクションをFirestoreに記録: {interaction_data.get('type')} (ID: {doc_ref[1].id})")
        
    except Exception as e:
        print(f'❌ Firestoreへの書き込みエラー: {e}')
        print(f'❌ 書き込もうとしたデータタイプ: {interaction_data.get("type", "unknown")}')
        print(f'❌ ユーザーID: {interaction_data.get("userId", "unknown")}')
        print(f'❌ ギルドID: {interaction_data.get("guildId", "unknown")}')

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
        print(f"📅 イベント情報をFirestoreに保存: {event_data.get('name', 'イベント名不明')}")
        
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
    
    # Firebase初期化を実行
    if not firebase_initialized:
        print("🔧 Firebase初期化を実行中...")
        success = await init_firebase_async()
        if success:
            print("📝 ログ記録の準備ができました (Firestore)。")
        else:
            print("⚠️ Firebase Firestoreが初期化されていないため、ログ機能は動作しません。")
    else:
        print("📝 ログ記録の準備ができました (Firestore)。")
    
    # 参加しているすべてのギルドの情報を更新
    if firebase_initialized:
        for guild in bot.guilds:
            await update_guild_info(guild)
            # 日次分析セッションの作成
            await create_daily_analytics_session(str(guild.id))
        
        # バックグラウンドメンテナンスタスクを開始
        asyncio.create_task(schedule_maintenance())
        print("⏰ バックグラウンドメンテナンスタスクを開始しました")
    
    print('------')

# --- 各種イベントリスナー関数 ---

# メッセージが送信されたとき
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    
    try:
        # ギルド情報の取得
        guild_id, guild_name = get_guild_info_safe(message.guild)
        
        # チャンネル名の取得
        channel_name = get_channel_name_safe(message.channel)
        
        # ユーザー情報の取得
        user_name = get_user_name_safe(message.author)
        user_id = str(message.author.id)
        message_id = str(message.id)
        content = message.clean_content

        # ユーザー情報の更新
        if guild_id:
            await update_user_info(user_id, guild_id, user_name, 'MESSAGE_CREATE')

        # トピック人気度の更新
        keywords = extract_keywords(content)
        if guild_id and keywords:
            await update_topic_popularity(guild_id, keywords)

        # 管理者コマンドの処理
        if message.content.startswith('!nyanco'):
            await handle_admin_commands(message)
            return  # 管理者コマンドの場合は他の処理をスキップ

        # ボットがメンションされた場合の応答処理
        if bot.user in message.mentions:
            await handle_mention_response(message)

        # インタラクションデータの作成（拡張版）
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
            'keywords': keywords,  # 既に抽出済み
            'sentiment': 0.0,  # 今後実装予定
            'metadata': {
                'hasAttachments': len(message.attachments) > 0,
                'hasEmbeds': len(message.embeds) > 0,
                'mentionCount': len(message.mentions),
                'reactionCount': len(message.reactions) if message.reactions else 0,
                'isMention': bot.user in message.mentions,
                'channelType': type(message.channel).__name__,
                'messageLength': len(content),
                'hasCodeBlock': '```' in content,
                'hasLinks': 'http' in content.lower(),
                'isReply': message.reference is not None,
                'threadId': str(message.thread.id) if hasattr(message, 'thread') and message.thread else None
            }
        }
        
        asyncio.create_task(log_interaction_to_firestore(interaction_data))
        
    except Exception as e:
        print(f'❌ メッセージ処理エラー: {e}')
        print(f'   メッセージID: {getattr(message, "id", "unknown")}')
        print(f'   ユーザーID: {getattr(message.author, "id", "unknown") if hasattr(message, "author") else "unknown"}')

# メッセージが編集されたとき
@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if after.author.bot:
        return
    if before.content == after.content:
        return

    try:
        # ギルド情報の取得
        guild_id, guild_name = get_guild_info_safe(after.guild)
        
        # チャンネル名の取得
        channel_name = get_channel_name_safe(after.channel)
        
        # ユーザー情報の取得
        user_name = get_user_name_safe(after.author)
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
                'contentAfter': after.clean_content,
                'channelType': type(after.channel).__name__
            }
        }
        
        asyncio.create_task(log_interaction_to_firestore(interaction_data))
        
    except Exception as e:
        print(f'❌ メッセージ編集処理エラー: {e}')

# メッセージが削除されたとき
@bot.event
async def on_message_delete(message: discord.Message):
    if message.author.bot:
        return

    try:
        # ギルド情報の取得
        guild_id, guild_name = get_guild_info_safe(message.guild)
        
        # チャンネル名の取得
        channel_name = get_channel_name_safe(message.channel)
        
        # ユーザー情報の取得
        user_name = get_user_name_safe(message.author)
        user_id = str(message.author.id)
        content = message.clean_content if message.clean_content else "(コンテンツ取得不可)"

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
            'keywords': extract_keywords(content) if content != "(コンテンツ取得不可)" else [],
            'metadata': {
                'deletedContent': content,
                'channelType': type(message.channel).__name__
            }
        }
        
        asyncio.create_task(log_interaction_to_firestore(interaction_data))
        
    except Exception as e:
        print(f'❌ メッセージ削除処理エラー: {e}')

# メンバーがサーバーに参加したとき
@bot.event
async def on_member_join(member: discord.Member):
    try:
        guild_id = str(member.guild.id)
        user_name = get_user_name_safe(member)
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
                'roles': [role.name for role in member.roles if role.name != '@everyone'],
                'joinedAt': member.joined_at.isoformat() if member.joined_at else None
            }
        }
        
        asyncio.create_task(log_interaction_to_firestore(interaction_data))
        
    except Exception as e:
        print(f'❌ メンバー参加処理エラー: {e}')

# メンバーがサーバーから退出したとき
@bot.event
async def on_member_remove(member: discord.Member):
    try:
        guild_id = str(member.guild.id)
        user_name = get_user_name_safe(member)
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
                'roles': [role.name for role in member.roles if role.name != '@everyone'],
                'leftAt': datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        }
        
        asyncio.create_task(log_interaction_to_firestore(interaction_data))
        
    except Exception as e:
        print(f'❌ メンバー退出処理エラー: {e}')

# リアクションが追加されたとき
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return

    try:
        guild = bot.get_guild(payload.guild_id) if payload.guild_id else None
        guild_id, guild_name = get_guild_info_safe(guild)

        channel = bot.get_channel(payload.channel_id)
        channel_name = get_channel_name_safe(channel)

        user = bot.get_user(payload.user_id)
        user_name = get_user_name_safe(user)
        user_id = str(payload.user_id)

        # ユーザー情報の更新
        if guild_id and user:
            await update_user_info(user_id, guild_id, user_name, 'REACTION_ADD')

        # 絵文字情報の安全な取得
        emoji_name = getattr(payload.emoji, 'name', '絵文字名不明')
        emoji_id = str(payload.emoji.id) if hasattr(payload.emoji, 'id') and payload.emoji.id else None
        is_custom = hasattr(payload.emoji, 'is_custom_emoji') and payload.emoji.is_custom_emoji()

        interaction_data = {
            'type': 'reaction_add',
            'userId': user_id,
            'username': user_name,
            'guildId': guild_id,
            'guildName': guild_name,
            'channelId': str(payload.channel_id),
            'channelName': channel_name,
            'messageId': str(payload.message_id),
            'keywords': ['リアクション', emoji_name],
            'metadata': {
                'emojiName': emoji_name,
                'emojiId': emoji_id,
                'isCustomEmoji': is_custom,
                'channelType': type(channel).__name__ if channel else 'チャンネル不明'
            }
        }
        
        asyncio.create_task(log_interaction_to_firestore(interaction_data))
        
    except Exception as e:
        print(f'❌ リアクション追加処理エラー: {e}')

# リアクションが削除されたとき
@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return

    try:
        guild = bot.get_guild(payload.guild_id) if payload.guild_id else None
        guild_id, guild_name = get_guild_info_safe(guild)

        channel = bot.get_channel(payload.channel_id)
        channel_name = get_channel_name_safe(channel)

        user = bot.get_user(payload.user_id)
        user_name = get_user_name_safe(user)
        user_id = str(payload.user_id)

        # 絵文字情報の安全な取得
        emoji_name = getattr(payload.emoji, 'name', '絵文字名不明')
        emoji_id = str(payload.emoji.id) if hasattr(payload.emoji, 'id') and payload.emoji.id else None
        is_custom = hasattr(payload.emoji, 'is_custom_emoji') and payload.emoji.is_custom_emoji()

        interaction_data = {
            'type': 'reaction_remove',
            'userId': user_id,
            'username': user_name,
            'guildId': guild_id,
            'guildName': guild_name,
            'channelId': str(payload.channel_id),
            'channelName': channel_name,
            'messageId': str(payload.message_id),
            'keywords': ['リアクション削除', emoji_name],
            'metadata': {
                'emojiName': emoji_name,
                'emojiId': emoji_id,
                'isCustomEmoji': is_custom,
                'channelType': type(channel).__name__ if channel else 'チャンネル不明'
            }
        }
        
        asyncio.create_task(log_interaction_to_firestore(interaction_data))
        
    except Exception as e:
        print(f'❌ リアクション削除処理エラー: {e}')

# --- スケジュールイベント関連のリスナー ---

# スケジュールイベントが作成されたとき
@bot.event
async def on_scheduled_event_create(event: discord.ScheduledEvent):
    try:
        guild_id = str(event.guild.id)
        guild_name = event.guild.name
        creator_id = str(event.creator.id) if event.creator else None
        creator_name = get_user_name_safe(event.creator)

        # イベントステータス情報の安全な取得
        status_info = get_event_status_safe(event)

        # イベントデータの作成
        event_data = {
            'eventId': str(event.id),
            'name': event.name or 'イベント名不明',
            'description': event.description or '',
            'guildId': guild_id,
            'guildName': guild_name,
            'creatorId': creator_id,
            'creatorName': creator_name,
            'startTime': event.start_time.isoformat() if event.start_time else None,
            'endTime': event.end_time.isoformat() if event.end_time else None,
            'location': event.location or '',
            'status': status_info['status'],
            'entityType': status_info['entityType'],
            'privacyLevel': status_info['privacyLevel'],
            'userCount': event.user_count or 0,
            'createdAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'keywords': extract_keywords(f"{event.name or ''} {event.description or ''}"),
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
            'eventName': event.name or 'イベント名不明',
            'keywords': ['イベント作成', 'スケジュール'] + extract_keywords(event.name or ''),
            'metadata': {
                'eventDescription': event.description or '',
                'startTime': event.start_time.isoformat() if event.start_time else None,
                'endTime': event.end_time.isoformat() if event.end_time else None,
                'location': event.location or '',
                'entityType': status_info['entityType']
            }
        }

        asyncio.create_task(log_interaction_to_firestore(interaction_data))
        print(f"📅 新しいイベントが作成されました: {event.name or 'イベント名不明'}")
        
    except Exception as e:
        print(f'❌ イベント作成処理エラー: {e}')

# スケジュールイベントが更新されたとき
@bot.event
async def on_scheduled_event_update(before: discord.ScheduledEvent, after: discord.ScheduledEvent):
    try:
        guild_id = str(after.guild.id)
        guild_name = after.guild.name
        creator_id = str(after.creator.id) if after.creator else None
        creator_name = get_user_name_safe(after.creator)

        # イベントステータス情報の安全な取得
        status_info = get_event_status_safe(after)

        # 更新されたイベントデータ
        event_data = {
            'eventId': str(after.id),
            'name': after.name or 'イベント名不明',
            'description': after.description or '',
            'guildId': guild_id,
            'guildName': guild_name,
            'creatorId': creator_id,
            'creatorName': creator_name,
            'startTime': after.start_time.isoformat() if after.start_time else None,
            'endTime': after.end_time.isoformat() if after.end_time else None,
            'location': after.location or '',
            'status': status_info['status'],
            'entityType': status_info['entityType'],
            'privacyLevel': status_info['privacyLevel'],
            'userCount': after.user_count or 0,
            'createdAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'keywords': extract_keywords(f"{after.name or ''} {after.description or ''}"),
            'isActive': True
        }

        # Firestoreに更新保存
        await save_event_to_firestore(event_data)

        # 変更内容を記録
        changes = []
        if before.name != after.name:
            changes.append(f"名前: {before.name or '(なし)'} → {after.name or '(なし)'}")
        if before.description != after.description:
            changes.append(f"説明: {before.description or '(なし)'} → {after.description or '(なし)'}")
        if before.start_time != after.start_time:
            changes.append(f"開始時間: {before.start_time} → {after.start_time}")
        
        # ステータス変更の安全な記録
        before_status = get_event_status_safe(before)
        after_status = get_event_status_safe(after)
        if before_status['status'] != after_status['status']:
            changes.append(f"ステータス: {before_status['status']} → {after_status['status']}")

        # インタラクションとしても記録
        interaction_data = {
            'type': 'scheduled_event_update',
            'userId': creator_id,
            'username': creator_name,
            'guildId': guild_id,
            'guildName': guild_name,
            'eventId': str(after.id),
            'eventName': after.name or 'イベント名不明',
            'keywords': ['イベント更新', 'スケジュール変更'] + extract_keywords(after.name or ''),
            'metadata': {
                'changes': changes,
                'beforeStatus': before_status['status'],
                'afterStatus': after_status['status'],
                'eventDescription': after.description or '',
                'startTime': after.start_time.isoformat() if after.start_time else None,
                'endTime': after.end_time.isoformat() if after.end_time else None
            }
        }

        asyncio.create_task(log_interaction_to_firestore(interaction_data))
        print(f"📅 イベントが更新されました: {after.name or 'イベント名不明'} ({len(changes)}件の変更)")
        
    except Exception as e:
        print(f'❌ イベント更新処理エラー: {e}')

# スケジュールイベントが削除されたとき
@bot.event
async def on_scheduled_event_delete(event: discord.ScheduledEvent):
    try:
        guild_id = str(event.guild.id)
        guild_name = event.guild.name
        creator_id = str(event.creator.id) if event.creator else None
        creator_name = get_user_name_safe(event.creator)

        # イベントステータス情報の安全な取得
        status_info = get_event_status_safe(event)

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
            'eventName': event.name or 'イベント名不明',
            'keywords': ['イベント削除', 'スケジュール削除'] + extract_keywords(event.name or ''),
            'metadata': {
                'eventDescription': event.description or '',
                'startTime': event.start_time.isoformat() if event.start_time else None,
                'endTime': event.end_time.isoformat() if event.end_time else None,
                'location': event.location or '',
                'finalStatus': status_info['status'],
                'userCount': event.user_count or 0
            }
        }

        asyncio.create_task(log_interaction_to_firestore(interaction_data))
        print(f"🗑️ イベントが削除されました: {event.name or 'イベント名不明'}")
        
    except Exception as e:
        print(f'❌ イベント削除処理エラー: {e}')

# ユーザーがスケジュールイベントに参加したとき
@bot.event
async def on_scheduled_event_user_add(event: discord.ScheduledEvent, user: discord.User):
    try:
        guild_id = str(event.guild.id)
        guild_name = event.guild.name
        user_id = str(user.id)
        user_name = get_user_name_safe(user)

        # ユーザー情報の更新（イベント参加でエンゲージメントスコア+2）
        await update_user_info(user_id, guild_id, user_name, 'EVENT_JOIN')

        # ユーザーマッチングの実行（イベント参加時は良いタイミング）
        await find_user_matches(guild_id, user_id)

        # イベントステータス情報の安全な取得
        status_info = get_event_status_safe(event)

        # インタラクションとして記録
        interaction_data = {
            'type': 'scheduled_event_user_add',
            'userId': user_id,
            'username': user_name,
            'guildId': guild_id,
            'guildName': guild_name,
            'eventId': str(event.id),
            'eventName': event.name or 'イベント名不明',
            'keywords': ['イベント参加', 'スケジュール参加'] + extract_keywords(event.name or ''),
            'metadata': {
                'eventDescription': event.description or '',
                'startTime': event.start_time.isoformat() if event.start_time else None,
                'eventStatus': status_info['status'],
                'currentUserCount': event.user_count or 0
            }
        }

        asyncio.create_task(log_interaction_to_firestore(interaction_data))
        print(f"👥 {user_name} がイベント '{event.name or 'イベント名不明'}' に参加しました")
        
    except Exception as e:
        print(f'❌ イベント参加処理エラー: {e}')

# ユーザーがスケジュールイベントから退出したとき
@bot.event
async def on_scheduled_event_user_remove(event: discord.ScheduledEvent, user: discord.User):
    try:
        guild_id = str(event.guild.id)
        guild_name = event.guild.name
        user_id = str(user.id)
        user_name = get_user_name_safe(user)

        # イベントステータス情報の安全な取得
        status_info = get_event_status_safe(event)

        # インタラクションとして記録
        interaction_data = {
            'type': 'scheduled_event_user_remove',
            'userId': user_id,
            'username': user_name,
            'guildId': guild_id,
            'guildName': guild_name,
            'eventId': str(event.id),
            'eventName': event.name or 'イベント名不明',
            'keywords': ['イベント退出', 'スケジュール退出'] + extract_keywords(event.name or ''),
            'metadata': {
                'eventDescription': event.description or '',
                'startTime': event.start_time.isoformat() if event.start_time else None,
                'eventStatus': status_info['status'],
                'currentUserCount': event.user_count or 0
            }
        }

        asyncio.create_task(log_interaction_to_firestore(interaction_data))
        print(f"👋 {user_name} がイベント '{event.name or 'イベント名不明'}' から退出しました")
        
    except Exception as e:
        print(f'❌ イベント退出処理エラー: {e}')

# --- ユーティリティ関数 ---
def get_channel_name_safe(channel) -> str:
    """チャンネル名を安全に取得する関数"""
    try:
        if channel is None:
            return 'チャンネル不明'
        
        if isinstance(channel, discord.TextChannel):
            return f"#{channel.name}"
        elif isinstance(channel, discord.VoiceChannel):
            return f"🔊{channel.name}"
        elif isinstance(channel, discord.Thread):
            parent_name = channel.parent.name if channel.parent else "不明"
            return f"🧵{channel.name} (in #{parent_name})"
        elif isinstance(channel, discord.DMChannel):
            if channel.recipient:
                return f"DM with {channel.recipient.display_name or channel.recipient.name}"
            else:
                return "DM (相手不明)"
        elif isinstance(channel, discord.GroupChannel):
            return f"グループDM: {channel.name or 'グループチャット'}"
        elif isinstance(channel, discord.CategoryChannel):
            return f"📁{channel.name}"
        elif isinstance(channel, discord.StageChannel):
            return f"🎤{channel.name}"
        elif isinstance(channel, discord.ForumChannel):
            return f"💬{channel.name}"
        else:
            # その他のチャンネルタイプ
            return f"{type(channel).__name__}: {getattr(channel, 'name', 'チャンネル名不明')}"
    except Exception as e:
        print(f"⚠️ チャンネル名取得エラー: {e}")
        return f"チャンネル取得エラー (ID: {getattr(channel, 'id', 'unknown')})"

def get_user_name_safe(user) -> str:
    """ユーザー名を安全に取得する関数"""
    try:
        if user is None:
            return 'ユーザー不明'
        
        # display_nameを優先し、なければnameを使用
        if hasattr(user, 'display_name') and user.display_name:
            return user.display_name
        elif hasattr(user, 'name') and user.name:
            return user.name
        elif hasattr(user, 'global_name') and user.global_name:
            return user.global_name
        else:
            return f"ユーザー名不明 (ID: {getattr(user, 'id', 'unknown')})"
    except Exception as e:
        print(f"⚠️ ユーザー名取得エラー: {e}")
        return f"ユーザー名取得エラー (ID: {getattr(user, 'id', 'unknown')})"

def get_guild_info_safe(guild) -> tuple:
    """ギルド情報を安全に取得する関数"""
    try:
        if guild is None:
            return None, 'DM'
        
        guild_id = str(guild.id)
        guild_name = guild.name or f"サーバー名不明 (ID: {guild_id})"
        return guild_id, guild_name
    except Exception as e:
        print(f"⚠️ ギルド情報取得エラー: {e}")
        return None, 'ギルド情報取得エラー'

def get_event_status_safe(event) -> dict:
    """イベントのステータス情報を安全に取得する関数"""
    try:
        status_info = {}
        
        # ステータス
        if hasattr(event, 'status') and event.status:
            status_info['status'] = event.status.name
        else:
            status_info['status'] = 'ステータス不明'
        
        # エンティティタイプ
        if hasattr(event, 'entity_type') and event.entity_type:
            status_info['entityType'] = event.entity_type.name
        else:
            status_info['entityType'] = 'タイプ不明'
        
        # プライバシーレベル
        if hasattr(event, 'privacy_level') and event.privacy_level:
            status_info['privacyLevel'] = event.privacy_level.name
        else:
            status_info['privacyLevel'] = 'プライバシー設定不明'
        
        return status_info
    except Exception as e:
        print(f"⚠️ イベントステータス取得エラー: {e}")
        return {
            'status': 'ステータス取得エラー',
            'entityType': 'タイプ取得エラー',
            'privacyLevel': 'プライバシー取得エラー'
        }

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
    keywords = [word for word, _ in word_counts.most_common()]
    
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

# --- 定期実行タスク ---
async def daily_maintenance_task():
    """日次メンテナンスタスクを実行する"""
    if not firebase_initialized:
        return
    
    try:
        print("🔄 日次メンテナンスタスクを開始...")
        
        for guild in bot.guilds:
            guild_id = str(guild.id)
            
            # 日次分析セッションの作成
            await create_daily_analytics_session(guild_id)
            
            # ユーザーマッチングの実行
            await find_user_matches(guild_id)
            
            # エンゲージメント分析の生成
            insights = await generate_engagement_insights(guild_id, 7)
            if insights:
                print(f"📊 {guild.name} のエンゲージメント分析完了")
        
        print("✅ 日次メンテナンスタスク完了")
        
    except Exception as e:
        print(f"❌ 日次メンテナンスタスクエラー: {e}")

# スケジュール実行用のバックグラウンドタスク
async def schedule_maintenance():
    """メンテナンスタスクのスケジュール実行"""
    import asyncio
    
    while True:
        try:
            # 毎日午前2時に実行（UTC）
            now = datetime.datetime.now(datetime.timezone.utc)
            target_time = now.replace(hour=2, minute=0, second=0, microsecond=0)
            
            # 今日の2時が過ぎていれば明日の2時に設定
            if now > target_time:
                target_time += datetime.timedelta(days=1)
            
            wait_seconds = (target_time - now).total_seconds()
            print(f"⏰ 次回メンテナンスまで {wait_seconds/3600:.1f}時間")
            
            await asyncio.sleep(wait_seconds)
            await daily_maintenance_task()
            
        except Exception as e:
            print(f"❌ スケジュール実行エラー: {e}")
            # エラー時は1時間後に再試行
            await asyncio.sleep(3600)

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
            # 高度なボットアクション記録
            guild_id = str(message.guild.id) if message.guild else None
            if guild_id:
                payload = {
                    'character': detect_character_from_mention(message.content),
                    'responseType': 'mention_response',
                    'originalMessage': message.content,
                    'responseMessage': response,
                    'confidence': 0.8,  # 固定値（今後動的に設定可能）
                    'messageLength': len(response)
                }
                await log_advanced_bot_action(guild_id, str(message.author.id), 'mention_response', payload, str(message.id))
            
    except Exception as e:
        print(f'❌ メンション応答エラー: {e}')
        # エラー時のフォールバック応答
        await message.reply("にゃーん？ちょっと調子が悪いみたいだにゃ... 🐱💦")

def detect_character_from_mention(content: str) -> str:
    """メンション内容からキャラクターを判定"""
    content_lower = content.lower()
    
    # みやにゃん関連のキーワード
    miya_keywords = ['みやにゃん', 'miya', '技術', 'プログラミング', 'コード', 'チュートリアル', 'ヘルプ', '進捗', '統計']
    
    # イヴにゃん関連のキーワード
    eve_keywords = ['イヴにゃん', 'eve', 'データ', '分析', '統計', 'レポート']
    
    # キーワードマッチング
    miya_score = sum(1 for keyword in miya_keywords if keyword in content_lower)
    eve_score = sum(1 for keyword in eve_keywords if keyword in content_lower)
    
    if miya_score > eve_score:
        return 'miya'
    elif eve_score > miya_score:
        return 'eve'
    else:
        # デフォルトはランダム（ユーザー名のハッシュ値で決定）
        return 'miya' if hash(content) % 2 == 0 else 'eve'

async def generate_response(content: str, user_name: str, message: discord.Message) -> str:
    """メッセージ内容に基づいて適切な応答を生成（みやにゃん・イヴにゃん仕様）"""
    content_lower = content.lower()
    
    # キャラクターを判定
    character = detect_character_from_mention(content)
    
    # キャラクター別の基本設定
    if character == 'miya':
        char_emoji = '🐈'
    else:  # eve
        char_emoji = '🐱'
    
    # 挨拶系
    if any(word in content_lower for word in ['こんにちは', 'おはよう', 'こんばんは', 'はじめまして', 'よろしく']):
        if character == 'miya':
            responses = [
                f"{char_emoji} {user_name}さん、こんにちはだにゃ！新しい技術の話ができて嬉しいにゃ〜",
                f"{char_emoji} にゃーん！{user_name}さん、ようこそですにゃ！プログラミングのことなら何でも聞いてにゃ〜",
                f"{char_emoji} {user_name}さん、よろしくお願いしますにゃ！一緒にコードを書いたり学んだりしましょうにゃ〜"
            ]
        else:  # eve
            responses = [
                f"{char_emoji} {user_name}さん、こんにちはですにゃ。データ分析のお手伝いができるのですにゃ",
                f"{char_emoji} {user_name}さん、はじめましてですにゃ。統計やレポート作成が得意なのにゃ",
                f"{char_emoji} よろしくお願いしますにゃ、{user_name}さん。論理的に問題を解決していきましょうにゃ"
            ]
        return responses[hash(user_name) % len(responses)]
    
    # 技術・プログラミング系（みやにゃん専門）
    elif any(word in content_lower for word in ['技術', 'プログラミング', 'コード', 'code', 'プログラム', '開発', 'dev']):
        if character == 'miya':
            responses = [
                f"{char_emoji} おお！{user_name}さん、技術の話だにゃ〜！どんなプログラミング言語を使ってるのかにゃ？",
                f"{char_emoji} {user_name}さん、コードの話は大好きだにゃ！一緒に新しい技術を学びましょうにゃ〜",
                f"{char_emoji} 技術的な質問だにゃ？{user_name}さん、詳しく教えてくださいにゃ〜！実装方法も一緒に考えるにゃ！"
            ]
        else:  # eve
            responses = [
                f"{char_emoji} {user_name}さん、技術的な統計分析でしょうかにゃ？データドリブンなアプローチが重要ですにゃ",
                f"{char_emoji} プログラミングのパフォーマンス分析などでしたら、データを見て改善提案ができますにゃ",
                f"{char_emoji} {user_name}さん、コードの効率性やバグの傾向分析などは得意分野ですにゃ"
            ]
        return responses[hash(content) % len(responses)]
    
    # データ・分析系（イヴにゃん専門）
    elif any(word in content_lower for word in ['データ', '分析', '統計', 'data', 'analytics', 'レポート', 'report']):
        if character == 'eve':
            responses = [
                f"{char_emoji} {user_name}さん、データ分析のご依頼ですにゃ？どのようなデータを分析したいのですかにゃ？",
                f"{char_emoji} 統計分析でしたら私の得意分野ですにゃ。{user_name}さん、具体的な要件を教えてくださいにゃ",
                f"{char_emoji} {user_name}さん、レポート作成も承りますにゃ。客観的で論理的な分析結果をお出しできますにゃ"
            ]
        else:  # miya
            responses = [
                f"{char_emoji} {user_name}さん、データ分析かにゃ？イヴにゃんの方が詳しいにゃ〜でも技術的な実装なら手伝えるにゃ！",
                f"{char_emoji} 分析ツールの使い方とかなら教えられるにゃ〜！{user_name}さん、どんなデータを扱うのかにゃ？",
                f"{char_emoji} {user_name}さん、統計はイヴにゃんが専門だにゃ〜でも分析用のコードを書くのは得意だにゃ！"
            ]
        return responses[hash(content) % len(responses)]
    
    # 質問・ヘルプ系
    elif any(word in content_lower for word in ['質問', '教えて', 'ヘルプ', 'help', '分からない', 'わからない']):
        if character == 'miya':
            responses = [
                f"{char_emoji} {user_name}さん、何か困ったことがあるのかにゃ？技術的なサポートは任せてにゃ〜！",
                f"{char_emoji} 質問大歓迎だにゃ！{user_name}さん、どんなことでも一緒に解決していきましょうにゃ〜",
                f"{char_emoji} {user_name}さん、チュートリアルが必要かにゃ？ステップバイステップで説明するにゃ〜！"
            ]
        else:  # eve
            responses = [
                f"{char_emoji} {user_name}さん、どのような問題でお困りですかにゃ？データに基づいて解決策を考えましょうにゃ",
                f"{char_emoji} 質問をありがとうございますにゃ。{user_name}さん、論理的に整理して回答いたしますにゃ",
                f"{char_emoji} {user_name}さん、具体的な状況を教えていただければ、分析的にアプローチできますにゃ"
            ]
        return responses[hash(content) % len(responses)]
    
    # 感謝系
    elif any(word in content_lower for word in ['ありがとう', 'ありがと', 'サンキュー', 'thanks']):
        if character == 'miya':
            responses = [
                f"{char_emoji} {user_name}さん、どういたしましてだにゃ〜！お役に立てて嬉しいにゃ！",
                f"{char_emoji} にゃーん！{user_name}さんの笑顔が一番の報酬だにゃ〜また何でも聞いてにゃ！",
                f"{char_emoji} {user_name}さん、こちらこそありがとうにゃ〜！一緒に学べて楽しいにゃ！"
            ]
        else:  # eve
            responses = [
                f"{char_emoji} {user_name}さん、どういたしましてですにゃ。お役に立てて光栄ですにゃ",
                f"{char_emoji} いえいえ、{user_name}さん。効率的に問題解決できて満足ですにゃ",
                f"{char_emoji} {user_name}さん、論理的なサポートができて嬉しいですにゃ"
            ]
        return responses[hash(user_name + content) % len(responses)]
    
    # イベント・活動系
    elif any(word in content_lower for word in ['イベント', 'event', '活動', '参加', '企画']):
        if character == 'miya':
            responses = [
                f"{char_emoji} {user_name}さん、イベント企画かにゃ？技術勉強会とかハッカソンとか楽しそうだにゃ〜！",
                f"{char_emoji} イベントの話だにゃ！{user_name}さん、みんなで新しいことを学ぶのは最高だにゃ〜",
                f"{char_emoji} {user_name}さん、コミュニティ活動は大切だにゃ〜！一緒に盛り上げていこうにゃ！"
            ]
        else:  # eve
            responses = [
                f"{char_emoji} {user_name}さん、イベントの効果測定や参加者分析などでしたらお任せくださいにゃ",
                f"{char_emoji} イベント企画ですかにゃ？{user_name}さん、データに基づいた企画立案をサポートできますにゃ",
                f"{char_emoji} {user_name}さん、過去のイベント実績を分析して改善提案もできますにゃ"
            ]
        return responses[hash(content + user_name) % len(responses)]
    
    # 一般的な応答
    else:
        if character == 'miya':
            responses = [
                f"{char_emoji} {user_name}さん、お話ししてくれてありがとうにゃ〜！もっと詳しく聞かせてほしいにゃ！",
                f"{char_emoji} にゃにゃ〜！{user_name}さんのお話、興味深いにゃ！技術的なことでも雑談でも大歓迎だにゃ〜",
                f"{char_emoji} {user_name}さん、このコミュニティはみんな優しくて技術好きが多いにゃ〜！",
                f"{char_emoji} {user_name}さん、今日は何か新しいことを学んだかにゃ？みんなの学習記録も聞いてみたいにゃ〜！"
            ]
        else:  # eve
            responses = [
                f"{char_emoji} {user_name}さん、お話をありがとうございますにゃ。データ的に興味深い内容ですにゃ",
                f"{char_emoji} {user_name}さんの観点は論理的で素晴らしいですにゃ。もう少し詳細を聞かせてくださいにゃ",
                f"{char_emoji} {user_name}さん、客観的な視点からコメントさせていただくと興味深い話題ですにゃ",
                f"{char_emoji} {user_name}さん、今日のコミュニティ活動の分析結果はいかがでしたかにゃ？"
            ]
        return responses[hash(content + user_name + str(message.created_at.hour)) % len(responses)]

# --- 管理者コマンド処理 ---
async def handle_admin_commands(message: discord.Message):
    """管理者向けのコマンドを処理する"""
    if not message.content.startswith('!nyanco'):
        return
    
    guild_id = str(message.guild.id) if message.guild else None
    if not guild_id:
        return
    
    content = message.content[8:].strip()  # '!nyanco ' の部分を除去
    
    try:
        if content == 'analytics':
            # エンゲージメント分析の実行
            insights = await generate_engagement_insights(guild_id, 7)
            if insights:
                summary = insights['summary']
                response = f"📊 **過去7日間の分析結果**\n"
                response += f"• 総インタラクション数: {summary['totalInteractions']}\n"
                response += f"• アクティブユーザー数: {summary['activeUsers']}\n"
                response += f"• 1日平均: {summary['averageInteractionsPerDay']:.1f}インタラクション\n"
                response += f"• 人気キーワード: {', '.join(list(insights['topKeywords'].keys())[:5])}"
                await message.reply(response)
            else:
                await message.reply("❌ 分析データの取得に失敗しました")
        
        elif content == 'matching':
            # ユーザーマッチングの実行
            matches = await find_user_matches(guild_id)
            if matches:
                response = f"🤝 **新しいマッチング結果**\n"
                for match in matches[:3]:  # 最大3件表示
                    response += f"• {match['metadata']['user1Name']} ↔ {match['metadata']['user2Name']} "
                    response += f"(スコア: {match['matchScore']:.2f})\n"
                    response += f"  共通関心事: {', '.join(match['commonInterests'][:3])}\n"
                await message.reply(response)
            else:
                await message.reply("🤝 新しいマッチングは見つかりませんでした")
        
        elif content == 'daily':
            # 日次分析の実行
            analytics = await create_daily_analytics_session(guild_id)
            if analytics:
                response = f"📈 **本日の統計**\n"
                response += f"• アクティブユーザー: {analytics['activeUsers']}人\n"
                response += f"• メッセージ数: {analytics['messageCount']}\n"
                response += f"• 新規メンバー: {analytics['newMembers']}人\n"
                top_topics = list(analytics['topTopics'].keys())[:3]
                if top_topics:
                    response += f"• 人気トピック: {', '.join(top_topics)}"
                await message.reply(response)
            else:
                await message.reply("❌ 日次分析の作成に失敗しました")
        
        elif content.startswith('export'):
            # データエクスポート
            filename = await export_data_to_json(guild_id)
            if filename:
                await message.reply(f"📤 データエクスポート完了: `{filename}`")
            else:
                await message.reply("❌ データエクスポートに失敗しました")
        
        else:
            help_text = """🤖 **にゃんこボット管理コマンド**
`!nyanco analytics` - 過去7日間の分析結果を表示
`!nyanco matching` - ユーザーマッチングを実行
`!nyanco daily` - 本日の統計を表示
`!nyanco export` - データをエクスポート"""
            await message.reply(help_text)
    
    except Exception as e:
        print(f"❌ 管理者コマンド処理エラー: {e}")
        await message.reply("❌ コマンドの実行中にエラーが発生しました")

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

# --- ギルド情報をFirestoreに保存/更新する関数 ---
async def update_guild_info(guild: discord.Guild):
    """ギルド情報をFirestoreのguildsコレクションに保存/更新する"""
    if db is None:
        return
    
    try:
        guild_id = str(guild.id)
        guild_ref = db.collection('guilds').document(guild_id)
        guild_doc = await asyncio.to_thread(guild_ref.get)
        
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
        # デフォルトのボット設定
        default_bot_settings = {
            'traNyanPersonality': {
                'energyLevel': 0.8,
                'friendliness': 0.9,
                'endPhrases': ['だにゃ', 'にゃ', 'にゃ〜'],
                'customMessages': {
                    'welcome': 'ようこそだにゃ！一緒に楽しくお話ししよう！',
                    'reengagement': '久しぶりだにゃ！待ってたにゃ〜'
                }
            },
            'kuroNyanPersonality': {
                'analyticalLevel': 0.85,
                'helpfulness': 0.75,
                'endPhrases': ['のにゃ', 'ですにゃ', 'にゃ'],
                'customMessages': {
                    'analysis': 'データを分析してみたのにゃ。',
                    'recommendation': 'こちらがおすすめですにゃ。'
                }
            },
            'podcastFrequency': '0 18 * * MON',  # 毎週月曜日18時
            'inactiveThreshold': 14,  # 14日間非アクティブで判定
            'reengagementFrequency': 3,  # 3日間隔
            'maxReengagementAttempts': 3,
            'matchingEnabled': True,
            'matchingThreshold': 0.7,
            'analyticsEnabled': True
        }
        
        if guild_doc.exists:
            # 既存ギルドの更新
            update_data = {
                'name': guild.name,
                'ownerId': str(guild.owner_id) if guild.owner_id else None,
                'updatedAt': current_time.isoformat(),
                'analytics': {
                    'totalMembers': guild.member_count or 0,
                    'lastUpdated': current_time.isoformat()
                }
            }
            await asyncio.to_thread(guild_ref.update, update_data)
            print(f"📝 ギルド情報を更新: {guild.name}")
        else:
            # 新規ギルドの作成
            guild_data = {
                'id': guild_id,
                'name': guild.name,
                'ownerId': str(guild.owner_id) if guild.owner_id else None,
                'botSettings': default_bot_settings,
                'welcomeChannelId': None,
                'podcastChannelId': None,
                'createdAt': current_time.isoformat(),
                'updatedAt': current_time.isoformat(),
                'analytics': {
                    'totalMembers': guild.member_count or 0,
                    'activeMembers': 0,
                    'averageEngagement': 0.0,
                    'topChannels': [],
                    'lastUpdated': current_time.isoformat()
                }
            }
            await asyncio.to_thread(guild_ref.set, guild_data)
            print(f"📝 新規ギルド情報を作成: {guild.name}")
            
    except Exception as e:
        print(f'❌ ギルド情報更新エラー: {e}')

# --- トピック管理機能 ---
async def update_topic_popularity(guild_id: str, keywords: list):
    """キーワードからトピックの人気度を更新する"""
    if db is None or not keywords:
        return
    
    try:
        for keyword in keywords:
            if len(keyword) < 2:  # 短いキーワードはスキップ
                continue
                
            # トピック検索または作成
            topic_id = f"topic_{keyword.lower()}_{guild_id}"
            topic_ref = db.collection('topics').document(topic_id)
            topic_doc = await asyncio.to_thread(topic_ref.get)
            
            current_time = datetime.datetime.now(datetime.timezone.utc)
            
            if topic_doc.exists:
                # 既存トピックの更新
                topic_data = topic_doc.to_dict()
                current_popularity = topic_data.get('popularity', 0)
                mention_count = topic_data.get('mentionCount', 0)
                
                # 人気度スコアの更新（減衰を考慮）
                new_popularity = min(100, current_popularity * 0.99 + 1.5)  # 減衰 + 新規言及
                
                update_data = {
                    'popularity': new_popularity,
                    'mentionCount': mention_count + 1,
                    'updatedAt': current_time.isoformat(),
                    'lastMentioned': current_time.isoformat()
                }
                await asyncio.to_thread(topic_ref.update, update_data)
            else:
                # 新規トピックの作成
                topic_data = {
                    'id': topic_id,
                    'guildId': guild_id,
                    'name': keyword,
                    'keywords': [keyword.lower()],
                    'channelIds': [],
                    'popularity': 1.0,
                    'trendScore': 1.0,
                    'mentionCount': 1,
                    'uniqueUsers': [],  # setはJSONシリアライズ不可のため配列に変更
                    'createdAt': current_time.isoformat(),
                    'updatedAt': current_time.isoformat(),
                    'lastMentioned': current_time.isoformat(),
                    'relatedTopics': {}
                }
                await asyncio.to_thread(topic_ref.set, topic_data)
                print(f"📈 新規トピック作成: {keyword}")
                
    except Exception as e:
        print(f'❌ トピック更新エラー: {e}')

# --- 日次分析セッション管理 ---
async def create_daily_analytics_session(guild_id: str):
    """日次分析セッションを作成・更新する"""
    if db is None:
        return
    
    try:
        today = datetime.datetime.now(datetime.timezone.utc).date()
        session_id = f"analytics_{today.strftime('%Y%m%d')}_{guild_id}"
        
        # 今日のインタラクション数を集計
        interactions_ref = db.collection('interactions')
        today_start = datetime.datetime.combine(today, datetime.time.min, datetime.timezone.utc)
        today_end = today_start + datetime.timedelta(days=1)
        
        # 今日のデータを取得
        today_interactions = await asyncio.to_thread(
            interactions_ref
            .where('guildId', '==', guild_id)
            .where('timestamp', '>=', today_start)
            .where('timestamp', '<', today_end)
            .get
        )
        
        # 統計データの集計
        message_count = 0
        active_users = set()
        channel_activity = {}
        topic_mentions = {}
        
        for doc in today_interactions:
            interaction = doc.to_dict()
            
            if interaction.get('type') == 'message':
                message_count += 1
                
            user_id = interaction.get('userId')
            if user_id:
                active_users.add(user_id)
                
            channel_name = interaction.get('channelName', 'unknown')
            channel_activity[channel_name] = channel_activity.get(channel_name, 0) + 1
            
            # キーワード集計
            keywords = interaction.get('keywords', [])
            for keyword in keywords:
                topic_mentions[keyword] = topic_mentions.get(keyword, 0) + 1
        
        # 新規メンバー数の取得
        new_members_today = await asyncio.to_thread(
            interactions_ref
            .where('guildId', '==', guild_id)
            .where('type', '==', 'member_join')
            .where('timestamp', '>=', today_start)
            .where('timestamp', '<', today_end)
            .get
        )
        
        # 分析データの作成
        analytics_data = {
            'id': session_id,
            'guildId': guild_id,
            'date': today.strftime('%Y-%m-%d'),
            'activeUsers': len(active_users),
            'messageCount': message_count,
            'newMembers': len(new_members_today),
            'reengagements': 0,  # 今後実装
            'topTopics': dict(sorted(topic_mentions.items(), key=lambda x: x[1], reverse=True)[:10]),
            'channelActivity': dict(sorted(channel_activity.items(), key=lambda x: x[1], reverse=True)[:10]),
            'createdAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'metadata': {
                'totalInteractions': len(today_interactions),
                'uniqueChannels': len(channel_activity),
                'topicVariety': len(topic_mentions)
            }
        }
        
        # Firestoreに保存
        analytics_ref = db.collection('analytics_sessions').document(session_id)
        await asyncio.to_thread(analytics_ref.set, analytics_data, merge=True)
        
        print(f"📊 日次分析セッション作成: {today.strftime('%Y-%m-%d')} ({len(active_users)}人アクティブ)")
        return analytics_data
        
    except Exception as e:
        print(f'❌ 日次分析セッション作成エラー: {e}')
        return None

# --- ユーザーマッチング機能 ---
async def find_user_matches(guild_id: str, user_id: str = None):
    """ユーザーマッチングを実行する"""
    if db is None:
        return []
    
    try:
        # アクティブユーザーの取得
        users_ref = db.collection('users').where('guildId', '==', guild_id).where('isActive', '==', True)
        users_docs = await asyncio.to_thread(users_ref.get)
        
        users = []
        for doc in users_docs:
            user_data = doc.to_dict()
            user_data['id'] = doc.id
            users.append(user_data)
        
        if len(users) < 2:
            return []
        
        matches = []
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
        # 対象ユーザーを決定
        target_users = [u for u in users if u['id'] == user_id] if user_id else users
        
        for user in target_users:
            user_interests = set(user.get('interests', []))
            if not user_interests:
                continue
                
            for other_user in users:
                if user['id'] == other_user['id']:
                    continue
                    
                other_interests = set(other_user.get('interests', []))
                if not other_interests:
                    continue
                
                # 共通の関心事を計算
                common_interests = user_interests.intersection(other_interests)
                if len(common_interests) < 1:
                    continue
                
                # マッチングスコアの計算
                match_score = calculate_match_score(user, other_user, common_interests)
                
                if match_score >= 0.7:  # 閾値以上のマッチング
                    match_id = f"match_{min(user['id'], other_user['id'])}_{max(user['id'], other_user['id'])}"
                    
                    # 既存マッチの確認
                    existing_match_ref = db.collection('user_matches').document(match_id)
                    existing_match = await asyncio.to_thread(existing_match_ref.get)
                    
                    if not existing_match.exists:
                        match_data = {
                            'id': match_id,
                            'guildId': guild_id,
                            'user1Id': user['id'],
                            'user2Id': other_user['id'],
                            'commonInterests': list(common_interests),
                            'matchScore': match_score,
                            'status': 'suggested',
                            'createdAt': current_time.isoformat(),
                            'lastInteraction': None,
                            'isIntroduced': False,
                            'metadata': {
                                'user1Name': user.get('username', ''),
                                'user2Name': other_user.get('username', ''),
                                'engagementScores': {
                                    'user1': user.get('engagementScore', 0),
                                    'user2': other_user.get('engagementScore', 0)
                                }
                            }
                        }
                        
                        await asyncio.to_thread(existing_match_ref.set, match_data)
                        matches.append(match_data)
                        print(f"🤝 新しいマッチング: {user.get('username')} ↔ {other_user.get('username')} (スコア: {match_score:.2f})")
        
        return matches
        
    except Exception as e:
        print(f'❌ ユーザーマッチング実行エラー: {e}')
        return []

def calculate_match_score(user1: dict, user2: dict, common_interests: set) -> float:
    """マッチングスコアを計算する"""
    try:
        user1_interests = set(user1.get('interests', []))
        user2_interests = set(user2.get('interests', []))
        
        # 共通関心事の重み（0-0.4）
        if len(user1_interests) == 0 or len(user2_interests) == 0:
            common_weight = 0
        else:
            common_weight = len(common_interests) / max(len(user1_interests), len(user2_interests)) * 0.4
        
        # エンゲージメントレベルの類似度（0-0.2）
        engagement1 = user1.get('engagementScore', 0)
        engagement2 = user2.get('engagementScore', 0)
        if engagement1 == 0 and engagement2 == 0:
            engagement_similarity = 0
        else:
            engagement_similarity = 1 - abs(engagement1 - engagement2) / max(engagement1, engagement2, 1) * 0.2
        
        # 活動時間の類似度（簡易版）（0-0.2）
        activity_similarity = 0.1  # 仮の値
        
        # 基本的な互換性（0-0.2）
        basic_compatibility = 0.1 if len(common_interests) > 0 else 0
        
        total_score = common_weight + engagement_similarity + activity_similarity + basic_compatibility
        return min(1.0, total_score)
        
    except Exception as e:
        print(f'❌ マッチングスコア計算エラー: {e}')
        return 0.0

# --- ポッドキャスト管理機能 ---
async def create_podcast_entry(guild_id: str, title: str, content: str, topics: list):
    """ポッドキャストエントリーをFirestoreに保存する"""
    if db is None:
        return None
    
    try:
        current_time = datetime.datetime.now(datetime.timezone.utc)
        podcast_id = f"podcast_{current_time.strftime('%Y%m%d_%H%M%S')}_{guild_id}"
        
        podcast_data = {
            'id': podcast_id,
            'guildId': guild_id,
            'title': title,
            'content': content,
            'topics': topics,
            'publishedAt': current_time.isoformat(),
            'channelId': None,  # 後で設定
            'views': 0,
            'reactions': [],
            'metadata': {
                'generationTime': current_time.isoformat(),
                'weeklyDataRange': {
                    'start': (current_time - datetime.timedelta(days=7)).isoformat(),
                    'end': current_time.isoformat()
                },
                'topContributors': [],
                'dataSourcesUsed': ['interactions', 'topics', 'analytics_sessions']
            }
        }
        
        podcast_ref = db.collection('podcasts').document(podcast_id)
        await asyncio.to_thread(podcast_ref.set, podcast_data)
        
        print(f"🎙️ ポッドキャストエントリー作成: {title}")
        return podcast_data
        
    except Exception as e:
        print(f'❌ ポッドキャスト作成エラー: {e}')
        return None

# --- 高度なボットアクション記録 ---
async def log_advanced_bot_action(guild_id: str, user_id: str, action_type: str, payload: dict, target_id: str = None):
    """高度なボットアクションをFirestoreに記録する"""
    if db is None:
        return
    
    try:
        current_time = datetime.datetime.now(datetime.timezone.utc)
        action_id = f"bot_action_{action_type}_{current_time.strftime('%Y%m%d%H%M%S')}_{user_id}"
        
        action_data = {
            'id': action_id,
            'guildId': guild_id,
            'userId': user_id,
            'actionType': action_type,
            'targetId': target_id,
            'payload': payload,
            'timestamp': current_time.isoformat(),
            'status': 'completed',
            'result': None,  # 後で更新
            'metadata': {
                'actionId': action_id,
                'payloadSize': len(str(payload)),
                'executionTime': current_time.isoformat()
            }
        }
        
        bot_action_ref = db.collection('bot_actions').document(action_id)
        await asyncio.to_thread(bot_action_ref.set, action_data)
        
        print(f"🤖 高度なボットアクション記録: {action_type}")
        return action_id
        
    except Exception as e:
        print(f'❌ 高度なボットアクション記録エラー: {e}')
        return None

# --- 管理者情報管理 ---
async def get_admin_permissions(uid: str, guild_id: str):
    """管理者の権限情報を取得する"""
    if db is None:
        return None
    
    try:
        admin_ref = db.collection('admin_users').document(uid)
        admin_doc = await asyncio.to_thread(admin_ref.get)
        
        if not admin_doc.exists:
            return None
            
        admin_data = admin_doc.to_dict()
        
        # ギルド権限の確認
        if guild_id not in admin_data.get('guildIds', []):
            return None
            
        return admin_data.get('permissions', {})
        
    except Exception as e:
        print(f'❌ 管理者権限取得エラー: {e}')
        return None

# --- 統合データ分析機能 ---
async def generate_engagement_insights(guild_id: str, days: int = 7):
    """エンゲージメント分析レポートを生成する"""
    if db is None:
        return None
    
    try:
        current_time = datetime.datetime.now(datetime.timezone.utc)
        start_time = current_time - datetime.timedelta(days=days)
        
        # 期間内のインタラクション取得
        interactions_ref = db.collection('interactions')
        interactions_docs = await asyncio.to_thread(
            interactions_ref
            .where('guildId', '==', guild_id)
            .where('timestamp', '>=', start_time)
            .order_by('timestamp', direction=firestore.Query.DESCENDING)
            .get
        )
        
        # 分析データの集計
        total_interactions = len(interactions_docs)
        active_users = set()
        hourly_activity = {}
        popular_keywords = {}
        channel_engagement = {}
        
        for doc in interactions_docs:
            interaction = doc.to_dict()
            
            user_id = interaction.get('userId')
            if user_id:
                active_users.add(user_id)
            
            # 時間別活動
            timestamp = interaction.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    hour = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00')).hour
                else:
                    hour = timestamp.hour
                hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
            
            # キーワード分析
            keywords = interaction.get('keywords', [])
            for keyword in keywords:
                popular_keywords[keyword] = popular_keywords.get(keyword, 0) + 1
            
            # チャンネル別エンゲージメント
            channel_name = interaction.get('channelName', 'unknown')
            channel_engagement[channel_name] = channel_engagement.get(channel_name, 0) + 1
        
        # 分析結果
        insights = {
            'period': {
                'start': start_time.isoformat(),
                'end': current_time.isoformat(),
                'days': days
            },
            'summary': {
                'totalInteractions': total_interactions,
                'activeUsers': len(active_users),
                'averageInteractionsPerUser': total_interactions / max(len(active_users), 1),
                'averageInteractionsPerDay': total_interactions / days
            },
            'hourlyActivity': dict(sorted(hourly_activity.items())),
            'topKeywords': dict(sorted(popular_keywords.items(), key=lambda x: x[1], reverse=True)[:20]),
            'channelEngagement': dict(sorted(channel_engagement.items(), key=lambda x: x[1], reverse=True)[:10]),
            'generatedAt': current_time.isoformat()
        }
        
        print(f"📈 エンゲージメント分析完了: {days}日間 ({total_interactions}インタラクション)")
        return insights
        
    except Exception as e:
        print(f'❌ エンゲージメント分析エラー: {e}')
        return None