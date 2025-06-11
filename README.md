# Discord エンタメコンテンツ制作アプリ

Discord内のアクションに対するまとめ情報生成、週次コンテンツ自動制作システムです。3匹のキャラクター（みやにゃん・イヴにゃん・ナレにゃん）によるAI対話形式のエンタメコンテンツを自動生成し、テキスト・音声ファイルをGoogle Driveに保存してDiscordに投稿する統合システムです。

[![CI/CD Pipeline](https://github.com/kozyszoo/commupro-guild/actions/workflows/ci.yml/badge.svg)](https://github.com/kozyszoo/commupro-guild/actions/workflows/ci.yml)

## 🎯 主要機能

### 1. Discord アクティビティ分析
- Discord内のメッセージ、リアクション、イベントを自動収集
- ユーザー活動、チャンネル活動、キーワード分析
- 週次・月次統計レポート生成

### 2. AI による週次まとめ生成
- **Vertex AI (Gemini)** を使用した高品質なまとめテキスト生成
- **Bot同士の対話形式**でのエンタメコンテンツ作成
- 3つのキャラクター（みやにゃん、イヴにゃん、ナレにゃん）による自然な会話

### 3. Text-to-Speech 音声生成
- **Google Cloud Text-to-Speech** による高品質音声合成
- キャラクター別音声設定（感情、話速、音調）
- SSML対応による自然な音声表現

### 4. Google Drive 自動保存
- 生成されたテキストファイルと音声ファイルを自動でGoogle Driveに保存
- 共有リンク自動生成
- フォルダ管理とアクセス権限設定

### 5. Discord 自動投稿
- 指定チャンネルへの週次まとめ自動投稿
- 埋め込み形式での美しい投稿レイアウト
- Google Driveリンク付き投稿

### 6. 週次スケジューラー
- 指定曜日・時刻での自動実行
- 手動実行コマンド対応
- 実行ログとエラー監視

## 🚀 セットアップ手順

### 1. 必要な依存関係をインストール

#### Python依存関係（Discord Bot）
```bash
cd bot
pip install -r requirements.txt
```

#### Node.js依存関係（Firebase Functions）
```bash
npm install
```

### 2. 環境変数の設定

`bot/env_example.txt` をコピーして `bot/.env` を作成し、必要な値を設定：

```bash
cd bot
cp env_example.txt .env
```

### 3. 必要なAPI設定

#### Discord Bot
1. [Discord Developer Portal](https://discord.com/developers/applications) でアプリケーション作成
2. Bot トークンを取得
3. 必要な権限を設定：
   - Send Messages
   - Read Message History
   - Embed Links
   - Attach Files

#### Firebase / Firestore
1. [Firebase Console](https://console.firebase.google.com/) でプロジェクト作成
2. Firestoreデータベースを有効化
3. サービスアカウントキーを生成・ダウンロード

#### Google Cloud APIs
1. 以下のAPIを有効化：
   - Vertex AI API
   - Text-to-Speech API
   - Drive API
2. サービスアカウントに必要な権限を付与

#### Google Drive
1. 保存先フォルダを作成
2. フォルダIDを取得（URLの最後の部分）
3. サービスアカウントにフォルダの編集権限を付与

### 4. 実行

#### エンタメコンテンツ制作Bot
```bash
cd bot
python run_entertainment_bot.py
```

#### Firebase Functions（従来システム）
```bash
npm run build
npm start
```

## 🎮 使用方法

### Bot コマンド

#### 基本コマンド
- `!help` - ヘルプメッセージ表示
- `!status` - システム状態確認

#### 管理者コマンド（設定された管理者ユーザーのみ）
- `!scheduler start` - スケジューラー開始
- `!scheduler stop` - スケジューラー停止
- `!scheduler status` - スケジューラー状態確認
- `!scheduler run` - 手動でコンテンツ生成実行
- `!summary [days]` - 手動で週次まとめ生成（デフォルト7日）
- `!analytics [days]` - アクティビティ分析表示
- `!podcast [days]` - ポッドキャスト生成

### 自動実行設定

`.env` ファイルで自動実行を設定：

```env
AUTO_START_SCHEDULER=true
WEEKLY_SCHEDULE_DAY=monday
WEEKLY_SCHEDULE_TIME=09:00
```

これにより、毎週月曜日の9:00に自動でコンテンツが生成・投稿されます。

## 🎭 キャラクター設定

### みやにゃん 🐈
- **性格**: フレンドリーで好奇心旺盛、新しい技術に興味津々
- **話し方**: だにゃ、にゃ〜、だよにゃ
- **役割**: コミュニティの盛り上げ役
- **音声**: 明るい女性の声、話速1.2倍、高めの音調

### イヴにゃん 🐱
- **性格**: クールで分析的、データや統計の解釈が得意
- **話し方**: ですにゃ、なのにゃ、ですね
- **役割**: データ分析とインサイト提供
- **音声**: 低めの男性の声、標準話速、落ち着いた音調

### ナレにゃん 📢
- **性格**: 司会進行が得意で、まとめるのが上手
- **話し方**: ですね、でしょう、ということで
- **役割**: まとめと進行役
- **音声**: 中性的な声、標準話速、中間音調

## 📊 データ構造

### Firestore コレクション

#### `interactions`
Discord内のメッセージや活動ログ

#### `weekly_summaries`
AI生成された週次まとめデータ

#### `content_records`
コンテンツ制作記録

#### `scheduler_logs`
スケジューラー実行ログ

## 🎬 動作確認結果

### ✅ 確認済み機能

1. **すべての依存関係のインストール**
2. **全モジュールのインポート**
3. **システム初期化**
   - Discord Analytics
   - Content Creator
   - Weekly Scheduler
   - Character Configuration

4. **AI プロンプト生成機能**
   - キャラクター設定
   - データ駆動型プロンプト
   - フォールバック機能

5. **統合システム機能**
   - Google APIs初期化
   - Firebase接続
   - スケジューラー設定

### 🧪 テスト実行

```bash
cd bot
python test_startup.py
```

### 従来機能（後方互換性）
- 新規参加者自動歓迎機能
- 過去の人気投稿・イベント案内機能
- 非アクティブユーザー再エンゲージメント機能
- ユーザーマッチング機能（同じ関心を持つメンバー紹介）

## 📁 プロジェクト構造

```
commupro-guild/
├── bot/                                  # Discord エンタメコンテンツ制作Bot
│   ├── src/
│   │   ├── core/
│   │   │   ├── discord_analytics.py    # Discord活動分析
│   │   │   ├── content_creator.py      # コンテンツ制作統合
│   │   │   ├── scheduler.py           # スケジューラー
│   │   │   ├── entertainment_bot.py   # メインBot実装
│   │   │   └── podcast.py            # 既存ポッドキャスト機能
│   │   └── utils/
│   │       ├── firestore.py          # Firestore接続
│   │       └── ...
│   ├── docs/
│   │   └── ENTERTAINMENT_APP.md       # 詳細ドキュメント
│   ├── run_entertainment_bot.py       # メイン実行スクリプト
│   ├── test_startup.py               # 起動テスト
│   ├── requirements.txt              # Python依存関係
│   └── env_example.txt              # 環境変数テンプレート
├── src/                              # Firebase Functions（従来システム）
├── functions/                        # Firebase Functions
├── public/                          # 静的ファイル（管理パネル）
├── dist/                           # ビルド済みファイル
└── docs/                          # プロジェクトドキュメント
```

## 📚 ドキュメント

### エンタメコンテンツ制作アプリ
- `bot/docs/ENTERTAINMENT_APP.md` - 詳細ドキュメント
- `bot/test_startup.py` - 起動テスト・動作確認

### 従来システム
- `system_structure.md` - システム構造の詳細
- `data_structure.md` - データ構造の詳細
- `checklist.md` - 開発チェックリスト

## 🚨 トラブルシューティング

### よくある問題

#### 1. Firebase接続エラー
- サービスアカウントキーのパスが正しいか確認
- Firestore APIが有効化されているか確認

#### 2. Vertex AI エラー
- Google Cloud プロジェクトIDが正しいか確認
- Vertex AI APIが有効化されているか確認
- サービスアカウントに必要な権限があるか確認

#### 3. Google Drive アップロードエラー
- Drive APIが有効化されているか確認
- フォルダIDが正しいか確認
- サービスアカウントにフォルダのアクセス権があるか確認

#### 4. Discord投稿エラー
- Bot トークンが有効か確認
- チャンネルIDが正しいか確認
- Botに必要な権限があるか確認

### ログ確認

実行ログを確認してエラーの詳細を調べてください：

```bash
cd bot
python run_entertainment_bot.py
```

## 🛠️ 開発環境

### エンタメコンテンツ制作Bot
- Python 3.9+
- Discord.py v2.3+
- Firebase Admin SDK v6.2+
- Google Cloud AI Platform
- Vertex AI (Gemini)
- Google Cloud Text-to-Speech
- Google Drive API

### 従来システム
- TypeScript
- Node.js 18+
- Firebase Functions v2
- Discord.js v14

## 📈 今後の拡張予定

- [ ] Webダッシュボード追加
- [ ] 複数サーバー対応
- [ ] カスタムテンプレート機能
- [ ] 音声ファイル統合機能（ffmpeg連携）
- [ ] 詳細な分析レポート
- [ ] ユーザー別統計
- [ ] イベント連動機能

## 📝 ライセンス

このプロジェクトは既存のpodcastアプリを拡張したDiscordエンタメコンテンツ制作システムです。