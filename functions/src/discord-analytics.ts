import { onRequest } from 'firebase-functions/v2/https';
import { onDocumentCreated } from 'firebase-functions/v2/firestore';
import { getFirestore } from 'firebase-admin/firestore';
import { initializeApp, getApps } from 'firebase-admin/app';
import { logger } from 'firebase-functions';

// Firebase Admin SDK の初期化（重複を避ける）
if (getApps().length === 0) {
  initializeApp();
}
const db = getFirestore();

// Vertex AI のインポート（Google Cloud SDK）
import { VertexAI } from '@google-cloud/vertexai';

// Vertex AI クライアントの初期化
const vertex_ai = new VertexAI({
  project: process.env.GOOGLE_CLOUD_PROJECT || 'nyanco-bot',
  location: 'asia-northeast1', // 東京リージョン
});

// Gemini モデルの設定
const model = 'gemini-1.5-pro';

interface DiscordLog {
  type: string;
  userId: string;
  username?: string; // Optional field for compatibility
  guildId: string;
  guildName: string;
  channelId: string;
  channelName: string;
  content?: string;
  timestamp: Date;
  metadata?: Record<string, any>;
  keywords?: string[];
}

interface AnalysisResult {
  userPostRanking: Array<{ username: string; count: number; ratio: number }>;
  channelActivity: Array<{ channel: string; count: number; ratio: number }>;
  neglectedUsers: Array<{ username: string; posts: number; reactions: number; neglectRate: number }>;
  suspiciousContent: Array<{ username: string; content: string; severity: 'low' | 'medium' | 'high'; words: string[] }>;
  communityHealth: {
    participation: number;
    engagement: number;
    safety: number;
    overall: number;
  };
}

interface AIAdvice {
  type: 'participation' | 'engagement' | 'moderation' | 'structure' | 'health';
  priority: 'critical' | 'high' | 'medium' | 'low' | 'info';
  title: string;
  message: string;
  action: string;
  icon: string;
  timestamp: Date;
}

// 不適切なワードのリスト
const SUSPICIOUS_WORDS = [
  '馬鹿', 'バカ', 'ばか', 'アホ', 'あほ', '死ね', 'しね', 'きもい', 'キモい', 'キモイ',
  'うざい', 'ウザい', 'ウザイ', 'クソ', 'くそ', '殺す', 'ころす', 'ブス', 'ぶす',
  'デブ', 'でぶ', 'チビ', 'ちび', 'ハゲ', 'はげ', '消えろ', 'きえろ', '最悪', 'さいあく'
];

/**
 * ユーザーIDからユーザー名を解決する
 */
async function resolveUsernames(userIds: string[]): Promise<Record<string, string>> {
  const userMap: Record<string, string> = {};
  
  if (userIds.length === 0) return userMap;
  
  try {
    // Firestoreのusersコレクションからユーザー情報を取得
    const usersSnapshot = await db.collection('users')
      .where('userId', 'in', userIds.slice(0, 10)) // Firestoreのin制限 (10個まで)
      .get();
    
    usersSnapshot.forEach(doc => {
      const userData = doc.data();
      const userId = userData.userId;
      const username = userData.displayName || userData.username || `User_${userId.slice(0, 8)}`;
      userMap[userId] = username;
    });
    
    // 残りのユーザーIDも処理（10個ずつ）
    for (let i = 10; i < userIds.length; i += 10) {
      const batch = userIds.slice(i, i + 10);
      const batchSnapshot = await db.collection('users')
        .where('userId', 'in', batch)
        .get();
      
      batchSnapshot.forEach(doc => {
        const userData = doc.data();
        const userId = userData.userId;
        const username = userData.displayName || userData.username || `User_${userId.slice(0, 8)}`;
        userMap[userId] = username;
      });
    }
    
    // 見つからなかったユーザーIDには fallback 名を設定
    userIds.forEach(userId => {
      if (!userMap[userId]) {
        userMap[userId] = `User_${userId.slice(0, 8)}`;
      }
    });
    
  } catch (error) {
    logger.error('ユーザー名解決エラー', { error });
    // エラー時はfallback名を使用
    userIds.forEach(userId => {
      userMap[userId] = `User_${userId.slice(0, 8)}`;
    });
  }
  
  return userMap;
}

