#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
entertainment_bot.py
Discordエンタメコンテンツ制作アプリ統合メインシステム

全ての機能を統合したメインBot実装
"""

import discord
import datetime
import asyncio
import os
import json
from typing import Optional, Dict, Any, List
from firebase_admin import firestore
from dotenv import load_dotenv

# 内部モジュール
from .discord_analytics import DiscordAnalytics
from .content_creator import ContentCreator
from .scheduler import SchedulerManager
from .podcast import PodcastGenerator
from .daily_analytics import DailyAnalytics

# .envファイルから環境変数を読み込み
load_dotenv()

class EntertainmentBot(discord.Client):
    """Discordエンタメコンテンツ制作Bot"""
    
    def __init__(self, firestore_client, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.db = firestore_client
        # Firestoreクライアントの正規化
        self._firestore_client = self._get_firestore_client()
        
        # コア機能の初期化
        self.analytics = DiscordAnalytics(firestore_client)
        self.daily_analytics = DailyAnalytics(self, firestore_client)
        self.content_creator = ContentCreator(firestore_client, self)
        self.scheduler_manager = SchedulerManager(firestore_client, self)
        self.podcast_generator = PodcastGenerator()
        
        # 設定
        self.command_prefix = os.getenv('BOT_COMMAND_PREFIX', '!')
        self.admin_user_ids = self._load_admin_users()
        
        print("🎬 エンタメコンテンツ制作Bot初期化完了")
    
    def _get_firestore_client(self):
        """Firestoreクライアントを取得"""
        if hasattr(self.db, 'collection'):
            return self.db
        elif hasattr(self.db, 'db'):
            return self.db.db
        else:
            raise ValueError("無効なFirestoreクライアント")
    
    def _load_admin_users(self) -> List[int]:
        """管理者ユーザーIDを読み込み"""
        admin_ids_str = os.getenv('BOT_ADMIN_USER_IDS', '')
        if admin_ids_str:
            try:
                return [int(id_str.strip()) for id_str in admin_ids_str.split(',')]
            except ValueError:
                print("⚠️ 管理者ユーザーID設定エラー")
        return []
    
    async def on_ready(self):
        """Botが準備完了時の処理"""
        print(f'✅ {self.user} がログインしました')
        print(f'📊 接続サーバー数: {len(self.guilds)}')
        
        # ギルド情報をFirestoreに記録
        await self._update_guild_info()
        
        # 自動スケジューラー開始（設定されている場合）
        auto_start_scheduler = os.getenv('AUTO_START_SCHEDULER', 'false').lower() == 'true'
        if auto_start_scheduler:
            print("🚀 自動スケジューラー開始...")
            self.scheduler_manager.scheduler.start_scheduler()
    
    async def on_message(self, message):
        """メッセージ受信時の処理"""
        # Bot自身のメッセージは無視
        if message.author == self.user:
            return
        
        # メンション処理（最優先）
        if self.user in message.mentions:
            await self._handle_mention(message)
            return
        
        # 管理者コマンド処理（管理者のみ）
        if message.content.startswith(self.command_prefix) and message.author.id in self.admin_user_ids:
            await self._handle_command(message)
            return
        
        # 自然な会話（メンションなしでも特定の条件で応答）
        if await self._should_respond_naturally(message):
            await self._handle_natural_conversation(message)
            return
        
        # メッセージログ記録（既存機能との連携）
        await self._log_message_activity(message)

    async def on_message_edit(self, before, after):
        """メッセージ編集時の処理"""
        if after.author == self.user:
            return
        
        await self._log_message_edit_activity(before, after)

    async def on_message_delete(self, message):
        """メッセージ削除時の処理"""
        if message.author == self.user:
            return
        
        await self._log_message_delete_activity(message)

    async def on_reaction_add(self, reaction, user):
        """リアクション追加時の処理"""
        if user == self.user:
            return
        
        await self._log_reaction_activity(reaction, user, 'reaction_add')

    async def on_reaction_remove(self, reaction, user):
        """リアクション削除時の処理"""
        if user == self.user:
            return
        
        await self._log_reaction_activity(reaction, user, 'reaction_remove')

    async def on_member_join(self, member):
        """メンバー参加時の処理"""
        await self._log_member_activity(member, 'member_join')

    async def on_member_remove(self, member):
        """メンバー退出時の処理"""
        await self._log_member_activity(member, 'member_leave')

    async def on_scheduled_event_create(self, event):
        """スケジュールイベント作成時の処理"""
        await self._log_event_activity(event, 'scheduled_event_create')

    async def on_scheduled_event_update(self, before, after):
        """スケジュールイベント更新時の処理"""
        await self._log_event_activity(after, 'scheduled_event_update', before)

    async def on_scheduled_event_delete(self, event):
        """スケジュールイベント削除時の処理"""
        await self._log_event_activity(event, 'scheduled_event_delete')

    async def on_scheduled_event_user_add(self, event, user):
        """スケジュールイベント参加時の処理"""
        await self._log_event_user_activity(event, user, 'scheduled_event_user_add')

    async def on_scheduled_event_user_remove(self, event, user):
        """スケジュールイベント離脱時の処理"""
        await self._log_event_user_activity(event, user, 'scheduled_event_user_remove')
    
    async def _handle_command(self, message):
        """コマンド処理"""
        content = message.content[len(self.command_prefix):].strip()
        if not content:
            return
        
        command_parts = content.split()
        command = command_parts[0].lower()
        
        try:
            # 管理者権限が必要なコマンド
            admin_commands = ['scheduler', 'summary', 'analytics', 'podcast', 'advice', 'daily_analytics']
            if command in admin_commands and message.author.id not in self.admin_user_ids:
                await message.reply("❌ このコマンドは管理者専用です")
                return
            
            # コマンド処理
            if command == 'help':
                await self._cmd_help(message)
            
            elif command == 'scheduler':
                response = await self.scheduler_manager.handle_scheduler_command(message, command_parts)
                await message.reply(response)
            
            elif command == 'summary':
                await self._cmd_summary(message, command_parts)
            
            elif command == 'analytics':
                await self._cmd_analytics(message, command_parts)
            
            elif command == 'podcast':
                await self._cmd_podcast(message, command_parts)
            
            elif command == 'status':
                await self._cmd_status(message)
            
            elif command == 'dashboard':
                await self._cmd_dashboard(message)
            
            elif command == 'testlog':
                await self._cmd_test_log(message)
            
            elif command == 'botactions':
                await self._cmd_bot_actions(message, command_parts)
            
            elif command == 'advice':
                await self._cmd_generate_advice(message)
            
            elif command == 'daily_analytics':
                await self._cmd_daily_analytics(message)
            
            else:
                await message.reply(f"❓ 不明なコマンド: {command}")
        
        except Exception as e:
            print(f"❌ コマンド処理エラー: {e}")
            await message.reply(f"❌ コマンド実行エラー: {e}")
    
    async def _handle_mention(self, message):
        """自然な会話でのメンション処理"""
        try:
            # メンションを除いたメッセージ内容を取得
            content = message.content
            for mention in message.mentions:
                content = content.replace(f'<@{mention.id}>', '').replace(f'<@!{mention.id}>', '')
            content = content.strip()
            
            # 空のメンションの場合
            if not content:
                greetings = [
                    "はい、何でしょうか？😊",
                    "こんにちは！何かお話ししましょうか？",
                    "お疲れさまです！どうされましたか？",
                    "何かお手伝いできることはありますか？"
                ]
                import random
                await message.reply(random.choice(greetings))
                return
            
            # AI応答を使った自然な会話
            await self._natural_conversation_response(message, content)
            
            # メンション処理をログに記録
            await self._log_bot_action(
                'conversation',
                str(message.author.id),
                str(message.guild.id) if message.guild else None,
                {'content': content[:100], 'response_type': 'natural_conversation'},
                status='completed'
            )
            
        except Exception as e:
            print(f"❌ メンション処理エラー: {e}")
            error_responses = [
                "ごめんなさい、ちょっと混乱してしまいました💦",
                "申し訳ございません、うまく理解できませんでした",
                "エラーが発生してしまいました。もう一度お話しいただけますか？"
            ]
            import random
            await message.reply(random.choice(error_responses))
    
    async def _natural_conversation_response(self, message, content):
        """自然な会話応答"""
        try:
            # 応答生成中のメッセージ
            thinking_messages = [
                "考え中です...🤔",
                "ちょっと待ってくださいね💭",
                "なるほど...✨"
            ]
            import random
            thinking_msg = await message.reply(random.choice(thinking_messages))
            
            # 過去7日間のアクティビティデータを取得
            activities = await self.analytics.collect_weekly_activities(days=7)
            
            # Vertex AIを使って自然な会話応答を生成
            import vertexai
            from vertexai.generative_models import GenerativeModel
            
            # ユーザーの名前を取得
            user_name = message.author.display_name or message.author.name
            
            prompt = f"""
