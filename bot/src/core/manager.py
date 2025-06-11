#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discord にゃんこエージェント - 複数Bot管理システム
2つのキャラクター（みやにゃん、イヴにゃん）を管理
新規参加者向けチュートリアル機能付き
"""

import discord
import asyncio
import os
import datetime
import json
import random
from typing import Dict, List, Optional, Set
from dotenv import load_dotenv
from dataclasses import dataclass, asdict
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel
from tutorial_content import TutorialStep

load_dotenv()

@dataclass
class BotCharacter:
    """Bot キャラクター設定"""
    name: str
    token_env_var: str
    emoji: str
    personality: str
    speaking_style: str
    role: str
    color: int
    response_triggers: List[str]

@dataclass
class TutorialProgress:
    """チュートリアル進捗管理"""
    user_id: str
    username: str
    guild_id: str
    current_step: int
    completed_steps: Set[int]
    started_at: datetime.datetime
    last_activity: datetime.datetime
    feedback_scores: Dict[int, int]  # step_index -> score (1-5)
    custom_notes: List[str]
    reminder_count: int
    is_paused: bool
    completion_time: Optional[datetime.datetime] = None

@dataclass
class TutorialStats:
    """チュートリアル統計"""
    total_users: int
    completed_users: int
    completion_rate: float
    average_completion_time: float
    step_abandonment_rates: Dict[int, float]
    average_feedback_scores: Dict[int, float]
    most_common_help_requests: List[str]

class MultiBotManager:
    """複数Discord Botの管理クラス"""
    
    def __init__(self):
        # Vertex AI の初期化
        self.init_vertex_ai()
        
        # チュートリアルデータの永続化ファイル
        self.tutorial_data_file = "tutorial_progress.json"
        self.tutorial_stats_file = "tutorial_stats.json"
        
        # チュートリアル進捗データの読み込み
        self.tutorial_progress: Dict[str, TutorialProgress] = self.load_tutorial_progress()
        self.tutorial_stats: TutorialStats = self.load_tutorial_stats()
        
        # 基本チュートリアルステップの定義
        self.base_tutorial_steps = [
            TutorialStep(
                title="🎉 ようこそ！",
                description="このサーバーへようこそ！私たちがDiscordサーバーの使い方をご案内しますにゃ〜",
                action_prompt="まずは自己紹介チャンネルで簡単な挨拶をしてみませんか？",
                emoji="👋"
            ),
            TutorialStep(
                title="📋 ルールの確認",
                description="サーバーのルールを確認して、みんなが気持ちよく過ごせるようにしましょうにゃ",
                action_prompt="#rules チャンネルを見て、「✅」リアクションを押してくださいにゃ！",
                emoji="📜"
            ),
            TutorialStep(
                title="🎭 ロールの選択",
                description="あなたの興味や役割に応じてロールを選択できますにゃ",
                action_prompt="#role-selection チャンネルでお好きなロールを選んでくださいにゃ〜",
                emoji="🏷️"
            ),
            TutorialStep(
                title="💬 コミュニケーション",
                description="他のメンバーとの交流を始めましょうにゃ！",
                action_prompt="#general チャンネルで雑談や質問をしてみてくださいにゃ",
                emoji="🗣️"
            ),
            TutorialStep(
                title="🔔 通知設定",
                description="必要な通知だけを受け取れるように設定しましょうにゃ",
                action_prompt="サーバー名を右クリック→「通知設定」から調整できますにゃ〜",
                emoji="🔔"
            ),
            TutorialStep(
                title="❓ 困った時は",
                description="何か分からないことがあったら、いつでも私たちに聞いてくださいにゃ！",
                action_prompt="「@みやにゃん ヘルプ」または「@イヴにゃん ヘルプ」と呼んでくださいにゃ〜",
                emoji="🆘"
            )
        ]
        
        # カスタムチュートリアルステップ（サーバー固有）
        self.custom_tutorial_steps = self.load_custom_tutorial_steps()
        
        # 統合されたチュートリアルステップ
        self.tutorial_steps = self.base_tutorial_steps + self.custom_tutorial_steps
        
        # キャラクター設定（みやにゃんとイヴにゃんの2体）
        self.characters = {
            'miya': BotCharacter(
                name='みやにゃん',
                token_env_var='DISCORD_BOT_TOKEN_MIYA', # みやにゃん用トークン環境変数
                emoji='🐈',
                personality='フレンドリーで好奇心旺盛、新しい技術に興味津々',
                speaking_style='だにゃ、にゃ〜、だよにゃ',
                role='技術解説・コミュニティサポート・チュートリアル案内',
                color=0xFF69B4,  # ピンク
                response_triggers=['みやにゃん', 'miya', '技術', 'プログラミング', 'コード', 'チュートリアル', 'ヘルプ', '進捗', '統計']
            ),
            'eve': BotCharacter(
                name='イヴにゃん',
                token_env_var='DISCORD_BOT_TOKEN_EVE', # イヴにゃん用トークン環境変数
                emoji='🐱',
                personality='クールで分析的、データや統計が得意',
                speaking_style='ですにゃ、なのにゃ、ですね',
                role='データ分析・レポート作成',
                color=0x9370DB,  # 紫
                response_triggers=['イヴにゃん', 'eve', 'データ', '分析', '統計']
            )
        }
        
        # 新規参加者の管理（後方互換性のため保持）
        self.new_members: Dict[str, dict] = {}  # user_id -> tutorial_state
        
        self.bots: Dict[str, discord.Client] = {}
        self.bot_tasks: Dict[str, asyncio.Task] = {}
        
        # リマインダータスクの管理
        self.reminder_tasks: Dict[str, asyncio.Task] = {}
        
    def init_vertex_ai(self):
        """Vertex AI を初期化"""
        try:
            # プロジェクトIDとリージョンを環境変数から取得
            project_id = os.getenv('GCP_PROJECT_ID')
            location = os.getenv('GCP_LOCATION', 'us-central1')
            
            if not project_id:
                print("⚠️ GCP_PROJECT_ID が設定されていません。固定応答モードで動作します。")
                self.gemini_model = None
                return
            
            # Vertex AI を初期化
            aiplatform.init(project=project_id, location=location)
            
            # Gemini モデルを初期化
            self.gemini_model = GenerativeModel('gemini-1.5-flash-002')
            print(f"✅ Vertex AI が初期化されました (Project: {project_id}, Location: {location})")
        except Exception as e:
            print(f"❌ Vertex AI の初期化に失敗: {e}")
            self.gemini_model = None
    
    def get_character_system_prompt(self, character_id: str) -> str:
        """キャラクター別のシステムプロンプトを取得"""
        character = self.characters[character_id]
        
        base_prompt = f"""あなたは「{character.name}」というDiscordサーバーのAIアシスタントです。

