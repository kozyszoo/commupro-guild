
## 🤖 Discordボット1：ログ取得bot

### 開発要件
- [ ] **Docker コンテナ作成**
  - [ ] Python 実行環境構築
  - [ ] Discord.py ライブラリ導入
  - [ ] Firebase Admin SDK 導入
  - [ ] Dockerfile 作成

- [ ] **Discord API 連携**
  - [ ] Discord Bot 作成・トークン取得
  - [ ] 必要な権限設定（メッセージ読み取り、チャンネル参加）
  - [ ] Discord Gateway 接続実装

- [ ] **ログ取得機能**
  - [ ] メッセージ受信リスナー実装
  - [ ] メッセージデータ正規化（JSON形式）
  - [ ] ユーザー情報・チャンネル情報取得
  - [ ] 添付ファイル・リアクション情報取得

- [ ] **Firestore データ保存**
  - [ ] メッセージコレクション設計
  - [ ] ユーザーコレクション設計
  - [ ] チャンネルコレクション設計
  - [ ] データ重複防止機能
  - [ ] インデックス最適化

- [ ] **Cloud Run デプロイ**
  - [ ] Cloud Run サービス設定
  - [ ] 環境変数設定（Discord Token等）
  - [ ] 自動スケーリング設定
  - [ ] ヘルスチェック実装

---

## 🎧 Discordボット2：接客bot

### 開発要件
- [ ] **Docker コンテナ作成**
  - [ ] Python 実行環境構築
  - [ ] Discord.py + Vertex AI SDK 導入
  - [ ] Dockerfile 作成

- [ ] **Vertex AI (Gemini) 連携**
  - [ ] Gemini API 認証設定
  - [ ] プロンプトテンプレート設計
  - [ ] レスポンス生成機能実装

- [ ] **応答機能**
  - [ ] メンション検知機能
  - [ ] 質問内容解析
  - [ ] Discordルール取得（Firestore）
  - [ ] Gemini による回答生成
  - [ ] Discord メッセージ返信

- [ ] **ルール管理**
  - [ ] ルールチャンネル監視
  - [ ] ルール情報 Firestore 保存
  - [ ] ルール更新検知・同期

- [ ] **Cloud Run デプロイ**
  - [ ] サービス設定・環境変数
  - [ ] Vertex AI API アクセス権限

---

## 🎉 Discordボット3：盛り上げbot

### 開発要件
- [ ] **Docker コンテナ作成**
  - [ ] Python 実行環境構築
  - [ ] 必要ライブラリ導入
  - [ ] Dockerfile 作成

- [ ] **リアクション生成機能**
  - [ ] メッセージ監視・フィルタリング
  - [ ] 過去ログ取得（Firestore）
  - [ ] Gemini による盛り上げコンテンツ生成
  - [ ] 適切なタイミングでのリアクション

- [ ] **エンタメコンテンツ投稿**
  - [ ] 週次まとめ投稿機能
  - [ ] Google Drive 連携（音声・テキスト取得）
  - [ ] Discord 投稿フォーマット最適化

- [ ] **Cloud Run デプロイ**
  - [ ] サービス設定・スケジューリング
  - [ ] Google Drive API アクセス権限

---

## 📊 ログ閲覧Web画面

### フロントエンド開発
- [ ] **React アプリケーション構築**
  - [ ] Create React App / Next.js セットアップ
  - [ ] Firebase SDK 導入
  - [ ] UI コンポーネントライブラリ導入（Material-UI等）

- [ ] **認証機能**
  - [ ] Firebase Authentication 連携
  - [ ] ログイン・ログアウト機能
  - [ ] 権限管理（管理者のみアクセス）

- [ ] **ダッシュボード機能**
  - [ ] メッセージ一覧表示
  - [ ] 投稿数ランキング表示
  - [ ] チャンネル別統計
  - [ ] ユーザー別活動状況

- [ ] **アドバイス機能**
  - [ ] Vertex AI による分析結果表示
  - [ ] 不適切ワード検知アラート
  - [ ] メンバー対立検知
  - [ ] リアクション・返信忘れ通知

### バックエンド API
- [ ] **Firebase Functions 実装**
  - [ ] Firestore データ集計 API
  - [ ] Vertex AI 分析結果取得 API
  - [ ] 統計データ生成 API

### デプロイ
- [ ] **Firebase Hosting**
  - [ ] ビルド設定・自動デプロイ
  - [ ] カスタムドメイン設定（必要に応じて）

---

## 🎬 エンタメコンテンツ制作アプリ

### 開発要件
- [ ] **週次まとめ生成機能**
  - [ ] Cloud Functions スケジューラー設定
  - [ ] 週次ログデータ集計
  - [ ] Gemini による まとめテキスト生成
  - [ ] Discord Bot 間の対話シミュレーション

- [ ] **音声生成機能**
  - [ ] Text-to-Speech API 連携
  - [ ] 音声品質設定・最適化
  - [ ] 音声ファイル生成

- [ ] **Google Drive 連携**
  - [ ] Drive API 認証設定
  - [ ] テキスト・音声ファイルアップロード
  - [ ] フォルダ構造・命名規則設定

- [ ] **スケジューリング**
  - [ ] Cloud Scheduler 設定
  - [ ] 週次実行タイミング調整
  - [ ] エラーハンドリング・リトライ機能
