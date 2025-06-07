# Discord にゃんこエージェント ボット - GCP Docker Compose デプロイメント

このドキュメントでは、GCP Compute Engine上でDocker Composeを使用してボットを稼働させる方法について説明します。

## 🎯 概要

GCP上でdocker-compose.ymlを実行するために、以下のアーキテクチャを使用します：

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
          │                    │                    │
          ▼                    ▼                    ▼
    Load Balancer      Secret Manager      Cloud Logging
```

## 🛠️ 前提条件

### 必要なツール
- Google Cloud SDK (`gcloud`)
- Docker
- 適切なGCPプロジェクトアクセス権限

### GCPプロジェクト設定
```bash
# プロジェクト設定
gcloud config set project nyanco-bot

# 必要なAPIを有効化
gcloud services enable compute.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

## 📁 ファイル構成

```
bot/
├── docker-compose.gcp.yml      # GCP用Docker Compose設定
├── nginx.conf                  # Nginxプロキシ設定
├── deploy_gcp_compose.sh       # GCPデプロイメントスクリプト
├── cloudbuild.gcp-compose.yaml # Cloud Build設定
└── README_GCP_COMPOSE.md       # このファイル
```

## 🚀 デプロイメント手順

### 1. 環境変数の設定

```bash
# .env ファイルに必要な変数を設定
cp .env.example .env
vi .env
```

必要な環境変数：
```bash
DISCORD_BOT_TOKEN_MIYA=your_miya_bot_token
DISCORD_BOT_TOKEN_EVE=your_eve_bot_token
FIREBASE_SERVICE_ACCOUNT={"type": "service_account", ...}
GEMINI_API_KEY=your_gemini_api_key
```

### 2. 一括デプロイ（推奨）

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

### 3. 段階的デプロイ

個別に実行する場合：

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

## 🎛️ 管理コマンド

### ボット管理
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
```

### インスタンス管理
```bash
# SSH接続
./deploy_gcp_compose.sh ssh

# インスタンス削除
./deploy_gcp_compose.sh delete
```

### 手動Docker Compose操作
```bash
# SSH接続後
gcloud compute ssh nyanco-bot-compose --zone=asia-northeast1-a

# インスタンス内で
cd ~
docker-compose ps              # ステータス確認
docker-compose logs -f         # ログ表示
docker-compose restart miya-bot  # 個別再起動
```

## ☁️ Cloud Build によるCI/CD

### 自動ビルド・デプロイ設定

```bash
# Cloud Buildトリガーを作成
gcloud builds triggers create github \
  --repo-name=commupro-guild \
  --repo-owner=your-username \
  --branch-pattern="^main$" \
  --build-config=bot/cloudbuild.gcp-compose.yaml
```

### 手動ビルド実行

```bash
# ローカルからCloud Buildを実行
gcloud builds submit . --config=cloudbuild.gcp-compose.yaml
```

## 🔧 設定詳細

### Compute Engine インスタンス仕様

| 項目 | 値 |
|------|-----|
| **マシンタイプ** | e2-standard-2 (2 vCPU, 8GB RAM) |
| **OS** | Container-Optimized OS |
| **ディスク** | 50GB Standard Persistent Disk |
| **ネットワーク** | デフォルトVPC |
| **ファイアウォール** | HTTP, HTTPS, 8081, 8082 |

### リソース制限

各コンテナのリソース制限：

| コンテナ | CPU制限 | メモリ制限 | CPU予約 | メモリ予約 |
|----------|---------|------------|---------|------------|
| **Miya Bot** | 0.5 CPU | 1GB | 0.25 CPU | 512MB |
| **Eve Bot** | 0.5 CPU | 1GB | 0.25 CPU | 512MB |
| **Nginx** | 0.25 CPU | 256MB | - | - |

### ネットワーク設定

| サービス | 内部ポート | 外部ポート | URL |
|----------|------------|------------|-----|
| **Nginx** | 80 | 80 | `http://EXTERNAL_IP/` |
| **Miya Bot** | 8080 | 8081 | `http://EXTERNAL_IP/miya/` |
| **Eve Bot** | 8080 | 8082 | `http://EXTERNAL_IP/eve/` |

## 📊 モニタリング

### ヘルスチェック

