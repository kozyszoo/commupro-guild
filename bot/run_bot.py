#!/usr/bin/env python3
"""
Discord にゃんこエージェント ボット実行スクリプト
現在のFirestore構造と連動したDiscordボット
Cloud Run 対応版
"""

import os
import sys
import threading
import time
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
    elif discord_token == 'your_discord_bot_token_here':
        print("⚠️ 警告: DISCORD_BOT_TOKEN が仮の値です")
        print("   テストモードで実行されます（Firebase接続のみ確認）")
    
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

def start_health_server():
    """ヘルスチェックサーバーを別スレッドで開始"""
    try:
        from health_server import start_health_server, update_bot_status
        print("🏥 ヘルスチェックサーバーを開始中...")
        
        # 別スレッドでヘルスサーバーを起動
        health_thread = threading.Thread(target=start_health_server, daemon=True)
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

def main():
    """メイン実行関数"""
    print("🐱 Discord にゃんこエージェント ボット起動中...")
    print("=" * 50)
    
    # Cloud Run 環境の検出
    is_cloud_run = os.getenv('K_SERVICE') is not None
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
    
    # Discord Bot Tokenの確認
    discord_token = os.getenv('DISCORD_BOT_TOKEN')
    if discord_token == 'your_discord_bot_token_here':
        print("📋 テストモード: Firebase接続のみ確認します...")
        print("=" * 50)
        
        try:
            # discord_bot.pyをインポートして初期化部分のみ実行
            import discord_bot
            print("=" * 50)
            print("🔧 実際にボットを動作させるには:")
            print("   1. Discord Developer Portal (https://discord.com/developers/applications) でボットを作成")
            print("   2. Bot Tokenを取得")
            print("   3. 環境変数 DISCORD_BOT_TOKEN に設定")
            print("   4. ボットをDiscordサーバーに招待")
            print("   5. 再度実行")
            print("=" * 50)
        except Exception as e:
            print(f"❌ テストモード実行中にエラーが発生しました: {e}")
        
        if is_cloud_run:
            # Cloud Run環境では、ヘルスサーバーを動作させ続ける
            print("☁️ Cloud Run環境のため、ヘルスサーバーを維持します")
            try:
                # 無限ループでヘルスサーバーを維持
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                pass
        return
    
    # ボットの実行
    print("🚀 ボットを起動します...")
    print("   停止するには Ctrl+C を押してください")
    print("=" * 50)
    
    try:
        # discord_bot.pyをインポート
        import discord_bot
        
        # ボットを実際に起動（Firebase初期化はon_readyイベントで実行される）
        print("🚀 Discord ボットを起動中...")
        
        # Cloud Run環境の場合、ボット状態を更新
        if is_cloud_run:
            try:
                from health_server import update_bot_status
                update_bot_status(True)
            except:
                pass
        
        discord_bot.bot.run(discord_token)
        
    except KeyboardInterrupt:
        print("\n🛑 ボットが停止されました")
        
        # Cloud Run環境の場合、ボット状態を更新
        if is_cloud_run:
            try:
                from health_server import update_bot_status
                update_bot_status(False)
            except:
                pass
                
    except Exception as e:
        print(f"❌ ボット実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        
        # Cloud Run環境の場合、ボット状態を更新
        if is_cloud_run:
            try:
                from health_server import update_bot_status
                update_bot_status(False)
                # ヘルスサーバーを維持
                print("☁️ Cloud Run環境のため、ヘルスサーバーを維持します")
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                pass
        
        sys.exit(1)

if __name__ == "__main__":
    main() 