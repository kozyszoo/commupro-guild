/**
 * Import function triggers from their respective submodules:
 *
 * import {onCall} from "firebase-functions/v2/https";
 * import {onDocumentWritten} from "firebase-functions/v2/firestore";
 *
 * See a full list of supported triggers at https://firebase.google.com/docs/functions
 */

import {onCall} from "firebase-functions/v2/https";
import {onDocumentCreated} from "firebase-functions/v2/firestore";
import {onSchedule} from "firebase-functions/v2/scheduler";
import * as logger from "firebase-functions/logger";
import * as admin from "firebase-admin";
import { setGlobalOptions } from 'firebase-functions/v2';

// ユーザータイプの定義
interface User {
  id: string;
  username: string;
  interests: string[];
  joinedAt: Date;
  lastActive: Date;
  engagementScore: number;
}

// マッチングユーザー結果タイプの定義
interface MatchedUser {
  id: string;
  username: string;
  interests: string[];
}

admin.initializeApp();

// Start writing functions
// https://firebase.google.com/docs/functions/typescript

// export const helloWorld = onRequest((request, response) => {
//   logger.info("Hello logs!", {structuredData: true});
//   response.send("Hello from Firebase!");
// });

// グローバル設定
setGlobalOptions({
  region: 'asia-northeast1', // 東京リージョン
  maxInstances: 10
});

// Discord 分析機能をエクスポート
export { 
  analyzeDiscordLogs, 
  onInteractionAdded, 
  getAnalysisHistory 
} from './discord-analytics';

// Discordウェルカムメッセージの関数
export const welcomeNewMember = onDocumentCreated("users/{userId}", async (event) => {
  const snapshot = event.data;
  if (!snapshot) {
    logger.error("No data associated with the event");
    return;
  }
  
  const userData = snapshot.data() as User;
  logger.info(`新しいユーザーが登録されました: ${userData.username}`);
  // ここにDiscordボットを通じてメッセージを送信するロジックを追加
});

// 非アクティブユーザーの再エンゲージメント
export const reengageInactiveUsers = onSchedule({
  schedule: "0 12 * * *", // 毎日正午に実行
  timeZone: "Asia/Tokyo",
}, async (event) => {
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
  
  const inactiveUsersSnapshot = await admin.firestore()
    .collection("users")
    .where("lastActive", "<", thirtyDaysAgo)
    .get();
  
  logger.info(`非アクティブユーザー数: ${inactiveUsersSnapshot.size}`);
  // ここに非アクティブユーザーへのDMを送信するロジックを追加
});

// ユーザーマッチング
export const matchSimilarUsers = onCall(async (request) => {
  const data = request.data;
  const auth = request.auth;
  
  // 認証チェック
  if (!auth) {
    throw new Error("認証が必要です");
  }
  
  const userId = data.userId;
  const userDoc = await admin.firestore().collection("users").doc(userId).get();
  
  if (!userDoc.exists) {
    throw new Error("ユーザーが見つかりません");
  }
  
  const userData = userDoc.data() as User;
  const userInterests = userData?.interests || [];
  
  // 同じ興味を持つユーザーを検索
  const similarUsers = await admin.firestore()
    .collection("users")
    .where("interests", "array-contains-any", userInterests)
    .limit(5)
    .get();
  
  const result: MatchedUser[] = [];
  similarUsers.forEach((doc) => {
    if (doc.id !== userId) {
      const user = doc.data() as User;
      result.push({
        id: doc.id,
        username: user.username,
        interests: user.interests
      });
    }
  });
  
  return { users: result };
});

// 接続しているサーバー情報を取得
export const getConnectedGuilds = onCall({
  region: 'asia-northeast1',
  cors: true,
}, async (request) => {
  try {
    logger.info("接続サーバー情報を取得中...");
    
    // Firestoreからguildsコレクションを取得
    const guildsSnapshot = await admin.firestore()
      .collection("guilds")
      .orderBy("lastUpdated", "desc")
      .get();
    
    const guilds: any[] = [];
    
    guildsSnapshot.forEach((doc) => {
      const guildData = doc.data();
      guilds.push({
        id: doc.id,
        ...guildData,
        // 最終更新から5分以内のものを「オンライン」とみなす
        isActive: guildData.lastUpdated && 
          (new Date().getTime() - guildData.lastUpdated.toDate().getTime()) < 5 * 60 * 1000
      });
    });
    
    logger.info(`${guilds.length}個のサーバー情報を取得しました`);
    
    return { 
      success: true, 
      guilds: guilds,
      totalCount: guilds.length,
      activeCount: guilds.filter(g => g.isActive).length
    };
    
  } catch (error) {
    logger.error("サーバー情報取得エラー:", error);
    throw new Error("サーバー情報の取得に失敗しました");
  }
});

