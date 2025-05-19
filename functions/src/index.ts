/**
 * Import function triggers from their respective submodules:
 *
 * import {onCall} from "firebase-functions/v2/https";
 * import {onDocumentWritten} from "firebase-functions/v2/firestore";
 *
 * See a full list of supported triggers at https://firebase.google.com/docs/functions
 */

import {onRequest} from "firebase-functions/v2/https";
import * as logger from "firebase-functions/logger";
import * as functions from "firebase-functions";
import * as admin from "firebase-admin";

admin.initializeApp();

// Start writing functions
// https://firebase.google.com/docs/functions/typescript

// export const helloWorld = onRequest((request, response) => {
//   logger.info("Hello logs!", {structuredData: true});
//   response.send("Hello from Firebase!");
// });

// Discordウェルカムメッセージの関数
export const welcomeNewMember = functions.firestore
  .document("users/{userId}")
  .onCreate(async (snap, context) => {
    const userData = snap.data();
    console.log(`新しいユーザーが登録されました: ${userData.username}`);
    // ここにDiscordボットを通じてメッセージを送信するロジックを追加
    return null;
  });

// 非アクティブユーザーの再エンゲージメント
export const reengageInactiveUsers = functions.pubsub
  .schedule("0 12 * * *") // 毎日正午に実行
  .timeZone("Asia/Tokyo")
  .onRun(async (context) => {
    const now = admin.firestore.Timestamp.now();
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    
    const inactiveUsers = await admin.firestore()
      .collection("users")
      .where("lastActive", "<", thirtyDaysAgo)
      .get();
    
    console.log(`非アクティブユーザー数: ${inactiveUsers.size}`);
    // ここに非アクティブユーザーへのDMを送信するロジックを追加
    return null;
  });

// ユーザーマッチング
export const matchSimilarUsers = functions.https.onCall(async (data, context) => {
  // 認証チェック
  if (!context.auth) {
    throw new functions.https.HttpsError(
      "unauthenticated",
      "認証が必要です"
    );
  }
  
  const userId = data.userId;
  const userDoc = await admin.firestore().collection("users").doc(userId).get();
  
  if (!userDoc.exists) {
    throw new functions.https.HttpsError(
      "not-found",
      "ユーザーが見つかりません"
    );
  }
  
  const userData = userDoc.data();
  const userInterests = userData?.interests || [];
  
  // 同じ興味を持つユーザーを検索
  const similarUsers = await admin.firestore()
    .collection("users")
    .where("interests", "array-contains-any", userInterests)
    .limit(5)
    .get();
  
  const result = [];
  similarUsers.forEach((doc) => {
    if (doc.id !== userId) {
      const user = doc.data();
      result.push({
        id: doc.id,
        username: user.username,
        interests: user.interests
      });
    }
  });
  
  return { users: result };
});
