import { initializeApp, cert } from 'firebase-admin/app';
import { getFirestore } from 'firebase-admin/firestore';
import dotenv from 'dotenv';

dotenv.config();

// 環境変数から設定を読み込むか、サービスアカウントファイルを使用
const initializeFirebase = () => {
  if (process.env.FIREBASE_SERVICE_ACCOUNT) {
    const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
    initializeApp({
      credential: cert(serviceAccount)
    });
  } else {
    try {
      const serviceAccount = require('../../service-account.json');
      initializeApp({
        credential: cert(serviceAccount)
      });
    } catch (error) {
      console.error('Firebaseの初期化に失敗しました。service-account.jsonを確認してください:', error);
      process.exit(1);
    }
  }
};

initializeFirebase();
export const db = getFirestore(); 