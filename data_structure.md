# Discord にゃんこエージェント データ構造詳細

## 概要

DiscordにゃんこエージェントはFirestoreをメインデータベースとして使用し、以下の主要コレクションで構成されています：

- **users**: ユーザー情報とエンゲージメントデータ
- **interactions**: 全ユーザーインタラクションログ
- **discord_analysis**: Discord分析結果とAIアドバイス
- **weekly_advice**: 週次アドバイス情報
- **bot_actions**: ボットアクション履歴
- **moderation_alerts**: リアルタイムモデレーションアラート

このドキュメントでは、各コレクションの詳細なフィールド構造、データ型、および使用目的について説明します。

## 1. Users Collection

### 概要
Discordサーバーの各ユーザーの情報を管理するメインテーブル。ユーザーのプロフィール情報、活動状況、興味関心、エンゲージメント履歴を格納する。

### フィールド詳細

| フィールド名 | 型 | 必須 | 説明 | 例 |
|-------------|---|------|------|---|
| `id` | string | ✓ | Discord User ID（プライマリキー） | "123456789012345678" |
| `guildId` | string | ✓ | 所属するDiscord Guild ID | "987654321098765432" |
| `username` | string | ✓ | Discordユーザー名 | "TechUser2024" |
| `displayName` | string | | 表示名（ニックネーム） | "Tech Enthusiast" |
| `joinedAt` | string | ✓ | サーバー参加日時（ISO 8601） | "2024-01-15T09:30:00Z" |
| `isActive` | boolean | ✓ | 現在アクティブかどうか | true |
| `lastActivity` | string | ✓ | 最終活動日時 | "2024-05-24T14:22:00Z" |
| `interests` | array | | 関心事のリスト | ["JavaScript", "React"] |
| `channels` | array | | よく利用するチャンネル | ["general", "tech-talk"] |
| `engagementScore` | number | | エンゲージメントスコア（0-100） | 85.5 |
| `reengagementHistory` | object | | 再エンゲージメント履歴 | 下記参照 |
| `timezone` | string | | タイムゾーン | "Asia/Tokyo" |
| `preferences` | object | | ユーザー設定 | 下記参照 |

### サブオブジェクト構造

```typescript
// reengagementHistory の構造
interface ReengagementHistory {
  totalAttempts: number;        // 総試行回数
  successfulReengagements: number; // 成功回数
  lastAttempt: string | null;   // 最終試行日時 (ISO 8601)
  lastSuccess: string | null;   // 最終成功日時 (ISO 8601)
}

// preferences の構造
interface UserPreferences {
  podcastNotifications: boolean;  // ポッドキャスト通知
  matchingNotifications: boolean; // マッチング通知
  dmNotifications: boolean;       // DM通知
  language: string;               // 言語設定 ('ja', 'en')
}

// TypeScriptインターフェース
interface User {
  id: string;
  guildId: string;
  username: string;
  displayName?: string;
  joinedAt: string;
  isActive: boolean;
  lastActivity: string;
  interests: string[];
  channels: string[];
  engagementScore: number;
  reengagementHistory: ReengagementHistory;
  timezone: string;
  preferences: UserPreferences;
}
```

### 主な用途
- 新規参加者の歓迎処理
- 非アクティブユーザーの検出
- ユーザーマッチング
- エンゲージメント分析

## 2. Guilds Collection

### 概要
Discordサーバー（Guild）の設定情報を管理。ボットの動作設定、キャラクター設定、チャンネル設定などを格納する。

### フィールド詳細

| フィールド名 | 型 | 必須 | 説明 | 例 |
|-------------|---|------|------|---|
| `id` | string | ✓ | Discord Guild ID（プライマリキー） | "987654321098765432" |
| `name` | string | ✓ | サーバー名 | "Tech Community Japan" |
| `ownerId` | string | ✓ | サーバーオーナーのUser ID | "111222333444555666" |
| `botSettings` | object | ✓ | ボット設定オブジェクト | 下記参照 |
| `welcomeChannelId` | string | | 歓迎メッセージ送信チャンネル | "channel_welcome_123" |
| `podcastChannelId` | string | | ポッドキャスト配信チャンネル | "channel_podcast_456" |
| `createdAt` | string | ✓ | ボット導入日時 | "2023-12-01T00:00:00Z" |
| `updatedAt` | string | ✓ | 最終更新日時 | "2024-05-24T12:00:00Z" |
| `analytics` | object | | 分析データサマリー | 下記参照 |

