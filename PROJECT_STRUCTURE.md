# CommuPro Guild プロジェクト構造

Discord エンタテインメントコンテンツ制作アプリケーションのプロジェクト構造と各ファイルの役割。

## プロジェクト概要

このシステムは、Discordコミュニティの活動を自動的に分析し、AIキャラクターによる対話形式の週次まとめを生成、音声化してGoogle Driveに保存し、Discordに自動投稿する統合システムです。

## ディレクトリ構造

```
.
├── CLAUDE.md                    # Claude AI用のプロジェクト固有の指示とガイドライン
├── README.md                    # プロジェクトの概要とセットアップ手順
├── bot/                         # Pythonベースのメインボット実装
│   ├── config/                  # 設定ファイル群
│   │   ├── docker/              # Docker関連の設定
│   │   │   ├── Dockerfile       # 開発環境用Dockerfile
│   │   │   ├── Dockerfile.single # 単一ボット用Dockerfile
│   │   │   ├── cloudbuild.gcp-compose.yaml # GCP Cloud Build（Compose版）
│   │   │   ├── cloudbuild.yaml  # GCP Cloud Build設定
│   │   │   ├── docker-compose.gcp.yml # GCP用Docker Compose
│   │   │   └── docker-compose.yml # ローカル開発用Docker Compose
│   │   └── nginx.conf           # Nginx設定（ヘルスチェック用）
│   ├── docs/                    # ドキュメント
│   │   ├── DEPLOYMENT.md        # デプロイ手順
│   │   ├── DISCORD_BOT.md       # Discord Bot設定ガイド
│   │   ├── ENTERTAINMENT_APP.md # エンタメアプリ詳細仕様
│   │   ├── ONBOARDING.md        # オンボーディングBot仕様
│   │   ├── PODCAST.md           # ポッドキャスト機能仕様
│   │   ├── README.md            # ドキュメント一覧
│   │   ├── UPLOAD.md            # データアップロード手順
│   │   └── VERTEX_AI_MIGRATION.md # Vertex AI移行ガイド
│   ├── env_example.txt          # 環境変数のサンプル
│   ├── nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json # Firebase認証情報
│   ├── pytest.ini               # pytest設定
│   ├── requirements.txt         # Python依存関係
│   ├── run_bot.py               # 従来のマルチボット起動スクリプト（レガシー）
│   ├── run_entertainment_bot.py # エンタメBot専用起動スクリプト（推奨）
│   ├── run_single_bot.py        # 単一ボット起動スクリプト
│   ├── src/                     # ソースコード
│   │   ├── core/                # コア機能
│   │   │   ├── bot.py           # 基本的なDiscord Bot実装（レガシー）
│   │   │   ├── content_creator.py # コンテンツ制作のワークフロー管理
│   │   │   ├── discord_analytics.py # Discord活動の分析機能
│   │   │   ├── entertainment_bot.py # エンタメBot本体（全機能統合）
│   │   │   ├── manager.py       # ボット管理機能（レガシー）
│   │   │   ├── podcast.py       # AIキャラクター対話とTTS機能
│   │   │   └── scheduler.py     # スケジュール管理とジョブ実行
│   │   ├── scripts/             # ユーティリティスクリプト
│   │   │   ├── clear_data.py    # データクリアスクリプト
│   │   │   ├── deploy.py        # デプロイスクリプト
│   │   │   ├── deploy_gcp.py    # GCPデプロイスクリプト
│   │   │   ├── deploy_separate.py # 個別デプロイスクリプト
│   │   │   ├── start_bots.py    # ボット起動スクリプト
│   │   │   └── upload_data.py   # データアップロードスクリプト
│   │   └── utils/               # ユーティリティ
│   │       ├── firestore.py     # Firestore操作ユーティリティ
│   │       ├── health.py        # ヘルスチェック機能
│   │       ├── health_server.py # ヘルスチェックサーバー
│   │       ├── onbording-bot.py # オンボーディングBot
│   │       ├── tutorial_content.py # チュートリアルコンテンツ
│   │       └── voice.py         # 音声合成ユーティリティ
│   ├── test_output/             # テスト出力ディレクトリ
│   ├── test_startup.py          # 起動テスト
│   └── tests/                   # テストコード
│       ├── conftest.py          # pytest設定
│       ├── output/              # テスト出力
│       ├── test_all.py          # 統合テスト
│       ├── test_data.py         # データ関連テスト
│       ├── test_simple.py       # 単体テスト
│       └── test_voice.py        # 音声機能テスト
├── checklist.md                 # 開発チェックリスト
├── data_structure.md            # データ構造の説明
├── dist/                        # TypeScriptビルド出力（JavaScript）
│   ├── config/                  # 設定モジュール
│   │   └── firebase.js          # Firebase設定
│   ├── handlers/                # イベントハンドラー
│   │   └── welcome.js           # ウェルカムメッセージ処理
│   ├── index.js                 # メインエントリーポイント
│   ├── models/                  # データモデル
│   │   └── user.js              # ユーザーモデル
│   └── services/                # サービス層
│       ├── discord/             # Discord関連サービス
│       │   └── bot.js           # Discord Bot接続
│       └── firebase/            # Firebase関連サービス
│           └── database.js      # データベース操作
├── docs/                        # プロジェクトドキュメント
│   ├── CI_CD_SETUP.md           # CI/CDセットアップガイド
│   ├── DATA_STRUCTURE.md        # データ構造詳細
│   └── FIREBASE_CONFIG.md       # Firebase設定ガイド
├── firebase-debug.log           # Firebaseデバッグログ
├── firebase.json                # Firebase設定ファイル
├── functions/                   # Firebase Cloud Functions
│   ├── lib/                     # ビルド出力
│   │   ├── discord-analytics.js # Discord分析機能
│   │   ├── discord-analytics.js.map
│   │   ├── index.js             # Functions エントリーポイント
│   │   └── index.js.map
│   ├── package-lock.json        # 依存関係ロックファイル
│   ├── package.json             # Functions依存関係
│   ├── src/                     # TypeScriptソース
│   │   ├── discord-analytics.ts # Discord分析実装
│   │   └── index.ts             # Functionsメイン
│   └── tsconfig.json            # TypeScript設定
├── package-lock.json            # プロジェクト依存関係ロック
├── package.json                 # プロジェクト依存関係とスクリプト
├── public/                      # 公開ディレクトリ
│   ├── 404.html                 # 404エラーページ
│   ├── data/                    # データディレクトリ
│   │   └── tmp/                 # 一時データ（テスト用）
│   │       ├── admin_users.json # 管理者ユーザーデータ
│   │       ├── analytics_sessions.json # 分析セッションデータ
│   │       ├── bot_actions.json # ボットアクションログ
│   │       ├── events.json      # イベントデータ
│   │       ├── guilds.json      # ギルド（サーバー）データ
│   │       ├── interactions.json # インタラクションデータ
│   │       ├── podcasts.json    # ポッドキャストデータ
│   │       ├── topics.json      # トピックデータ
│   │       ├── user_matches.json # ユーザーマッチングデータ
│   │       └── users.json       # ユーザーデータ
│   └── index.html               # Webインターフェースのエントリーポイント
├── src/                         # TypeScriptソースコード（メイン）
│   ├── config/                  # 設定モジュール
│   │   └── firebase.ts          # Firebase初期化
│   ├── handlers/                # イベントハンドラー
│   │   └── welcome.ts           # ウェルカムメッセージ実装
│   ├── index.ts                 # アプリケーションエントリーポイント
│   ├── models/                  # データモデル定義
│   │   └── user.ts              # ユーザーモデル定義
│   └── services/                # サービス層実装
│       ├── discord/             # Discord関連
│       │   └── bot.ts           # Discord Bot初期化
│       └── firebase/            # Firebase関連
│           └── database.ts      # Firestoreデータベース操作
├── system_structure.md          # システム構造の説明
├── tsconfig.base.json           # TypeScript基本設定
└── tsconfig.json                # TypeScriptプロジェクト設定
```

