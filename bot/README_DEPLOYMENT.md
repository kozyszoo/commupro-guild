# Discord にゃんこエージェント ボット - デプロイメントガイド

このガイドでは、Discord にゃんこエージェント ボットの各種デプロイメント方法について説明します。

## 📋 目次

1. [デプロイメント方式の選択](#デプロイメント方式の選択)
2. [共通の前提条件](#共通の前提条件)
3. [Cloud Runデプロイメント](#cloud-runデプロイメント)
4. [GCP Docker Composeデプロイメント](#gcp-docker-composeデプロイメント)
5. [分離デプロイメント](#分離デプロイメント)
6. [監視とトラブルシューティング](#監視とトラブルシューティング)
7. [コスト最適化](#コスト最適化)

## 🎯 デプロイメント方式の選択

| 方式 | 用途 | メリット | デメリット |
|------|------|----------|------------|
| **Cloud Run** | 本番環境・シンプル運用 | サーバーレス、自動スケール、保守性 | 常時稼働コスト |
| **GCP Compute + Docker Compose** | 本番環境・詳細制御 | リソース効率、複数サービス管理 | インフラ管理必要 |
| **分離デプロイメント** | 開発・テスト環境 | 独立性、デバッグしやすさ | 複雑性増加 |

## 🛠️ 共通の前提条件

### 必要なツール
- Google Cloud Platform アカウント
- Google Cloud SDK (gcloud) がインストール済み
- Docker がインストール済み
- Discord Bot Token（各ボット用）
- Firebase プロジェクトとサービスアカウント

### GCPプロジェクトの基本設定

```bash
# Google Cloud にログイン
gcloud auth login

# プロジェクトを設定
gcloud config set project nyanco-bot

# 必要なAPIを有効化
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

---

## ☁️ Cloud Runデプロイメント

サーバーレスでシンプルな運用に最適です。

### 環境変数の設定

`.env.cloudrun` ファイルを作成：

```bash
# Google Cloud プロジェクト ID
PROJECT_ID=nyanco-bot

# Discord Bot Token
DISCORD_BOT_TOKEN_MIYA=your_miya_discord_bot_token
DISCORD_BOT_TOKEN_EVE=your_eve_discord_bot_token

# Firebase Service Account（JSON文字列）
FIREBASE_SERVICE_ACCOUNT={"type":"service_account",...}

# Gemini API Key
GEMINI_API_KEY=your_gemini_api_key
```

### 自動デプロイ

```bash
# 環境変数を読み込み
source .env.cloudrun

# デプロイスクリプトを実行
./deploy.sh
```

### 手動デプロイ

```bash
# Docker イメージをビルド
docker build -t gcr.io/nyanco-bot/discord-nyanco-agent:latest .

# イメージをプッシュ
docker push gcr.io/nyanco-bot/discord-nyanco-agent:latest

# Cloud Run にデプロイ
gcloud run deploy discord-nyanco-agent \
    --image gcr.io/nyanco-bot/discord-nyanco-agent:latest \
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
    --set-env-vars "DISCORD_BOT_TOKEN_MIYA=your_token" \
    --set-env-vars "FIREBASE_SERVICE_ACCOUNT=your_service_account_json"
```

### リソース設定の調整

```bash
# メモリやCPUを調整
gcloud run services update discord-nyanco-agent \
    --region asia-northeast1 \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 3
```

---

## 🐳 GCP Docker Composeデプロイメント

複数サービスの詳細制御が可能です。

### アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│                    GCP Compute Engine                   │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                Docker Compose                       │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │ │
│  │  │   Nginx      │  │  Miya Bot    │  │ Eve Bot  │  │ │
│  │  │   Proxy      │  │  Container   │  │Container │  │ │
│  │  │   :80        │  │   :8081      │  │  :8082   │  │ │
│  │  └──────────────┘  └──────────────┘  └──────────┘  │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 一括デプロイ

```bash
# 全ての処理を自動実行
./deploy_gcp_compose.sh all
```

この一つのコマンドで以下が実行されます：
1. Secret Managerにシークレット設定
2. Compute Engineインスタンス作成
3. インスタンスセットアップ
4. ボットデプロイ
5. ボット開始
6. ステータス確認

### 段階的デプロイ

```bash
# 1. インスタンス作成
./deploy_gcp_compose.sh create

# 2. インスタンスセットアップ
./deploy_gcp_compose.sh setup

# 3. ボットデプロイ
./deploy_gcp_compose.sh deploy

# 4. ボット開始
./deploy_gcp_compose.sh start
```

### 管理コマンド

```bash
# ボット開始
./deploy_gcp_compose.sh start

# ボット停止
./deploy_gcp_compose.sh stop

# ボット再起動
./deploy_gcp_compose.sh restart

# ステータス確認
./deploy_gcp_compose.sh status

# ログ確認
./deploy_gcp_compose.sh logs

# SSH接続
./deploy_gcp_compose.sh ssh

# インスタンス削除
./deploy_gcp_compose.sh delete
```

### インスタンス仕様

| 項目 | 値 |
|------|-----|
| **マシンタイプ** | e2-standard-2 (2 vCPU, 8GB RAM) |
| **OS** | Container-Optimized OS |
| **ディスク** | 50GB Standard Persistent Disk |
| **ネットワーク** | デフォルトVPC |
| **ファイアウォール** | HTTP, HTTPS, 8081, 8082 |

---

## 🔀 分離デプロイメント

開発・テスト環境やボット別の独立運用に適しています。

### メリット
- **独立性**: 一方のボットがクラッシュしても他方に影響しない
- **スケーラビリティ**: 各ボットを独立してスケール可能
- **リソース管理**: ボット毎にリソース制限を設定可能
- **デバッグ**: 個別のログとモニタリング

### ローカル実行

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

### Cloud Runでの分離デプロイ

```bash
# 両方のボットをビルド・プッシュ・デプロイ
./deploy_separate.sh all both

# みやにゃんのみデプロイ
./deploy_separate.sh all miya

# イヴにゃんのみデプロイ
./deploy_separate.sh all eve
```

### 手動分離デプロイ

```bash
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

---

## 📊 監視とトラブルシューティング

### ヘルスチェック

```bash
# Cloud Run
curl https://your-service-url/health

# Docker Compose
curl http://EXTERNAL_IP/health

# 分離デプロイ
curl http://localhost:8081/health  # みやにゃん
curl http://localhost:8082/health  # イヴにゃん
```

### ログの確認

#### Cloud Run
```bash
# リアルタイムログ
gcloud logs tail --follow \
    --project=nyanco-bot \
    --resource-type=cloud_run_revision \
    --resource-labels=service_name=discord-nyanco-agent

# 過去のログ
gcloud logs read \
    --project=nyanco-bot \
    --resource-type=cloud_run_revision \
    --resource-labels=service_name=discord-nyanco-agent \
    --limit=100
```

#### Docker Compose
```bash
# SSH接続後
gcloud compute ssh nyanco-bot-compose --zone=asia-northeast1-a

# インスタンス内で
docker-compose logs -f
docker-compose logs -f miya-bot
docker-compose logs -f eve-bot
```

#### 分離デプロイ
```bash
# Docker Composeログ
docker-compose logs -f miya-bot
docker-compose logs -f eve-bot

# Cloud Runログ
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=discord-nyanco-agent-miya"
```

### よくある問題とトラブルシューティング

1. **ボットが起動しない**
   - Discord Bot Token が正しく設定されているか確認
   - Firebase Service Account の JSON が正しいか確認
   - ネットワーク接続を確認

2. **メモリ不足エラー**
   - メモリ制限を増やす: `--memory 2Gi`
   - 不要なサービスを停止

3. **タイムアウトエラー**
   - タイムアウト時間を延長: `--timeout 3600`
   - 処理の並列化を検討

4. **権限エラー**
   - サービスアカウントの権限を確認
   - Firebase プロジェクトのアクセス権限を確認
   - IAMロールの設定を確認

### デバッグ方法

```bash
# Cloud Run サービスの詳細情報
gcloud run services describe discord-nyanco-agent --region asia-northeast1

# 最新のリビジョン確認
gcloud run revisions list --service discord-nyanco-agent --region asia-northeast1

# エラーログの確認
gcloud logs read --project=nyanco-bot --filter="severity>=ERROR"

# Compute Engine インスタンスの状態確認
gcloud compute instances describe nyanco-bot-compose --zone=asia-northeast1-a
```

---

## 💰 コスト最適化

### Cloud Run推奨設定

- **最小インスタンス数**: 1（常時稼働が必要なため）
- **最大インスタンス数**: 1（Discord ボットは1インスタンスで十分）
- **CPU**: 1（軽量な処理のため）
- **メモリ**: 1Gi（Firebase接続とDiscord.pyに十分）

### Docker Compose推奨設定

| コンテナ | CPU制限 | メモリ制限 | CPU予約 | メモリ予約 |
|----------|---------|------------|---------|------------|
| **Miya Bot** | 0.5 CPU | 1GB | 0.25 CPU | 512MB |
| **Eve Bot** | 0.5 CPU | 1GB | 0.25 CPU | 512MB |
| **Nginx** | 0.25 CPU | 256MB | - | - |

### コスト見積もり

- **Cloud Run**: 月額約 $15-25（常時稼働の場合）
- **Compute Engine**: 月額約 $30-50（e2-standard-2使用時）
- **分離デプロイ**: 各ボットごとに上記コストが発生

実際のコストは使用量により変動します。

---

## 🔒 セキュリティベストプラクティス

### 環境変数管理
- 本番環境では Secret Manager を使用
- ローカル開発では `.env` ファイル（.gitignoreに追加）
- ハードコードされた認証情報は絶対に使用しない

### ネットワークセキュリティ
- 必要最小限のポートのみ開放
- HTTPS通信の使用
- VPC ファイアウォールルールの適切な設定

### アクセス制御
- IAMロールの最小権限原則
- サービスアカウントの定期的なローテーション
- 監査ログの有効化

---

## 🔄 CI/CD パイプライン

### Cloud Build設定

```bash
# Cloud Buildトリガーを作成
gcloud builds triggers create github \
  --repo-name=commupro-guild \
  --repo-owner=your-username \
  --branch-pattern="^main$" \
  --build-config=bot/cloudbuild.yaml
```

### 手動ビルド実行

```bash
# ローカルからCloud Buildを実行
gcloud builds submit . --config=cloudbuild.yaml
```

このガイドに従って、プロジェクトの要件に最適なデプロイメント方式を選択し、運用してください。 