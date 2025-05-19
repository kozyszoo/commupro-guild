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
