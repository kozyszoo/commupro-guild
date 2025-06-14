#!/usr/bin/env python3
"""
ユーザーデータ移行スクリプト
既存のinteractionsコレクションからusernameフィールドを削除し、
usersコレクションにユーザー情報を分離するスクリプト
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Set
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import asyncio

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

def migrate_interactions_data(db: firestore.Client, batch_size: int = 100, dry_run: bool = True):
    """interactionsコレクションのデータを移行"""
    print(f"🔄 interactionsコレクションの移行を開始{'（DRY RUN）' if dry_run else ''}...")
    
    try:
        # 全てのinteractionsドキュメントを取得（バッチ処理）
        interactions_ref = db.collection('interactions')
        total_processed = 0
        users_created = 0
        interactions_updated = 0
        user_data_cache: Dict[str, Dict[str, Any]] = {}
        
        # ページング処理
        last_doc = None
        
        while True:
            # バッチでドキュメントを取得
            query = interactions_ref.limit(batch_size)
            if last_doc:
                query = query.start_after(last_doc)
                
            docs = query.stream()
            batch_docs = list(docs)
            
            if not batch_docs:
                break
            
            batch = db.batch()
            batch_users_to_create = {}
            
            for doc in batch_docs:
                doc_data = doc.to_dict()
                total_processed += 1
                
                # usernameフィールドが存在し、userIdも存在する場合のみ処理
                if 'username' in doc_data and 'userId' in doc_data:
                    user_id = doc_data['userId']
                    username = doc_data['username']
                    
                    # ユーザーデータをキャッシュに保存
                    if user_id not in user_data_cache:
                        user_data_cache[user_id] = {
                            'userId': user_id,
                            'username': username,
                            'displayName': username,
                            'discriminator': None,
                            'avatar': None,
                            'isBot': False,
                            'createdAt': doc_data.get('timestamp', datetime.now()).isoformat() if hasattr(doc_data.get('timestamp'), 'isoformat') else str(doc_data.get('timestamp', datetime.now())),
                            'firstSeen': doc_data.get('timestamp', datetime.now()),
                            'lastSeen': doc_data.get('timestamp', datetime.now()),
                            'updatedAt': datetime.now()
                        }
                        batch_users_to_create[user_id] = user_data_cache[user_id]
                        users_created += 1
                    else:
                        # 既存ユーザーの lastSeen を更新
                        existing_last_seen = user_data_cache[user_id].get('lastSeen', datetime.now())
                        current_timestamp = doc_data.get('timestamp', datetime.now())
                        
                        if hasattr(current_timestamp, 'timestamp'):
                            current_timestamp = datetime.fromtimestamp(current_timestamp.timestamp())
                        elif hasattr(current_timestamp, 'isoformat'):
                            pass  # already datetime
                        
                        if hasattr(existing_last_seen, 'timestamp'):
                            existing_last_seen = datetime.fromtimestamp(existing_last_seen.timestamp())
                            
                        if current_timestamp > existing_last_seen:
                            user_data_cache[user_id]['lastSeen'] = current_timestamp
                            user_data_cache[user_id]['updatedAt'] = datetime.now()
                            batch_users_to_create[user_id] = user_data_cache[user_id]
                    
                    # interactionドキュメントからusernameフィールドを削除
                    updated_data = {k: v for k, v in doc_data.items() if k != 'username'}
                    if not dry_run:
                        batch.update(doc.reference, {'username': firestore.DELETE_FIELD})
                    interactions_updated += 1
                
                if total_processed % 100 == 0:
                    print(f"  📊 処理済み: {total_processed} ドキュメント")
            
            # usersコレクションにバッチでユーザーデータを作成/更新
            for user_id, user_data in batch_users_to_create.items():
                if not dry_run:
                    user_ref = db.collection('users').document(user_id)
                    batch.set(user_ref, user_data, merge=True)
            
            # バッチをコミット
            if not dry_run and (batch_users_to_create or interactions_updated > 0):
                try:
                    batch.commit()
                    print(f"  ✅ バッチコミット完了: {len(batch_users_to_create)} ユーザー作成/更新")
                except Exception as e:
                    print(f"  ❌ バッチコミットエラー: {e}")
                    return False
            
            last_doc = batch_docs[-1]
            
            # 進捗表示
            print(f"  📈 進捗: {total_processed} 処理済み, {users_created} ユーザー作成, {interactions_updated} インタラクション更新")
        
        print(f"\n🎉 移行完了{'（DRY RUN）' if dry_run else ''}!")
        print(f"  📊 総処理ドキュメント数: {total_processed}")
        print(f"  👥 作成されたユーザー数: {users_created}")
        print(f"  🔄 更新されたインタラクション数: {interactions_updated}")
        
        return True
        
    except Exception as e:
        print(f"❌ 移行エラー: {e}")
        return False

def validate_migration(db: firestore.Client):
    """移行結果を検証"""
    print("\n🔍 移行結果を検証中...")
    
    try:
        # usersコレクションの件数確認
        users_count = len(list(db.collection('users').stream()))
        print(f"  👥 usersコレクション: {users_count} ドキュメント")
        
        # interactionsコレクションでusernameフィールドが残っているドキュメント数確認
        interactions_with_username = 0
        interactions_total = 0
        
        for doc in db.collection('interactions').stream():
            interactions_total += 1
            if 'username' in doc.to_dict():
                interactions_with_username += 1
                
        print(f"  💬 interactionsコレクション: {interactions_total} ドキュメント")
        print(f"  ⚠️  usernameフィールドが残っているドキュメント: {interactions_with_username}")
        
        if interactions_with_username == 0:
            print("  ✅ 移行が正常に完了しました！")
        else:
            print("  ⚠️  一部のドキュメントで移行が完了していません")
            
    except Exception as e:
        print(f"❌ 検証エラー: {e}")

def main():
    """メイン処理"""
    print("🚀 ユーザーデータ移行スクリプトを開始します...")
    
    # コマンドライン引数の確認
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    force_run = '--force' in sys.argv or '-f' in sys.argv
    validate_only = '--validate' in sys.argv or '-v' in sys.argv
    
    if dry_run:
        print("📋 DRY RUN モード: 実際の変更は行いません")
    elif not force_run and not validate_only:
        print("⚠️  このスクリプトはFirestoreデータを変更します。")
        print("   DRY RUN で確認する場合: --dry-run または -d")
        print("   実際に実行する場合: --force または -f")
        print("   検証のみ行う場合: --validate または -v")
        sys.exit(1)
    
    # Firebase初期化
    db = initialize_firebase()
    print("✅ Firebase接続が完了しました")
    
    if validate_only:
        validate_migration(db)
        return
    
    # 移行実行
    success = migrate_interactions_data(db, batch_size=100, dry_run=dry_run)
    
    if success:
        if not dry_run:
            validate_migration(db)
        print("\n✨ スクリプトが正常に完了しました")
    else:
        print("\n❌ スクリプトの実行中にエラーが発生しました")
        sys.exit(1)

if __name__ == "__main__":
    main()