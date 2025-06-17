#!/usr/bin/env python3
"""
Discord にゃんこエージェント - 単一ボット実行スクリプト
環境変数BOT_CHARACTERで指定されたキャラクターのボットを起動
"""

import os
import sys
import asyncio
import threading
import time
from pathlib import Path
from dotenv import load_dotenv
import traceback

# 環境変数の読み込み
load_dotenv()

def check_requirements():
    """必要な環境変数とファイルの存在確認"""
    print("🔍 環境設定を確認中...")
    
    # BOT_CHARACTER の確認
    bot_character = os.getenv('BOT_CHARACTER')
    if not bot_character:
        print("❌ エラー: BOT_CHARACTER が設定されていません")
        print("   BOT_CHARACTER=miya または BOT_CHARACTER=eve を設定してください")
        return False
    
    if bot_character not in ['miya', 'eve']:
        print(f"❌ エラー: 不正なBOT_CHARACTER: {bot_character}")
        print("   BOT_CHARACTER は 'miya' または 'eve' である必要があります")
        return False
    
    # Discord Bot Token の確認
    if bot_character == 'miya':
        token_var = 'DISCORD_BOT_TOKEN_MIYA'
    else:
        token_var = 'DISCORD_BOT_TOKEN_EVE'
    
    discord_token = os.getenv(token_var)
    if not discord_token:
        print(f"❌ エラー: {token_var} が設定されていません")
        return False
    elif discord_token == 'your_discord_bot_token_here':
        print(f"⚠️ 警告: {token_var} が仮の値です")
        print("   テストモードで実行されます")
    
    # Firebase設定の確認
    firebase_service_account = os.getenv('FIREBASE_SERVICE_ACCOUNT')
    firebase_key_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH')
    
    if not firebase_service_account and not firebase_key_path:
        print("❌ エラー: Firebase設定が見つかりません")
        print("   FIREBASE_SERVICE_ACCOUNT または FIREBASE_SERVICE_ACCOUNT_KEY_PATH を設定してください")
        return False
    
    if firebase_key_path and not Path(firebase_key_path).exists():
        print(f"❌ エラー: Firebaseサービスアカウントキーファイルが見つかりません: {firebase_key_path}")
        return False
    
    # Gemini API Key の確認
    gemini_key = os.getenv('GEMINI_API_KEY')
    if not gemini_key:
        print("⚠️ 警告: GEMINI_API_KEY が設定されていません")
        print("   固定応答モードで動作します")
    
    print(f"✅ 環境設定の確認が完了しました (キャラクター: {bot_character})")
    return True

def install_dependencies():
    """依存関係のインストール確認"""
    print("📦 依存関係を確認中...")
    
    try:
        import discord
        import firebase_admin
        import google.generativeai
        print("✅ 必要なライブラリがインストールされています")
        return True
    except ImportError as e:
        print(f"❌ エラー: 必要なライブラリがインストールされていません: {e}")
        print("   以下のコマンドで依存関係をインストールしてください:")
        print("   pip install -r requirements.txt")
        return False

def start_health_server():
    """ヘルスチェックサーバーを別スレッドで開始"""
    try:
        from health_server import start_health_server as start_health, update_bot_status
        print("🏥 ヘルスチェックサーバーを開始中...")
        print(f"   ポート: {os.getenv('PORT', '8080')}")
        
        # 別スレッドでヘルスサーバーを起動
        health_thread = threading.Thread(target=start_health, daemon=True)
        health_thread.start()
        
        # 少し待ってからボット状態を更新
        time.sleep(2)
        update_bot_status(True)
        
        print("✅ ヘルスチェックサーバーが起動しました")
        return True
    except Exception as e:
        print(f"⚠️ ヘルスチェックサーバーの起動に失敗: {e}")
        print("   ボットは継続して動作しますが、Cloud Run のヘルスチェックが利用できません")
        return False

