#!/usr/bin/env python3
"""
Firestore データアップロードスクリプト
public/data 配下の JSON ファイルを Firestore にアップロードします。
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

def initialize_firebase():
    """Firebase Admin SDK を初期化"""
    try:
        # サービスアカウントキーファイルのパスを環境変数から取得
        service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        if service_account_path and os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
        else:
            # デフォルトの認証情報を使用（Cloud環境など）
            cred = credentials.ApplicationDefault()
        
        firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        print(f"Firebase初期化エラー: {e}")
        print("GOOGLE_APPLICATION_CREDENTIALS環境変数が正しく設定されているか確認してください。")
        sys.exit(1)

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """JSONファイルを読み込み"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"ファイル読み込みエラー {file_path}: {e}")
        return {}

def upload_collection_data(db: firestore.Client, collection_name: str, data: Dict[str, Any], batch_size: int = 500):
    """コレクションデータをFirestoreにアップロード"""
    if not data:
        print(f"⚠️  {collection_name}: データが空です")
        return
    
    print(f"📤 {collection_name} コレクションをアップロード中... ({len(data)} ドキュメント)")
    
    # バッチ処理でアップロード
    batch = db.batch()
    batch_count = 0
    total_uploaded = 0
    
    for doc_id, doc_data in data.items():
        doc_ref = db.collection(collection_name).document(doc_id)
        batch.set(doc_ref, doc_data)
        batch_count += 1
        
        # バッチサイズに達したらコミット
        if batch_count >= batch_size:
            try:
                batch.commit()
                total_uploaded += batch_count
                print(f"  ✅ {total_uploaded}/{len(data)} ドキュメントをアップロード完了")
                batch = db.batch()
                batch_count = 0
            except Exception as e:
                print(f"  ❌ バッチアップロードエラー: {e}")
                return False
    
    # 残りのドキュメントをコミット
    if batch_count > 0:
        try:
            batch.commit()
            total_uploaded += batch_count
            print(f"  ✅ {total_uploaded}/{len(data)} ドキュメントをアップロード完了")
        except Exception as e:
            print(f"  ❌ 最終バッチアップロードエラー: {e}")
            return False
    
    print(f"🎉 {collection_name} コレクションのアップロードが完了しました！")
    return True

def get_collection_name_from_filename(filename: str) -> str:
    """ファイル名からコレクション名を取得"""
    # .json拡張子を除去
    return filename.replace('.json', '')

def main():
    """メイン処理"""
    print("🚀 Firestore データアップロードを開始します...")
    
    # Firebase初期化
    db = initialize_firebase()
    print("✅ Firebase接続が完了しました")
    
    # データディレクトリのパス
    data_dir = Path(__file__).parent.parent.parent.parent / 'public' / 'data' / 'tmp'
    
    if not data_dir.exists():
        print(f"❌ データディレクトリが見つかりません: {data_dir}")
        sys.exit(1)
    
    # JSONファイルを取得
    json_files = list(data_dir.glob('*.json'))
    
    if not json_files:
        print(f"❌ {data_dir} にJSONファイルが見つかりません")
        sys.exit(1)
    
    print(f"📁 {len(json_files)} 個のJSONファイルが見つかりました")
    
    success_count = 0
    total_files = len(json_files)
    
    # 各JSONファイルを処理
    for json_file in sorted(json_files):
        print(f"\n📄 処理中: {json_file.name}")
        
        # JSONデータを読み込み
        json_data = load_json_file(json_file)
        
        if not json_data:
            print(f"⚠️  {json_file.name}: データが空またはエラーです")
            continue
        
        # ファイル名からコレクション名を決定
        collection_name = get_collection_name_from_filename(json_file.name)
        
        # JSONの構造を確認（トップレベルキーがコレクション名の場合）
        if len(json_data) == 1 and collection_name in json_data:
            # {"users": {...}} のような構造の場合
            collection_data = json_data[collection_name]
            actual_collection_name = collection_name
        elif len(json_data) == 1:
            # {"some_key": {...}} のような構造の場合
            key = list(json_data.keys())[0]
            collection_data = json_data[key]
            actual_collection_name = key
        else:
            # 直接オブジェクトの場合
            collection_data = json_data
            actual_collection_name = collection_name
        
        # データをアップロード
        if upload_collection_data(db, actual_collection_name, collection_data):
            success_count += 1
    
    # 結果を表示
    print(f"\n🎯 アップロード結果:")
    print(f"  ✅ 成功: {success_count}/{total_files} ファイル")
    print(f"  ❌ 失敗: {total_files - success_count}/{total_files} ファイル")
    
    if success_count == total_files:
        print("🎉 すべてのデータのアップロードが完了しました！")
    else:
        print("⚠️  一部のファイルでエラーが発生しました。ログを確認してください。")

if __name__ == "__main__":
    main()
