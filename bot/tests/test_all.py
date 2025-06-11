#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_all.py
Discord にゃんこエージェント - 統合テスト

音声生成とデータ取得のテストを統合
"""

import os
import sys
import unittest
from pathlib import Path
import asyncio
from typing import Dict, Any, Optional
import json
from datetime import datetime, timezone

# プロジェクトのルートディレクトリをPythonパスに追加
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from src.core.podcast import PodcastGenerator
from src.utils.firestore import FirestoreManager

class TestVoiceGeneration(unittest.TestCase):
    """音声生成テスト"""
    
    def setUp(self):
        """テストの準備"""
        self.generator = PodcastGenerator()
        self.test_dir = root_dir / 'tests' / 'output'
        self.test_dir.mkdir(exist_ok=True)
    
    def test_voice_settings(self):
        """音声設定のテスト"""
        # みやにゃんの音声設定
        miya_settings = self.generator.characters['miya']['voice_settings']
        self.assertEqual(miya_settings['language_code'], 'ja-JP')
        self.assertEqual(miya_settings['name'], 'ja-JP-Neural2-B')
        
        # イヴにゃんの音声設定
        eve_settings = self.generator.characters['eve']['voice_settings']
        self.assertEqual(eve_settings['language_code'], 'ja-JP')
        self.assertEqual(eve_settings['name'], 'ja-JP-Neural2-C')
    
    def test_ssml_generation(self):
        """SSML生成のテスト"""
        test_text = "こんにちは！にゃんこエージェントですにゃ〜"
        
        # みやにゃん用SSML
        miya_ssml = self.generator.create_ssml_content(test_text, 'miya')
        self.assertIn('<speak>', miya_ssml)
        self.assertIn('rate="1.2"', miya_ssml)
        self.assertIn('pitch="+0.5st"', miya_ssml)
        
        # イヴにゃん用SSML
        eve_ssml = self.generator.create_ssml_content(test_text, 'eve')
        self.assertIn('<speak>', eve_ssml)
        self.assertIn('rate="1.0"', eve_ssml)
        self.assertIn('pitch="-1.5st"', eve_ssml)
    
    @unittest.skipIf(not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'), "Google Cloud認証情報が設定されていません")
    def test_audio_generation(self):
        """音声生成のテスト"""
        test_text = "テスト音声ですにゃ〜"
        output_file = self.test_dir / 'test_voice.mp3'
        
        # 音声生成
        result = asyncio.run(self.generator.generate_audio(
            test_text,
            str(output_file),
            self.generator.characters['miya']['voice_settings'],
            'miya'
        ))
        
        self.assertIsNotNone(result)
        self.assertTrue(output_file.exists())
        self.assertGreater(output_file.stat().st_size, 0)

class TestDataRetrieval(unittest.TestCase):
    """データ取得テスト"""
    
    def setUp(self):
        """テストの準備"""
        self.db = FirestoreManager()
        self.test_data = {
            'test_user': {
                'name': 'テストユーザー',
                'created_at': datetime.now(timezone.utc),
                'interactions': 0
            }
        }
    
    def test_data_operations(self):
        """データ操作のテスト"""
        # テストデータの追加
        self.db.add_test_data(self.test_data)
        
        # データの取得
        user_data = self.db.get_user_data('test_user')
        self.assertIsNotNone(user_data)
        self.assertEqual(user_data['name'], 'テストユーザー')
        
        # データの更新
        self.db.update_user_data('test_user', {'interactions': 1})
        updated_data = self.db.get_user_data('test_user')
        self.assertEqual(updated_data['interactions'], 1)
        
        # データの削除
        self.db.delete_test_data('test_user')
        deleted_data = self.db.get_user_data('test_user')
        self.assertIsNone(deleted_data)
    
    def test_interaction_recording(self):
        """インタラクション記録のテスト"""
        # インタラクションの記録
        self.db.record_interaction('test_user', 'message', 'テストメッセージ')
        
        # インタラクションの取得
        interactions = self.db.get_user_interactions('test_user')
        self.assertGreater(len(interactions), 0)
        self.assertEqual(interactions[0]['type'], 'message')
        self.assertEqual(interactions[0]['content'], 'テストメッセージ')
        
        # テストデータのクリーンアップ
        self.db.delete_test_data('test_user')

def main():
    """メイン実行関数"""
    # テストスイートの作成
    suite = unittest.TestSuite()
    
    # 音声生成テスト
    suite.addTest(unittest.makeSuite(TestVoiceGeneration))
    
    # データ取得テスト
    suite.addTest(unittest.makeSuite(TestDataRetrieval))
    
    # テストの実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # テスト結果に基づいて終了コードを設定
    sys.exit(not result.wasSuccessful())

if __name__ == '__main__':
    main() 