### botSettings の詳細構造

```typescript
{
  traNyanPersonality: {
    energyLevel: number,          // エネルギーレベル（0-1）
    friendliness: number,         // フレンドリーさ（0-1）
    endPhrases: string[],         // 語尾パターン
    customMessages: object        // カスタムメッセージ
  },
  kuroNyanPersonality: {
    analyticalLevel: number,      // 分析レベル（0-1）
    helpfulness: number,          // 親切さ（0-1）
    endPhrases: string[],         // 語尾パターン
    customMessages: object        // カスタムメッセージ
  },
  podcastFrequency: string,       // Cron形式のスケジュール
  inactiveThreshold: number,      // 非アクティブ判定日数
  reengagementFrequency: number,  // 再エンゲージメント頻度
  maxReengagementAttempts: number, // 最大試行回数
  matchingEnabled: boolean,       // マッチング機能有効
  matchingThreshold: number,      // マッチング閾値
  analyticsEnabled: boolean       // 分析機能有効
}
```

### 主な用途
- サーバーメタデータの記録と追跡
- コミュニティサイズ分析
- サーバー成長のモニタリング
- ボット対応サーバーの管理

## 3. Interactions Collection

### 概要
ユーザーのすべてのインタラクション（メッセージ、リアクション、ボットとの対話）を記録。分析とユーザー理解のためのログデータ。

### フィールド詳細

| フィールド名 | 型 | 必須 | 説明 | 例 |
|-------------|---|------|------|---|
| `id` | string | ✓ | 一意のインタラクションID | "interaction_001" |
| `userId` | string | ✓ | インタラクションしたユーザーID | "123456789012345678" |
| `guildId` | string | ✓ | サーバーID | "987654321098765432" |
| `type` | string | ✓ | インタラクションタイプ | "message", "reaction", "bot_interaction" |
| `channelId` | string | | チャンネルID | "channel_tech_talk_789" |
| `messageId` | string | | メッセージID | "msg_987654321" |
| `content` | string | | メッセージ内容 | "ReactのuseEffectについて質問があります" |
| `metadata` | object | | 追加メタデータ | 下記参照 |
| `timestamp` | string | ✓ | 発生日時 | "2024-05-24T14:22:00Z" |
| `sentiment` | number | | 感情分析スコア（-1 ～ 1） | 0.1 |
| `keywords` | array | | 抽出されたキーワード | ["React", "useEffect", "質問"] |

### インタラクションタイプ

| タイプ | 説明 | metadata 例 |
|--------|------|-------------|
| `message` | 通常のメッセージ | `{messageLength: 22, hasCodeBlock: false, hasLinks: false}` |
| `reaction` | リアクション（絵文字） | `{reactionType: "👍", targetUserId: "xxx", targetMessageContent: "..."}` |
| `bot_interaction` | ボットとの対話 | `{botActionId: "xxx", botCharacter: "tra_nyan", interactionType: "response_to_welcome"}` |
| `voice_activity` | ボイスチャンネル参加 | `{duration: 3600, channelType: "general_voice"}` |
| `thread_creation` | スレッド作成 | `{threadTitle: "React質問", parentMessageId: "xxx"}` |

### 主な用途
- ユーザーの関心分析
- エンゲージメント測定
- トレンド検出
- ボット効果測定

## 4. Discord_Analysis Collection

### 概要
Firebase Functionsの`analyzeDiscordLogs`関数によって生成されるDiscordコミュニティの分析結果。AIによる運営アドバイスやコミュニティ健康度スコアを含む。

### フィールド詳細