/**
 * Discord ログを分析して統計データを生成
 */
async function analyzeDiscordLogsData(logs: DiscordLog[]): Promise<AnalysisResult> {
  // ユニークなユーザーIDを取得
  const uniqueUserIds = [...new Set(logs.map(log => log.userId).filter(Boolean))];
  
  // ユーザー名を解決
  const userMap = await resolveUsernames(uniqueUserIds);
  const userStats: Record<string, { posts: number; reactions: number }> = {};
  const channelStats: Record<string, number> = {};
  const suspiciousContent: Array<{ username: string; content: string; severity: 'low' | 'medium' | 'high'; words: string[] }> = [];

  // ログデータの分析
  logs.forEach(log => {
    const username = userMap[log.userId] || log.username || `User_${log.userId?.slice(0, 8)}`;
    
    // ユーザー統計
    if (log.type === 'message' && log.userId) {
      if (!userStats[username]) {
        userStats[username] = { posts: 0, reactions: 0 };
      }
      userStats[username].posts++;
      userStats[username].reactions += log.metadata?.reactionCount || 0;
    }

    // チャンネル統計
    if (log.channelName) {
      channelStats[log.channelName] = (channelStats[log.channelName] || 0) + 1;
    }

    // 不適切コンテンツの検知
    if (log.content) {
      const foundWords = SUSPICIOUS_WORDS.filter(word => 
        log.content!.toLowerCase().includes(word.toLowerCase())
      );
      
      if (foundWords.length > 0) {
        const severity = foundWords.length > 2 ? 'high' : foundWords.length > 1 ? 'medium' : 'low';
        suspiciousContent.push({
          username: username,
          content: log.content,
          severity,
          words: foundWords
        });
      }
    }
  });

  // 投稿数ランキング
  const totalPosts = Object.values(userStats).reduce((sum, stats) => sum + stats.posts, 0);
  const userPostRanking = Object.entries(userStats)
    .map(([username, stats]) => ({
      username,
      count: stats.posts,
      ratio: totalPosts > 0 ? (stats.posts / totalPosts) * 100 : 0
    }))
    .sort((a, b) => b.count - a.count);

  // チャンネル別アクティビティ
  const totalChannelActivity = Object.values(channelStats).reduce((sum, count) => sum + count, 0);
  const channelActivity = Object.entries(channelStats)
    .map(([channel, count]) => ({
      channel,
      count,
      ratio: totalChannelActivity > 0 ? (count / totalChannelActivity) * 100 : 0
    }))
    .sort((a, b) => b.count - a.count);

  // リアクション不足のユーザー
  const neglectedUsers = Object.entries(userStats)
    .map(([username, stats]) => ({
      username,
      posts: stats.posts,
      reactions: stats.reactions,
      neglectRate: stats.posts > 0 ? stats.reactions / stats.posts : 0
    }))
    .filter(user => user.posts >= 3) // 3投稿以上のユーザーのみ
    .sort((a, b) => a.neglectRate - b.neglectRate);

  // コミュニティ健康度の計算
  const participationScore = Math.min(100, (Object.keys(userStats).length / 20) * 100);
  const engagementScore = Math.min(100, (Object.values(userStats).reduce((sum, user) => sum + user.reactions, 0) / Math.max(1, Object.values(userStats).reduce((sum, user) => sum + user.posts, 0))) * 10);
  const safetyScore = Math.max(0, 100 - (suspiciousContent.length * 5));
  const overallScore = (participationScore + engagementScore + safetyScore) / 3;

  return {
    userPostRanking,
    channelActivity,
    neglectedUsers,
    suspiciousContent,
    communityHealth: {
      participation: Math.round(participationScore),
      engagement: Math.round(engagementScore),
      safety: Math.round(safetyScore),
      overall: Math.round(overallScore)
    }
  };
}

/**
 * Vertex AI (Gemini) を使用して運営アドバイスを生成
 */
