#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_advanced.py
Discord エンタメコンテンツ制作アプリ 高度な機能テスト
"""

import sys
import os
import asyncio
import json
from datetime import datetime, timezone, timedelta
sys.path.append('src')

# テスト用環境変数読み込み
from dotenv import load_dotenv
load_dotenv('.env.test')

print('🎬 Discord エンタメコンテンツ制作アプリ - 高度な機能テスト')
print('=' * 70)

# 拡張モッククラス
class ExtendedMockFirestoreClient:
    def __init__(self):
        self.collections = {}
        
    def collection(self, name):
        if name not in self.collections:
            self.collections[name] = ExtendedMockCollection(name)
        return self.collections[name]

class ExtendedMockCollection:
    def __init__(self, name):
        self.name = name
        self.documents = []
        
    def add(self, data):
        doc_id = f"mock_doc_{len(self.documents)}"
        self.documents.append({'id': doc_id, 'data': data})
        return (None, type('Doc', (), {'id': doc_id}))
    
    def where(self, field, op, value):
        return self
    
    def order_by(self, field, direction=None):
        return self
    
    def limit(self, count):
        return self
    
    def get(self):
        # モックドキュメントを返す
        mock_docs = []
        for i in range(min(3, len(self.documents) + 3)):  # 最低3つのモックデータ
            mock_data = {
                'id': f'mock_doc_{i}',
                'timestamp': datetime.now(timezone.utc) - timedelta(days=i),
                'username': f'test_user_{i}',
                'channelName': f'test_channel_{i}',
                'content': f'テストメッセージ {i}',
                'keywords': ['test', 'python', 'discord'],
                'type': 'message'
            }
            mock_doc = type('MockDoc', (), {
                'id': mock_data['id'],
                'to_dict': lambda self=mock_data: mock_data
            })()
            mock_docs.append(mock_doc)
        
        return mock_docs

async def test_analytics_system():
    """Discord Analytics システムテスト"""
    print('\n📊 Discord Analytics システムテスト')
    print('-' * 50)
    
    try:
        from core.discord_analytics import DiscordAnalytics
        
        # モッククライアント初期化
        mock_client = ExtendedMockFirestoreClient()
        analytics = DiscordAnalytics(mock_client)
        
        print('✅ DiscordAnalytics初期化成功')
        
        # 週次アクティビティ収集テスト
        print('🔍 週次アクティビティ収集テスト...')
        activities = await analytics.collect_weekly_activities(days=7)
        
        print(f'   📈 収集結果:')
        print(f'     - メッセージ数: {len(activities["messages"])}')
        print(f'     - ユーザーアクティビティ: {len(activities["user_activities"])}')
        print(f'     - チャンネルアクティビティ: {len(activities["channel_activities"])}')
        print(f'     - 統計データキー: {list(activities["summary_stats"].keys())}')
        
        # AI要約生成テスト（フォールバック）
        print('🤖 AI要約生成テスト（フォールバック）...')
        summary_text = await analytics.generate_weekly_summary_with_ai(activities)
        print(f'   📝 生成された要約（{len(summary_text)}文字）:')
        print(f'     {summary_text[:150]}...')
        
        # 保存テスト
        print('💾 要約保存テスト...')
        summary_id = await analytics.save_weekly_summary(summary_text, activities)
        print(f'   ✅ 保存ID: {summary_id}')
        
        return True
        
    except Exception as e:
        print(f'   ❌ Analytics システムテストエラー: {e}')
        return False

async def test_content_creator():
    """Content Creator システムテスト"""
    print('\n🎬 Content Creator システムテスト')
    print('-' * 50)
    
    try:
        from core.content_creator import ContentCreator
        
        # モッククライアント初期化
        mock_client = ExtendedMockFirestoreClient()
        creator = ContentCreator(mock_client)
        
        print('✅ ContentCreator初期化成功')
        print(f'   🔗 Google Drive Service: {"✅ 初期化済み" if creator.drive_service else "❌ 未初期化"}')
        print(f'   🎤 TTS Client: {"✅ 初期化済み" if creator.tts_client else "❌ 未初期化"}')
        
        # テスト用サマリーテキスト
        test_summary = """みやにゃん: 今週も活発な活動があったにゃ〜！

イヴにゃん: データを見ると、150件のメッセージと12名のアクティブユーザーがいましたにゃ