| フィールド名 | 型 | 必須 | 説明 | 例 |
|-------------|---|------|------|---|
| `id` | string | ✓ | 分析結果ID | "analysis_20241220_143000" |
| `analysis` | object | ✓ | 分析結果オブジェクト | 下記参照 |
| `aiAdvices` | array | ✓ | AI運営アドバイス配列 | 下記参照 |
| `logCount` | number | ✓ | 分析対象ログ数 | 1247 |
| `analysisDate` | timestamp | ✓ | 分析実行日時 | Firestore Timestamp |
| `guildIds` | array | ✓ | 対象サーバーID群 | ["987654321098765432"] |
| `channels` | array | ✓ | 分析対象チャンネル | ["general", "tech-talk"] |

### analysisオブジェクト構造

```typescript
interface AnalysisResult {
  userPostRanking: Array<{
    username: string;
    count: number;
    ratio: number;  // 全体に占める割合
  }>;
  channelActivity: Array<{
    channel: string;
    count: number;
    ratio: number;
  }>;
  neglectedUsers: Array<{
    username: string;
    posts: number;
    reactions: number;
    neglectRate: number;  // リアクション/投稿数
  }>;
  suspiciousContent: Array<{
    username: string;
    content: string;
    severity: 'low' | 'medium' | 'high';
    words: string[];  // 不適切ワード
  }>;
  communityHealth: {
    participation: number;    // 参加度 (0-100)
    engagement: number;       // エンゲージメント (0-100)
    safety: number;           // 安全性 (0-100)
    overall: number;          // 総合スコア (0-100)
  };
}
```

### aiAdvices配列構造

```typescript
interface AIAdvice {
  type: 'participation' | 'engagement' | 'moderation' | 'structure' | 'health';
  priority: 'critical' | 'high' | 'medium' | 'low' | 'info';
  title: string;
  message: string;
  action: string;
  icon: string;
  timestamp: Date;
}
```

### 主な用途
- Webダッシュボードでのリアルタイム分析表示
- コミュニティ健康度の追跡と改善提案
- AIアドバイスを通じた運営改善
- 不適切コンテンツの検知とモデレーション
- ユーザーエンゲージメントの分析
- 長期的なトレンド分析

## 5. Weekly_Advice Collection

### 概要
Vertex AI (Gemini)によって生成される週次コミュニティ運営アドバイス。過去1週間のアクティビティデータを分析し、コミュニティ改善のための具体的な提案を提供。

### フィールド詳細

| フィールド名 | 型 | 必須 | 説明 | 例 |
|-------------|---|------|------|---|
| `adviceId` | string | ✓ | アドバイスID | "advice_20241220_143000" |
| `weekOf` | string | ✓ | 対象週の開始日 | "2024-12-16" |
| `weekStart` | timestamp | ✓ | 分析期間開始 | Firestore Timestamp |
| `weekEnd` | timestamp | ✓ | 分析期間終了 | Firestore Timestamp |
| `content` | string | ✓ | アドバイス内容 | "今週はアクティブユーザー数が增加し..." |
| `activityStats` | object | ✓ | 対象期間のアクティビティ統計 | 下記参照 |
| `createdAt` | timestamp | ✓ | 作成日時 | Firestore Timestamp |
| `isActive` | boolean | ✓ | アクティブ状態 | true |
| `guildId` | string | | 対象サーバーID | "987654321098765432" |
| `generatedBy` | string | ✓ | 生成手段 | "vertex_ai_gemini" |
| `version` | string | ✓ | バージョン | "1.0" |

### activityStatsオブジェクト構造

```typescript
interface ActivityStats {
  total_messages: number;           // 総メッセージ数
  active_users_count: number;       // アクティブユーザー数
  active_channels_count: number;    // アクティブチャンネル数
  events_count: number;             // イベント数
  top_users: Array<[string, number]>; // [ユーザー名, メッセージ数]
  popular_keywords: Array<[string, number]>; // [キーワード, 回数]
  top_channels: string[];           // アクティブチャンネル名
}

// TypeScriptインターフェース
interface WeeklyAdvice {
  adviceId: string;
  weekOf: string;
  weekStart: Date;
  weekEnd: Date;
  content: string;
  activityStats: ActivityStats;
  createdAt: Date;
  isActive: boolean;
  guildId?: string;
  generatedBy: string;
  version: string;
}
```