あなたは親しみやすいDiscordのコミュニティBotです。ユーザー「{user_name}」さんとの自然な会話を心がけてください。

ユーザーからのメッセージ: {content}

現在のサーバー状況:
- 総メッセージ数: {activities['summary_stats']['total_messages']}
- アクティブユーザー数: {activities['summary_stats']['active_users_count']}
- アクティブチャンネル数: {activities['summary_stats']['active_channels_count']}
- 人気キーワード: {activities['summary_stats']['popular_keywords'][:5] if activities['summary_stats']['popular_keywords'] else 'なし'}

以下のガイドラインで応答してください:
1. 自然で親しみやすい口調
2. 絵文字を適度に使用
3. ユーザーの質問や話題に共感的に応答
4. 必要に応じてサーバー情報を参考にする
5. 150文字程度で簡潔に
6. コマンドの説明は避け、普通の会話として応答

ユーザーの名前を時々使って親近感を演出してください。
            """
            
            model = GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            ai_response = response.text
            
            # 考え中メッセージを削除
            await thinking_msg.delete()
            
            # 自然な応答を送信
            await message.reply(ai_response)
            
        except Exception as e:
            print(f"❌ 会話応答生成エラー: {e}")
            # エラー時はシンプルな応答
            fallback_responses = [
                f"{message.author.display_name}さん、ちょっと考えがまとまりませんでした💦 もう一度お話しいただけますか？",
                "すみません、うまくお答えできませんでした😅",
                "申し訳ございません、今は少し調子が悪いみたいです🤖"
            ]
            import random
            await message.reply(random.choice(fallback_responses))
    
    async def _should_respond_naturally(self, message):
        """自然な会話に応答するかの判定"""
        content = message.content.lower()
        
        # Bot名が含まれている場合
        bot_names = ['ミヤ', 'miya', 'エヴ', 'eve', 'bot', 'ボット']
        if any(name in content for name in bot_names):
            return True
        
        # 挨拶や感謝の言葉
        greetings = ['おはよう', 'こんにちは', 'こんばんは', 'お疲れ', 'ありがとう', 'thanks', 'hello', 'hi']
        if any(greeting in content for greeting in greetings):
            # 10%の確率で応答（スパム防止）
            import random
            return random.random() < 0.1
        
        # 質問形式
        if '？' in content or '?' in content:
            # 20%の確率で応答
            import random
            return random.random() < 0.2
        
        # 感情表現
        emotions = ['楽しい', '嬉しい', '悲しい', '困った', '大変', 'やばい', 'すごい', '面白い']
        if any(emotion in content for emotion in emotions):
            # 15%の確率で応答
            import random
            return random.random() < 0.15
        
        return False
    
    async def _handle_natural_conversation(self, message):
        """自然な会話処理（メンションなし）"""
        try:
            # よりカジュアルな応答
            thinking_messages = [
                "🤔",
                "💭",
                "✨"
            ]
            import random
            thinking_msg = await message.reply(random.choice(thinking_messages))
            
            # 簡略化されたプロンプト
            import vertexai
            from vertexai.generative_models import GenerativeModel
            
            user_name = message.author.display_name or message.author.name
            content = message.content
            
            prompt = f"""
