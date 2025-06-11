#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firestore データ取得テストスクリプト

discord_bot.py のデータ取得機能をテストし、
全コレクションからデータを取得してJSONファイルにエクスポートします。
"""

import asyncio
import sys
import os
from datetime import datetime

# discord_bot.py のデータ取得機能をインポート
from discord_bot import (
    initialize_firebase,
    get_all_users,
    get_all_guilds,
    get_all_interactions,
    get_all_topics,
    get_all_podcasts,
    get_all_user_matches,
    get_all_events,
    get_all_analytics_sessions,
    get_all_bot_actions,
    get_all_data,
    export_data_to_json
)

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