### 主な用途
- WebダッシュボードでのAIアドバイス表示
- コミュニティ運営の改善方向性提供
- 週次レポートとしての活用
- AIによる自動化された運営サポート
- ユーザー設定による表示/非表示制御

## 6. Bot_Actions Collection

### 概要
Discord Botが実行したすべてのアクション（自然会話、コマンド処理、週次アドバイス生成など）の履歴を記録。Botの効果測定やデバッグに利用。

### フィールド詳細

| フィールド名 | 型 | 必須 | 説明 | 例 |
|-------------|---|------|------|---|
| `id` | string | ✓ | アクションID | "bot_action_20241220_001" |
| `actionType` | string | ✓ | アクションの種類 | "conversation", "admin_command", "natural_conversation" |
| `userId` | string | ✓ | 対象ユーザーID | "123456789012345678" |
| `guildId` | string | | サーバーID | "987654321098765432" |
| `targetId` | string | | 対象ID（チャンネル、メッセージ等） | "1234567890123456789" |
| `payload` | object | ✓ | アクション詳細データ | 下記参照 |
| `timestamp` | timestamp | ✓ | 実行日時 | Firestore Timestamp |
| `status` | string | ✓ | 実行状態 | "completed", "pending", "failed" |
| `result` | object | | 実行結果 | 下記参照 |
| `botCharacter` | string | ✓ | ボットキャラクター | "entertainment_bot", "miya", "eve" |
| `version` | string | ✓ | バージョン | "1.0.0" |

### actionTypeとpayload構造

| actionType | 説明 | payload例 |
|------------|------|----------|
| `conversation` | メンション応答 | `{content: "...", response_type: "natural_conversation"}` |
| `natural_conversation` | 自然会話 | `{content: "...", response_type: "casual"}` |
| `admin_command` | 管理者コマンド | `{command: "analytics", options: ["--limit=20"]}` |
| `weekly_advice_generation` | 週次アドバイス生成 | `{weekOf: "2024-12-16", stats: {...}}` |
| `podcast_generation` | ポッドキャスト生成 | `{days: 7, success: true}` |

### resultオブジェクト構造

```typescript
interface BotActionResult {
  userResponse?: 'positive' | 'negative' | 'neutral';
  engagementGenerated?: boolean;
  errorCode?: string;
  errorMessage?: string;
  responseTime?: number;  // ミリ秒
  aiTokensUsed?: number;
  [key: string]: any;  // その他の結果データ
}

// TypeScriptインターフェース
interface BotAction {
  id?: string;
  actionType: string;
  userId: string;
  guildId?: string;
  targetId?: string;
  payload: Record<string, any>;
  timestamp: Date;
  status: 'completed' | 'pending' | 'failed';
  result?: BotActionResult;
  botCharacter: string;
  version: string;
}
```

### 主な用途
- Botの効果測定とパフォーマンス分析
- ユーザーとのBotインタラクション追跡
- エラー分析とデバッグ
- AIレスポンス品質の改善
- 管理者コマンド使用状況の監視
- Botアクション履歴の監視とレポート

## 7. Events Collection

### 概要
サーバー内で開催されるイベント情報を管理。もくもく会、勉強会、ゲーム大会などのイベント詳細と参加者情報を格納。

### フィールド詳細

| フィールド名 | 型 | 必須 | 説明 | 例 |
|-------------|---|------|------|---|
| `id` | string | ✓ | イベントID | "event_mokumoku_001" |
| `guildId` | string | ✓ | サーバーID | "987654321098765432" |
| `title` | string | ✓ | イベントタイトル | "週末もくもく会" |
| `description` | string | ✓ | 説明 | "みんなで集まって各自の作業を進めましょう！" |
| `startTime` | string | ✓ | 開始日時 | "2024-05-25T13:00:00Z" |
| `endTime` | string | ✓ | 終了日時 | "2024-05-25T17:00:00Z" |
| `channelId` | string | ✓ | 開催チャンネル | "voice_mokumoku_room" |
| `attendees` | array | | 参加者UserIDリスト | ["123456789012345678", "234567890123456789"] |
| `createdBy` | string | ✓ | 作成者UserID | "111222333444555666" |
| `metadata` | object | | イベントメタデータ | 下記参照 |