## 主要コンポーネント

### 1. Python側（bot/ディレクトリ）
- **エンタメBot本体**: Discord活動の分析、週次まとめ生成、音声合成を統合
- **Vertex AI (Gemini)**: コンテンツ生成AI
- **Google Cloud Text-to-Speech**: 音声合成
- **Google Drive API**: コンテンツ保存
- **Discord.py**: Discord Bot実装

### 2. TypeScript側（src/, functions/ディレクトリ）
- **Firebase Functions**: サーバーレスバックエンド
- **Firestore**: NoSQLデータベース
- **Webダッシュボード**: 管理画面（未実装）

### 3. インフラストラクチャ
- **Docker**: コンテナ化
- **Google Cloud Platform**: ホスティング環境
- **GitHub Actions**: CI/CDパイプライン

## 主要機能

1. **週次まとめ生成**
   - Discord活動の自動収集と分析
   - AI（Gemini）による要約テキスト生成
   - キャラクター対話形式でのコンテンツ制作

2. **音声合成**
   - Google Cloud Text-to-Speechによる高品質音声生成
   - 複数キャラクターの音声対応

3. **自動投稿**
   - Google Driveへのファイル保存
   - Discordチャンネルへの自動投稿
   - スケジュール実行（毎週日曜10:00）

4. **データ管理**
   - Firestoreによるデータ永続化
   - ユーザー、イベント、インタラクションの追跡

## 開発ワークフロー

1. ローカル開発: `docker-compose up`
2. テスト実行: `pytest`
3. デプロイ: GitHub ActionsによるCI/CD

## 注意事項

- Firebase認証情報（.json）はGitにコミットしないこと
- 環境変数は`.env`ファイルで管理
- Python側とTypeScript側は独立して動作可能