#!/usr/bin/env python3
"""
Discord にゃんこエージェント ボット実行スクリプト
現在のFirestore構造と連動したDiscordボット
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

def check_requirements():
    """必要な環境変数とファイルの存在確認"""
    print("🔍 環境設定を確認中...")
    
    # Discord Bot Token の確認
    discord_token = os.getenv('DISCORD_BOT_TOKEN')
    if not discord_token:
        print("❌ エラー: DISCORD_BOT_TOKEN が設定されていません")
        print("   環境変数またはenv_example.txtを参考に.envファイルを作成してください")
        return False
    
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
    
    print("✅ 環境設定の確認が完了しました")
    return True

def install_dependencies():
    """依存関係のインストール確認"""
    print("📦 依存関係を確認中...")
    
    try:
        import discord
        import firebase_admin
        print("✅ 必要なライブラリがインストールされています")
        return True
    except ImportError as e:
        print(f"❌ エラー: 必要なライブラリがインストールされていません: {e}")
        print("   以下のコマンドで依存関係をインストールしてください:")
        print("   pip install -r requirements.txt")
        return False

def main():
    """メイン実行関数"""
    print("🐱 Discord にゃんこエージェント ボット起動中...")
    print("=" * 50)
    
    # 環境確認
    if not check_requirements():
        sys.exit(1)
    
    if not install_dependencies():
        sys.exit(1)
    
    # ボットの実行
    print("🚀 ボットを起動します...")
    print("   停止するには Ctrl+C を押してください")
    print("=" * 50)
    
    try:
        # discord-bot.pyをインポートして実行
        import discord_bot
    except KeyboardInterrupt:
        print("\n🛑 ボットが停止されました")
    except Exception as e:
        print(f"❌ ボット実行中にエラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 