キャラクター設定:
- 名前: {character.name}
- 性格: {character.personality}
- 話し方: {character.speaking_style}
- 役割: {character.role}
- 絵文字: {character.emoji}

応答ルール:
1. 必ず{character.speaking_style}で話してください
2. {character.role}に関連する内容を優先的に扱ってください
3. 親しみやすく、サポート的な態度で応答してください
4. 応答は簡潔で分かりやすくしてください（200文字以内推奨）
5. 必要に応じて{character.emoji}絵文字を使ってください
"""
        
        if character_id == 'miya':
            base_prompt += """
6. 技術的な質問には具体的で実践的なアドバイスを提供してください
7. 初心者にも分かりやすく説明してください
8. チュートリアルや学習のサポートを積極的に行ってください
"""
        elif character_id == 'eve':
            base_prompt += """
6. データや統計に基づいた客観的な情報を提供してください
7. 論理的で分析的な視点から回答してください
8. 具体的な数値や事実を含めて説明してください
"""
        
        return base_prompt

    def create_bot_client(self, character_id: str) -> discord.Client:
        """キャラクター用のDiscord Clientを作成"""
        character = self.characters[character_id]
        
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        intents.members = True
        intents.reactions = True
        intents.guild_scheduled_events = True
        
        bot = discord.Client(intents=intents)
        
        # イベントハンドラーを動的に作成
        @bot.event
        async def on_ready():
            print(f"✅ {character.emoji} {character.name} がログインしました！")
            print(f"   役割: {character.role}")
        
        @bot.event
        async def on_member_join(member):
            """新規メンバー参加時のウェルカムメッセージとチュートリアル開始"""
            if member.bot:
                return  # ボットは無視
            
            # みやにゃんのみが新規参加者対応を担当
            if character_id == 'miya':
                await self.handle_new_member_join(member, bot)
        
        @bot.event
        async def on_message(message):
            # 自分のメッセージは無視
            if message.author == bot.user:
                return
            
            # ボットメッセージは無視
            if message.author.bot:
                return
            
            # チュートリアル進行チェック
            if character_id == 'miya' and str(message.author.id) in self.new_members:
                await self.handle_tutorial_progress(message, bot)
            
            # トリガーワードの検出
            content_lower = message.content.lower()
            should_respond = False
            
            for trigger in character.response_triggers:
                if trigger.lower() in content_lower:
                    should_respond = True
                    break
            
            # @メンションされた場合も応答
            if bot.user.mentioned_in(message):
                should_respond = True
            
            if should_respond:
                await self.handle_character_response(message, character_id, bot)
        
        @bot.event
        async def on_raw_reaction_add(payload):
            """リアクション追加時のチュートリアル進行チェック"""
            if payload.user_id == bot.user.id:
                return  # 自分のリアクションは無視
            
            if character_id == 'miya' and str(payload.user_id) in self.new_members:
                await self.handle_tutorial_reaction(payload, bot)
        
        return bot
    
    async def handle_new_member_join(self, member: discord.Member, bot: discord.Client):
        """新規メンバー参加時の処理"""
        try:
            # 新規参加者を登録（新システム）
            user_id = str(member.id)
            
            # 既存の進捗がある場合はスキップ
            if user_id in self.tutorial_progress:
                return
            
            # 新しい進捗を作成
            self.tutorial_progress[user_id] = TutorialProgress(
                user_id=user_id,
                username=member.display_name,
                guild_id=str(member.guild.id),
                current_step=0,
                completed_steps=set(),
                started_at=datetime.datetime.now(),
                last_activity=datetime.datetime.now(),
                feedback_scores={},
                custom_notes=[],
                reminder_count=0,
                is_paused=False
            )
            
            # 後方互換性のため旧システムも更新
            self.new_members[user_id] = {
                'current_step': 0,
                'joined_at': datetime.datetime.now(),
                'completed_steps': set(),
                'username': member.display_name,
                'guild_id': str(member.guild.id)
            }
            
            # 進捗を保存
            self.save_tutorial_progress()
            
            # 統計を更新
            self.update_tutorial_stats()
            
            # ウェルカムメッセージの作成
            welcome_embed = discord.Embed(
                title="🎉 ようこそ！",
                description=f"{member.mention} さん、{member.guild.name}へようこそですにゃ〜！",
                color=0xFF69B4,
                timestamp=datetime.datetime.now()
            )
            
            welcome_embed.add_field(
                name="🐈 みやにゃんと申しますにゃ！",
                value="私がこのサーバーの使い方をご案内させていただきますにゃ〜\n"
                      "技術的なことやコミュニティのサポートが得意ですにゃ！",
                inline=False
            )
            
            welcome_embed.add_field(
                name="📚 チュートリアルを始めませんか？",
                value="このサーバーを最大限活用できるように、\n"
                      "ステップバイステップでご案内しますにゃ〜\n\n"
                      "下の 🎓 ボタンを押してチュートリアルを開始してくださいにゃ！",
                inline=False
            )
            
            welcome_embed.set_footer(text="困ったことがあったら「@みやにゃん ヘルプ」と呼んでくださいにゃ〜")
            welcome_embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
            
            # システムチャンネルまたは一般チャンネルに送信
            target_channel = member.guild.system_channel
            if not target_channel:
                # 一般的なチャンネル名を探す
                for channel in member.guild.channels:
                    if isinstance(channel, discord.TextChannel) and channel.name.lower() in ['general', 'welcome', '雑談', 'ようこそ']:
                        target_channel = channel
                        break
            
            if target_channel:
                welcome_message = await target_channel.send(embed=welcome_embed)
                await welcome_message.add_reaction("🎓")  # チュートリアル開始ボタン
                
                # DMでもご挨拶
                try:
                    dm_embed = discord.Embed(
                        title="🐈 みやにゃんからのご挨拶",
                        description="DMでもサポートしますにゃ〜！\n"
                                  "何か質問があったら、ここに気軽にメッセージしてくださいにゃ！",
                        color=0xFF69B4
                    )
                    await member.send(embed=dm_embed)
                except discord.Forbidden:
                    pass  # DMが送れない場合は無視
            
        except Exception as e:
            print(f"❌ 新規メンバー対応エラー: {e}")
    
    async def handle_tutorial_reaction(self, payload: discord.RawReactionActionEvent, bot: discord.Client):
        """チュートリアル関連のリアクション処理"""
        if str(payload.emoji) == "🎓":
            user_id = str(payload.user_id)
            if user_id in self.new_members:
                guild = bot.get_guild(payload.guild_id)
                user = guild.get_member(payload.user_id)
                if user:
                    await self.start_tutorial(user, bot)
    
    async def start_tutorial(self, member: discord.Member, bot: discord.Client):
        """チュートリアルを開始"""
        user_id = str(member.id)
        if user_id not in self.new_members:
            return
        
        # 最初のステップを送信
        await self.send_tutorial_step(member, 0, bot)
    
    async def send_tutorial_step(self, member: discord.Member, step_index: int, bot: discord.Client):
        """指定されたチュートリアルステップを送信"""
        if step_index >= len(self.tutorial_steps):
            await self.complete_tutorial(member, bot)
            return
        
        step = self.tutorial_steps[step_index]
        user_id = str(member.id)
        
        # チュートリアルステップの埋め込みメッセージ作成
        embed = discord.Embed(
            title=f"{step.title} (ステップ {step_index + 1}/{len(self.tutorial_steps)})",
            description=step.description,
            color=0xFF69B4,
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(
            name=f"{step.emoji} やってみてにゃ！",
            value=step.action_prompt,
            inline=False
        )
        
        embed.add_field(
            name="💡 ヒント",
            value="完了したら「次へ」または「できた」と言ってくださいにゃ〜\n"
                  "スキップしたい場合は「スキップ」と言ってくださいにゃ！",
            inline=False
        )
        
        embed.set_footer(text="みやにゃんがサポートしますにゃ〜 | 困ったら「ヘルプ」と言ってくださいにゃ")
        
        # 現在のステップを更新
        self.new_members[user_id]['current_step'] = step_index
        
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            # DMが送れない場合はサーバーのチャンネルに送信
            channel = member.guild.system_channel
            if channel:
                embed.description = f"{member.mention} さん、{embed.description}"
                await channel.send(embed=embed)
    
    async def handle_tutorial_progress(self, message: discord.Message, bot: discord.Client):
        """チュートリアルの進行状況を処理"""
        user_id = str(message.author.id)
        tutorial_state = self.new_members[user_id]
        content = message.content.lower()
        
        # 進行コマンドの判定
        if any(word in content for word in ['次へ', 'つぎ', 'できた', 'ok', 'おk', 'next']):
            current_step = tutorial_state['current_step']
            tutorial_state['completed_steps'].add(current_step)
            await self.send_tutorial_step(message.author, current_step + 1, bot)
            
        elif 'スキップ' in content or 'skip' in content:
            current_step = tutorial_state['current_step']
            await self.send_tutorial_step(message.author, current_step + 1, bot)
            
        elif any(word in content for word in ['終了', 'しゅうりょう', 'やめる', 'quit', 'exit']):
            await self.end_tutorial(message.author, bot)
            
        elif 'ヘルプ' in content or 'help' in content:
            await self.send_tutorial_help(message.author, bot)
    
    async def end_tutorial(self, member: discord.Member, bot: discord.Client):
        """チュートリアルを途中で終了"""
        user_id = str(member.id)
        
        end_embed = discord.Embed(
            title="📝 チュートリアル終了",
            description=f"{member.display_name}さん、チュートリアルを終了しますにゃ",
            color=0xFFAA00,
            timestamp=datetime.datetime.now()
        )
        
        end_embed.add_field(
            name="🎯 いつでも再開できますにゃ",
            value="また困った時は「@みやにゃん チュートリアル」と呼んでくださいにゃ〜\n"
                  "私たちはいつでもサポートしますにゃ！",
            inline=False
        )
        
        end_embed.set_footer(text="みやにゃんより | お疲れ様でしたにゃ〜")
        
        try:
            await member.send(embed=end_embed)
        except discord.Forbidden:
            pass
        
        # 新規参加者リストから削除
        if user_id in self.new_members:
            del self.new_members[user_id]
    
    async def send_tutorial_help(self, member: discord.Member, bot: discord.Client):
        """チュートリアルヘルプメッセージを送信"""
        help_embed = discord.Embed(
            title="🆘 チュートリアルヘルプ",
            description="チュートリアルでお困りですか？みやにゃんがお手伝いしますにゃ〜",
            color=0xFF69B4
        )
        
        help_embed.add_field(
            name="📝 使えるコマンド",
            value="• `次へ` / `できた` - 次のステップに進む\n"
                  "• `スキップ` - 現在のステップをスキップ\n"
                  "• `ヘルプ` - このヘルプを表示\n"
                  "• `終了` - チュートリアルを終了",
            inline=False
        )
        
        help_embed.add_field(
            name="❓ よくある質問",
            value="**Q: チャンネルが見つからない**\n"
                  "A: サーバーによってチャンネル名が違う場合があります。似た名前のチャンネルを探してみてくださいにゃ\n\n"
                  "**Q: 権限がない**\n"
                  "A: 一部の機能は時間が経ってから使えるようになりますにゃ〜",
            inline=False
        )
        
        try:
            await member.send(embed=help_embed)
        except discord.Forbidden:
            pass
    
    async def complete_tutorial(self, member: discord.Member, bot: discord.Client):
        """チュートリアル完了処理"""
        user_id = str(member.id)
        
        # 新システムでの完了処理
        if user_id in self.tutorial_progress:
            progress = self.tutorial_progress[user_id]
            progress.completion_time = datetime.datetime.now()
            progress.last_activity = datetime.datetime.now()
            
            # 完了時間の計算
            completion_duration = progress.completion_time - progress.started_at
            completion_hours = completion_duration.total_seconds() / 3600
            
            completion_embed = discord.Embed(
                title="🎉 チュートリアル完了！",
                description=f"{member.display_name}さん、お疲れ様でしたにゃ〜！\n"
                          "これでサーバーの基本的な使い方は完璧ですにゃ！",
                color=0x00FF00,
                timestamp=datetime.datetime.now()
            )
            
            completion_embed.add_field(
                name="📊 あなたの統計",
                value=f"• 完了時間: {completion_hours:.1f}時間\n"
                      f"• 完了ステップ数: {len(progress.completed_steps)}/{len(self.tutorial_steps)}\n"
                      f"• リマインダー受信: {progress.reminder_count}回",
                inline=False
            )
            
            completion_embed.add_field(
                name="✨ 今後のお楽しみ",
                value="• 他のメンバーとの交流を楽しんでくださいにゃ〜\n"
                      "• 定期的なイベントにも参加してみてくださいにゃ\n"
                      "• 質問があったらいつでも私たちを呼んでくださいにゃ！",
                inline=False
            )
            
            completion_embed.add_field(
                name="📝 フィードバックをお願いします",
                value="チュートリアルの改善のため、「フィードバック」と言って評価をお聞かせくださいにゃ〜",
                inline=False
            )
            
            completion_embed.set_footer(text="みやにゃんより愛をこめて 💕")
            
            try:
                await member.send(embed=completion_embed)
            except discord.Forbidden:
                pass
            
            # 進捗を保存
            self.save_tutorial_progress()
            self.update_tutorial_stats()
        
        # 新規参加者リストから削除
        if user_id in self.new_members:
            del self.new_members[user_id]
        
        # 完了通知をサーバーにも送信
        channel = member.guild.system_channel
        if channel:
            await channel.send(f"🎉 {member.mention} さんがチュートリアルを完了しましたにゃ〜！みんなで歓迎してあげてくださいにゃ！")
    
    async def handle_character_response(self, message: discord.Message, character_id: str, bot: discord.Client):
        """キャラクター別の応答処理"""
        character = self.characters[character_id]
        
        # キャラクター別の応答生成
        response = await self.generate_character_response(message.content, character_id, message.author.name, message)
        
        if response:
            # 埋め込みメッセージで応答
            embed = discord.Embed(
                title=f"{character.emoji} {character.name}",
                description=response,
                color=character.color,
                timestamp=datetime.datetime.now()
            )
            embed.set_footer(text=f"役割: {character.role}")
            
            await message.channel.send(embed=embed)
    
    async def generate_character_response(self, content: str, character_id: str, user_name: str, message: discord.Message = None) -> str:
        """キャラクター別の応答を生成（Gemini API使用）"""
        character = self.characters[character_id]
        content_lower = content.lower()
        
        # チュートリアル関連の応答（みやにゃんのみ）
        if character_id == 'miya':
            user_id = str(message.author.id) if message else None
            
            # 新しいチュートリアル機能
            if any(word in content_lower for word in ['チュートリアル', 'tutorial', 'ガイド', 'guide', '使い方', 'つかいかた']):
                if message and user_id not in self.tutorial_progress:
                    # 新規ユーザーのチュートリアル開始（新システム）
                    await self.handle_new_member_join(message.author, None)
                    asyncio.create_task(self.send_tutorial_step(message.author, 0, None))
                    return f"{user_name}さん、チュートリアルを開始しますにゃ〜！DMをチェックしてくださいにゃ！"
                else:
                    return f"{user_name}さん、既にチュートリアル中ですにゃ〜！「次へ」「スキップ」「ヘルプ」が使えますにゃ！"
            
            # 進捗確認
            if any(word in content_lower for word in ['進捗', 'しんちょく', 'progress', '統計', 'とうけい', 'stats']):
                if message:
                    await self.show_tutorial_stats(message.channel, user_id)
                    return f"{user_name}さんの統計を表示しましたにゃ〜！"
            
            # フィードバック機能
            if any(word in content_lower for word in ['フィードバック', 'feedback', '評価', 'ひょうか']):
                if message:
                    await self.handle_tutorial_feedback(message.author, None)
                    return f"{user_name}さん、フィードバック画面をDMに送りましたにゃ〜！"
            
            # 一時停止機能
            if any(word in content_lower for word in ['一時停止', '停止', 'pause']):
                if user_id and await self.pause_tutorial(user_id):
                    return f"{user_name}さん、チュートリアルを一時停止しましたにゃ〜！「再開」で続きができますにゃ！"
                else:
                    return f"{user_name}さん、チュートリアルが見つからないですにゃ〜"
            
            # 再開機能
            if any(word in content_lower for word in ['再開', 'さいかい', 'resume', '続き', 'つづき']):
                if user_id and await self.resume_tutorial(user_id):
                    return f"{user_name}さん、チュートリアルを再開しましたにゃ〜！"
                else:
                    return f"{user_name}さん、チュートリアルが見つからないですにゃ〜"
            
            # フィードバック処理（数値の場合）
            if message and user_id in self.tutorial_progress:
                import re
                feedback_match = re.search(r'(\d+)点\s*(\d+)', content)
                if feedback_match:
                    step_index = int(feedback_match.group(1)) - 1  # 1-based to 0-based
                    score = int(feedback_match.group(2))
                    await self.process_tutorial_feedback(message, step_index, score)
                    return  # 既にprocess_tutorial_feedbackで応答済み
            
            if any(word in content_lower for word in ['ヘルプ', 'help', '助けて', 'たすけて', '困った']):
                return (f"{user_name}さん、どんなことでお困りですか？にゃ〜\n"
                       f"• チュートリアルが必要なら「チュートリアル」と言ってくださいにゃ\n"
                       f"• 進捗確認なら「進捗」と言ってくださいにゃ\n"
                       f"• フィードバックなら「フィードバック」と言ってくださいにゃ〜\n"
                       f"• 技術的な質問なら詳しく教えてくださいにゃ〜")
        
        # Vertex AI を使用した応答生成
        if self.gemini_model:
            try:
                return await self.generate_gemini_response(content, character_id, user_name, message)
            except Exception as e:
                print(f"❌ Vertex AI エラー ({character.name}): {e}")
                # フォールバック応答
                return await self.generate_fallback_response(character_id, user_name)
        else:
            # Vertex AIが利用できない場合のフォールバック
            return await self.generate_fallback_response(character_id, user_name)
    
    async def generate_gemini_response(self, content: str, character_id: str, user_name: str, message: discord.Message = None) -> str:
        """Vertex AIを使用して応答を生成"""
        try:
            # システムプロンプトを取得
            system_prompt = self.get_character_system_prompt(character_id)
            
            # コンテキスト情報を作成
            context_info = f"""
