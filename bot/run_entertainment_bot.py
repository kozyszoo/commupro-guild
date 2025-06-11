#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_entertainment_bot.py
Discordエンタメコンテンツ制作アプリ メイン実行スクリプト

統合されたエンタメBotを実行
"""

import asyncio
import os
import sys
import signal
from dotenv import load_dotenv

# プロジェクトのsrcディレクトリをPythonパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.entertainment_bot import create_entertainment_bot
from utils.firestore import initialize_firebase

# 環境変数読み込み
load_dotenv()

class EntertainmentBotRunner:
    """エンタメBot実行管理クラス"""
    
    def __init__(self):
        self.bot = None
        self.db = None
        self.running = False
    
    async def initialize(self):
        """Bot初期化"""
        print("🎬 Discordエンタメコンテンツ制作アプリを初期化中...")
        
        try:
            # Firebase初期化
            print("🔥 Firebase接続中...")
            self.db = await initialize_firebase()
            if not self.db:
                raise Exception("Firebase初期化に失敗しました")
            
            # Bot作成
            print("🤖 Bot作成中...")
            self.bot = await create_entertainment_bot(self.db)
            
            print("✅ 初期化完了")
            return True
            
        except Exception as e:
            print(f"❌ 初期化エラー: {e}")
            return False
    
    async def start(self):
        """Bot開始"""
        if not self.bot:
            print("❌ Botが初期化されていません")
            return False
        
        try:
            discord_token = os.getenv('DISCORD_BOT_TOKEN')
            if not discord_token:
                raise Exception("DISCORD_BOT_TOKENが設定されていません")
            
            print("🚀 Discord エンタメコンテンツ制作Bot を開始...")
            self.running = True
            
            await self.bot.start(discord_token)
            
        except Exception as e:
            print(f"❌ Bot開始エラー: {e}")
            self.running = False
            return False
    
    async def stop(self):
        """Bot停止"""
        if self.bot and self.running:
            print("🛑 Bot停止中...")
            await self.bot.shutdown()
            self.running = False
            print("✅ Bot停止完了")
    
    def setup_signal_handlers(self):
        """シグナルハンドラー設定"""
        def signal_handler(signum, frame):
            print(f"\n📡 シグナル受信: {signum}")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """メイン実行関数"""
    print("=" * 60)
    print("🎬 Discord エンタメコンテンツ制作アプリ")
    print("=" * 60)
    
    runner = EntertainmentBotRunner()
    
    try:
        # シグナルハンドラー設定
        runner.setup_signal_handlers()
        
        # 初期化
        if not await runner.initialize():
            print("❌ 初期化に失敗しました")
            return
        
        # 環境設定の表示
        print("\n📋 設定情報:")
        print(f"   コマンドプレフィックス: {os.getenv('BOT_COMMAND_PREFIX', '!')}")
        print(f"   自動スケジューラー: {os.getenv('AUTO_START_SCHEDULER', 'false')}")
        print(f"   週次スケジュール: 毎週{os.getenv('WEEKLY_SCHEDULE_DAY', 'monday')} {os.getenv('WEEKLY_SCHEDULE_TIME', '09:00')}")
        print(f"   要約投稿チャンネルID: {os.getenv('DISCORD_SUMMARY_CHANNEL_ID', '未設定')}")
        print(f"   Google Drive フォルダID: {os.getenv('GOOGLE_DRIVE_FOLDER_ID', '未設定')}")
        
        print("\n🎯 主要機能:")
        print("   ✅ Discord アクティビティ分析")
        print("   ✅ Vertex AI (Gemini) による週次まとめ生成")
        print("   ✅ Bot同士の対話形式コンテンツ")
        print("   ✅ Text-to-Speech 音声生成")
        print("   ✅ Google Drive 自動保存")
        print("   ✅ Discord 自動投稿")
        print("   ✅ 週次スケジューラー")
        
        print("\n💡 利用可能なコマンド:")
        print("   !help - ヘルプ表示")
        print("   !status - システム状態")
        print("   !scheduler start/stop/status - スケジューラー操作")
        print("   !summary [days] - 手動まとめ生成")
        print("   !analytics [days] - アクティビティ分析")
        print("   !podcast [days] - ポッドキャスト生成")
        
        print("\n🚀 Bot開始...")
        
        # Bot開始
        await runner.start()
        
    except KeyboardInterrupt:
        print("\n⏹️ ユーザーによる停止")
    except Exception as e:
        print(f"\n❌ 実行エラー: {e}")
    finally:
        await runner.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 終了")
    except Exception as e:
        print(f"\n💥 予期しないエラー: {e}")
        sys.exit(1)