```bash
# インスタンスの外部IPを取得
EXTERNAL_IP=$(gcloud compute instances describe nyanco-bot-compose \
  --zone=asia-northeast1-a \
  --format="value(networkInterfaces[0].accessConfigs[0].natIP)")

# ヘルスチェック実行
curl http://$EXTERNAL_IP/health          # 全体
curl http://$EXTERNAL_IP/miya/health     # みやにゃん
curl http://$EXTERNAL_IP/eve/health      # イヴにゃん
```

### ログ確認

```bash
# Cloud Loggingでログ確認
gcloud logging read "resource.type=gce_instance AND resource.labels.instance_id=nyanco-bot-compose"

# SSH接続してローカルログ確認
gcloud compute ssh nyanco-bot-compose --zone=asia-northeast1-a
docker-compose logs -f
```

### リソース使用量確認

```bash
# インスタンス内でリソース確認
docker stats
htop
df -h
```

## 💰 コスト見積もり

### 月額コスト概算（asia-northeast1リージョン）

| リソース | 仕様 | 月額（USD） |
|----------|------|-------------|
| **Compute Engine** | e2-standard-2 | ~$49 |
| **Persistent Disk** | 50GB Standard | ~$2 |
| **External IP** | 静的IP | ~$3 |
| **Network Egress** | 1GB/月 | ~$0.12 |
| **合計** | | **~$54** |

### コスト最適化

```bash
# インスタンスをpreemptibleにして約70%削減
gcloud compute instances create nyanco-bot-compose \
  --preemptible \
  --machine-type=e2-medium  # よりコンパクトなマシンタイプ
```

## 🔒 セキュリティ

### Secret Manager 設定

機密情報はSecret Managerで管理：

```bash
# シークレット一覧
gcloud secrets list

# シークレット値確認
gcloud secrets versions access latest --secret="discord-bot-token-miya"
```

### ファイアウォール設定

```bash
# 特定IPからのアクセスのみ許可
gcloud compute firewall-rules update nyanco-bot-http \
  --source-ranges="YOUR_IP/32"
```

### SSL/TLS設定

SSL証明書を使用する場合：

```bash
# Let's Encrypt証明書の取得
sudo certbot certonly --standalone -d your-domain.com

# nginx.confのHTTPS設定を有効化
```

## 🐛 トラブルシューティング

### よくある問題

1. **インスタンスに接続できない**
   ```bash
   # ファイアウォールルールを確認
   gcloud compute firewall-rules list
   
   # インスタンスの状態を確認
   gcloud compute instances describe nyanco-bot-compose --zone=asia-northeast1-a
   ```

2. **ボットが起動しない**
   ```bash
   # ログを確認
   ./deploy_gcp_compose.sh logs
   
   # Secret Managerの値を確認
   gcloud secrets versions access latest --secret="discord-bot-token-miya"
   ```

3. **リソース不足**
   ```bash
   # マシンタイプをアップグレード
   gcloud compute instances set-machine-type nyanco-bot-compose \
     --machine-type=e2-standard-4 --zone=asia-northeast1-a
   ```

### デバッグモード

```bash
# デバッグ情報を有効化してデプロイ
export DEBUG=true
./deploy_gcp_compose.sh deploy
```

## 🔄 更新とメンテナンス

### ボットコードの更新

```bash
# 1. 新しいイメージをビルド・プッシュ
./deploy_separate.sh build both
./deploy_separate.sh push both

# 2. Compute Engineで更新を適用
./deploy_gcp_compose.sh restart
```

### システム更新

```bash
# Container-Optimized OSの更新
gcloud compute ssh nyanco-bot-compose --zone=asia-northeast1-a
sudo update_engine_client

# Docker Composeの更新
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```

## 📝 注意事項

1. **リソース制限**: 適切なリソース制限を設定してコスト管理
2. **バックアップ**: 重要なデータの定期バックアップ
3. **モニタリング**: Cloud Monitoringでアラート設定
4. **セキュリティ**: 定期的なセキュリティ更新
5. **コスト管理**: Budget アラートの設定

## 🔗 関連ドキュメント

- [Google Compute Engine](https://cloud.google.com/compute/docs)
- [Docker Compose](https://docs.docker.com/compose/)
- [Google Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Google Cloud Build](https://cloud.google.com/build/docs)