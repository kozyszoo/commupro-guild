# Discord にゃんこエージェント ボット

Discord上で動作するAIエージェント「にゃんこエージェント」のボットシステムです。
Firebase/Firestoreと連動して、ユーザーのインタラクションを記録・分析します。

## 🚀 クイックスタート

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. Discord Bot Tokenの設定

#### 2.1 Discord Developer Portalでボットを作成

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. 「New Application」をクリック
3. アプリケーション名を入力して「Create」
4. 左メニューの「Bot」を選択
5. 「Add Bot」をクリック
6. 「Reset Token」をクリックしてTokenを生成
7. Tokenをコピー

#### 2.2 Bot権限の設定

「Bot」ページで以下の設定を行います：

**Privileged Gateway Intents:**
- ✅ PRESENCE INTENT
- ✅ SERVER MEMBERS INTENT  
- ✅ MESSAGE CONTENT INTENT

**Bot Permissions:**
- ✅ Read Messages
- ✅ Send Messages
- ✅ Read Message History
- ✅ Add Reactions
- ✅ Use Slash Commands

#### 2.3 ボットをサーバーに招待

1. 左メニューの「OAuth2」→「URL Generator」を選択
2. **Scopes:** `bot` を選択
3. **Bot Permissions:** 必要な権限を選択
4. 生成されたURLでボットをサーバーに招待

### 3. 環境変数の設定

`.env`ファイルを作成して、必要な設定を行います：

```bash
# .envファイルを作成（env_example.txtをコピーして編集）
cp env_example.txt .env

# .envファイルを編集
# 複数ボット管理システム用（推奨）
DISCORD_BOT_TOKEN_MIYA=あなたのみやにゃん用Discord_Bot_Token
DISCORD_BOT_TOKEN_EVE=あなたのイヴにゃん用Discord_Bot_Token

# Firebase設定（どちらか一方を設定）
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=./nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json
# または
# FIREBASE_SERVICE_ACCOUNT={"type":"service_account",...}
```

> **💡 Firebase設定について**: `FIREBASE_SERVICE_ACCOUNT_KEY_PATH`（ファイルパス）と`FIREBASE_SERVICE_ACCOUNT`（JSON文字列）のどちらか一方を設定すれば十分です。ローカル開発では`FIREBASE_SERVICE_ACCOUNT_KEY_PATH`、Cloud環境では`FIREBASE_SERVICE_ACCOUNT`を推奨します。

### 4. Firebase設定の確認

Firebase設定が正しく行われているか確認：

```bash
# サービスアカウントキーファイルが存在するか確認
ls -la nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json
```

### 5. ボットの起動

```bash
# 複数ボット管理システム（推奨）
python3 run_bot.py

# レガシーボット（旧版）
python3 discord_bot.py
```

> **💡 ヒント**: `run_bot.py`が最新の複数ボット管理システムです。みやにゃんとイヴにゃんの2体を同時に管理し、新規参加者チュートリアル機能も含まれています。

## 📋 機能一覧

### 🎭 にゃんこエージェント機能

#### 🐈 みやにゃん（技術サポート）
- **新規参加者チュートリアル**: 6段階の詳細ガイド配信
- **技術サポート**: プログラミング・技術相談対応
- **コミュニティサポート**: サーバー利用方法の案内
- **エージェント秘書機能**: 親しみやすい対話形式でのサポート

#### 🐱 イヴにゃん（データ分析）
- **データ分析**: ユーザー行動・エンゲージメント分析
- **レポート作成**: 統計情報の可視化・報告
- **論理的サポート**: データに基づく問題解決支援

### 🎓 チュートリアルシステム
- **新規参加者自動検出**: サーバー参加時の自動ウェルカム
- **段階的ガイド**: 6つのステップでサーバー活用方法を習得
- **インタラクティブ進行**: 「次へ」「スキップ」「ヘルプ」コマンド
- **既存ユーザー対応**: いつでもチュートリアル再受講可能
- **DM配信**: プライベートな学習環境

### 🔍 インタラクション記録（レガシー機能）
- メッセージの送信・編集・削除
- リアクションの追加・削除
- メンバーの参加・退出
- スケジュールイベントの作成・更新・削除・参加

### 📊 データ分析（レガシー機能）
- ユーザーエンゲージメントスコア
- キーワード抽出
- トピック分析
- アクティビティ統計

### 🎵 音声・Podcast機能
- **AI音声生成**: VOICEVOXによるキャラクター音声
- **Podcast自動生成**: テキストから音声コンテンツ作成
- **キャラクター音声**: みやにゃん・イヴにゃんの個性的な声

