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

`.env`ファイルを編集して、Discord Bot Tokenを設定：

```bash
# .envファイルを編集
DISCORD_BOT_TOKEN=あなたのDiscord_Bot_Token
```

### 4. Firebase設定の確認

Firebase設定が正しく行われているか確認：

```bash
# サービスアカウントキーファイルが存在するか確認
ls -la nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json
```

### 5. ボットの起動

```bash
python3 run_bot.py
```

## 📋 機能一覧

### 🔍 インタラクション記録
- メッセージの送信・編集・削除
- リアクションの追加・削除
- メンバーの参加・退出
- スケジュールイベントの作成・更新・削除・参加

### 📊 データ分析
- ユーザーエンゲージメントスコア
- キーワード抽出
- トピック分析
- アクティビティ統計

### 🗄️ データ管理
- Firestore自動同期
- データエクスポート機能
- リアルタイム更新

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

```
bot/
├── run_bot.py              # ボット起動スクリプト
├── discord_bot.py          # メインボットロジック
├── requirements.txt        # Python依存関係
├── .env                   # 環境変数設定
├── env_example.txt        # 環境変数設定例
├── README.md              # このファイル
└── nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json  # Firebase設定
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

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `DISCORD_BOT_TOKEN` | Discord Bot Token | ✅ |
| `FIREBASE_SERVICE_ACCOUNT_KEY_PATH` | Firebaseキーファイルパス | ✅ |
| `FIREBASE_SERVICE_ACCOUNT` | Firebase設定JSON | - |

## 📞 サポート

問題が発生した場合は、以下の情報を含めてお問い合わせください：

1. エラーメッセージの全文
2. 実行環境（OS、Pythonバージョン）
3. 実行したコマンド
4. `.env`ファイルの設定（Tokenは除く）

## 📄 ライセンス

このプロジェクトは内部使用のためのものです。