あなたは親しみやすいDiscordコミュニティの住人です。ユーザー「{user_name}」さんの以下のメッセージに、自然で簡潔に応答してください。

メッセージ: {content}

ガイドライン:
1. 自然で親しみやすい口調
2. 絵文字を1-2個使用
3. 50-80文字程度で簡潔に
4. 共感や相槌を中心に
5. 普通の人として応答（Bot感を出さない）

例:
- 「そうですね😊」
- 「わかります！」
- 「いいですね✨」
            """
            
            model = GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            ai_response = response.text
            
            # 考え中メッセージを削除
            await thinking_msg.delete()
            
            # 短めの自然な応答
            await message.reply(ai_response)
            
            # ログ記録
            await self._log_bot_action(
                'natural_conversation',
                str(message.author.id),
                str(message.guild.id) if message.guild else None,
                {'content': content[:50], 'response_type': 'casual'},
                status='completed'
            )
            
        except Exception as e:
            print(f"❌ 自然会話応答エラー: {e}")
            # エラー時は控えめな応答
            casual_responses = [
                "😊",
                "なるほど！",
                "そうですね✨",
                "いいですね！"
            ]
            import random
            await message.reply(random.choice(casual_responses))
    
    async def _cmd_help(self, message):
        """ヘルプコマンド"""
        help_embed = discord.Embed(
            title="🎬 エンタメコンテンツ制作Bot ヘルプ",
            description="利用可能なコマンド一覧",
            color=0x00ff00
        )
        
        help_embed.add_field(
            name="📊 基本コマンド",
            value="""
`!help` - このヘルプを表示
`!status` - Bot状態を表示
`!dashboard` - 分析ダッシュボードリンクを表示
`!testlog` - テストログを記録（デバッグ用）
            """,
            inline=False
        )
        
        if message.author.id in self.admin_user_ids:
            help_embed.add_field(
                name="🔧 管理者コマンド",
                value="""
`!scheduler start/stop/status/run` - スケジューラー操作
`!summary [days]` - 手動で週次まとめ生成
`!analytics [days]` - アクティビティ分析
`!podcast [days]` - ポッドキャスト生成
`!advice` - 週次運営アドバイス生成
`!botactions [--limit=N] [--type=TYPE]` - Botアクション履歴表示
`!daily_analytics` - 日次アナリティクス生成
                """,
                inline=False
            )
        
        help_embed.set_footer(text="Powered by Discord Entertainment Bot")
        await message.reply(embed=help_embed)
    
    async def _cmd_summary(self, message, command_parts):
        """週次まとめ生成コマンド"""
        days = 7
        if len(command_parts) > 1:
            try:
                days = int(command_parts[1])
                days = max(1, min(days, 30))  # 1-30日の範囲
            except ValueError:
                await message.reply("❌ 日数は数字で指定してください")
                return
        
        await message.reply("🎬 週次エンタメコンテンツ制作を開始します...")
        
        try:
            result = await self.content_creator.create_weekly_content(days)
            
            if result['success']:
                embed = discord.Embed(
                    title="✅ 週次コンテンツ制作完了",
                    description=f"過去{days}日間のデータからコンテンツを生成しました",
                    color=0x00ff00
                )
                
                stats = result.get('stats', {})
                embed.add_field(
                    name="📊 統計情報",
                    value=f"""
メッセージ数: {stats.get('total_messages', 0)}
アクティブユーザー: {stats.get('active_users_count', 0)}名
アクティブチャンネル: {stats.get('active_channels_count', 0)}個
                    """,
                    inline=True
                )
                
                if result.get('discord_posted'):
                    embed.add_field(
                        name="📝 投稿状態",
                        value="✅ Discord投稿完了",
                        inline=True
                    )
                
                await message.reply(embed=embed)
            else:
                await message.reply(f"❌ コンテンツ制作失敗: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            await message.reply(f"❌ コマンド実行エラー: {e}")
    
    async def _cmd_analytics(self, message, command_parts):
        """アナリティクスコマンド"""
        days = 7
        if len(command_parts) > 1:
            try:
                days = int(command_parts[1])
                days = max(1, min(days, 30))
            except ValueError:
                await message.reply("❌ 日数は数字で指定してください")
                return
        
        await message.reply(f"📊 過去{days}日間のアクティビティを分析中...")
        
        try:
            activities = await self.analytics.collect_weekly_activities(days)
            stats = activities['summary_stats']
            
            embed = discord.Embed(
                title="📊 Discord アクティビティ分析",
                description=f"過去{days}日間の活動状況",
                color=0x0099ff
            )
            
            embed.add_field(
                name="📈 基本統計",
                value=f"""
