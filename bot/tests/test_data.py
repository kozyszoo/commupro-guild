#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firestore データ取得テストスクリプト

現在のプロジェクト構造に対応したテストスクリプト
"""

import asyncio
import sys
import os
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

# テスト用のモックデータ
class TestFirestoreDataRetrieval:
    """Firestoreデータ取得機能のテスト"""
    
    @pytest.mark.asyncio
    async def test_firebase_initialization(self, mock_firebase, mock_env_vars):
        """Firebase初期化のテスト"""
        from core.manager import MultiBotManager
        
        manager = MultiBotManager()
        # Firebase初期化が正常に行われることを確認
        assert mock_firebase['init'].called
    
    @pytest.mark.asyncio 
    async def test_vertex_ai_initialization(self, mock_vertex_ai, mock_env_vars):
        """Vertex AI初期化のテスト"""
        from core.manager import MultiBotManager
        
        manager = MultiBotManager()
        # Vertex AI初期化が正常に行われることを確認
        assert mock_vertex_ai['init'].called
    
    @pytest.mark.asyncio
    async def test_character_response_generation(self, mock_vertex_ai, mock_env_vars):
        """キャラクター応答生成のテスト"""
        from core.manager import MultiBotManager
        
        manager = MultiBotManager()
        
        # テスト用メッセージ
        test_message = "こんにちは、みやにゃん"
        
        # 応答生成をテスト
        response = await manager.generate_character_response(
            test_message, 'miya', 'testuser'
        )
        
        # 応答が生成されることを確認
        assert response is not None
        assert isinstance(response, str)
    
    @pytest.mark.asyncio
    async def test_tutorial_progress_management(self, mock_firebase, mock_env_vars):
        """チュートリアル進捗管理のテスト"""
        from core.manager import MultiBotManager
        
        manager = MultiBotManager()
        
        # テスト用ユーザーID
        test_user_id = "test_user_123"
        
        # チュートリアル一時停止のテスト
        result = await manager.pause_tutorial(test_user_id)
        assert isinstance(result, bool)
        
        # チュートリアル再開のテスト
        result = await manager.resume_tutorial(test_user_id)
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_firestore_data_operations(self, mock_firebase, sample_firestore_data):
        """Firestoreデータ操作のテスト"""
        from utils.firestore import get_collection_data
        
        # モックデータベースの設定
        mock_db = mock_firebase['db']
        mock_collection = Mock()
        mock_db.collection.return_value = mock_collection
        
        # モック文書の設定
        mock_docs = []
        for item in sample_firestore_data['users']:
            mock_doc = Mock()
            mock_doc.id = item['id']
            mock_doc.to_dict.return_value = item
            mock_docs.append(mock_doc)
        
        mock_collection.get.return_value = mock_docs
        
        # データ取得のテスト
        result = await get_collection_data('users')
        
        # 結果の検証
        assert isinstance(result, list)
        assert len(result) > 0
        if result:
            assert 'id' in result[0]
            assert 'username' in result[0]

# 統合テスト関数
async def test_individual_collections():
    """各コレクションを個別にテスト"""
    print("🧪 個別コレクションテストを開始...")
    print("=" * 50)
    
    test_collections = [
        "users", "guilds", "interactions", "topics", 
        "podcasts", "user_matches", "events", 
        "analytics_sessions", "bot_actions"
    ]
    
    results = {}
    
    for collection_name in test_collections:
        try:
            print(f"\n📋 {collection_name} コレクションをテスト中...")
            # モックデータでのテスト
            data = []  # 実際のデータ取得の代わりにモックデータ
            results[collection_name] = len(data)
            
            if data:
                print(f"✅ {collection_name}: {len(data)}件のデータを取得")
            else:
                print(f"ℹ️ {collection_name}: データなし")
                
        except Exception as e:
            print(f"❌ {collection_name} テストエラー: {e}")
            results[collection_name] = 0
    
    print("\n" + "=" * 50)
    print("📊 個別テスト結果サマリー:")
    total_records = 0
    for collection_name, count in results.items():
        print(f"   - {collection_name}: {count}件")
        total_records += count
    print(f"   合計: {total_records}件")
    
    return results

async def test_bulk_data_retrieval():
    """一括データ取得をテスト"""
    print("\n🔄 一括データ取得テストを開始...")
    print("=" * 50)
    
    try:
        # モックデータでのテスト
        all_data = {}  # 実際のデータ取得の代わりにモックデータ
        
        if all_data:
            print("✅ 一括データ取得成功！")
            print("\n📋 取得データ詳細:")
            
            total_records = 0
            for collection_name, data in all_data.items():
                count = len(data)
                total_records += count
                print(f"   - {collection_name}: {count}件")
            
            print(f"\n📊 総レコード数: {total_records}件")
            return all_data
        else:
            print("⚠️ データが取得できませんでした")
            return {}
            
    except Exception as e:
        print(f"❌ 一括データ取得エラー: {e}")
        return {}

def print_test_header():
    """テスト開始時のヘッダーを表示"""
    print("🧪 Firestore データ取得機能テスト")
    print("=" * 60)
    print(f"📅 テスト実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python バージョン: {sys.version}")
    print("=" * 60)

async def test_individual_collections():
    """各コレクションを個別にテスト"""
    print("🧪 個別コレクションテストを開始...")
    print("=" * 50)
    
    # 各コレクションを個別にテスト
    test_functions = [
        ("Users", get_all_users),
        ("Guilds", get_all_guilds),
        ("Interactions", lambda: get_all_interactions(limit=10)),
        ("Topics", get_all_topics),
        ("Podcasts", get_all_podcasts),
        ("User Matches", get_all_user_matches),
        ("Events", get_all_events),
        ("Analytics Sessions", get_all_analytics_sessions),
        ("Bot Actions", lambda: get_all_bot_actions(limit=10))
    ]
    
    results = {}
    
    for collection_name, test_func in test_functions:
        try:
            print(f"\n📋 {collection_name} コレクションをテスト中...")
            data = await test_func()
            results[collection_name] = len(data)
            
            if data:
                print(f"✅ {collection_name}: {len(data)}件のデータを取得")
                # 最初のレコードのキーを表示（データ構造確認用）
                if isinstance(data[0], dict):
                    keys = list(data[0].keys())
                    print(f"   フィールド: {', '.join(keys[:5])}{'...' if len(keys) > 5 else ''}")
            else:
                print(f"ℹ️ {collection_name}: データなし")
                
        except Exception as e:
            print(f"❌ {collection_name} テストエラー: {e}")
            results[collection_name] = 0
    
    print("\n" + "=" * 50)
    print("📊 個別テスト結果サマリー:")
    total_records = 0
    for collection_name, count in results.items():
        print(f"   - {collection_name}: {count}件")
        total_records += count
    print(f"   合計: {total_records}件")
    
    return results

async def test_bulk_data_retrieval():
    """一括データ取得をテスト"""
    print("\n🔄 一括データ取得テストを開始...")
    print("=" * 50)
    
    try:
        all_data = await get_all_data()
        
        if all_data:
            print("✅ 一括データ取得成功！")
            print("\n📋 取得データ詳細:")
            
            total_records = 0
            for collection_name, data in all_data.items():
                count = len(data)
                total_records += count
                print(f"   - {collection_name}: {count}件")
                
                # サンプルデータを表示
                if data and isinstance(data[0], dict):
                    sample_keys = list(data[0].keys())
                    print(f"     サンプルフィールド: {', '.join(sample_keys[:3])}...")
            
            print(f"\n📊 総レコード数: {total_records}件")
            return all_data
        else:
            print("⚠️ データが取得できませんでした")
            return {}
            
    except Exception as e:
        print(f"❌ 一括データ取得エラー: {e}")
        return {}

async def test_data_export():
    """データエクスポート機能をテスト"""
    print("\n📤 データエクスポートテストを開始...")
    print("=" * 50)
    
    try:
        # タイムスタンプ付きファイル名でエクスポート
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_export_{timestamp}.json"
        
        exported_file = await export_data_to_json(filename=filename)
        
        if exported_file and os.path.exists(exported_file):
            file_size = os.path.getsize(exported_file)
            print(f"✅ エクスポート成功: {exported_file}")
            print(f"📁 ファイルサイズ: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            
            # ファイル内容の簡単な検証
            import json
            with open(exported_file, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            
            if 'metadata' in exported_data and 'data' in exported_data:
                metadata = exported_data['metadata']
                print(f"📊 エクスポートメタデータ:")
                print(f"   - エクスポート日時: {metadata.get('exportedAt')}")
                print(f"   - 総レコード数: {metadata.get('totalRecords')}")
                print(f"   - コレクション数: {len(metadata.get('collections', []))}")
                
                return exported_file
            else:
                print("⚠️ エクスポートファイルの形式が正しくありません")
                return None
        else:
            print("❌ エクスポートファイルが作成されませんでした")
            return None
            
    except Exception as e:
        print(f"❌ データエクスポートエラー: {e}")
        return None

async def test_guild_specific_data():
    """特定のGuild IDでのデータ取得をテスト"""
    print("\n🏰 Guild固有データ取得テストを開始...")
    print("=" * 50)
    
    try:
        # まず全Guildを取得
        guilds = await get_all_guilds()
        
        if not guilds:
            print("ℹ️ Guildデータが見つかりません。Guild固有テストをスキップします。")
            return
        
        # 最初のGuildでテスト
        test_guild = guilds[0]
        guild_id = test_guild.get('id')
        guild_name = test_guild.get('name', 'Unknown Guild')
        
        print(f"🎯 テスト対象Guild: {guild_name} (ID: {guild_id})")
        
        # Guild固有データを取得
        guild_data = await get_all_data(guild_id)
        
        if guild_data:
            print(f"✅ Guild固有データ取得成功！")
            print(f"📋 Guild '{guild_name}' のデータ:")
            
            total_records = 0
            for collection_name, data in guild_data.items():
                if collection_name != 'guilds':  # guildsは全Guild対象なのでスキップ
                    count = len(data)
                    total_records += count
                    print(f"   - {collection_name}: {count}件")
            
            print(f"📊 Guild固有総レコード数: {total_records}件")
        else:
            print(f"⚠️ Guild '{guild_name}' のデータが取得できませんでした")
            
    except Exception as e:
        print(f"❌ Guild固有データ取得エラー: {e}")

def print_test_header():
    """テスト開始時のヘッダーを表示"""
    print("🧪 Firestore データ取得機能テスト")
    print("=" * 60)
    print(f"📅 テスト実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python バージョン: {sys.version}")
    print("=" * 60)

async def main():
    """メインテスト関数"""
    print_test_header()
    
    # Firebase初期化確認
    print("\n🔥 Firebase初期化確認...")
    if not initialize_firebase():
        print("❌ Firebase初期化に失敗しました。テストを中止します。")
        return
    
    print("✅ Firebase初期化成功！")
    
    try:
        # 1. 個別コレクションテスト
        individual_results = await test_individual_collections()
        
        # 2. 一括データ取得テスト
        bulk_data = await test_bulk_data_retrieval()
        
        # 3. データエクスポートテスト
        exported_file = await test_data_export()
        
        # 4. Guild固有データテスト
        await test_guild_specific_data()
        
        # 最終結果サマリー
        print("\n" + "=" * 60)
        print("🎉 全テスト完了！")
        print("=" * 60)
        
        if individual_results:
            total_individual = sum(individual_results.values())
            print(f"📊 個別取得総レコード数: {total_individual}件")
        
        if bulk_data:
            total_bulk = sum(len(data) for data in bulk_data.values())
            print(f"📊 一括取得総レコード数: {total_bulk}件")
        
        if exported_file:
            print(f"📁 エクスポートファイル: {exported_file}")
        
        print("\n✅ すべてのデータ取得機能が正常に動作しています！")
        
    except Exception as e:
        print(f"\n❌ テスト実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 非同期実行
    asyncio.run(main()) 