ナレにゃん: 素晴らしい参加率ですね。来週も期待しています"""
        
        print('📄 テキストファイル生成テスト...')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        text_filename = f"test_summary_{timestamp}.txt"
        
        with open(text_filename, 'w', encoding='utf-8') as f:
            f.write("# Discord コミュニティ テスト要約\n")
            f.write(f"# 生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n\n")
            f.write(test_summary)
        
        print(f'   ✅ テキストファイル生成: {text_filename}')
        
        # ファイルサイズ確認
        file_size = os.path.getsize(text_filename)
        print(f'   📏 ファイルサイズ: {file_size} bytes')
        
        # クリーンアップ
        if os.path.exists(text_filename):
            os.remove(text_filename)
            print(f'   🧹 テストファイル削除: {text_filename}')
        
        return True
        
    except Exception as e:
        print(f'   ❌ Content Creator テストエラー: {e}')
        return False

def test_scheduler_system():
    """Scheduler システムテスト"""
    print('\n📅 Scheduler システムテスト')
    print('-' * 50)
    
    try:
        from core.scheduler import WeeklyContentScheduler, SchedulerManager
        
        # モッククライアント初期化
        mock_client = ExtendedMockFirestoreClient()
        scheduler = WeeklyContentScheduler(mock_client)
        
        print('✅ WeeklyContentScheduler初期化成功')
        
        # 状態確認
        status = scheduler.get_status()
        print(f'   📊 現在の状態:')
        print(f'     - 実行中: {status["is_running"]}')
        print(f'     - 設定曜日: {status["schedule_day"]}')
        print(f'     - 設定時刻: {status["schedule_time"]}')
        print(f'     - ジョブ数: {status["jobs_count"]}')
        
        # スケジュール更新テスト
        print('⚙️ スケジュール設定テスト...')
        update_result = scheduler.update_schedule('tuesday', '10:30')
        updated_status = scheduler.get_status()
        
        print(f'   ✅ 設定更新成功: {update_result}')
        print(f'   📅 新しい設定: 毎週{updated_status["schedule_day"]} {updated_status["schedule_time"]}')
        
        # SchedulerManagerテスト
        print('🎛️ SchedulerManager テスト...')
        manager = SchedulerManager(mock_client)
        
        # ヘルプメッセージテスト
        help_msg = manager._get_help_message()
        print(f'   📋 ヘルプメッセージ（{len(help_msg)}文字）: {help_msg[:100]}...')
        
        # 状態フォーマットテスト
        status_msg = manager._format_status(updated_status)
        print(f'   📊 状態メッセージ（{len(status_msg)}文字）: {status_msg[:100]}...')
        
        return True
        
    except Exception as e:
        print(f'   ❌ Scheduler システムテストエラー: {e}')
        return False

def test_character_system():
    """キャラクターシステムテスト"""
    print('\n🎭 キャラクターシステムテスト')
    print('-' * 50)
    
    try:
        from core.discord_analytics import DiscordAnalytics
        from core.podcast import PodcastGenerator
        
        # Analytics キャラクター設定
        mock_client = ExtendedMockFirestoreClient()
        analytics = DiscordAnalytics(mock_client)
        
        print('✅ キャラクター設定確認:')
        for key, persona in analytics.bot_personas.items():
            print(f'   🎭 {persona["name"]}:')
            print(f'     - 性格: {persona["personality"]}')
            print(f'     - 話し方: {persona["speaking_style"]}')
            print(f'     - 役割: {persona["role"]}')
        
        # Podcast キャラクター設定
        print('\n🎙️ ポッドキャストキャラクター設定確認:')
        podcast_gen = PodcastGenerator()
        
        for key, character in podcast_gen.characters.items():
            print(f'   🎤 {character["name"]}:')
            print(f'     - 性格: {character["personality"]}')
            print(f'     - 話し方: {character["speaking_style"]}')
            voice_settings = character["voice_settings"]
            print(f'     - 音声: {voice_settings["name"]}, 話速{voice_settings["speaking_rate"]}x')
        
        # テキストクリーンアップテスト
        print('\n🧹 テキストクリーンアップテスト:')
        test_text = "**みやにゃん**: こんにちはにゃ〜！今日は良い天気だにゃ！！"
        cleaned = podcast_gen.clean_text_for_tts(test_text)
        print(f'   📝 元テキスト: {test_text}')
        print(f'   ✨ クリーンアップ後: {cleaned}')
        
        # 感情検出テスト
        emotion_miya = podcast_gen.detect_emotion_from_content("すごい！素晴らしいにゃ〜！", 'miya')
        emotion_eve = podcast_gen.detect_emotion_from_content("統計データを見ると興味深い結果ですにゃ", 'eve')
        
        print(f'\n😊 感情検出テスト:')
        print(f'   みやにゃん感情: {emotion_miya}')
        print(f'   イヴにゃん感情: {emotion_eve}')
        
        return True
        
    except Exception as e:
        print(f'   ❌ キャラクターシステムテストエラー: {e}')
        return False

async def main():
    """メインテスト関数"""
    print('🚀 高度な機能テスト開始\n')
    
    results = []
    
    # 各システムテスト実行
    results.append(await test_analytics_system())
    results.append(await test_content_creator())
    results.append(test_scheduler_system())
    results.append(test_character_system())
    
    # 結果まとめ
    print('\n' + '=' * 70)
    print('📊 テスト結果サマリー')
    print('=' * 70)
    
    test_names = [
        'Discord Analytics システム',
        'Content Creator システム', 
        'Scheduler システム',
        'キャラクターシステム'
    ]
    
    passed = 0
    for i, result in enumerate(results):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f'{status} {test_names[i]}')
        if result:
            passed += 1
    
    print(f'\n🎯 総合結果: {passed}/{len(results)} テスト成功')
    
    if passed == len(results):
        print('🎉 全てのテストが成功しました！')
        print('\n💡 次のステップ:')
        print('   1. Discord Bot Token を設定')
        print('   2. Firebase プロジェクトをセットアップ')
        print('   3. Google Cloud APIs を有効化')
        print('   4. 実際のBot を起動: python run_entertainment_bot.py')
    else:
        print('⚠️ 一部のテストが失敗しました。ログを確認してください。')

if __name__ == "__main__":
    asyncio.run(main())