総メッセージ数: {stats['total_messages']}
アクティブユーザー: {stats['active_users_count']}名
アクティブチャンネル: {stats['active_channels_count']}個
イベント数: {stats['events_count']}
                """,
                inline=True
            )
            
            # トップユーザー
            if stats['top_users']:
                top_users_text = "\n".join([f"{user}: {count}メッセージ" 
                                          for user, count in stats['top_users'][:3]])
                embed.add_field(
                    name="👑 トップユーザー",
                    value=top_users_text,
                    inline=True
                )
            
            # 人気キーワード
            if stats['popular_keywords']:
                keywords_text = "\n".join([f"{keyword}: {count}回" 
                                         for keyword, count in stats['popular_keywords'][:5]])
                embed.add_field(
                    name="🔥 人気キーワード",
                    value=keywords_text,
                    inline=False
                )
            
            await message.reply(embed=embed)
        
        except Exception as e:
            await message.reply(f"❌ 分析エラー: {e}")
    
    async def _cmd_podcast(self, message, command_parts):
        """ポッドキャスト生成コマンド"""
        days = 7
        if len(command_parts) > 1:
            try:
                days = int(command_parts[1])
                days = max(1, min(days, 30))
            except ValueError:
                await message.reply("❌ 日数は数字で指定してください")
                return
        
        await message.reply(f"🎙️ 過去{days}日間のデータからポッドキャストを生成中...")
        
        try:
            result = await self.podcast_generator.generate_podcast(
                days=days,
                save_to_firestore=True,
                save_to_file=True,
                generate_audio=True
            )
            
            if result['success']:
                embed = discord.Embed(
                    title="🎙️ ポッドキャスト生成完了",
                    description="高品質な音声コンテンツを生成しました",
                    color=0xff6600
                )
                
                if 'audio_file' in result:
                    embed.add_field(
                        name="🎵 音声ファイル",
                        value=f"生成完了: {result['audio_file']}",
                        inline=False
                    )
                
                if 'character_audio_files' in result:
                    char_files = result['character_audio_files']
                    embed.add_field(
                        name="🎭 キャラクター別音声",
                        value=f"生成ファイル数: {len(char_files)}個",
                        inline=True
                    )
                
                await message.reply(embed=embed)
            else:
                await message.reply(f"❌ ポッドキャスト生成失敗: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            await message.reply(f"❌ ポッドキャスト生成エラー: {e}")
    
    async def _cmd_status(self, message):
        """システム状態表示コマンド"""
        scheduler_status = self.scheduler_manager.scheduler.get_status()
        
        embed = discord.Embed(
            title="🤖 Bot システム状態",
            description="各機能の動作状況",
            color=0x9932cc
        )
        
        # スケジューラー状態
        scheduler_text = "✅ 実行中" if scheduler_status['is_running'] else "⏹️ 停止中"
        next_run = scheduler_status['next_run'] if scheduler_status['next_run'] else "未設定"
        
        embed.add_field(
            name="📅 スケジューラー",
            value=f"""
状態: {scheduler_text}
設定: 毎週{scheduler_status['schedule_day']} {scheduler_status['schedule_time']}
次回実行: {next_run}
            """,
            inline=False
        )
        
        # Bot基本情報
        embed.add_field(
            name="🔧 Bot情報",
            value=f"""
サーバー数: {len(self.guilds)}
管理者数: {len(self.admin_user_ids)}
稼働時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """,
            inline=False
        )
        
        await message.reply(embed=embed)

    async def _cmd_dashboard(self, message):
        """ダッシュボードリンク表示コマンド"""
        # Firebase HostingのURL（設定から取得）
        dashboard_url = os.getenv('FIREBASE_HOSTING_URL', 'https://your-project.web.app')
        
        embed = discord.Embed(
            title="📊 Discord ログ分析ダッシュボード",
            description="Web上でサーバーのアクティビティ分析をご覧いただけます",
            color=0x7289da
        )
        
        embed.add_field(
            name="🔗 ダッシュボードアクセス",
            value=f"[Discord ログ分析ダッシュボード]({dashboard_url})",
            inline=False
        )
        
        embed.add_field(
            name="📈 利用可能な分析機能",
            value="""• メッセージ統計
