#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discord にゃんこエージェント - 複数Bot管理システム
4つのキャラクター（みやにゃん、イヴにゃん、みやにゃん2、いぶにゃん）を管理
"""

import discord
import asyncio
import os
import datetime
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv
from dataclasses import dataclass

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

class MultiBotManager:
    """複数Discord Botの管理クラス"""
    
    def __init__(self):
        # キャラクター設定（みやにゃんとイヴにゃんの2体）
        self.characters = {
            'miya': BotCharacter(
                name='みやにゃん',
                token_env_var='DISCORD_BOT_TOKEN_MIYA', # みやにゃん用トークン環境変数
                emoji='🐈',
                personality='フレンドリーで好奇心旺盛、新しい技術に興味津々',
                speaking_style='だにゃ、にゃ〜、だよにゃ',
                role='技術解説・コミュニティサポート',
                color=0xFF69B4,  # ピンク
                response_triggers=['みやにゃん', 'miya', '技術', 'プログラミング', 'コード']
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
        
        self.bots: Dict[str, discord.Client] = {}
        self.bot_tasks: Dict[str, asyncio.Task] = {}
        
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
        async def on_message(message):
            # 自分のメッセージは無視
            if message.author == bot.user:
                return
            
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
        
        return bot
    
    async def handle_character_response(self, message: discord.Message, character_id: str, bot: discord.Client):
        """キャラクター別の応答処理"""
        character = self.characters[character_id]
        
        # キャラクター別の応答生成
        response = await self.generate_character_response(message.content, character_id, message.author.name)
        
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
    
    async def generate_character_response(self, content: str, character_id: str, user_name: str) -> str:
        """キャラクター別の応答を生成"""
        character = self.characters[character_id]
        
        # 簡単な応答システム（実際はAIと連携）
        responses = {
            'miya': [
                f"こんにちはにゃ〜、{user_name}さん！技術的な質問があれば何でも聞いてくださいにゃ！",
                f"プログラミングの話だにゃ〜！楽しそうですにゃ！",
                f"新しい技術について一緒に学びましょうにゃ〜！"
            ],
            'eve': [
                f"{user_name}さん、データ分析のお手伝いをしますにゃ。",
                f"統計的に見ると興味深い内容ですにゃ。",
                f"分析結果をまとめてレポートしますにゃ。"
            ]
        }
        
        import random
        return random.choice(responses.get(character_id, [f"こんにちはにゃ、{user_name}さん！"]))
    
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
        
        # 起動結果の表示
        print("\n" + "="*50)
        print("🎪 Bot起動結果:")
        for character_id, success in results.items():
            character = self.characters[character_id]
            status = "✅ 起動成功" if success else "❌ 起動失敗"
            print(f"  {character.emoji} {character.name}: {status}")
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