### 🗄️ データ管理
- Firestore自動同期
- データエクスポート機能
- リアルタイム更新
- 一括データアップロード・クリア機能

## 🛠️ トラブルシューティング

### ボットが起動しない場合

1. **Discord Bot Tokenの確認**
   ```bash
   # .envファイルの内容を確認
   cat .env
   ```

2. **Firebase設定の確認**
   ```bash
   # サービスアカウントキーファイルの確認
   ls -la *.json
   ```

3. **依存関係の確認**
   ```bash
   # 必要なライブラリがインストールされているか確認
   pip list | grep discord
   pip list | grep firebase
   ```

### よくあるエラー

#### `❌ エラー: DISCORD_BOT_TOKEN が設定されていません`
- `.env`ファイルに正しいTokenが設定されているか確認
- Tokenに余分なスペースや改行が含まれていないか確認

#### `❌ エラー: Discord Bot Tokenが無効です`
- Discord Developer PortalでTokenを再生成
- 新しいTokenを`.env`ファイルに設定

#### `❌ エラー: Firebase Firestoreの初期化に失敗しました`
- サービスアカウントキーファイルのパスが正しいか確認
- ファイルの権限が適切に設定されているか確認

## 📁 ファイル構成

### 🎯 メインファイル

| ファイル名 | 説明 | 役割 |
|-----------|------|------|
| `run_bot.py` | **ボット起動スクリプト** | 複数ボット管理システムの起動、環境確認、Cloud Run対応 |
| `multi_bot_manager.py` | **複数ボット管理システム** | みやにゃん・イヴにゃんの管理、新規参加者チュートリアル機能 |
| `tutorial_content.py` | **チュートリアルコンテンツ管理** | 6段階の詳細なチュートリアル内容、運用者向けガイド |
| `discord_bot.py` | **レガシーボットロジック** | 旧版のDiscord.pyボット実装（Firestore連携機能付き） |

### 🎭 キャラクター機能

| ファイル名 | 説明 | 機能 |
|-----------|------|------|
| `multi_bot_manager.py` | **みやにゃん** | 技術サポート、新規参加者チュートリアル、コミュニティサポート |
| `multi_bot_manager.py` | **イヴにゃん** | データ分析、レポート作成、統計情報提供 |
| `onbording-bot.py` | **オンボーディングBot** | 新規参加者向けの動的挨拶生成（OpenAI連携） |

### 🎵 音声・Podcast機能

| ファイル名 | 説明 | 機能 |
|-----------|------|------|
| `make_podcast.py` | **Podcast生成システム** | VOICEVOXを使用したAI音声Podcast自動生成 |
| `test_voice_difference.py` | **音声テストスクリプト** | みやにゃん・イヴにゃんの音声設定テスト |
| `test_miya_voice.mp3` | **みやにゃん音声サンプル** | みやにゃんキャラクターの音声テスト用ファイル |
| `test_eve_voice.mp3` | **イヴにゃん音声サンプル** | イヴにゃんキャラクターの音声テスト用ファイル |

### 🔧 データ管理・ユーティリティ

| ファイル名 | 説明 | 機能 |
|-----------|------|------|
| `upload_firestore.py` | **Firestoreデータアップロード** | JSONデータのFirestore一括インポート |
| `clear_firestore_data.py` | **Firestoreデータクリア** | 開発・テスト用データクリア機能 |
| `test_data_retrieval.py` | **データ取得テスト** | Firestoreからのデータ取得動作確認 |
| `test_export_20250526_235736.json` | **テストデータ** | データ構造確認用のサンプルエクスポートファイル |

### ☁️ Cloud Run・デプロイ関連

| ファイル名 | 説明 | 機能 |
|-----------|------|------|
| `Dockerfile` | **Dockerコンテナ設定** | Cloud Run用のPythonコンテナ定義 |
| `cloudbuild.yaml` | **Cloud Build設定** | 自動ビルド・デプロイパイプライン設定 |
| `deploy.sh` | **デプロイスクリプト** | Cloud Runへの手動デプロイ自動化 |
| `health_server.py` | **ヘルスチェックサーバー** | Cloud Run用のHTTPヘルスチェック機能 |
| `env_vars.yaml` | **環境変数管理** | Cloud Run用の環境変数設定ファイル |
| `.dockerignore` | **Docker除外設定** | Dockerビルド時の除外ファイル指定 |

### 📚 設定・ドキュメント