• ユーザーアクティビティ
• チャンネル分析
• キーワードトレンド
• リアクション統計
• メンバー参加/退出""",
            inline=True
        )
        
        embed.add_field(
            name="🔄 データ更新",
            value="リアルタイムでDiscordアクティビティを記録中",
            inline=True
        )
        
        embed.set_footer(text="このボットがアクティビティデータを自動収集しています")
        
        await message.reply(embed=embed)

    async def _cmd_test_log(self, message):
        """テストログ記録コマンド（デバッグ用）"""
        if message.author.id not in self.admin_user_ids:
            await message.reply("❌ このコマンドは管理者専用です")
            return
        
        try:
            # ユーザー情報を分離して保存
            await self._ensure_user_exists(message.author)
            
            # テスト用のログエントリを作成
            test_data = {
                'type': 'test_log',
                'userId': str(message.author.id),
                'channelId': str(message.channel.id),
                'channelName': message.channel.name if hasattr(message.channel, 'name') else 'DM',
                'guildId': str(message.guild.id) if message.guild else None,
                'guildName': message.guild.name if message.guild else None,
                'content': 'テストログエントリ - ダッシュボード確認用',
                'timestamp': datetime.datetime.now(datetime.timezone.utc),
                'metadata': {
                    'isTestData': True,
                    'generatedBy': 'testlog_command'
                },
                'keywords': ['テスト', 'ダッシュボード', '動作確認']
            }
            
            # Firestoreに保存
            await asyncio.to_thread(self._firestore_client.collection('interactions').add, test_data)
            
            await message.reply("✅ テストログを記録しました。ダッシュボードで確認できます。")
            
        except Exception as e:
            await message.reply(f"❌ テストログ記録エラー: {e}")

    async def _log_message_activity(self, message):
        """メッセージアクティビティをログ記録（既存システムとの連携）"""
        try:
            # ユーザー情報を分離して保存
            await self._ensure_user_exists(message.author)
            
            # 既存のinteractionsコレクションに記録（usernameを削除）
            interaction_data = {
                'type': 'message',
                'userId': str(message.author.id),
                'channelId': str(message.channel.id),
                'channelName': message.channel.name if hasattr(message.channel, 'name') else 'DM',
                'guildId': str(message.guild.id) if message.guild else None,
                'guildName': message.guild.name if message.guild else None,
                'content': message.content[:500],  # 最初の500文字のみ保存
                'timestamp': datetime.datetime.now(datetime.timezone.utc),
                'messageId': str(message.id),
                'hasAttachments': len(message.attachments) > 0,
                'attachmentCount': len(message.attachments),
                'keywords': self._extract_keywords(message.content)
            }
            
            # 非同期でFirestoreに保存
            await asyncio.to_thread(self._firestore_client.collection('interactions').add, interaction_data)
            
        except Exception as e:
            print(f"⚠️ メッセージアクティビティログエラー: {e}")

    async def _log_message_edit_activity(self, before, after):
        """メッセージ編集アクティビティをログ記録"""
        try:
            await self._ensure_user_exists(after.author)
            
            interaction_data = {
                'type': 'message_edit',
                'userId': str(after.author.id),
                'channelId': str(after.channel.id),
                'channelName': after.channel.name if hasattr(after.channel, 'name') else 'DM',
                'guildId': str(after.guild.id) if after.guild else None,
                'guildName': after.guild.name if after.guild else None,
                'content': after.content[:500],
                'timestamp': datetime.datetime.now(datetime.timezone.utc),
                'messageId': str(after.id),
                'metadata': {
                    'contentBefore': before.content[:500],
                    'contentAfter': after.content[:500],
                    'hasAttachments': len(after.attachments) > 0,
                    'hasEmbeds': len(after.embeds) > 0
                },
                'keywords': self._extract_keywords(after.content)
            }
            
            await asyncio.to_thread(self._firestore_client.collection('interactions').add, interaction_data)
            
        except Exception as e:
            print(f"⚠️ メッセージ編集ログエラー: {e}")

    async def _log_message_delete_activity(self, message):
        """メッセージ削除アクティビティをログ記録"""
        try:
            await self._ensure_user_exists(message.author)
            
            interaction_data = {
                'type': 'message_delete',
                'userId': str(message.author.id),
                'channelId': str(message.channel.id),
                'channelName': message.channel.name if hasattr(message.channel, 'name') else 'DM',
                'guildId': str(message.guild.id) if message.guild else None,
                'guildName': message.guild.name if message.guild else None,
                'content': message.content[:500],
                'timestamp': datetime.datetime.now(datetime.timezone.utc),
                'messageId': str(message.id),
                'metadata': {
                    'deletedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'hadAttachments': len(message.attachments) > 0,
                    'hadEmbeds': len(message.embeds) > 0
                },
                'keywords': self._extract_keywords(message.content)
            }
            
            await asyncio.to_thread(self._firestore_client.collection('interactions').add, interaction_data)
            
        except Exception as e:
            print(f"⚠️ メッセージ削除ログエラー: {e}")

    async def _log_reaction_activity(self, reaction, user, reaction_type):
        """リアクションアクティビティをログ記録"""
        try:
            await self._ensure_user_exists(user)
            
            interaction_data = {
                'type': reaction_type,
                'userId': str(user.id),
                'channelId': str(reaction.message.channel.id),
                'channelName': reaction.message.channel.name if hasattr(reaction.message.channel, 'name') else 'DM',
                'guildId': str(reaction.message.guild.id) if reaction.message.guild else None,
                'guildName': reaction.message.guild.name if reaction.message.guild else None,
                'timestamp': datetime.datetime.now(datetime.timezone.utc),
                'messageId': str(reaction.message.id),
                'metadata': {
                    'emojiName': str(reaction.emoji),
                    'emojiId': reaction.emoji.id if hasattr(reaction.emoji, 'id') else None,
                    'isCustomEmoji': hasattr(reaction.emoji, 'id'),
                    'reactionCount': reaction.count
                },
                'keywords': ['リアクション', str(reaction.emoji)]
            }
            
            await asyncio.to_thread(self._firestore_client.collection('interactions').add, interaction_data)
            
        except Exception as e:
            print(f"⚠️ リアクションログエラー: {e}")

    async def _log_member_activity(self, member, activity_type):
        """メンバーアクティビティをログ記録"""
        try:
            await self._ensure_user_exists(member)
            
            interaction_data = {
                'type': activity_type,
                'userId': str(member.id),
                'guildId': str(member.guild.id),
                'guildName': member.guild.name,
                'timestamp': datetime.datetime.now(datetime.timezone.utc),
                'metadata': {
                    'accountCreated': member.created_at.isoformat(),
                    'isBot': member.bot,
                    'roles': [role.name for role in member.roles if role.name != '@everyone'],
                    'joinedAt': member.joined_at.isoformat() if member.joined_at else None
                },
                'keywords': ['新規参加' if activity_type == 'member_join' else 'メンバー退出', 'ウェルカム' if activity_type == 'member_join' else 'さよなら']
            }
            
            await asyncio.to_thread(self._firestore_client.collection('interactions').add, interaction_data)
            
        except Exception as e:
            print(f"⚠️ メンバーアクティビティログエラー: {e}")

    async def _log_event_activity(self, event, activity_type, before_event=None):
        """スケジュールイベントアクティビティをログ記録"""
        try:
            if event.creator:
                await self._ensure_user_exists(event.creator)
            
            interaction_data = {
                'type': activity_type,
                'userId': str(event.creator.id) if event.creator else None,
                'guildId': str(event.guild.id),
                'guildName': event.guild.name,
                'timestamp': datetime.datetime.now(datetime.timezone.utc),
                'eventId': str(event.id),
                'eventName': event.name,
                'metadata': {
                    'eventDescription': event.description[:200] if event.description else None,
                    'startTime': event.start_time.isoformat() if event.start_time else None,
                    'endTime': event.end_time.isoformat() if event.end_time else None,
                    'entityType': event.entity_type.name if event.entity_type else None,
                    'status': event.status.name if event.status else None,
                    'userCount': event.user_count if hasattr(event, 'user_count') else 0
                },
                'keywords': ['イベント作成' if 'create' in activity_type else 'イベント更新' if 'update' in activity_type else 'イベント削除', 'スケジュール']
            }
            
            await asyncio.to_thread(self._firestore_client.collection('interactions').add, interaction_data)
            
        except Exception as e:
            print(f"⚠️ イベントアクティビティログエラー: {e}")

    async def _log_event_user_activity(self, event, user, activity_type):
        """イベントユーザーアクティビティをログ記録"""
        try:
            await self._ensure_user_exists(user)
            
            interaction_data = {
                'type': activity_type,
                'userId': str(user.id),
                'guildId': str(event.guild.id),
                'guildName': event.guild.name,
                'timestamp': datetime.datetime.now(datetime.timezone.utc),
                'eventId': str(event.id),
                'eventName': event.name,
                'metadata': {
                    'eventDescription': event.description[:200] if event.description else None,
                    'startTime': event.start_time.isoformat() if event.start_time else None,
                    'userAction': 'joined' if 'add' in activity_type else 'left'
                },
                'keywords': ['イベント参加' if 'add' in activity_type else 'イベント離脱', event.name[:50]]
            }
            
            await asyncio.to_thread(self._firestore_client.collection('interactions').add, interaction_data)
            
        except Exception as e:
            print(f"⚠️ イベントユーザーアクティビティログエラー: {e}")

    async def _update_guild_info(self):
        """ギルド情報をFirestoreに更新"""
        try:
            for guild in self.guilds:
                guild_data = {
                    'guildId': str(guild.id),
                    'name': guild.name,
                    'memberCount': guild.member_count,
                    'description': guild.description if guild.description else None,
                    'icon': str(guild.icon.url) if guild.icon else None,
                    'ownerID': str(guild.owner_id),
                    'createdAt': guild.created_at.isoformat(),
                    'premiumTier': guild.premium_tier,
                    'premiumSubscriptionCount': guild.premium_subscription_count,
                    'channels': {
                        'text': len([ch for ch in guild.channels if str(ch.type) == 'text']),
                        'voice': len([ch for ch in guild.channels if str(ch.type) == 'voice']),
                        'category': len([ch for ch in guild.channels if str(ch.type) == 'category']),
                        'total': len(guild.channels)
                    },
                    'roles': len(guild.roles),
                    'emojis': len(guild.emojis),
                    'lastUpdated': datetime.datetime.now(datetime.timezone.utc),
                    'features': list(guild.features) if guild.features else []
                }
                
                # Firestoreのguildsコレクションに保存（ドキュメントIDはguildId）
                await asyncio.to_thread(
                    self._firestore_client.collection('guilds').document(str(guild.id)).set,
                    guild_data
                )
                
                print(f"📊 ギルド情報更新: {guild.name} ({guild.member_count}名)")
                
        except Exception as e:
            print(f"⚠️ ギルド情報更新エラー: {e}")
    
    def _extract_keywords(self, content: str) -> List[str]:
        """メッセージからキーワードを抽出"""
        if not content:
            return []
        
        import re
        
        # 基本的な単語抽出
        words = re.findall(r'\w+', content.lower())
        
        # 技術関連キーワード
        tech_keywords = [
            'react', 'typescript', 'javascript', 'python', 'node', 'firebase',
            'discord', 'api', 'database', 'frontend', 'backend', 'web', 'app',
            'github', 'git', 'docker', 'aws', 'gcp', 'azure', 'ai', 'ml',
            'vue', 'angular', 'next', 'nuxt', 'svelte', 'php', 'java', 'kotlin',
            'swift', 'go', 'rust', 'c++', 'sql', 'mongodb', 'mysql', 'postgres'
        ]
        
        # 日本語キーワード（感情・トピック）
        japanese_keywords = [
            'ありがとう', 'おめでとう', 'お疲れ', 'すごい', '面白い', '楽しい',
            '勉強', '学習', '開発', '実装', 'バグ', 'エラー', '解決', '質問',
            'プロジェクト', 'アプリ', 'サイト', 'システム', 'デザイン', 'ui',
            'ux', 'テスト', 'デバッグ', 'リリース', 'デプロイ', 'レビュー'
        ]
        
        # URLやメンション等の特殊パターン
        has_url = bool(re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content))
        has_mention = '@' in content
        has_emoji = bool(re.search(r':[a-zA-Z0-9_]+:', content))
        
        # マッチするキーワードを抽出
        keywords = []
        
        # 技術キーワード
        keywords.extend([word for word in words if word in tech_keywords])
        
        # 日本語キーワード
        for jp_keyword in japanese_keywords:
            if jp_keyword in content.lower():
                keywords.append(jp_keyword)
        
        # 長い単語（4文字以上）
        keywords.extend([word for word in words if len(word) >= 4 and word not in tech_keywords])
        
        # 特殊パターン
        if has_url:
            keywords.append('URL')
        if has_mention:
            keywords.append('メンション')
        if has_emoji:
            keywords.append('絵文字')
        
        return list(set(keywords))[:15]  # 重複削除、最大15個
    
    async def _ensure_user_exists(self, user):
        """ユーザー情報がFirestoreに存在することを確認し、なければ作成/更新"""
        try:
            user_id = str(user.id)
            user_doc_ref = self._firestore_client.collection('users').document(user_id)
            
            # 現在のユーザーデータを取得
            user_doc = await asyncio.to_thread(user_doc_ref.get)
            
            # ユーザーデータを準備
            user_data = {
                'userId': user_id,
                'username': user.name,
                'displayName': user.display_name,
                'discriminator': user.discriminator if hasattr(user, 'discriminator') else None,
                'avatar': str(user.avatar.url) if user.avatar else None,
                'isBot': user.bot,
                'createdAt': user.created_at.isoformat(),
                'lastSeen': datetime.datetime.now(datetime.timezone.utc),
                'updatedAt': datetime.datetime.now(datetime.timezone.utc)
            }
            
            # ユーザーが存在しない場合は作成、存在する場合は更新
            if not user_doc.exists:
                user_data['firstSeen'] = datetime.datetime.now(datetime.timezone.utc)
                await asyncio.to_thread(user_doc_ref.set, user_data)
            else:
                # 既存のユーザーデータを更新（firstSeenは保持）
                existing_data = user_doc.to_dict()
                user_data['firstSeen'] = existing_data.get('firstSeen', datetime.datetime.now(datetime.timezone.utc))
                await asyncio.to_thread(user_doc_ref.update, user_data)
            
        except Exception as e:
            print(f"⚠️ ユーザー情報保存エラー: {e}")
    
    async def _log_bot_action(self, action_type: str, user_id: str, guild_id: str = None, 
                             payload: Dict[str, Any] = None, target_id: str = None, 
                             status: str = "pending", result: Dict[str, Any] = None):
        """Botアクションをログに記録"""
        try:
            bot_action_data = {
                'actionType': action_type,
                'userId': user_id,
                'guildId': guild_id,
                'targetId': target_id,
                'payload': payload or {},
                'timestamp': datetime.datetime.now(datetime.timezone.utc),
                'status': status,
                'result': result or {},
                'botCharacter': 'entertainment_bot',
                'version': '1.0.0'
            }
            
            # Firestoreのbot_actionsコレクションに保存
            doc_ref = await asyncio.to_thread(
                self._firestore_client.collection('bot_actions').add, 
                bot_action_data
            )
            
            print(f"📝 Botアクションログ記録: {action_type} (ID: {doc_ref[1].id})")
            return doc_ref[1].id
            
        except Exception as e:
            print(f"⚠️ Botアクションログエラー: {e}")
            return None
    
    async def generate_weekly_advice(self, guild_id: str = None) -> Dict[str, Any]:
        """週次運営アドバイスを生成"""
        try:
            print("🧠 週次運営アドバイス生成開始...")
            
            # 過去7日間のアクティビティデータを収集
            activities = await self.analytics.collect_weekly_activities(days=7)
            
            # Vertex AIを使ってアドバイスを生成
            import vertexai
            from vertexai.generative_models import GenerativeModel
            
            # プロンプトを構築
            prompt = f"""
