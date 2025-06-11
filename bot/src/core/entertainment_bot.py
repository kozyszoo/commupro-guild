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

# .envファイルから環境変数を読み込み
load_dotenv()

class EntertainmentBot(discord.Client):
    """Discordエンタメコンテンツ制作Bot"""
    
    def __init__(self, firestore_client, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.db = firestore_client
        
        # コア機能の初期化
        self.analytics = DiscordAnalytics(firestore_client)
        self.content_creator = ContentCreator(firestore_client, self)
        self.scheduler_manager = SchedulerManager(firestore_client, self)
        self.podcast_generator = PodcastGenerator()
        
        # 設定
        self.command_prefix = os.getenv('BOT_COMMAND_PREFIX', '!')
        self.admin_user_ids = self._load_admin_users()
        
        print("🎬 エンタメコンテンツ制作Bot初期化完了")
    
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
        
        # コマンド処理
        if message.content.startswith(self.command_prefix):
            await self._handle_command(message)
        
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
            admin_commands = ['scheduler', 'summary', 'analytics', 'podcast']
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
            
            else:
                await message.reply(f"❓ 不明なコマンド: {command}")
        
        except Exception as e:
            print(f"❌ コマンド処理エラー: {e}")
            await message.reply(f"❌ コマンド実行エラー: {e}")
    
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
    
    async def _log_message_activity(self, message):
        """メッセージアクティビティをログ記録（既存システムとの連携）"""
        try:
            # 既存のinteractionsコレクションに記録
            interaction_data = {
                'type': 'message',
                'userId': str(message.author.id),
                'username': message.author.display_name,
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
            await asyncio.to_thread(self.db.collection('interactions').add, interaction_data)
            
        except Exception as e:
            print(f"⚠️ メッセージアクティビティログエラー: {e}")
    
    def _extract_keywords(self, content: str) -> List[str]:
        """メッセージからキーワードを抽出"""
        # 簡単なキーワード抽出（改善可能）
        import re
        
        # 基本的な単語抽出
        words = re.findall(r'\w+', content.lower())
        
        # 技術関連キーワード
        tech_keywords = [
            'react', 'typescript', 'javascript', 'python', 'node', 'firebase',
            'discord', 'api', 'database', 'frontend', 'backend', 'web', 'app',
            'github', 'git', 'docker', 'aws', 'gcp', 'azure', 'ai', 'ml'
        ]
        
        # マッチするキーワードを抽出
        keywords = [word for word in words if word in tech_keywords or len(word) > 3]
        
        return list(set(keywords))[:10]  # 重複削除、最大10個
    
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