| ファイル名 | 説明 | 内容 |
|-----------|------|------|
| `requirements.txt` | **Python依存関係** | 必要なライブラリとバージョン指定 |
| `env_example.txt` | **環境変数テンプレート** | .envファイル作成用のサンプル |
| `README.md` | **メインドキュメント** | このファイル（プロジェクト全体の説明） |
| `README_podcast.md` | **Podcast機能ドキュメント** | 音声生成機能の詳細説明 |
| `README_CLOUDRUN.md` | **Cloud Runドキュメント** | クラウドデプロイの詳細手順 |
| `README_discord_bot.md` | **Discordボットドキュメント** | レガシーボット機能の説明 |
| `README_upload.md` | **データアップロードガイド** | Firestoreデータ管理の説明 |

### 🔑 認証・設定ファイル

| ファイル名 | 説明 | 重要度 |
|-----------|------|---------|
| `nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json` | **Firebaseサービスアカウントキー** | 🔒 機密情報 |
| `.env` | **環境変数設定** | 🔒 Discord Token等を格納 |

### 📁 ディレクトリ構造

```
bot/
├── 🎯 メインシステム
│   ├── run_bot.py                    # 起動エントリーポイント
│   ├── multi_bot_manager.py          # 複数ボット管理（みやにゃん・イヴにゃん）
│   └── tutorial_content.py           # チュートリアルコンテンツ
├── 🎭 レガシー・特殊機能
│   ├── discord_bot.py               # 旧版ボット
│   └── onbording-bot.py             # オンボーディング機能
├── 🎵 音声・Podcast
│   ├── make_podcast.py              # Podcast生成
│   ├── test_voice_difference.py     # 音声テスト
│   ├── test_miya_voice.mp3          # みやにゃん音声
│   └── test_eve_voice.mp3           # イヴにゃん音声
├── 🔧 データ管理
│   ├── upload_firestore.py          # データアップロード
│   ├── clear_firestore_data.py      # データクリア
│   ├── test_data_retrieval.py       # データ取得テスト
│   └── test_export_*.json           # テストデータ
├── ☁️ Cloud Run・デプロイ
│   ├── Dockerfile                   # コンテナ定義
│   ├── cloudbuild.yaml             # ビルド設定
│   ├── deploy.sh                   # デプロイ自動化
│   ├── health_server.py            # ヘルスチェック
│   ├── env_vars.yaml               # 環境変数
│   └── .dockerignore               # Docker除外設定
├── 📚 設定・ドキュメント
│   ├── requirements.txt            # 依存関係
│   ├── env_example.txt             # 環境変数例
│   ├── README*.md                  # 各種ドキュメント
│   └── .env                       # 環境変数（要作成）
├── 🔑 認証ファイル
│   └── nyanco-bot-firebase-*.json  # Firebase認証
└── 📦 システムファイル
    └── __pycache__/                # Python キャッシュ
```

## 🔧 開発者向け情報

### コードの構成

- **`run_bot.py`**: 起動処理とエラーハンドリング
- **`discord_bot.py`**: Discord.pyを使用したボットロジック
- **Firebase連携**: Firestoreへのデータ保存・取得
- **非同期処理**: asyncio/awaitを使用した効率的な処理

### データベース構造

Firestoreコレクション：
- `users`: ユーザー情報
- `interactions`: インタラクション履歴
- `events`: スケジュールイベント
- `topics`: トピック分析結果
- `analytics_sessions`: 分析セッション

### 環境変数

| 変数名 | 説明 | 必須 | 対象システム |
|--------|------|------|-------------|
| `DISCORD_BOT_TOKEN` | Discord Bot Token（レガシー用） | - | レガシーボット |
| `DISCORD_BOT_TOKEN_MIYA` | みやにゃん用Discord Token | ✅ | 複数ボット管理 |
| `DISCORD_BOT_TOKEN_EVE` | イヴにゃん用Discord Token | ✅ | 複数ボット管理 |
| `FIREBASE_SERVICE_ACCOUNT_KEY_PATH` | Firebaseキーファイルパス | ✅ | 全システム |
| `FIREBASE_SERVICE_ACCOUNT` | Firebase設定JSON | - | 全システム |

> **🔑 重要**: 複数ボット管理システムでは、みやにゃんとイヴにゃん用に個別のDiscord Bot Tokenが必要です。

## 📞 サポート

問題が発生した場合は、以下の情報を含めてお問い合わせください：

1. エラーメッセージの全文
2. 実行環境（OS、Pythonバージョン）
3. 実行したコマンド
4. `.env`ファイルの設定（Tokenは除く）

## 📄 ライセンス

このプロジェクトは内部使用のためのものです。