### metadata の構造

```typescript
{
  eventType: string,           // イベントタイプ
  difficulty: string,          // 難易度
  requirements: string[],      // 参加要件
  materials: string[],         // 必要な資料・ツール
  tags: string[],             // タグ
  maxParticipants?: number,   // 最大参加者数
  isRecurring: boolean,       // 定期開催かどうか
  recurringPattern?: string   // 定期パターン（Cron形式）
}
```

### イベントタイプ

| eventType | 説明 | 典型的な duration |
|-----------|------|------------------|
| `mokumoku` | もくもく会 | 2-4時間 |
| `study_session` | 勉強会 | 1-2時間 |
| `workshop` | ワークショップ | 2-3時間 |
| `game_session` | ゲーム大会 | 1-3時間 |
| `networking` | 交流会 | 1-2時間 |
| `presentation` | 発表会 | 1-2時間 |

### 主な用途
- イベント管理
- 参加者追跡
- イベント効果測定
- コミュニティ活性化

## 8. Analytics Sessions Collection

### 概要
日次のコミュニティ活動統計データ。エンゲージメント分析やトレンド把握のためのサマリーデータ。

### フィールド詳細

| フィールド名 | 型 | 必須 | 説明 | 例 |
|-------------|---|------|------|---|
| `id` | string | ✓ | セッションID（日付ベース） | "analytics_20240524" |
| `guildId` | string | ✓ | サーバーID | "987654321098765432" |
| `date` | string | ✓ | 対象日（YYYY-MM-DD） | "2024-05-24" |
| `activeUsers` | number | ✓ | アクティブユーザー数 | 34 |
| `messageCount` | number | ✓ | 総メッセージ数 | 127 |
| `newMembers` | number | ✓ | 新規参加者数 | 2 |
| `reengagements` | number | ✓ | 再エンゲージメント成功数 | 1 |
| `topTopics` | object | ✓ | トピック別メンション数 | `{"React": 28, "デザイン": 15}` |
| `channelActivity` | object | ✓ | チャンネル別活動数 | `{"general": 45, "tech-talk": 38}` |

### 分析期間バリエーション

```typescript
// 週次サマリー
interface WeeklyAnalytics {
  id: string;              // "weekly_2024_W21"
  weekStart: string;       // "2024-05-20"
  weekEnd: string;         // "2024-05-26"
  // ... 他のフィールドは日次と同様
}

// 月次サマリー
interface MonthlyAnalytics {
  id: string;              // "monthly_2024_05"
  month: string;           // "2024-05"
  // ... 他のフィールドは日次と同様
}
```

### 主な用途
- ダッシュボード表示
- 長期トレンド分析
- パフォーマンス測定
- レポート生成

## 9. Bot Actions Collection

### 概要
ボットが実行したアクション（メッセージ送信、推薦、通知など）の履歴とその結果を記録。

### フィールド詳細

| フィールド名 | 型 | 必須 | 説明 | 例 |
|-------------|---|------|------|---|
| `id` | string | ✓ | アクションID | "bot_action_456" |
| `guildId` | string | ✓ | サーバーID | "987654321098765432" |
| `userId` | string | ✓ | 対象ユーザーID | "123456789012345678" |
| `actionType` | string | ✓ | アクションタイプ | "topic_recommendation", "reengagement_dm" |
| `targetId` | string | | 対象ID（チャンネル、メッセージなど） | null |
| `payload` | object | ✓ | アクション詳細データ | 下記参照 |
| `timestamp` | string | ✓ | 実行日時 | "2024-05-24T10:00:00Z" |
| `status` | string | ✓ | 実行状態 | "completed", "pending", "failed" |
| `result` | object | | 実行結果 | 下記参照 |

### アクションタイプと payload 構造

