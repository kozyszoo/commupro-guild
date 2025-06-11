#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_startup.py
Discord エンタメコンテンツ制作アプリ 起動テスト
"""

import sys
import os
sys.path.append('src')

# テスト用環境変数読み込み
from dotenv import load_dotenv
load_dotenv('.env.test')

print('🎬 Discord エンタメコンテンツ制作アプリ - 起動テスト')
print('=' * 60)

# 環境変数確認
print('📋 設定値確認:')
print(f'   コマンドプレフィックス: {os.getenv("BOT_COMMAND_PREFIX", "!")}')
print(f'   自動スケジューラー: {os.getenv("AUTO_START_SCHEDULER", "false")}')
print(f'   週次スケジュール: 毎週{os.getenv("WEEKLY_SCHEDULE_DAY", "monday")} {os.getenv("WEEKLY_SCHEDULE_TIME", "09:00")}')
print(f'   Google Cloud プロジェクト: {os.getenv("GOOGLE_CLOUD_PROJECT", "未設定")}')
print(f'   Google Drive フォルダ: {os.getenv("GOOGLE_DRIVE_FOLDER_ID", "未設定")}')

print('\n🧪 初期化テスト:')

# Firestoreクライアント（モック）
class MockFirestoreClient:
    def collection(self, name):
        return self
    def add(self, data):
        return (None, type('Doc', (), {'id': 'test_id'}))

print('✅ MockFirestoreClient作成')

# Discord Analytics テスト
try:
    from core.discord_analytics import DiscordAnalytics
    analytics = DiscordAnalytics(MockFirestoreClient())
    print('✅ DiscordAnalytics初期化成功')
except Exception as e:
    print(f'❌ DiscordAnalytics初期化エラー: {e}')

# Content Creator テスト  
try:
    from core.content_creator import ContentCreator
    content_creator = ContentCreator(MockFirestoreClient())
    print('✅ ContentCreator初期化成功')
except Exception as e:
    print(f'❌ ContentCreator初期化エラー: {e}')

# Scheduler テスト
try:
    from core.scheduler import WeeklyContentScheduler
    scheduler = WeeklyContentScheduler(MockFirestoreClient())
    status = scheduler.get_status()
    print(f'✅ WeeklyContentScheduler初期化成功')
    print(f'   状態: {"実行中" if status["is_running"] else "停止中"}')
    print(f'   設定: 毎週{status["schedule_day"]} {status["schedule_time"]}')
except Exception as e:
    print(f'❌ WeeklyContentScheduler初期化エラー: {e}')

print('\n🎯 機能テスト:')

# キャラクター設定確認
try:
    bot_personas = analytics.bot_personas
    print('✅ キャラクター設定:')
    for key, persona in bot_personas.items():
        print(f'   {persona["name"]}: {persona["role"]}')
except Exception as e:
    print(f'❌ キャラクター設定エラー: {e}')

# ダミーデータでのテスト
print('\n🔬 ダミーデータテスト:')
try:
    # ダミー統計データ
    dummy_stats = {
        'total_messages': 150,
        'active_users_count': 12,
        'active_channels_count': 5,
        'events_count': 2,
        'top_users': [('user1', 25), ('user2', 20), ('user3', 18)],
        'top_channels': [('general', 45), ('dev', 30), ('random', 25)],
        'popular_keywords': [('python', 8), ('discord', 6), ('bot', 5)]
    }
    
    # プロンプト生成テスト
    prompt = analytics._create_summary_prompt({'summary_stats': dummy_stats})
    print(f'✅ プロンプト生成テスト成功（長さ: {len(prompt)}文字）')
    
    # フォールバック要約テスト
    fallback = analytics._create_fallback_summary({'summary_stats': dummy_stats})
    print(f'✅ フォールバック要約テスト成功（長さ: {len(fallback)}文字）')
    
except Exception as e:
    print(f'❌ ダミーデータテストエラー: {e}')

print('\n✅ 起動テスト完了！')
print('\n💡 実際の使用時は以下を設定してください:')
print('   - Discord Bot Token')
print('   - Firebase Service Account Key')
print('   - Google Cloud APIs有効化')
print('   - Google Drive フォルダ権限')
print('\n🚀 起動コマンド: python run_entertainment_bot.py')