// 過去1週間のポッドキャスト作成
export const createWeeklyPodcast = onCall({
  region: 'asia-northeast1', // リージョンを統一
  cors: true, // CORSを明示的に有効化
}, async (request) => {
  const auth = request.auth;
  
  // 開発中は認証をスキップ
  // if (!auth) {
  //   throw new Error("認証が必要です");
  // }
  
  try {
    logger.info("週次ポッドキャスト作成を開始...");
    
    // ポッドキャスト作成ジョブをFirestoreに記録
    const jobRef = await admin.firestore().collection("podcast_jobs").add({
      status: "pending",
      requestedBy: auth?.uid || "anonymous",
      requestedAt: admin.firestore.FieldValue.serverTimestamp(),
      type: "weekly_podcast",
      parameters: {
        daysBack: 7
      }
    });
    
    // 実際のポッドキャスト作成は非同期で実行
    // このフラグをEntertainmentBotが監視して処理を行う
    logger.info(`ポッドキャスト作成ジョブを作成しました: ${jobRef.id}`);
    
    return { 
      success: true, 
      jobId: jobRef.id,
      message: "ポッドキャスト作成ジョブを開始しました。処理状況はダッシュボードで確認できます。" 
    };
    
  } catch (error) {
    logger.error("ポッドキャスト作成エラー:", error);
    throw new Error("ポッドキャスト作成に失敗しました");
  }
});

// 週次アドバイス取得API
export const getWeeklyAdvice = onCall({
  region: 'asia-northeast1',
  cors: true,
}, async (request) => {
  try {
    logger.info("週次アドバイス取得を開始...");
    
    // Firestoreから最新の週次アドバイスを取得
    const adviceQuery = admin.firestore()
      .collection('weekly_advice')
      .where('isActive', '==', true)
      .orderBy('createdAt', 'desc')
      .limit(5); // 最新5件を取得
    
    const adviceSnapshot = await adviceQuery.get();
    
    if (adviceSnapshot.empty) {
      return {
        success: true,
        data: [],
        message: "週次アドバイスがまだ生成されていません"
      };
    }
    
    const adviceList = adviceSnapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data(),
      createdAt: doc.data().createdAt?.toDate?.() || null,
      weekStart: doc.data().weekStart?.toDate?.() || null,
      weekEnd: doc.data().weekEnd?.toDate?.() || null
    }));
    
    logger.info(`週次アドバイス ${adviceList.length} 件を取得しました`);
    
    return {
      success: true,
      data: adviceList
    };
    
  } catch (error) {
    logger.error("週次アドバイス取得エラー:", error);
    throw new Error("週次アドバイスの取得に失敗しました");
  }
});

// アドバイス表示設定の更新API
export const updateAdviceSettings = onCall({
  region: 'asia-northeast1',
  cors: true,
}, async (request) => {
  const auth = request.auth;
  const data = request.data;
  
  try {
    logger.info("アドバイス表示設定更新を開始...");
    
    const userId = auth?.uid || 'anonymous';
    const { isVisible = true, adviceId } = data;
    
    // ユーザーのアドバイス表示設定を更新
    const settingsRef = admin.firestore()
      .collection('user_advice_settings')
      .doc(userId);
    
    const settingsData = {
      userId,
      isVisible,
      updatedAt: admin.firestore.FieldValue.serverTimestamp(),
      ...(adviceId && { lastHiddenAdviceId: adviceId })
    };
    
    await settingsRef.set(settingsData, { merge: true });
    
    logger.info(`ユーザー ${userId} のアドバイス表示設定を更新しました: ${isVisible ? '表示' : '非表示'}`);
    
    return {
      success: true,
      message: "アドバイス表示設定を更新しました"
    };
    
  } catch (error) {
    logger.error("アドバイス表示設定更新エラー:", error);
    throw new Error("アドバイス表示設定の更新に失敗しました");
  }
});

// ユーザーのアドバイス表示設定を取得API
export const getAdviceSettings = onCall({
  region: 'asia-northeast1',
  cors: true,
}, async (request) => {
  const auth = request.auth;
  
  try {
    logger.info("アドバイス表示設定取得を開始...");
    
    const userId = auth?.uid || 'anonymous';
    
    const settingsDoc = await admin.firestore()
      .collection('user_advice_settings')
      .doc(userId)
      .get();
    
    if (!settingsDoc.exists) {
      // デフォルト設定を返す
      return {
        success: true,
        data: {
          isVisible: true,
          updatedAt: null,
          lastHiddenAdviceId: null
        }
      };
    }
    
    const settings = settingsDoc.data();
    
    return {
      success: true,
      data: {
        ...settings,
        updatedAt: settings?.updatedAt?.toDate?.() || null
      }
    };
    
  } catch (error) {
    logger.error("アドバイス表示設定取得エラー:", error);
    throw new Error("アドバイス表示設定の取得に失敗しました");
  }
});
