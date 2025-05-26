#!/usr/bin/env python3
"""
Firestore データ削除スクリプト
データ構造（コレクション）は保持したまま、全ドキュメントを削除します
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()

def initialize_firebase():
    """Firebase Firestoreを初期化する関数"""
    try:
        if not firebase_admin._apps:
            # ファイルパスから読み込みを試行
            firebase_key_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH', 
                                        './nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json')
            
            if os.path.exists(firebase_key_path):
                print(f"🔑 Firebaseサービスアカウントキーファイルを読み込み中: {firebase_key_path}")
                cred = credentials.Certificate(firebase_key_path)
            elif os.getenv('FIREBASE_SERVICE_ACCOUNT'):
                print("🔑 環境変数からFirebaseサービスアカウント情報を読み込み中...")
                service_account_info = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT'))
                cred = credentials.Certificate(service_account_info)
            else:
                raise FileNotFoundError("Firebaseサービスアカウントキーが見つかりません")
            
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        print("✅ Firebase Firestoreへの接続準備ができました。")
        return db
    except Exception as e:
        print(f"❌ Firebase Firestoreの初期化に失敗しました: {e}")
        return None

def delete_collection_documents(db, collection_name):
    """指定されたコレクションの全ドキュメントを削除"""
    try:
        collection_ref = db.collection(collection_name)
        docs = collection_ref.stream()
        
        deleted_count = 0
        batch = db.batch()
        batch_count = 0
        
        for doc in docs:
            batch.delete(doc.reference)
            batch_count += 1
            deleted_count += 1
            
            # バッチサイズが500に達したらコミット（Firestoreの制限）
            if batch_count >= 500:
                batch.commit()
                batch = db.batch()
                batch_count = 0
                print(f"   📦 {collection_name}: {deleted_count}件削除済み...")
        
        # 残りのバッチをコミット
        if batch_count > 0:
            batch.commit()
        
        print(f"✅ {collection_name}: 合計 {deleted_count}件のドキュメントを削除しました")
        return deleted_count
        
    except Exception as e:
        print(f"❌ {collection_name}の削除中にエラーが発生しました: {e}")
        return 0

def main():
    """メイン実行関数"""
    print("🗑️ Firestore データ削除スクリプト")
    print("=" * 50)
    print("⚠️ 警告: この操作により全てのデータが削除されます！")
    print("データ構造（コレクション）は保持されます。")
    print("=" * 50)
    
    # 確認プロンプト
    confirm = input("本当に全データを削除しますか？ (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ 操作がキャンセルされました。")
        return
    
    # Firebase初期化
    db = initialize_firebase()
    if not db:
        print("❌ Firestoreに接続できませんでした。")
        return
    
    # 削除対象のコレクション一覧
    collections = [
        'interactions',      # インタラクション記録
        'users',            # ユーザー情報
        'guilds',           # ギルド情報
        'topics',           # トピック情報
        'user_matches',     # ユーザーマッチング
        'events',           # イベント情報
        'bot_actions',      # ボットアクション
        'analytics_sessions', # 分析セッション
        'podcasts'          # ポッドキャスト情報
    ]
    
    print(f"🎯 {len(collections)}個のコレクションからデータを削除します...")
    print()
    
    total_deleted = 0
    
    for collection_name in collections:
        print(f"🗂️ {collection_name} コレクションを処理中...")
        deleted_count = delete_collection_documents(db, collection_name)
        total_deleted += deleted_count
        print()
    
    print("=" * 50)
    print(f"🎉 削除完了！合計 {total_deleted}件のドキュメントを削除しました。")
    print("📋 コレクション構造は保持されています。")
    print("=" * 50)

if __name__ == "__main__":
    main() 