ユーザー名: {user_name}
メッセージ: {content}
サーバー: {message.guild.name if message and message.guild else "DM"}
チャンネル: {message.channel.name if message and hasattr(message.channel, 'name') else "DM"}
現在時刻: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            # プロンプト構築
            full_prompt = f"""{system_prompt}

{context_info}

上記の設定とコンテキストを踏まえて、ユーザーのメッセージに応答してください。"""
            
            # Vertex AIに送信
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                full_prompt
            )
            
            if response and response.text:
                # レスポンスの長さを制限（Discord埋め込みの制限）
                response_text = response.text.strip()
                if len(response_text) > 1000:
                    response_text = response_text[:950] + "..."
                return response_text
            else:
                return await self.generate_fallback_response(character_id, user_name)
                
        except Exception as e:
            print(f"❌ Vertex AI応答生成エラー: {e}")
            return await self.generate_fallback_response(character_id, user_name)
    
    async def generate_fallback_response(self, character_id: str, user_name: str) -> str:
        """フォールバック応答を生成"""
        fallback_responses = {
            'miya': [
                f"こんにちはにゃ〜、{user_name}さん！技術的な質問があれば何でも聞いてくださいにゃ！",
                f"プログラミングの話だにゃ〜！楽しそうですにゃ！",
                f"新しい技術について一緒に学びましょうにゃ〜！",
                f"{user_name}さん、何かお手伝いできることはありますか？にゃ〜",
                f"みやにゃんですにゃ〜！何でも聞いてくださいにゃ！"
            ],
            'eve': [
                f"{user_name}さん、データ分析のお手伝いをしますにゃ。",
                f"統計的に見ると興味深い内容ですにゃ。",
                f"分析結果をまとめてレポートしますにゃ。",
                f"イヴにゃんですにゃ。論理的に解決していきましょうにゃ。",
                f"{user_name}さん、データに基づいてお答えしますにゃ。"
            ]
        }
        
        return random.choice(fallback_responses.get(character_id, [f"こんにちはにゃ、{user_name}さん！"]))
    
    # ================== 新しいチュートリアル機能 ==================
    
    async def send_tutorial_reminder(self, user_id: str, bot: discord.Client):
        """チュートリアルリマインダーを送信"""
        if user_id not in self.tutorial_progress:
            return
        
        progress = self.tutorial_progress[user_id]
        if progress.is_paused or progress.completion_time:
            return
        
        # 最後の活動から24時間以上経過している場合
        time_since_activity = datetime.datetime.now() - progress.last_activity
        if time_since_activity.total_seconds() < 24 * 3600:  # 24時間未満
            return
        
        try:
            # ユーザーを取得
            guild = bot.get_guild(int(progress.guild_id))
            if not guild:
                return
            
            member = guild.get_member(int(user_id))
            if not member:
                return
            
            # リマインダーメッセージの作成
            current_step = progress.current_step
            if current_step < len(self.tutorial_steps):
                step = self.tutorial_steps[current_step]
                
                reminder_embed = discord.Embed(
                    title="📢 チュートリアルリマインダー",
                    description=f"{member.display_name}さん、チュートリアルの続きはいかがですか？にゃ〜",
                    color=0xFFAA00,
                    timestamp=datetime.datetime.now()
                )
                
                reminder_embed.add_field(
                    name=f"現在のステップ: {step.title}",
                    value=f"{step.description}\n\n**やること**: {step.action_prompt}",
                    inline=False
                )
                
                reminder_embed.add_field(
                    name="⏰ 進行方法",
                    value="「次へ」「できた」で次のステップに進めますにゃ〜\n"
                          "「一時停止」でリマインダーを止められますにゃ！",
                    inline=False
                )
                
                reminder_embed.set_footer(text="みやにゃんからの優しいリマインダー 💕")
                
                await member.send(embed=reminder_embed)
                
                # リマインダー回数を増加
                progress.reminder_count += 1
                self.save_tutorial_progress()
            
        except Exception as e:
            print(f"❌ リマインダー送信エラー: {e}")
    
    async def handle_tutorial_feedback(self, member: discord.Member, bot: discord.Client):
        """チュートリアルフィードバックの処理"""
        user_id = str(member.id)
        if user_id not in self.tutorial_progress:
            return
        
        progress = self.tutorial_progress[user_id]
        
        # フィードバック収集用の埋め込みメッセージ
        feedback_embed = discord.Embed(
            title="📝 チュートリアル フィードバック",
            description=f"{member.display_name}さん、チュートリアルの評価をお聞かせくださいにゃ〜",
            color=0xFF69B4,
            timestamp=datetime.datetime.now()
        )
        
        feedback_embed.add_field(
            name="⭐ 評価方法",
            value="各ステップに対して1〜5の数字で評価してくださいにゃ！\n"
                  "5: とても良い、4: 良い、3: 普通、2: 改善が必要、1: とても悪い",
            inline=False
        )
        
        # 完了したステップに対してフィードバックを求める
        for step_index in progress.completed_steps:
            if step_index < len(self.tutorial_steps):
                step = self.tutorial_steps[step_index]
                feedback_embed.add_field(
                    name=f"{step.emoji} {step.title}",
                    value=f"「{step_index + 1}点 {1-5}」の形で評価してくださいにゃ",
                    inline=True
                )
        
        feedback_embed.set_footer(text="例: 「1点 5」「2点 4」のように評価してくださいにゃ〜")
        
        try:
            await member.send(embed=feedback_embed)
        except discord.Forbidden:
            pass
    
    async def process_tutorial_feedback(self, message: discord.Message, step_index: int, score: int):
        """チュートリアルフィードバックの処理"""
        user_id = str(message.author.id)
        if user_id not in self.tutorial_progress:
            return
        
        progress = self.tutorial_progress[user_id]
        
        # スコアの検証
        if 1 <= score <= 5:
            progress.feedback_scores[step_index] = score
            progress.last_activity = datetime.datetime.now()
            
            self.save_tutorial_progress()
            self.update_tutorial_stats()
            
            # フィードバック確認メッセージ
            step = self.tutorial_steps[step_index] if step_index < len(self.tutorial_steps) else None
            if step:
                feedback_response = f"ありがとうございますにゃ〜！「{step.title}」に{score}点の評価をいただきましたにゃ！"
            else:
                feedback_response = f"評価をありがとうございますにゃ〜！{score}点をいただきましたにゃ！"
            
            await message.channel.send(feedback_response)
        else:
            await message.channel.send("評価は1〜5の数字でお願いしますにゃ〜")
    
    async def show_tutorial_stats(self, channel: discord.TextChannel, user_id: Optional[str] = None):
        """チュートリアル統計を表示"""
        if user_id and user_id in self.tutorial_progress:
            # 個人統計
            progress = self.tutorial_progress[user_id]
            
            stats_embed = discord.Embed(
                title="📊 あなたのチュートリアル統計",
                color=0xFF69B4,
                timestamp=datetime.datetime.now()
            )
            
            stats_embed.add_field(
                name="📈 進捗状況",
                value=f"現在のステップ: {progress.current_step + 1}/{len(self.tutorial_steps)}\n"
                      f"完了ステップ: {len(progress.completed_steps)}\n"
                      f"開始日時: {progress.started_at.strftime('%Y-%m-%d %H:%M')}",
                inline=False
            )
            
            if progress.completion_time:
                duration = progress.completion_time - progress.started_at
                hours = duration.total_seconds() / 3600
                stats_embed.add_field(
                    name="🎉 完了情報",
                    value=f"完了日時: {progress.completion_time.strftime('%Y-%m-%d %H:%M')}\n"
                          f"所要時間: {hours:.1f}時間",
                    inline=False
                )
            
            if progress.feedback_scores:
                avg_score = sum(progress.feedback_scores.values()) / len(progress.feedback_scores)
                stats_embed.add_field(
                    name="⭐ フィードバック平均",
                    value=f"{avg_score:.1f}/5.0 ({len(progress.feedback_scores)}ステップ評価済み)",
                    inline=False
                )
            
            await channel.send(embed=stats_embed)
        else:
            # 全体統計
            stats_embed = discord.Embed(
                title="📊 チュートリアル全体統計",
                description="サーバー全体のチュートリアル利用状況ですにゃ〜",
                color=0xFF69B4,
                timestamp=datetime.datetime.now()
            )
            
            stats_embed.add_field(
                name="👥 利用者数",
                value=f"総利用者: {self.tutorial_stats.total_users}人\n"
                      f"完了者: {self.tutorial_stats.completed_users}人\n"
                      f"完了率: {self.tutorial_stats.completion_rate:.1%}",
                inline=False
            )
            
            if self.tutorial_stats.average_completion_time > 0:
                stats_embed.add_field(
                    name="⏱️ 平均完了時間",
                    value=f"{self.tutorial_stats.average_completion_time:.1f}時間",
                    inline=True
                )
            
            if self.tutorial_stats.average_feedback_scores:
                avg_all_scores = sum(self.tutorial_stats.average_feedback_scores.values()) / len(self.tutorial_stats.average_feedback_scores)
                stats_embed.add_field(
                    name="⭐ 平均評価",
                    value=f"{avg_all_scores:.1f}/5.0",
                    inline=True
                )
            
            # 最も放棄率の高いステップ
            if self.tutorial_stats.step_abandonment_rates:
                max_abandonment_step = max(self.tutorial_stats.step_abandonment_rates.items(), key=lambda x: x[1])
                step_index, abandonment_rate = max_abandonment_step
                if step_index < len(self.tutorial_steps):
                    step = self.tutorial_steps[step_index]
                    stats_embed.add_field(
                        name="⚠️ 改善が必要なステップ",
                        value=f"{step.title}: {abandonment_rate:.1%}の放棄率",
                        inline=False
                    )
            
            stats_embed.set_footer(text="みやにゃんによる統計分析 📈")
            
            await channel.send(embed=stats_embed)
    
    async def pause_tutorial(self, user_id: str):
        """チュートリアルを一時停止"""
        if user_id in self.tutorial_progress:
            progress = self.tutorial_progress[user_id]
            progress.is_paused = True
            progress.last_activity = datetime.datetime.now()
            self.save_tutorial_progress()
            return True
        return False
    
    async def resume_tutorial(self, user_id: str):
        """チュートリアルを再開"""
        if user_id in self.tutorial_progress:
            progress = self.tutorial_progress[user_id]
            progress.is_paused = False
            progress.last_activity = datetime.datetime.now()
            self.save_tutorial_progress()
            return True
        return False
    
    async def start_reminder_system(self):
        """リマインダーシステムを開始"""
        while True:
            try:
                for user_id, progress in self.tutorial_progress.items():
                    if not progress.is_paused and not progress.completion_time:
                        # 24時間ごとにリマインダーをチェック
                        time_since_activity = datetime.datetime.now() - progress.last_activity
                        if time_since_activity.total_seconds() >= 24 * 3600:  # 24時間
                            # リマインダータスクを作成
                            for bot in self.bots.values():
                                await self.send_tutorial_reminder(user_id, bot)
                                break
                
                # 1時間ごとにチェック
                await asyncio.sleep(3600)
                
            except Exception as e:
                print(f"❌ リマインダーシステムエラー: {e}")
                await asyncio.sleep(3600)
    
    async def start_bot(self, character_id: str) -> bool:
        """指定されたキャラクターのBotを起動"""
        if character_id not in self.characters:
            print(f"❌ 未知のキャラクター: {character_id}")
            return False
        
        character = self.characters[character_id]
        token = os.getenv(character.token_env_var)
        
        if not token:
            print(f"⚠️ {character.name} のトークンが設定されていません: {character.token_env_var}")
            return False
        
        if token == 'your_discord_bot_token_here':
            print(f"⚠️ {character.name} のトークンが仮の値です")
            return False
        
        try:
            bot = self.create_bot_client(character_id)
            self.bots[character_id] = bot
            
            # バックグラウンドでBot起動
            task = asyncio.create_task(bot.start(token))
            self.bot_tasks[character_id] = task
            
            print(f"🚀 {character.emoji} {character.name} を起動中...")
            return True
            
        except Exception as e:
            print(f"❌ {character.name} の起動に失敗: {e}")
            return False
    
    async def start_all_bots(self) -> Dict[str, bool]:
        """すべてのBotを起動"""
        print("🎭 複数Bot管理システムを起動中...")
        results = {}
        
        for character_id in self.characters.keys():
            results[character_id] = await self.start_bot(character_id)
            await asyncio.sleep(2)  # 起動間隔を空ける
        
        # リマインダーシステムを起動
        if any(results.values()):
            print("⏰ チュートリアルリマインダーシステムを起動中...")
            asyncio.create_task(self.start_reminder_system())
        
        # 起動結果の表示
        print("\n" + "="*50)
        print("🎪 Bot起動結果:")
        for character_id, success in results.items():
            character = self.characters[character_id]
            status = "✅ 起動成功" if success else "❌ 起動失敗"
            print(f"  {character.emoji} {character.name}: {status}")
        print("🔔 チュートリアルリマインダー: ✅ 起動中")
        print("="*50)
        
        return results
    
    async def stop_bot(self, character_id: str):
        """指定されたBotを停止"""
        if character_id in self.bots:
            await self.bots[character_id].close()
            del self.bots[character_id]
        
        if character_id in self.bot_tasks:
            self.bot_tasks[character_id].cancel()
            del self.bot_tasks[character_id]
        
        character = self.characters[character_id]
        print(f"🛑 {character.emoji} {character.name} を停止しました")
    
    async def stop_all_bots(self):
        """すべてのBotを停止"""
        print("🛑 すべてのBotを停止中...")
        
        for character_id in list(self.bots.keys()):
            await self.stop_bot(character_id)
        
        print("✅ すべてのBotが停止しました")
    
    def get_active_bots(self) -> List[str]:
        """アクティブなBotのリストを取得"""
        return list(self.bots.keys())
    
    def get_character_info(self, character_id: str) -> Optional[BotCharacter]:
        """キャラクター情報を取得"""
        return self.characters.get(character_id)
    
    async def wait_for_bots(self):
        """すべてのBotタスクの完了を待機"""
        if self.bot_tasks:
            await asyncio.gather(*self.bot_tasks.values(), return_exceptions=True)

    def load_tutorial_progress(self) -> Dict[str, TutorialProgress]:
        """チュートリアル進捗データを読み込み"""
        try:
            if os.path.exists(self.tutorial_data_file):
                with open(self.tutorial_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                progress_dict = {}
                for user_id, progress_data in data.items():
                    # 日時の復元
                    progress_data['started_at'] = datetime.datetime.fromisoformat(progress_data['started_at'])
                    progress_data['last_activity'] = datetime.datetime.fromisoformat(progress_data['last_activity'])
                    if progress_data.get('completion_time'):
                        progress_data['completion_time'] = datetime.datetime.fromisoformat(progress_data['completion_time'])
                    
                    # Setの復元
                    progress_data['completed_steps'] = set(progress_data['completed_steps'])
                    
                    progress_dict[user_id] = TutorialProgress(**progress_data)
                
                return progress_dict
        except Exception as e:
            print(f"⚠️ チュートリアル進捗データの読み込みに失敗: {e}")
        
        return {}
    
    def save_tutorial_progress(self):
        """チュートリアル進捗データを保存"""
        try:
            data = {}
            for user_id, progress in self.tutorial_progress.items():
                progress_dict = asdict(progress)
                # 日時の変換
                progress_dict['started_at'] = progress.started_at.isoformat()
                progress_dict['last_activity'] = progress.last_activity.isoformat()
                if progress.completion_time:
                    progress_dict['completion_time'] = progress.completion_time.isoformat()
                else:
                    progress_dict['completion_time'] = None
                
                # Setの変換
                progress_dict['completed_steps'] = list(progress.completed_steps)
                
                data[user_id] = progress_dict
            
            with open(self.tutorial_data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ チュートリアル進捗データの保存に失敗: {e}")
    
    def load_tutorial_stats(self) -> TutorialStats:
        """チュートリアル統計データを読み込み"""
        try:
            if os.path.exists(self.tutorial_stats_file):
                with open(self.tutorial_stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return TutorialStats(**data)
        except Exception as e:
            print(f"⚠️ チュートリアル統計データの読み込みに失敗: {e}")
        
        return TutorialStats(
            total_users=0,
            completed_users=0,
            completion_rate=0.0,
            average_completion_time=0.0,
            step_abandonment_rates={},
            average_feedback_scores={},
            most_common_help_requests=[]
        )
    
    def save_tutorial_stats(self):
        """チュートリアル統計データを保存"""
        try:
            with open(self.tutorial_stats_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.tutorial_stats), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ チュートリアル統計データの保存に失敗: {e}")
    
    def load_custom_tutorial_steps(self) -> List[TutorialStep]:
        """カスタムチュートリアルステップを読み込み"""
        try:
            custom_steps_file = "custom_tutorial_steps.json"
            if os.path.exists(custom_steps_file):
                with open(custom_steps_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return [TutorialStep(**step_data) for step_data in data]
        except Exception as e:
            print(f"⚠️ カスタムチュートリアルステップの読み込みに失敗: {e}")
        
        return []
    
    def update_tutorial_stats(self):
        """チュートリアル統計を更新"""
        if not self.tutorial_progress:
            return
        
        completed_users = sum(1 for p in self.tutorial_progress.values() if p.completion_time is not None)
        total_users = len(self.tutorial_progress)
        
        completion_times = [
            (p.completion_time - p.started_at).total_seconds() / 3600  # 時間単位
            for p in self.tutorial_progress.values() 
            if p.completion_time is not None
        ]
        
        # ステップ別放棄率の計算
        step_abandonment_rates = {}
        for step_index in range(len(self.tutorial_steps)):
            users_reached_step = sum(1 for p in self.tutorial_progress.values() if p.current_step >= step_index)
            users_completed_step = sum(1 for p in self.tutorial_progress.values() if step_index in p.completed_steps)
            
            if users_reached_step > 0:
                step_abandonment_rates[step_index] = 1.0 - (users_completed_step / users_reached_step)
        
        # フィードバックスコア平均の計算
        average_feedback_scores = {}
        for step_index in range(len(self.tutorial_steps)):
            scores = [p.feedback_scores.get(step_index, 0) for p in self.tutorial_progress.values() if step_index in p.feedback_scores]
            if scores:
                average_feedback_scores[step_index] = sum(scores) / len(scores)
        
        # 統計の更新
        self.tutorial_stats = TutorialStats(
            total_users=total_users,
            completed_users=completed_users,
            completion_rate=completed_users / total_users if total_users > 0 else 0.0,
            average_completion_time=sum(completion_times) / len(completion_times) if completion_times else 0.0,
            step_abandonment_rates=step_abandonment_rates,
            average_feedback_scores=average_feedback_scores,
            most_common_help_requests=self.tutorial_stats.most_common_help_requests  # 保持
        )
        
        self.save_tutorial_stats()

# 使用例とテスト関数
async def main():
    """テスト用メイン関数"""
    manager = MultiBotManager()
    
    try:
        # すべてのBotを起動
        results = await manager.start_all_bots()
        
        # 成功したBotがあれば待機
        if any(results.values()):
            print("\n📱 Botが起動しました。停止するには Ctrl+C を押してください...")
            await manager.wait_for_bots()
        else:
            print("❌ すべてのBotの起動に失敗しました")
            
    except KeyboardInterrupt:
        print("\n🛑 停止シグナルを受信しました...")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
    finally:
        await manager.stop_all_bots()

if __name__ == "__main__":
    asyncio.run(main()) 