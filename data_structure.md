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
- ボットの動作カスタマイズ
- キャラクター性格設定
- 機能のON/OFF制御
- チャンネル設定管理

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

## 4. Topics Collection

### 概要
コミュニティ内で話題になっているトピックを管理。人気度やトレンドスコアを算出し、コンテンツ推薦に利用。

### フィールド詳細

| フィールド名 | 型 | 必須 | 説明 | 例 |
|-------------|---|------|------|---|
| `id` | string | ✓ | トピックID | "topic_react_001" |
| `guildId` | string | ✓ | サーバーID | "987654321098765432" |
| `name` | string | ✓ | トピック名 | "React開発" |
| `keywords` | array | ✓ | 関連キーワード | ["React", "JavaScript", "hooks"] |
| `channelIds` | array | | 関連チャンネル | ["channel_tech_talk_789"] |
| `popularity` | number | ✓ | 人気度スコア（0-100） | 78.5 |
| `trendScore` | number | ✓ | トレンドスコア（0-100） | 85.2 |
| `createdAt` | string | ✓ | 作成日時 | "2024-01-10T00:00:00Z" |
| `updatedAt` | string | ✓ | 最終更新日時 | "2024-05-24T14:22:00Z" |
| `relatedTopics` | object | | 関連トピックとスコア | `{"topic_javascript_002": 0.8}` |

### スコア算出方法

```typescript
// 人気度スコアの計算例
popularity = (
  mentionCount * 0.4 +          // 言及回数
  uniqueUsersCount * 0.3 +      // 参加ユーザー数
  recentActivity * 0.3          // 最近の活動度
) / maxPossibleScore * 100;

// トレンドスコアの計算例
trendScore = (
  recentGrowthRate * 0.5 +      // 最近の成長率
  newUserEngagement * 0.3 +     // 新規ユーザーエンゲージメント
  crossChannelSpread * 0.2      // クロスチャンネル拡散度
) / maxPossibleScore * 100;
```

### 主な用途
- コンテンツ推薦
- ポッドキャストトピック選定
- ユーザーマッチング
- トレンド分析

## 5. Podcasts Collection

### 概要
にゃんこキャラクターによる定期配信ポッドキャストの内容と統計情報を保存。

### フィールド詳細

| フィールド名 | 型 | 必須 | 説明 | 例 |
|-------------|---|------|------|---|
| `id` | string | ✓ | ポッドキャストID | "podcast_20240520_001" |
| `guildId` | string | ✓ | サーバーID | "987654321098765432" |
| `title` | string | ✓ | タイトル | "今週のテックトーク - React 19の新機能" |
| `content` | string | ✓ | 内容（対話形式） | "🐈 トラにゃん: みなさん、こんにちは..." |
| `topics` | array | ✓ | 取り上げたトピックID | ["topic_react_001", "topic_design_002"] |
| `publishedAt` | string | ✓ | 公開日時 | "2024-05-20T18:00:00Z" |
| `channelId` | string | ✓ | 公開チャンネル | "channel_podcast_456" |
| `views` | number | | 閲覧数 | 45 |
| `reactions` | array | | リアクション統計 | 下記参照 |
| `metadata` | object | | 生成メタデータ | 下記参照 |

### reactions 配列の構造

```typescript
[
  {
    emoji: string,    // 絵文字
    count: number     // 数
  }
]
```

### metadata オブジェクトの構造

```typescript
{
  generationTime: string,           // 生成日時
  weeklyDataRange: {
    start: string,                  // 対象期間開始
    end: string                     // 対象期間終了
  },
  topContributors: string[],        // 主要貢献者
  dataSourcesUsed: string[]         // 使用データソース
}
```

### 主な用途
- 定期的なコミュニティ情報配信
- エンゲージメント向上
- コミュニティ活動の可視化
- コンテンツ効果測定

## 6. User Matches Collection

### 概要
ユーザー同士のマッチング情報を管理。共通の関心事を持つユーザーの組み合わせとマッチング状況を追跡。

### フィールド詳細

| フィールド名 | 型 | 必須 | 説明 | 例 |
|-------------|---|------|------|---|
| `id` | string | ✓ | マッチID | "match_001" |
| `guildId` | string | ✓ | サーバーID | "987654321098765432" |
| `user1Id` | string | ✓ | ユーザー1のID | "123456789012345678" |
| `user2Id` | string | ✓ | ユーザー2のID | "345678901234567890" |
| `commonInterests` | array | ✓ | 共通の関心事 | ["React", "JavaScript", "Web開発"] |
| `matchScore` | number | ✓ | マッチングスコア（0-1） | 0.85 |
| `status` | string | ✓ | マッチング状態 | "suggested", "active", "declined", "expired" |
| `createdAt` | string | ✓ | 作成日時 | "2024-05-24T09:30:00Z" |
| `lastInteraction` | string | | 最終相互作用日時 | "2024-05-22T11:20:00Z" |
| `isIntroduced` | boolean | ✓ | 紹介済みフラグ | false |

### マッチング状態

| status | 説明 | 次のアクション |
|--------|------|---------------|
| `suggested` | マッチングが提案された | ボットが紹介メッセージを送信 |
| `active` | 両者が交流している | 定期的な関係性チェック |
| `declined` | どちらかが拒否 | マッチング終了 |
| `expired` | 一定期間反応なし | アーカイブまたは削除 |
| `successful` | 活発な交流が続いている | 成功事例として記録 |

### マッチングスコア算出

```typescript
matchScore = (
  commonInterestsWeight * 0.4 +     // 共通関心事の重み
  activityLevelSimilarity * 0.2 +   // 活動レベルの類似度
  channelOverlap * 0.2 +            // チャンネル重複度
  timezoneCompatibility * 0.1 +     // タイムゾーン互換性
  personalityMatch * 0.1            // 性格マッチ度
);
```

### 主な用途
- ユーザー同士の紹介
- コミュニティ内のネットワーク形成
- マッチング効果測定
- 孤立ユーザーの発見

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