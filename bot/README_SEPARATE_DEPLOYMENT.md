# Discord にゃんこエージェント ボット - 分離デプロイメント

このドキュメントでは、みやにゃんとイヴにゃんを別々のDockerコンテナ/Cloud Runサービスで動かす方法について説明します。

## 🎯 概要

従来の単一プロセスでの複数ボット管理から、各ボットを独立したコンテナで実行する方式に変更できます。

### メリット
- **独立性**: 一方のボットがクラッシュしても他方に影響しない
- **スケーラビリティ**: 各ボットを独立してスケール可能
- **リソース管理**: ボット毎にリソース制限を設定可能
- **デバッグ**: 個別のログとモニタリング

## 📁 ファイル構成

```
bot/
├── run_single_bot.py          # 単一ボット実行スクリプト
├── Dockerfile.single          # 単一ボット用Dockerfile
├── docker-compose.yml         # ローカル開発用Docker Compose
├── start_bots.sh             # ローカル起動スクリプト
├── deploy_separate.sh        # GCP個別デプロイスクリプト
├── .env.example              # 環境変数設定例
└── README_SEPARATE_DEPLOYMENT.md  # このファイル
```

## 🛠️ セットアップ

### 1. 環境変数の設定

```bash
# .env.example を .env にコピー
cp .env.example .env

# .env ファイルを編集して実際の値を設定
vi .env
```

必要な環境変数：
```bash
# 各ボット用のDiscordトークン
DISCORD_BOT_TOKEN_MIYA=your_miya_bot_token
DISCORD_BOT_TOKEN_EVE=your_eve_bot_token

# Firebase設定
FIREBASE_SERVICE_ACCOUNT={"type": "service_account", ...}
# または
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=./firebase-key.json

# Gemini API
GEMINI_API_KEY=your_gemini_api_key
```

### 2. Docker環境の準備

```bash
# Docker と Docker Compose がインストールされていることを確認
docker --version
docker-compose --version
```

## 🚀 ローカル実行

### Docker Composeを使用

```bash
# すべてのボットを起動
./start_bots.sh start

# みやにゃんのみ起動
./start_bots.sh miya

# イヴにゃんのみ起動
./start_bots.sh eve

# ステータス確認
./start_bots.sh status

# ログ確認
./start_bots.sh logs

# 停止
./start_bots.sh stop
```

### 手動実行

```bash
# イメージビルド
docker build -f Dockerfile.single -t nyanco-bot-single .

# みやにゃん起動
docker run -d --name miya-bot \
  --env-file .env \
  -e BOT_CHARACTER=miya \
  -p 8081:8080 \
  nyanco-bot-single

# イヴにゃん起動
docker run -d --name eve-bot \
  --env-file .env \
  -e BOT_CHARACTER=eve \
  -p 8082:8080 \
  nyanco-bot-single
```

## ☁️ GCP Cloud Run デプロイ

### 自動デプロイ

```bash
# 両方のボットをビルド・プッシュ・デプロイ
./deploy_separate.sh all both

# みやにゃんのみデプロイ
./deploy_separate.sh all miya

# イヴにゃんのみデプロイ
./deploy_separate.sh all eve
```

### 段階的デプロイ

```bash
# 1. イメージビルド
./deploy_separate.sh build both

# 2. Container Registryにpush
./deploy_separate.sh push both

# 3. Cloud Runにデプロイ
./deploy_separate.sh deploy both
```

### 手動デプロイ

```bash
# GCP認証
gcloud auth login
gcloud config set project nyanco-bot

# イメージビルド＆プッシュ
docker build -f Dockerfile.single -t gcr.io/nyanco-bot/discord-nyanco-agent-miya:latest .
docker push gcr.io/nyanco-bot/discord-nyanco-agent-miya:latest

# Cloud Runデプロイ
gcloud run deploy discord-nyanco-agent-miya \
  --image gcr.io/nyanco-bot/discord-nyanco-agent-miya:latest \
  --region asia-northeast1 \
  --platform managed \
  --set-env-vars BOT_CHARACTER=miya \
  --allow-unauthenticated
```

## 🔧 設定

### 環境変数

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `BOT_CHARACTER` | `miya` または `eve` | ✅ |
| `DISCORD_BOT_TOKEN_MIYA` | みやにゃん用トークン | ✅ |
| `DISCORD_BOT_TOKEN_EVE` | イヴにゃん用トークン | ✅ |
| `FIREBASE_SERVICE_ACCOUNT` | Firebase設定JSON | ✅ |
| `GEMINI_API_KEY` | Gemini API キー | ⚠️ |

### ポート設定

- みやにゃん: `8081`
- イヴにゃん: `8082`
- ヘルスチェック: `/health`

## 📊 モニタリング

### ヘルスチェック

```bash
# みやにゃんのヘルスチェック
curl http://localhost:8081/health

# イヴにゃんのヘルスチェック
curl http://localhost:8082/health
```

### ログ確認

```bash
# Docker Composeログ
docker-compose logs -f miya-bot
docker-compose logs -f eve-bot

# Cloud Runログ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=discord-nyanco-agent-miya"
```

## 🔄 従来方式との比較

| 項目 | 従来方式 | 分離方式 |
|------|----------|----------|
| **プロセス数** | 1つ | 2つ |
| **障害影響範囲** | 全ボット | 単一ボット |
| **リソース使用量** | 低 | 中 |
| **デプロイ複雑さ** | 簡単 | 中程度 |
| **スケーラビリティ** | 低 | 高 |
| **デバッグ容易さ** | 中 | 高 |

## 🐛 トラブルシューティング

### よくある問題

1. **ボットが起動しない**
   ```bash
   # ログを確認
   docker-compose logs miya-bot
   
   # 環境変数を確認
   docker-compose config
   ```

2. **トークンエラー**
   ```bash
   # .env ファイルの設定を確認
   grep DISCORD_BOT_TOKEN .env
   ```

3. **ポート競合**
   ```bash
   # 使用中のポートを確認
   netstat -tlnp | grep :808
   ```

### デバッグモード

```bash
# デバッグログ有効化
echo "DEBUG=true" >> .env

# コンテナ内でシェル実行
docker-compose exec miya-bot /bin/bash
```

## 📝 注意事項

1. **同一Discord Bot Token**: 同じトークンを複数のボットで使用しないでください
2. **リソース制限**: 各ボットに適切なメモリ・CPU制限を設定してください
3. **ファイアウォール**: 必要なポートが開放されていることを確認してください
4. **バックアップ**: 環境変数やFirebase設定のバックアップを取ってください

## 🔗 関連ドキュメント

- [Docker Compose公式ドキュメント](https://docs.docker.com/compose/)
- [Google Cloud Run ドキュメント](https://cloud.google.com/run/docs)
- [Discord.py ドキュメント](https://discordpy.readthedocs.io/)
- [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)