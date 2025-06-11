# CI/CD セットアップガイド

このドキュメントでは、GitHub ActionsとGoogle Cloud Platformを使用したCI/CDパイプラインの設定について説明します。

## 概要

プロジェクトには以下の2つのワークフローが設定されています：

1. **CI Pipeline** (`.github/workflows/ci.yml`) - テスト、リント、セキュリティチェック
2. **Deploy Pipeline** (`.github/workflows/deploy.yml`) - 本番環境へのデプロイ

## CIパイプライン

### 実行トリガー
- `main`、`develop`ブランチへのpush
- `main`、`develop`ブランチへのPull Request

### テストジョブ

#### 1. TypeScript Tests (`test-typescript`)
- Node.js 18を使用
- TypeScriptの型チェック
- ESLintによるコード品質チェック
- ユニットテストの実行

#### 2. Firebase Functions Tests (`test-functions`)
- Firebase Functionsのビルドテスト
- TypeScriptのコンパイル確認

#### 3. Python Bot Tests (`test-python-bot`)
- Python 3.11を使用
- flake8によるコード品質チェック
- pytestによるテスト実行
- カバレッジレポートの生成
- Codecovへのカバレッジアップロード

#### 4. Security Scan (`security-scan`)
- Trivyによる脆弱性スキャン
- GitHub Security tabへの結果アップロード

#### 5. Dependency Check (`dependency-check`)
- npm auditによるNode.js依存関係チェック
- safetyによるPython依存関係チェック

#### 6. Docker Build Test (`docker-build`)
- MiyaボットとEveボットのDockerイメージビルドテスト

## デプロイパイプライン

### 実行トリガー
- `main`ブランチへのpush（CIパイプライン成功後）

### デプロイジョブ

#### 1. Firebase Deploy (`deploy-firebase`)
- Firebase HostingとFunctionsのデプロイ
- TypeScriptプロジェクトのビルド

#### 2. Docker Build & Push (`build-and-push-docker`)
- Google Container RegistryへのDockerイメージプッシュ
- Miya/Eveボットの個別イメージ作成

#### 3. Cloud Run Deploy (`deploy-cloud-run`)
- Cloud Runサービスへのデプロイ
- 環境変数とシークレットの設定

#### 4. Health Check (`health-check`)
- デプロイ後のヘルスチェック
- Firebase HostingとCloud Runサービスの確認

#### 5. Slack Notification (`notify-deployment`)
- デプロイ結果のSlack通知

## 必要なGitHub Secrets

以下のシークレットをGitHubリポジトリに設定してください：

### Firebase関連
```
FIREBASE_SERVICE_ACCOUNT    # Firebase Admin SDKのJSON
FIREBASE_PROJECT_ID         # FirebaseプロジェクトID
```

### Google Cloud Platform関連
```
GCP_PROJECT_ID             # GCPプロジェクトID
GCP_SERVICE_ACCOUNT_KEY    # GCPサービスアカウントのJSON
```

### 通知関連
```
SLACK_WEBHOOK_URL          # Slack通知用WebhookURL
```

## セットアップ手順

### 1. GitHub Secretsの設定

```bash
# GitHub CLIを使用（推奨）
gh secret set FIREBASE_SERVICE_ACCOUNT < firebase-key.json
gh secret set FIREBASE_PROJECT_ID -b "your-firebase-project-id"
gh secret set GCP_PROJECT_ID -b "your-gcp-project-id"
gh secret set GCP_SERVICE_ACCOUNT_KEY < gcp-key.json
gh secret set SLACK_WEBHOOK_URL -b "your-slack-webhook-url"
```

### 2. Google Cloud Secretsの設定

```bash
# Secret Managerにシークレットを作成
gcloud secrets create discord-bot-token-miya --data-file=-
gcloud secrets create discord-bot-token-eve --data-file=-
gcloud secrets create firebase-service-account --data-file=firebase-key.json
gcloud secrets create gcp-project-id --data-file=-
gcloud secrets create gcp-location --data-file=-
```

### 3. サービスアカウント権限の設定

GitHub Actionsで使用するサービスアカウントに以下の権限を付与：

```bash
# Cloud Run Admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

# Container Registry Admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Secret Manager Accessor
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Firebase Admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/firebase.admin"
```

## ローカル開発でのテスト実行

### TypeScript/Node.js
```bash
npm install
npm test
npx tsc --noEmit
```

### Python Bot
```bash
cd bot
pip install -r requirements.txt
pip install pytest pytest-cov flake8
flake8 src/
pytest tests/ -v --cov=src
```

### Docker Build
```bash
cd bot
docker build -f config/docker/Dockerfile --build-arg BOT_CHARACTER=miya -t miya-bot .
docker build -f config/docker/Dockerfile --build-arg BOT_CHARACTER=eve -t eve-bot .
```

## トラブルシューティング

### よくあるエラー

#### 1. 認証エラー
```
Error: Could not load the default credentials
```
→ `GCP_SERVICE_ACCOUNT_KEY`シークレットが正しく設定されているか確認

#### 2. 権限エラー
```
Error: Permission denied
```
→ サービスアカウントに必要な権限が付与されているか確認

#### 3. Secret Manager エラー
```
Error: Secret not found
```
→ Secret Managerにシークレットが作成されているか確認

### デバッグ方法

1. **GitHub Actionsログの確認**
   - リポジトリの「Actions」タブでワークフロー実行結果を確認

2. **Cloud Loggingの確認**
   ```bash
   gcloud logging read "resource.type=cloud_run_revision" --limit=50
   ```

3. **ローカルでのテスト**
   - 各テストコマンドをローカルで実行して問題を特定

## パフォーマンス最適化

### キャッシュの活用
- Node.js: `cache: 'npm'`
- Python: `cache: 'pip'`
- Docker: `cache-from: type=gha`

### 並列実行
- テストジョブの並列実行
- マトリックス戦略によるマルチボットデプロイ

### リソース最適化
- Cloud Run: 最小限のCPU/メモリ設定
- Container Registry: 効率的なレイヤーキャッシュ

## 監視とアラート

### ヘルスチェック
- Firebase Hosting: `/health`エンドポイント
- Cloud Run: `/health`エンドポイント

### 通知
- Slack: デプロイ成功/失敗の通知
- GitHub Security: 脆弱性スキャン結果

### メトリクス
- Codecov: テストカバレッジ
- GitHub Actions: ビルド時間とステータス