#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
firestore.py
Discord にゃんこエージェント - Firestore管理ユーティリティ

Firestoreデータベースの操作を統合
- データの取得・更新・削除
- インタラクションの記録
- テストデータの管理
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# エンターテイメントボット用の独立した初期化関数
async def initialize_firebase():
    """
    Firebase Firestoreを初期化（エンターテイメントボット用）
    
    Returns:
        FirestoreManager: 初期化されたFirestoreManagerインスタンス
    """
    try:
        manager = FirestoreManager()
        if manager.db:
            print("✅ Firebase Firestore初期化完了（エンターテイメントボット用）")
            return manager
        else:
            print("❌ Firebase Firestore初期化失敗")
            return None
    except Exception as e:
        print(f"❌ Firebase初期化エラー: {e}")
        return None

class FirestoreManager:
    """Firestore管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.db = None
        self.initialize_firebase()
    
    def initialize_firebase(self) -> bool:
        """Firebase Firestoreを初期化"""
        try:
            if not firebase_admin._apps:
                # サービスアカウントキーファイルのパス
                key_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH', 
                                   './nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json')
                
                if os.path.exists(key_path):
                    print(f"🔑 Firebaseサービスアカウントキーファイルを読み込み中: {key_path}")
                    cred = credentials.Certificate(key_path)
                elif os.getenv('FIREBASE_SERVICE_ACCOUNT'):
                    print("🔑 環境変数からFirebaseサービスアカウント情報を読み込み中...")
                    service_account_info = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT'))
                    cred = credentials.Certificate(service_account_info)
                else:
                    raise FileNotFoundError("Firebaseサービスアカウントキーが見つかりません")
                
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            print("✅ Firebase Firestoreへの接続準備ができました。")
            return True
            
        except Exception as e:
            print(f"❌ Firebase Firestoreの初期化に失敗しました: {e}")
            return False
    
    async def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """ユーザーデータを取得"""
        if not self.db:
            return None
        
        try:
            doc = await asyncio.to_thread(self.db.collection('users').doc(user_id).get)
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            print(f"❌ ユーザーデータ取得エラー: {e}")
            return None
    
    async def update_user_data(self, user_id: str, data: Dict[str, Any]) -> bool:
        """ユーザーデータを更新"""
        if not self.db:
            return False
        
        try:
            await asyncio.to_thread(
                self.db.collection('users').doc(user_id).update,
                data
            )
            return True
        except Exception as e:
            print(f"❌ ユーザーデータ更新エラー: {e}")
            return False
    
    async def record_interaction(self, user_id: str, interaction_type: str, content: str) -> bool:
        """インタラクションを記録"""
        if not self.db:
            return False
        
        try:
            interaction_data = {
                'userId': user_id,
                'type': interaction_type,
                'content': content,
                'timestamp': datetime.now(timezone.utc)
            }
            
            await asyncio.to_thread(
                self.db.collection('interactions').add,
                interaction_data
            )
            return True
        except Exception as e:
            print(f"❌ インタラクション記録エラー: {e}")
            return False
    
    async def get_user_interactions(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """ユーザーのインタラクションを取得"""
        if not self.db:
            return []
        
        try:
            interactions_ref = (self.db.collection('interactions')
                              .where('userId', '==', user_id)
                              .order_by('timestamp', direction=firestore.Query.DESCENDING)
                              .limit(limit))
            
            docs = await asyncio.to_thread(interactions_ref.get)
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"❌ インタラクション取得エラー: {e}")
            return []
    
    async def add_test_data(self, data: Dict[str, Any]) -> bool:
        """テストデータを追加"""
        if not self.db:
            return False
        
        try:
            batch = self.db.batch()
            
            for user_id, user_data in data.items():
                doc_ref = self.db.collection('users').document(user_id)
                batch.set(doc_ref, user_data)
            
            await asyncio.to_thread(batch.commit)
            return True
        except Exception as e:
            print(f"❌ テストデータ追加エラー: {e}")
            return False
    
    async def delete_test_data(self, user_id: str) -> bool:
        """テストデータを削除"""
        if not self.db:
            return False
        
        try:
            # ユーザーデータの削除
            await asyncio.to_thread(
                self.db.collection('users').doc(user_id).delete
            )
            
            # 関連するインタラクションの削除
            interactions_ref = self.db.collection('interactions').where('userId', '==', user_id)
            docs = await asyncio.to_thread(interactions_ref.get)
            
            batch = self.db.batch()
            for doc in docs:
                batch.delete(doc.reference)
            
            await asyncio.to_thread(batch.commit)
            return True
        except Exception as e:
            print(f"❌ テストデータ削除エラー: {e}")
            return False
    
    async def export_data(self, output_file: str) -> bool:
        """データをエクスポート"""
        if not self.db:
            return False
        
        try:
            # ユーザーデータの取得
            users_ref = self.db.collection('users')
            users_docs = await asyncio.to_thread(users_ref.get)
            users_data = {doc.id: doc.to_dict() for doc in users_docs}
            
            # インタラクションデータの取得
            interactions_ref = self.db.collection('interactions')
            interactions_docs = await asyncio.to_thread(interactions_ref.get)
            interactions_data = [doc.to_dict() for doc in interactions_docs]
            
            # データをJSONファイルに保存
            export_data = {
                'users': users_data,
                'interactions': interactions_data,
                'exported_at': datetime.now(timezone.utc).isoformat()
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ データをエクスポート: {output_file}")
            return True
        except Exception as e:
            print(f"❌ データエクスポートエラー: {e}")
            return False
    
    async def import_data(self, input_file: str) -> bool:
        """データをインポート"""
        if not self.db:
            return False
        
        try:
            # JSONファイルからデータを読み込み
            with open(input_file, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            batch = self.db.batch()
            
            # ユーザーデータのインポート
            for user_id, user_data in import_data.get('users', {}).items():
                doc_ref = self.db.collection('users').document(user_id)
                batch.set(doc_ref, user_data)
            
            # インタラクションデータのインポート
            for interaction in import_data.get('interactions', []):
                doc_ref = self.db.collection('interactions').document()
                batch.set(doc_ref, interaction)
            
            await asyncio.to_thread(batch.commit)
            print(f"✅ データをインポート: {input_file}")
            return True
        except Exception as e:
            print(f"❌ データインポートエラー: {e}")
            return False

async def main():
    """メイン実行関数"""
    # 環境変数の読み込み
    load_dotenv()
    
    # FirestoreManagerのインスタンス化
    manager = FirestoreManager()
    
    # テストデータの追加
    test_data = {
        'test_user': {
            'name': 'テストユーザー',
            'created_at': datetime.now(timezone.utc),
            'interactions': 0
        }
    }
    
    if await manager.add_test_data(test_data):
        print("✅ テストデータを追加")
        
        # インタラクションの記録
        if await manager.record_interaction('test_user', 'message', 'テストメッセージ'):
            print("✅ インタラクションを記録")
        
        # データのエクスポート
        if await manager.export_data('test_export.json'):
            print("✅ データをエクスポート")
        
        # テストデータの削除
        if await manager.delete_test_data('test_user'):
            print("✅ テストデータを削除")

if __name__ == '__main__':
    asyncio.run(main()) 