以下のDiscordサーバーの過去1週間のアクティビティデータを分析し、運営改善のためのアドバイスを日本語で提供してください。

アクティビティ統計:
- 総メッセージ数: {activities['summary_stats']['total_messages']}
- アクティブユーザー数: {activities['summary_stats']['active_users_count']}
- アクティブチャンネル数: {activities['summary_stats']['active_channels_count']}
- トップユーザー: {activities['summary_stats']['top_users'][:3] if activities['summary_stats']['top_users'] else 'なし'}
- 人気キーワード: {activities['summary_stats']['popular_keywords'][:5] if activities['summary_stats']['popular_keywords'] else 'なし'}

以下の観点からアドバイスを提供してください:
1. コミュニティの活発さ評価
2. ユーザーエンゲージメント改善提案
3. チャンネル運営の最適化
4. イベントや企画の提案
5. モデレーション改善点

200-300文字程度で簡潔にまとめてください。
            """
            
            # Vertex AI (Gemini) でアドバイス生成
            model = GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            advice_content = response.text
            
            # 週の期間を計算
            now = datetime.datetime.now(datetime.timezone.utc)
            week_start = now - datetime.timedelta(days=7)
            week_end = now
            
            # アドバイスデータを構造化
            advice_data = {
                'adviceId': f"advice_{now.strftime('%Y%m%d_%H%M%S')}",
                'weekOf': week_start.strftime('%Y-%m-%d'),
                'weekStart': week_start,
                'weekEnd': week_end,
                'content': advice_content,
                'activityStats': activities['summary_stats'],
                'createdAt': now,
                'isActive': True,
                'guildId': guild_id,
                'generatedBy': 'vertex_ai_gemini',
                'version': '1.0'
            }
            
            # Firestoreに保存
            doc_ref = await asyncio.to_thread(
                self._firestore_client.collection('weekly_advice').add,
                advice_data
            )
            
            print(f"✅ 週次アドバイス生成完了: {doc_ref[1].id}")
            
            return {
                'success': True,
                'adviceId': advice_data['adviceId'],
                'content': advice_content,
                'docId': doc_ref[1].id,
                'weekOf': advice_data['weekOf']
            }
            
        except Exception as e:
            print(f"❌ 週次アドバイス生成エラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _cmd_generate_advice(self, message):
        """手動で週次アドバイスを生成するコマンド"""
        if message.author.id not in self.admin_user_ids:
            await message.reply("❌ このコマンドは管理者専用です")
            return
        
        await message.reply("🧠 週次運営アドバイスを生成中...")
        
        guild_id = str(message.guild.id) if message.guild else None
        result = await self.generate_weekly_advice(guild_id)
        
        if result['success']:
            embed = discord.Embed(
                title="🧠 週次運営アドバイス",
                description=result['content'],
                color=0x00ff88
            )
            embed.add_field(
                name="📅 対象期間",
                value=f"{result['weekOf']} からの1週間",
                inline=False
            )
            embed.set_footer(text="Vertex AI (Gemini) による分析")
            
            await message.reply(embed=embed)
        else:
            await message.reply(f"❌ アドバイス生成に失敗しました: {result['error']}")

    async def _cmd_bot_actions(self, message, command_parts):
        """Botアクション履歴表示コマンド"""
        if message.author.id not in self.admin_user_ids:
            await message.reply("❌ このコマンドは管理者専用です")
            return
        
        try:
            # コマンドオプション解析
            limit = 10
            action_type = None
            
            if len(command_parts) > 1:
                for i, part in enumerate(command_parts[1:], 1):
                    if part.startswith('--limit=') or part.startswith('-l='):
                        try:
                            limit = int(part.split('=')[1])
                            limit = max(1, min(50, limit))  # 1-50の範囲
                        except ValueError:
                            pass
                    elif part.startswith('--type=') or part.startswith('-t='):
                        action_type = part.split('=')[1]
            
            # Firestoreからbotアクション履歴を取得
            query = self._firestore_client.collection('bot_actions') \
                .order_by('timestamp', direction=firestore.Query.DESCENDING) \
                .limit(limit)
            
            if action_type:
                query = query.where('actionType', '==', action_type)
            
            if message.guild:
                query = query.where('guildId', '==', str(message.guild.id))
            
            docs = await asyncio.to_thread(query.get)
            
            if not docs:
                await message.reply("📋 Botアクション履歴が見つかりません")
                return
            
            # 結果をDiscord Embedで表示
            embed = discord.Embed(
                title="🤖 Botアクション履歴",
                description=f"最新 {len(docs)} 件のアクション",
                color=0x7289da
            )
            
            action_list = []
            for doc in docs:
                data = doc.to_dict()
                timestamp = data.get('timestamp')
                if hasattr(timestamp, 'strftime'):
                    time_str = timestamp.strftime('%m/%d %H:%M')
                else:
                    time_str = str(timestamp)[:16] if timestamp else 'N/A'
                
                # ユーザー名を解決（存在する場合）
                user_id = data.get('userId', 'Unknown')
                try:
                    if user_id != 'Unknown':
                        user_ref = self._firestore_client.collection('users').document(user_id)
                        user_doc = await asyncio.to_thread(user_ref.get)
                        if user_doc.exists:
                            user_data = user_doc.to_dict()
                            username = user_data.get('displayName', user_data.get('username', f'User_{user_id[:8]}'))
                        else:
                            username = f'User_{user_id[:8]}'
                    else:
                        username = 'Unknown'
                except:
                    username = f'User_{user_id[:8]}'
                
                status_icon = {'completed': '✅', 'pending': '⏳', 'failed': '❌', 'pending_response': '📤'}.get(data.get('status', 'unknown'), '❓')
                action_summary = f"{status_icon} `{data.get('actionType', 'unknown')}` - {username} ({time_str})"
                action_list.append(action_summary)
            
            if action_list:
                embed.add_field(
                    name="📋 アクション一覧",
                    value="\n".join(action_list[:10]),  # 最大10件表示
                    inline=False
                )
            
            # 統計情報
            action_types = {}
            status_counts = {}
            for doc in docs:
                data = doc.to_dict()
                action_type = data.get('actionType', 'unknown')
                status = data.get('status', 'unknown')
                
                action_types[action_type] = action_types.get(action_type, 0) + 1
                status_counts[status] = status_counts.get(status, 0) + 1
            
            if action_types:
                type_summary = ", ".join([f"{k}: {v}" for k, v in list(action_types.items())[:5]])
                embed.add_field(name="📊 アクション種別", value=type_summary, inline=True)
            
            if status_counts:
                status_summary = ", ".join([f"{k}: {v}" for k, v in status_counts.items()])
                embed.add_field(name="📈 ステータス", value=status_summary, inline=True)
            
            embed.set_footer(text=f"使用方法: {self.command_prefix}botactions --limit=20 --type=topic_recommendation")
            
            await message.reply(embed=embed)
            
            # アクション記録
            await self._log_bot_action(
                'admin_command',
                str(message.author.id),
                str(message.guild.id) if message.guild else None,
                {'command': 'botactions', 'options': command_parts[1:] if len(command_parts) > 1 else []},
                status='completed',
                result={'actions_displayed': len(docs), 'query_limit': limit}
            )
            
        except Exception as e:
            await message.reply(f"❌ Botアクション履歴取得エラー: {e}")
            print(f"❌ Botアクション履歴コマンドエラー: {e}")
    
    async def _cmd_daily_analytics(self, message):
        """日次アナリティクス生成コマンド"""
        if message.author.id not in self.admin_user_ids:
            await message.reply("❌ このコマンドは管理者専用です")
            return
        
        await message.reply("📊 日次アナリティクスを生成中...")
        
        try:
            result = await self.daily_analytics.run_daily_analytics()
            
            if result['success']:
                embed = discord.Embed(
                    title="📊 日次アナリティクス生成完了",
                    description=f"日付: {result['date']}",
                    color=0x0099ff
                )
                
                summary = result['summary']
                embed.add_field(
                    name="📈 今日の統計",
                    value=f"""
