# Discord にゃんこエージェント ボット - Cloud Run デプロイガイド

このガイドでは、Discord にゃんこエージェント ボットを Google Cloud Run にデプロイする手順を説明します。

## 🚀 クイックスタート

### 1. 前提条件

- Google Cloud Platform アカウント
- Google Cloud SDK (gcloud) がインストール済み
- Docker がインストール済み
- Discord Bot Token
- Firebase プロジェクトとサービスアカウント

### 2. Google Cloud プロジェクトの準備

```bash
# Google Cloud にログイン
gcloud auth login

# プロジェクトを作成（既存の場合はスキップ）
gcloud projects create your-project-id

# プロジェクトを設定
gcloud config set project your-project-id

# 必要なAPIを有効化
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 3. 環境変数の設定

`.env.cloudrun.example` をコピーして `.env.cloudrun` を作成し、実際の値を設定：

```bash
cp .env.cloudrun.example .env.cloudrun
```

`.env.cloudrun` を編集して以下を設定：

```bash
# Google Cloud プロジェクト ID
PROJECT_ID=your-gcp-project-id

# Discord Bot Token
DISCORD_BOT_TOKEN=your_actual_discord_bot_token

# Firebase Service Account（JSON文字列）
FIREBASE_SERVICE_ACCOUNT={"type":"service_account",...}
```

### 4. デプロイの実行

#### 方法1: 自動デプロイスクリプト使用

```bash
# 環境変数を読み込み
source .env.cloudrun

# デプロイスクリプトを実行
./deploy.sh
```

#### 方法2: 手動デプロイ

```bash
# Docker イメージをビルド
docker build -t gcr.io/your-project-id/discord-nyanco-agent:latest .

# イメージをプッシュ
docker push gcr.io/your-project-id/discord-nyanco-agent:latest

# Cloud Run にデプロイ
gcloud run deploy discord-nyanco-agent \
    --image gcr.io/your-project-id/discord-nyanco-agent:latest \
    --region asia-northeast1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --concurrency 1 \
    --max-instances 1 \
    --min-instances 1 \
    --port 8080 \
    --timeout 3600 \
    --set-env-vars "DISCORD_BOT_TOKEN=your_token" \
    --set-env-vars "FIREBASE_SERVICE_ACCOUNT=your_service_account_json"
```

## 📊 監視とログ

### ヘルスチェック

デプロイ後、以下のエンドポイントでボットの状態を確認できます：

- `https://your-service-url/` - 全体的なステータス
- `https://your-service-url/health` - ヘルスチェック
- `https://your-service-url/ready` - レディネスプローブ

### ログの確認

```bash
# リアルタイムログの確認
gcloud logs tail --follow \
    --project=your-project-id \
    --resource-type=cloud_run_revision \
    --resource-labels=service_name=discord-nyanco-agent

# 過去のログの確認
gcloud logs read \
    --project=your-project-id \
    --resource-type=cloud_run_revision \
    --resource-labels=service_name=discord-nyanco-agent \
    --limit=100
```

## 🔧 設定とカスタマイズ

### リソース設定

Cloud Run サービスのリソースを調整する場合：

```bash
gcloud run services update discord-nyanco-agent \
    --region asia-northeast1 \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 3
```

### 環境変数の更新

```bash
gcloud run services update discord-nyanco-agent \
    --region asia-northeast1 \
    --set-env-vars "NEW_VAR=value"
```

### 新しいバージョンのデプロイ

```bash
# 新しいイメージをビルドしてプッシュ
docker build -t gcr.io/your-project-id/discord-nyanco-agent:v2 .
docker push gcr.io/your-project-id/discord-nyanco-agent:v2

# 新しいバージョンをデプロイ
gcloud run services update discord-nyanco-agent \
    --region asia-northeast1 \
    --image gcr.io/your-project-id/discord-nyanco-agent:v2
```

## 🛠️ トラブルシューティング

### よくある問題

1. **ボットが起動しない**
   - Discord Bot Token が正しく設定されているか確認
   - Firebase Service Account の JSON が正しいか確認

2. **メモリ不足エラー**
   - メモリ制限を増やす: `--memory 2Gi`

3. **タイムアウトエラー**
   - タイムアウト時間を延長: `--timeout 3600`

4. **権限エラー**
   - サービスアカウントの権限を確認
   - Firebase プロジェクトのアクセス権限を確認

### デバッグ方法

```bash
# サービスの詳細情報を確認
gcloud run services describe discord-nyanco-agent --region asia-northeast1

# 最新のリビジョンを確認
gcloud run revisions list --service discord-nyanco-agent --region asia-northeast1

# エラーログを確認
gcloud logs read --project=your-project-id --filter="severity>=ERROR"
```

## 💰 コスト最適化

### 推奨設定

- **最小インスタンス数**: 1（常時稼働が必要なため）
- **最大インスタンス数**: 1（Discord ボットは1インスタンスで十分）
- **CPU**: 1（軽量な処理のため）
- **メモリ**: 1Gi（Firebase接続とDiscord.pyに十分）

### コスト見積もり

- 月額約 $15-25（常時稼働の場合）
- 実際のコストは使用量により変動

## 🔒 セキュリティ

### 重要な注意事項

1. **環境変数の管理**
   - Discord Bot Token や Firebase Service Account は絶対に公開しない
   - `.env` ファイルは `.gitignore` に追加

2. **アクセス制御**
   - Cloud Run サービスは認証不要に設定（ヘルスチェックのため）
   - Firebase セキュリティルールで適切にアクセス制御

3. **ログの管理**
   - 機密情報がログに出力されないよう注意
   - 定期的にログを確認

## 📞 サポート

問題が発生した場合は、以下の情報を含めてお問い合わせください：

- エラーメッセージ
- ログの内容
- 実行した手順
- 環境情報（GCP プロジェクト、リージョンなど）