async function generateAIAdvice(analysis: AnalysisResult, logs: DiscordLog[]): Promise<AIAdvice[]> {
  try {
    const generativeModel = vertex_ai.preview.getGenerativeModel({
      model: model,
      generationConfig: {
        maxOutputTokens: 2048,
        temperature: 0.7,
        topP: 0.8,
      },
    });

    // プロンプトの構築
    const prompt = `
あなたはDiscordコミュニティの運営アドバイザーです。以下のDiscordログ分析結果を基に、コミュニティ運営の改善案を5つ以内で提案してください。

【分析結果】
■投稿ランキング上位5名:
${analysis.userPostRanking.slice(0, 5).map((user, i) => `${i+1}. ${user.username}: ${user.count}投稿 (${user.ratio.toFixed(1)}%)`).join('\n')}

■チャンネル別アクティビティ:
${analysis.channelActivity.slice(0, 5).map(ch => `#${ch.channel}: ${ch.count}件 (${ch.ratio.toFixed(1)}%)`).join('\n')}

■リアクション不足ユーザー（上位3名）:
${analysis.neglectedUsers.slice(0, 3).map(user => `${user.username}: ${user.posts}投稿に対し${user.reactions}リアクション (平均${user.neglectRate.toFixed(2)}/投稿)`).join('\n')}

■不適切表現検知:
- 総件数: ${analysis.suspiciousContent.length}件
- 高リスク: ${analysis.suspiciousContent.filter(c => c.severity === 'high').length}件
- 中リスク: ${analysis.suspiciousContent.filter(c => c.severity === 'medium').length}件

■コミュニティ健康度:
- 参加度: ${analysis.communityHealth.participation}%
- エンゲージメント: ${analysis.communityHealth.engagement}%  
- 安全性: ${analysis.communityHealth.safety}%
- 総合: ${analysis.communityHealth.overall}%

【アドバイス要件】
1. 各提案は「タイトル」「説明」「具体的なアクション」の形式で記述
2. 優先度を「critical/high/medium/low/info」で設定
3. アドバイスタイプを「participation/engagement/moderation/structure/health」で分類
4. 日本語で回答し、実用的で具体的な提案を行う
5. JSONフォーマットで出力（下記例を参考）

出力例:
[
  {
    "type": "engagement",
    "priority": "high", 
    "title": "エンゲージメント向上策",
    "message": "具体的な問題と解決方針の説明",
    "action": "具体的に実行すべきアクション"
  }
]
`;

    const result = await generativeModel.generateContent(prompt);
    const response = result.response;
    
    // 候補の最初のテキストを取得
    const text = response.candidates?.[0]?.content?.parts?.[0]?.text || '';

    // JSONの抽出と解析
    let advices: any[] = [];
    try {
      // JSONの部分を抽出
      const jsonMatch = text.match(/\[([\s\S]*)\]/);
      if (jsonMatch) {
        advices = JSON.parse(jsonMatch[0]);
      }
    } catch (parseError) {
      logger.warn('AI レスポンスのJSON解析に失敗、デフォルトアドバイスを生成', { parseError, text });
      advices = generateDefaultAdvice(analysis);
    }

    // AIAdvice 形式に変換
    return advices.map((advice, index) => ({
      type: advice.type || 'health',
      priority: advice.priority || 'medium',
      title: advice.title || `アドバイス ${index + 1}`,
      message: advice.message || 'AIによる自動生成アドバイス',
      action: advice.action || '詳細な検討が必要です',
      icon: getIconForType(advice.type || 'health'),
      timestamp: new Date()
    }));

  } catch (error) {
    logger.error('Vertex AI API 呼び出しエラー', { error });
    // エラー時はデフォルトアドバイスを返す
    return generateDefaultAdvice(analysis);
  }
}

/**
 * デフォルトアドバイスの生成（AI API失敗時のフォールバック）
 */
function generateDefaultAdvice(analysis: AnalysisResult): AIAdvice[] {
  const advices: AIAdvice[] = [];

  // 参加バランスのチェック
  if (analysis.userPostRanking.length > 0 && analysis.userPostRanking[0].ratio > 30) {
    advices.push({
      type: 'participation',
      priority: 'medium',
      title: '参加バランスの改善',
      message: `特定ユーザーの投稿が集中しています（${analysis.userPostRanking[0].ratio.toFixed(1)}%）。他のメンバーの発言を促進する施策が必要です。`,
      action: '質問投稿やアイスブレイク企画で他のメンバーの参加を促してください',
      icon: 'group_work',
      timestamp: new Date()
    });
  }

  // エンゲージメントのチェック
  if (analysis.communityHealth.engagement < 50) {
    advices.push({
      type: 'engagement',
      priority: 'high',
      title: 'エンゲージメント向上が必要',
      message: `コミュニティのエンゲージメントが低下しています（${analysis.communityHealth.engagement}%）。リアクションやコメントの促進が重要です。`,
      action: 'モデレーターから積極的なリアクションを行い、メンバーにも参加を呼びかけてください',
      icon: 'favorite',
      timestamp: new Date()
    });
  }

  // 安全性のチェック
  if (analysis.suspiciousContent.length > 0) {
    const highRiskCount = analysis.suspiciousContent.filter(c => c.severity === 'high').length;
    advices.push({
      type: 'moderation',
      priority: highRiskCount > 0 ? 'critical' : 'high',
      title: '不適切表現への対応',
      message: `不適切な表現が${analysis.suspiciousContent.length}件検出されました。コミュニティルールの周知が必要です。`,
      action: '該当ユーザーへの個別指導とガイドラインの再共有を実施してください',
      icon: 'warning',
      timestamp: new Date()
    });
  }

  // コミュニティ健康度
  advices.push({
    type: 'health',
    priority: 'info',
    title: 'コミュニティ健康度レポート',
    message: `参加度: ${analysis.communityHealth.participation}%, エンゲージメント: ${analysis.communityHealth.engagement}%, 安全性: ${analysis.communityHealth.safety}%`,
    action: '定期的な健康度チェックを継続し、数値の改善を目指してください',
    icon: 'health_and_safety',
    timestamp: new Date()
  });

  return advices;
}

/**
 * アドバイスタイプに応じたアイコンを取得
 */
function getIconForType(type: string): string {
  const iconMap: Record<string, string> = {
    'participation': 'group_work',
    'engagement': 'favorite',
    'moderation': 'warning',
    'structure': 'view_list',
    'health': 'health_and_safety'
  };
  return iconMap[type] || 'info';
}

/**
 * Discord ログ分析 API エンドポイント
 */
export const analyzeDiscordLogs = onRequest(
  { 
    cors: true,
    region: 'asia-northeast1',
    memory: '1GiB',
    timeoutSeconds: 300
  },
  async (request, response) => {
    try {
      logger.info('Discord ログ分析 API が呼び出されました');

      // 認証チェック（オプション）
      const authHeader = request.headers.authorization;
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        logger.warn('認証ヘッダーが不正', { authHeader });
        // 開発中は認証をスキップ
        // response.status(401).json({ error: '認証が必要です' });
        // return;
      }

      // Firestore から最新のインタラクションデータを取得
      logger.info('Firestoreからインタラクションデータを取得中...');
      let interactionsSnapshot;
      try {
        interactionsSnapshot = await db.collection('interactions')
          .orderBy('timestamp', 'desc')
          .limit(1000) // 最新1000件を分析対象とする
          .get();
      } catch (firestoreError) {
        logger.error('Firestoreからのデータ取得エラー', { firestoreError });
        // timestampフィールドでのソートが失敗する場合、フィールドなしで取得
        try {
          interactionsSnapshot = await db.collection('interactions')
            .limit(1000)
            .get();
          logger.info('timestampなしでFirestoreデータを取得しました');
        } catch (fallbackError) {
          logger.error('Firestore取得の代替方法も失敗', { fallbackError });
          throw new Error(`Firestoreデータ取得失敗: ${fallbackError instanceof Error ? fallbackError.message : String(fallbackError)}`);
        }
      }

      const logs: DiscordLog[] = [];
      if (interactionsSnapshot && !interactionsSnapshot.empty) {
        interactionsSnapshot.forEach(doc => {
          try {
            const data = doc.data();
            if (data) {
              logs.push({
                type: data.type || 'unknown',
                userId: data.userId || '',
                username: data.username || '',
                guildId: data.guildId || '',
                guildName: data.guildName || '',
                channelId: data.channelId || '',
                channelName: data.channelName || '',
                content: data.content,
                timestamp: data.timestamp?.toDate() || new Date(),
                metadata: data.metadata || {},
                keywords: data.keywords || []
              });
            }
          } catch (docError) {
            logger.warn('ドキュメント処理エラー', { docId: doc.id, docError });
          }
        });
      } else {
        logger.warn('Firestoreクエリ結果が空です');
      }

      logger.info(`${logs.length}件のログを取得しました`);

      // ログの分析（非同期に変更）
      logger.info('ログデータの分析を開始...');
      const analysis = await analyzeDiscordLogsData(logs);
      
      // AI による運営アドバイスの生成
      logger.info('AI アドバイスの生成を開始...');
      let aiAdvices;
      try {
        aiAdvices = await generateAIAdvice(analysis, logs);
      } catch (aiError) {
        logger.error('AI アドバイス生成エラー、デフォルトアドバイスを使用', { aiError });
        aiAdvices = generateDefaultAdvice(analysis);
      }

      // 分析結果を Firestore に保存
      const analysisResult = {
        analysis,
        aiAdvices,
        logCount: logs.length,
        analysisDate: new Date(),
        guildIds: [...new Set(logs.map(log => log.guildId))],
        channels: [...new Set(logs.map(log => log.channelName))].filter(Boolean)
      };

      try {
        await db.collection('discord_analysis').add(analysisResult);
        logger.info('分析結果をFirestoreに保存しました');
      } catch (saveError) {
        logger.error('分析結果の保存エラー', { saveError });
        // 保存に失敗してもレスポンスは返す
      }

      logger.info('Discord ログ分析が完了しました', {
        logCount: logs.length,
        adviceCount: aiAdvices.length,
        healthScore: analysis.communityHealth.overall
      });

      // レスポンスを返す
      response.json({
        success: true,
        data: analysisResult,
        message: 'Discord ログ分析が完了しました'
      });

    } catch (error) {
      logger.error('Discord ログ分析中にエラーが発生しました', { error });
      response.status(500).json({
        success: false,
        error: '分析処理中にエラーが発生しました',
        details: error instanceof Error ? error.message : String(error)
      });
    }
  }
);

/**
 * 新しいインタラクションが追加された時の自動分析トリガー
 */
export const onInteractionAdded = onDocumentCreated(
  {
    document: 'interactions/{docId}',
    region: 'asia-northeast1'
  },
  async (event) => {
    try {
      const snapshot = event.data;
      if (!snapshot) {
        logger.warn('スナップショットが空です');
        return;
      }

      const data = snapshot.data();
      
      // ユーザー名を解決
      const userMap = await resolveUsernames([data.userId]);
      const username = userMap[data.userId] || data.username || `User_${data.userId?.slice(0, 8)}`;
      
      logger.info('新しいインタラクションが追加されました', {
        docId: snapshot.id,
        type: data.type,
        userId: data.userId,
        username: username,
        guildName: data.guildName
      });

      // 不適切表現の即座チェック
      if (data.content && typeof data.content === 'string') {
        const foundWords = SUSPICIOUS_WORDS.filter(word => 
          data.content.toLowerCase().includes(word.toLowerCase())
        );

        if (foundWords.length > 0) {
          const severity = foundWords.length > 2 ? 'critical' : foundWords.length > 1 ? 'high' : 'medium';
          
          // 緊急アラートを作成
          await db.collection('moderation_alerts').add({
            type: 'suspicious_content',
            severity,
            userId: data.userId,
            username: username,
            guildId: data.guildId,
            guildName: data.guildName,
            channelId: data.channelId,
            channelName: data.channelName,
            content: data.content,
            suspiciousWords: foundWords,
            timestamp: new Date(),
            status: 'pending',
            autoDetected: true
          });

          logger.warn('不適切な表現を検知しました', {
            userId: data.userId,
            username: username,
            guildName: data.guildName,
            severity,
            words: foundWords
          });
        }
      }

    } catch (error) {
      logger.error('インタラクション処理中にエラーが発生しました', { error });
    }
  }
);

/**
 * 過去の分析結果を取得する API
 */
export const getAnalysisHistory = onRequest(
  { 
    cors: true,
    region: 'asia-northeast1'
  },
  async (request, response) => {
    try {
      const limit = parseInt(request.query.limit as string) || 10;
      const guildId = request.query.guildId as string;

      let query = db.collection('discord_analysis')
        .orderBy('analysisDate', 'desc')
        .limit(limit);

      if (guildId) {
        query = query.where('guildIds', 'array-contains', guildId);
      }

      const snapshot = await query.get();
      const analyses = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));

      response.json({
        success: true,
        data: analyses,
        count: analyses.length
      });

    } catch (error) {
      logger.error('分析履歴取得中にエラーが発生しました', { error });
      response.status(500).json({
        success: false,
        error: '分析履歴の取得に失敗しました'
      });
    }
  }
);

/**
 * Botアクション履歴を取得する API
 */
export const getBotActionsHistory = onRequest(
  {
    cors: true,
    region: 'asia-northeast1'
  },
  async (request, response) => {
    try {
      logger.info('Botアクション履歴 API が呼び出されました');

      // クエリパラメータの取得
      const limit = Math.min(parseInt(request.query.limit as string) || 50, 100); // 最大100件
      const guildId = request.query.guildId as string;
      const actionType = request.query.actionType as string;
      const status = request.query.status as string;
      const userId = request.query.userId as string;
      const startDate = request.query.startDate as string;
      const endDate = request.query.endDate as string;

      // Firestoreクエリの構築
      let query = db.collection('bot_actions')
        .orderBy('timestamp', 'desc')
        .limit(limit);

      // フィルター条件の適用
      if (guildId) {
        query = query.where('guildId', '==', guildId);
      }
      if (actionType) {
        query = query.where('actionType', '==', actionType);
      }
      if (status) {
        query = query.where('status', '==', status);
      }
      if (userId) {
        query = query.where('userId', '==', userId);
      }

      // 日付範囲フィルター（基本的な実装）
      if (startDate) {
        const start = new Date(startDate);
        query = query.where('timestamp', '>=', start);
      }
      if (endDate) {
        const end = new Date(endDate);
        query = query.where('timestamp', '<=', end);
      }

      const snapshot = await query.get();
      
      if (snapshot.empty) {
        response.json({
          success: true,
          data: [],
          count: 0,
          message: 'Botアクション履歴が見つかりません'
        });
        return;
      }

      // ドキュメントデータの処理
      const actions: any[] = [];
      const userIds = new Set<string>();

      snapshot.forEach(doc => {
        const data = doc.data();
        actions.push({
          id: doc.id,
          ...data,
          timestamp: data.timestamp?.toDate?.() || data.timestamp
        });
        
        if (data.userId) {
          userIds.add(data.userId);
        }
      });

      // ユーザー名を解決
      const userMap = await resolveUsernames(Array.from(userIds));

      // アクションデータにユーザー名を追加
      const enrichedActions = actions.map(action => ({
        ...action,
        username: userMap[action.userId] || `User_${action.userId?.slice(0, 8)}` || 'Unknown'
      }));

      // 統計情報の生成
      const stats = {
        total: enrichedActions.length,
        byActionType: {} as Record<string, number>,
        byStatus: {} as Record<string, number>,
        byCharacter: {} as Record<string, number>,
        recentActivity: enrichedActions.slice(0, 10)
      };

      enrichedActions.forEach(action => {
        // アクション種別統計
        const actionType = action.actionType || 'unknown';
        stats.byActionType[actionType] = (stats.byActionType[actionType] || 0) + 1;

        // ステータス統計
        const status = action.status || 'unknown';
        stats.byStatus[status] = (stats.byStatus[status] || 0) + 1;

        // キャラクター統計
        const character = action.botCharacter || action.payload?.character || 'unknown';
        stats.byCharacter[character] = (stats.byCharacter[character] || 0) + 1;
      });

      logger.info('Botアクション履歴取得完了', {
        count: enrichedActions.length,
        guildId,
        actionType,
        status
      });

      response.json({
        success: true,
        data: enrichedActions,
        count: enrichedActions.length,
        stats,
        query: {
          limit,
          guildId,
          actionType,
          status,
          userId,
          startDate,
          endDate
        }
      });

    } catch (error) {
      logger.error('Botアクション履歴取得中にエラーが発生しました', { error });
      response.status(500).json({
        success: false,
        error: 'Botアクション履歴の取得に失敗しました',
        details: error instanceof Error ? error.message : String(error)
      });
    }
  }
); 