アクティブユーザー: {summary['activeUsers']}名
メッセージ数: {summary['messageCount']}件
新規メンバー: {summary['newMembers']}名
再エンゲージメント: {summary['reengagements']}件
                    """,
                    inline=False
                )
                
                if summary['topChannels']:
                    embed.add_field(
                        name="📺 アクティブチャンネル",
                        value=" • ".join(summary['topChannels']),
                        inline=False
                    )
                
                embed.add_field(
                    name="💾 保存状況",
                    value=f"Firestore ID: `{result['analytics_id']}`",
                    inline=False
                )
                
                embed.set_footer(text="データはindex.htmlのダッシュボードで確認できます")
                
                await message.reply(embed=embed)
            else:
                await message.reply("❌ 日次アナリティクスの生成に失敗しました")
        
        except Exception as e:
            await message.reply(f"❌ エラー: {e}")
            print(f"❌ 日次アナリティクスコマンドエラー: {e}")
    
    async def shutdown(self):
        """Bot終了処理"""
        print("🛑 Bot終了処理を開始...")
        
        # スケジューラー停止
        if self.scheduler_manager.scheduler.is_running:
            self.scheduler_manager.scheduler.stop_scheduler()
        
        print("✅ Bot終了処理完了")
        await self.close()


async def create_entertainment_bot(firestore_client) -> EntertainmentBot:
    """エンタメBot インスタンス作成"""
    # Discord Intents設定
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True
    intents.members = True
    intents.reactions = True
    intents.guild_scheduled_events = True
    intents.voice_states = True
    intents.presences = True
    
    # Bot作成
    bot = EntertainmentBot(firestore_client, intents=intents)
    
    return bot