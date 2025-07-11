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
import asyncio
import traceback
# from multi_bot_manager import MultiBotManager  # このファイルは存在しないため無効化

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
        # ヘルスチェックサーバーを別スレッドで開始
        if not start_health_server():
            print("⚠️ ヘルスチェックサーバーの起動に失敗しましたが、ボットの起動を続行します")
    
    # 環境確認
    if not check_requirements():
        print("❌ 環境設定に問題があります")
        if is_cloud_run:
            print("☁️ Cloud Run環境のため、ヘルスサーバーのみ動作させます")
            # ヘルスサーバーがすでに別スレッドで起動しているので、メインスレッドで待機
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                pass
        sys.exit(1)
    
    if not install_dependencies():
        print("❌ 依存関係に問題があります")
        if is_cloud_run:
            print("☁️ Cloud Run環境のため、ヘルスサーバーのみ動作させます")
            # ヘルスサーバーがすでに別スレッドで起動しているので、メインスレッドで待機
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                pass
        sys.exit(1)
    
    # MultiBotManagerのインスタンスを作成（ファイルが存在しないため無効化）
    # bot_manager = MultiBotManager()
    print("❌ エラー: multi_bot_manager.py が存在しないため、このスクリプトは使用できません")
    print("   代わりに run_entertainment_bot.py を使用してください")
    if is_cloud_run:
        # Cloud Run環境では、ヘルスサーバーのみ維持
        print("☁️ Cloud Run環境のため、ヘルスサーバーのみ維持します")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            pass
    sys.exit(1)
    
    # ボットの実行
    print("🚀 複数ボットを起動します...")
    print("   停止するには Ctrl+C を押してください")
    print("=" * 50)
    
    try:
        # 非同期でボットを起動
        async def run_bots():
            # 全てのボットを非同期で起動
            results = await bot_manager.start_all_bots()
            
            # ヘルスチェックサーバーにボット状態を通知
            if is_cloud_run:
                try:
                    from health_server import update_bot_status
                    update_bot_status(any(results.values()))
                except Exception as e:
                    print(f"⚠️ ヘルスステータス更新に失敗: {e}")
            
            # 成功したボットがあれば待機
            if any(results.values()):
                print("\n📱 Botが起動しました。")
                if is_cloud_run:
                    print("☁️ Cloud Run環境で動作中...")
                else:
                    print("   停止するには Ctrl+C を押してください")
                await bot_manager.wait_for_bots()
            else:
                print("❌ 全てのBotの起動に失敗しました")
                if is_cloud_run:
                    print("☁️ Cloud Run環境のため、ヘルスサーバーのみ維持します")
                    # 無限待機（ヘルスサーバーは別スレッドで動作）
                    while True:
                        await asyncio.sleep(60)
        
        # イベントループで実行
        asyncio.run(run_bots())

    except KeyboardInterrupt:
        print("\n🛑 ボットが停止されました")
        if is_cloud_run:
            try:
                from health_server import update_bot_status
                update_bot_status(False)
            except:
                pass
        # ボット停止処理
        asyncio.run(bot_manager.stop_all_bots())
                
    except Exception as e:
        print(f"❌ ボット実行中にエラーが発生しました: {e}")
        traceback.print_exc()
        
        if is_cloud_run:
            try:
                from health_server import update_bot_status
                update_bot_status(False)
                print("☁️ Cloud Run環境のため、ヘルスサーバーを維持します")
                # 無限待機（ヘルスサーバーは別スレッドで動作）
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                pass
        
        # エラー時もボット停止処理
        asyncio.run(bot_manager.stop_all_bots())
        sys.exit(1)

if __name__ == "__main__":
    main() 