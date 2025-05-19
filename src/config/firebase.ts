import { initializeApp, cert } from 'firebase-admin/app';
import { getFirestore } from 'firebase-admin/firestore';
import dotenv from 'dotenv';

dotenv.config();

// 開発環境用のモックデータベース
const mockDb = {
  collection: (collectionName: string) => ({
    doc: (docId: string) => ({
      set: async (data: any) => {
        console.log(`[Mock Firebase] データを保存: ${collectionName}/${docId}`, data);
        return Promise.resolve();
      },
      get: async () => ({
        exists: true,
        data: () => ({ 
          id: docId, 
          username: 'テストユーザー', 
          joinedAt: new Date(), 
          lastActive: new Date(),
          interests: ['テスト'],
          engagementScore: 0
        })
      }),
      update: async (data: any) => {
        console.log(`[Mock Firebase] データを更新: ${collectionName}/${docId}`, data);
        return Promise.resolve();
      }
    })
  })
};

// 環境変数から設定を読み込むか、サービスアカウントファイルを使用
const initializeFirebase = () => {
  try {
    if (process.env.FIREBASE_SERVICE_ACCOUNT) {
      const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
      initializeApp({
        credential: cert(serviceAccount)
      });
      console.log('Firebaseを初期化しました。');
      return getFirestore();
    } else {
      try {
        const serviceAccount = require('../../service-account.json');
        initializeApp({
          credential: cert(serviceAccount)
        });
        console.log('Firebaseを初期化しました。(service-account.json)');
        return getFirestore();
      } catch (error) {
        console.log('Firebase設定が見つからないため、モックデータベースを使用します。');
        return mockDb;
      }
    }
  } catch (error) {
    console.log('Firebase設定が見つからないため、モックデータベースを使用します。');
    return mockDb;
  }
};

export const db = initializeFirebase(); 