```typescript
// topic_recommendation
{
  character: "kuro_nyan",
  recommendedTopics: string[],
  confidence: number,
  baseInterests: string[]
}

// reengagement_dm
{
  character: "tra_nyan",
  message: string,
  reengagementAttempt: number,
  personalizedContent: string[]
}

// user_matching
{
  character: "kuro_nyan",
  matchedUserId: string,
  commonInterests: string[],
  matchScore: number
}

// welcome_message
{
  character: "tra_nyan",
  welcomeMessage: string,
  includedFeatures: string[]
}
```

### 実行状態と結果

| status | 説明 | result の内容例 |
|--------|------|----------------|
| `completed` | 正常完了 | `{userResponse: "positive", engagementGenerated: true}` |
| `pending` | 実行中または応答待ち | `{deliveryConfirmed: true, responseReceived: false}` |
| `failed` | 実行失敗 | `{errorCode: "CHANNEL_NOT_FOUND", errorMessage: "..."}` |
| `expired` | タイムアウト | `{timeoutReason: "no_user_response", waitTime: 86400}` |

### 主な用途
- ボット効果測定
- アクション履歴追跡
- 失敗分析
- パフォーマンス最適化

## 10. Admin Users Collection

### 概要
ボット管理権限を持つユーザーの情報と権限設定を管理。Firebase Authenticationと連携。

### フィールド詳細

| フィールド名 | 型 | 必須 | 説明 | 例 |
|-------------|---|------|------|---|
| `uid` | string | ✓ | Firebase Auth UID | "firebase_uid_abc123" |
| `guildIds` | array | ✓ | 管理可能なサーバーIDリスト | ["987654321098765432"] |
| `email` | string | ✓ | メールアドレス | "admin@techcommunity.jp" |
| `role` | string | ✓ | 管理者ロール | "super_admin", "moderator", "viewer" |
| `createdAt` | string | ✓ | アカウント作成日時 | "2023-12-01T00:00:00Z" |
| `lastLogin` | string | ✓ | 最終ログイン日時 | "2024-05-24T08:30:00Z" |
| `permissions` | object | ✓ | 権限設定 | 下記参照 |

### 権限設定（permissions）

```typescript
{
  canEditBotSettings: boolean,    // ボット設定編集
  canViewAnalytics: boolean,      // 分析データ閲覧
  canManageUsers: boolean,        // ユーザー管理
  canExportData: boolean,         // データエクスポート
  canDeleteData: boolean,         // データ削除
  canManageAdmins: boolean,       // 管理者管理
  canAccessLogs: boolean          // ログアクセス
}
```

### 管理者ロール

| role | 説明 | 典型的な権限 |
|------|------|-------------|
| `super_admin` | 最高管理者 | すべての権限 |
| `admin` | 管理者 | データ削除以外のすべて |
| `moderator` | モデレーター | 設定編集、分析閲覧 |
| `viewer` | 閲覧者 | 分析データ閲覧のみ |

### 主な用途
- 管理画面アクセス制御
- 権限ベースの機能制限
- 監査ログ
- セキュリティ管理

---

## データ関連性とクエリパターン

### よく使用されるクエリ例

```typescript
// 1. アクティブユーザーの取得
db.collection('users')
  .where('guildId', '==', guildId)
  .where('isActive', '==', true)
  .orderBy('lastActivity', 'desc')

// 2. 非アクティブユーザーの検出
db.collection('users')
  .where('guildId', '==', guildId)
  .where('isActive', '==', false)
  .where('lastActivity', '<', cutoffDate)

// 3. トピック別の最近の活動
db.collection('interactions')
  .where('guildId', '==', guildId)
  .where('keywords', 'array-contains', 'React')
  .orderBy('timestamp', 'desc')

// 4. ユーザーマッチング候補の検索
db.collection('users')
  .where('guildId', '==', guildId)
  .where('interests', 'array-contains-any', userInterests)
```

これらのテーブル設計により、効率的なデータ管理と高速なクエリ実行が可能になり、にゃんこエージェントの機能を適切にサポートできます。