class SingleBotManager:
    """単一ボット管理クラス"""
    
    def __init__(self, character_id: str):
        self.character_id = character_id
        # MultiBotManagerから必要な部分をインポート（ファイルが存在しないため無効化）
        # from multi_bot_manager import MultiBotManager
        # self.multi_manager = MultiBotManager()
        print("❌ エラー: multi_bot_manager.py が存在しないため、このスクリプトは使用できません")
        print("   代わりに run_entertainment_bot.py を使用してください")
        raise ImportError("multi_bot_manager.py が存在しません")
        
        if character_id not in self.multi_manager.characters:
            raise ValueError(f"Unknown character: {character_id}")
        
        self.character = self.multi_manager.characters[character_id]
        print(f"🎭 {self.character.emoji} {self.character.name} を初期化中...")
    
    async def start_bot(self):
        """ボットを起動"""
        try:
            # トークンを取得
            token = os.getenv(self.character.token_env_var)
            if not token:
                print(f"❌ エラー: {self.character.name} のトークンが設定されていません: {self.character.token_env_var}")
                return False
            
            if token == 'your_discord_bot_token_here':
                print(f"⚠️ 警告: {self.character.name} のトークンが仮の値です")
                return False
            
            # ボットクライアントを作成
            bot = self.multi_manager.create_bot_client(self.character_id)
            
            print(f"🚀 {self.character.emoji} {self.character.name} を起動中...")
            print(f"   役割: {self.character.role}")
            print(f"   トリガーワード: {', '.join(self.character.response_triggers)}")
            
            # ボットを起動
            await bot.start(token)
            
        except Exception as e:
            print(f"❌ {self.character.name} の起動に失敗: {e}")
            traceback.print_exc()
            return False

def main():
    """メイン実行関数"""
    print("🐱 Discord にゃんこエージェント - 単一ボット起動中...")
    print("=" * 50)
    
    # BOT_CHARACTER環境変数を取得
    character_id = os.getenv('BOT_CHARACTER')
    if not character_id:
        print("❌ エラー: BOT_CHARACTER 環境変数が設定されていません")
        sys.exit(1)
    
    # Cloud Run 環境の検出
    is_cloud_run = os.getenv('K_SERVICE') is not None or os.getenv('PORT') is not None
    if is_cloud_run:
        print("☁️ Cloud Run 環境を検出しました")
        # ヘルスチェックサーバーを最初に開始
        if not start_health_server():
            print("⚠️ ヘルスチェックサーバーの起動に失敗しましたが、ボットの起動を続行します")
    
    # 環境確認
    if not check_requirements():
        if is_cloud_run:
            # Cloud Run環境では、ヘルスサーバーを動作させ続ける
            print("⚠️ 環境設定エラーですが、Cloud Run環境のためヘルスサーバーを維持します")
            try:
                # 無限ループでヘルスサーバーを維持
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                pass
        sys.exit(1)
    
    if not install_dependencies():
        if is_cloud_run:
            # Cloud Run環境では、ヘルスサーバーを動作させ続ける
            print("⚠️ 依存関係エラーですが、Cloud Run環境のためヘルスサーバーを維持します")
            try:
                # 無限ループでヘルスサーバーを維持
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                pass
        sys.exit(1)
    
    # 単一ボットマネージャーを作成
    try:
        bot_manager = SingleBotManager(character_id)
    except ValueError as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)
    
    # ボットの実行
    print(f"🚀 {bot_manager.character.name} を起動します...")
    print("   停止するには Ctrl+C を押してください")
    print("=" * 50)
    
    try:
        # ボットを非同期で起動
        loop = asyncio.get_event_loop()
        loop.run_until_complete(bot_manager.start_bot())

    except KeyboardInterrupt:
        print(f"\n🛑 {bot_manager.character.name} が停止されました")
        if is_cloud_run:
            try:
                from health_server import update_bot_status
                update_bot_status(False)  # ヘルスチェックサーバーにも通知
            except:
                pass
                
    except Exception as e:
        print(f"❌ ボット実行中にエラーが発生しました: {e}")
        traceback.print_exc()
        
        if is_cloud_run:
            try:
                from health_server import update_bot_status
                update_bot_status(False)  # ヘルスチェックサーバーにも通知
                print("☁️ Cloud Run環境のため、ヘルスサーバーを維持します")
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                pass
        
        sys.exit(1)

if __name__ == "__main__":
    main()