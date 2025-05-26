# Discord にゃんこエージェント ボット

現在のFirestore構造と連動したPython製Discordボットです。

## 機能

### 📝 インタラクション記録
- メッセージの送信・編集・削除
- リアクションの追加・削除
- メンバーの参加・退出
- 全てのアクティビティをFirestoreの`interactions`コレクションに記録

### 👥 ユーザー管理
- ユーザー情報の自動作成・更新
- エンゲージメントスコアの自動計算
- 最終アクティブ時間の追跡
- Firestoreの`users`コレクションと連動

### 🔍 キーワード抽出
- メッセージから自動的にキーワードを抽出
- 日本語・英語対応
- トピック分析に活用

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`env_example.txt`を参考に`.env`ファイルを作成してください。

```bash
# Discord Bot Token
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# Firebase Service Account (どちらか一方を設定)
# オプション1: JSON文字列として設定
FIREBASE_SERVICE_ACCOUNT={"type":"service_account","project_id":"your-project-id",...}

# オプション2: ファイルパスとして設定
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=/path/to/your/service-account-key.json
```

### 3. Discord Bot の作成

1. [Discord Developer Portal](https://discord.com/developers/applications)にアクセス
2. 新しいアプリケーションを作成
3. Botセクションでボットを作成
4. トークンをコピーして環境変数に設定
5. 必要な権限を設定：
   - `Send Messages`
   - `Read Message History`
   - `Add Reactions`
   - `View Channels`
   - `Read Messages/View Channels`

### 4. Firebase設定

1. Firebase Consoleでサービスアカウントキーを生成
2. JSONファイルをダウンロードまたは内容をコピー
3. 環境変数に設定

## 実行方法

### 方法1: 実行スクリプトを使用（推奨）

```bash
python run_bot.py
```

### 方法2: 直接実行

```bash
python discord-bot.py
```

## Firestore データ構造

### interactions コレクション

```json
{
  "type": "message|message_edit|message_delete|member_join|member_leave|reaction_add|reaction_remove",
  "userId": "Discord User ID",
  "username": "ユーザー名",
  "guildId": "Discord Guild ID",
  "guildName": "サーバー名",
  "channelId": "Discord Channel ID",
  "channelName": "チャンネル名",
  "messageId": "Discord Message ID",
  "content": "メッセージ内容",
  "keywords": ["抽出されたキーワード"],
  "metadata": {
    "hasAttachments": false,
    "hasEmbeds": false,
    "mentionCount": 0,
    "reactionCount": 0
  },
  "timestamp": "Firestore SERVER_TIMESTAMP"
}
```

### users コレクション

```json
{
  "id": "Discord User ID",
  "username": "ユーザー名",
  "guildId": "Discord Guild ID",
  "joinedAt": "参加日時",
  "lastActive": "最終アクティブ日時",
  "interests": ["興味のあるトピック"],
  "engagementScore": 100,
  "isActive": true,
  "preferences": {
    "podcastNotifications": true,
    "matchingNotifications": true,
    "dmNotifications": true,
    "language": "ja"
  }
}
```

## エンゲージメントスコア計算

- メッセージ送信: +1ポイント
- メッセージ編集: +0.5ポイント
- リアクション追加: +0.3ポイント
- サーバー参加: +5ポイント

## トラブルシューティング

### よくあるエラー

1. **Discord Botトークンが不正**
   - Discord Developer Portalでトークンを再生成
   - 環境変数が正しく設定されているか確認

2. **Firebase接続エラー**
   - サービスアカウントキーの権限を確認
   - Firestore APIが有効になっているか確認

3. **依存関係エラー**
   - `pip install -r requirements.txt`を再実行
   - Pythonバージョンが3.8以上であることを確認

### ログの確認

ボットは詳細なログを出力します：
- ✅ 成功メッセージ
- ⚠️ 警告メッセージ  
- ❌ エラーメッセージ

## 開発者向け情報

### カスタマイズ

- `extract_keywords()`: キーワード抽出ロジックの改善
- `update_user_info()`: ユーザー情報更新ロジックの拡張
- エンゲージメントスコア計算の調整

### 拡張機能

- 自然言語処理ライブラリの統合
- 感情分析の追加
- より高度なトピック分析

## ライセンス

このプロジェクトは内部使用を目的としています。 