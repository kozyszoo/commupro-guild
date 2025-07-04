# GitHub Actions デプロイメント権限設定

## 必要なGoogle Cloud IAM権限

GitHub ActionsでDockerイメージをGCRにプッシュするためのサービスアカウント権限：

### GitHub Actionsサービスアカウント権限（推奨）
```
roles/storage.admin
roles/cloudbuild.builds.builder
roles/container.developer
roles/artifactregistry.writer
roles/iam.serviceAccountTokenCreator
roles/run.admin
roles/iam.serviceAccountUser
roles/compute.serviceAgent
```

### Cloud Run用Compute Engine サービスアカウント権限
```
roles/secretmanager.secretAccessor
```

### 最小権限セット（セキュリティ重視）
```
# Container Registry push用
roles/storage.objectAdmin
roles/container.developer

# サービスアカウント認証用  
iam.serviceAccounts.getAccessToken
iam.serviceAccountKeys.create
iam.serviceAccountKeys.get

# Cloud Run デプロイ用
roles/run.admin
roles/iam.serviceAccountUser
```

### 個別権限（最小権限原則）
```
# Google Container Registry (GCR)
storage.buckets.get
storage.buckets.create
storage.objects.create
storage.objects.delete
storage.objects.get
storage.objects.list

# Artifact Registry
artifactregistry.repositories.uploadArtifacts
artifactregistry.repositories.downloadArtifacts
artifactregistry.repositories.get
artifactregistry.repositories.list
artifactregistry.repositories.create

# Cloud Build
cloudbuild.builds.create
cloudbuild.builds.get
cloudbuild.builds.list

# Container Registry
container.images.create
container.images.get
container.images.list
container.images.push
```

## 権限設定コマンド

```bash
# プロジェクトIDを設定
export PROJECT_ID="your-project-id"
export SERVICE_ACCOUNT_EMAIL="github-actions@${PROJECT_ID}.iam.gserviceaccount.com"

# 基本権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/cloudbuild.builds.builder"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/container.developer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/artifactregistry.writer"

# サービスアカウント認証権限（重要）
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/iam.serviceAccountTokenCreator"

# Cloud Runデプロイ権限
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/iam.serviceAccountUser"

# Compute Engine Service Account権限（Cloud Runのデフォルトサービスアカウント使用のため）
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/compute.serviceAgent"

# Cloud Run用Compute Engine サービスアカウントにSecret Manager権限を付与
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/secretmanager.secretAccessor"
```

## トラブルシューティング

### "Permission 'iam.serviceAccounts.getAccessToken' denied" エラー
```bash
# 解決策：サービスアカウント認証権限を追加
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/iam.serviceAccountTokenCreator"
```

### "Permission 'iam.serviceaccounts.actAs' denied" エラー
```bash
# 解決策：Service Account User権限とCompute Service Agent権限を追加
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/compute.serviceAgent"
```

### Cloud RunでSecret Manager権限エラーが発生する場合
```bash
# 解決策：Compute Engine サービスアカウントにSecret Manager権限を追加
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/secretmanager.secretAccessor"
```

### "Permission denied" エラーの一般的な対処法
1. サービスアカウントキーが正しく設定されているか確認
2. 上記の権限が全て付与されているか確認
3. Artifact Registryが有効化されているか確認
4. サービスアカウントが存在し、アクティブであることを確認

### GitHub Actions認証エラーの対処
1. `GCP_SERVICE_ACCOUNT_KEY` secretが正しくbase64エンコードされているか確認
2. サービスアカウントキーのJSON形式が正しいか確認
3. プロジェクトIDが正しく設定されているか確認

## Artifact Registry セットアップ

### リポジトリ作成
```bash
# Docker用Artifact Registryリポジトリを作成
gcloud artifacts repositories create docker-repo \
    --repository-format=docker \
    --location=asia-northeast1 \
    --description="Docker images for Discord bots"

# リポジトリの確認
gcloud artifacts repositories list --location=asia-northeast1
```

### 権限確認コマンド
```bash
# 現在の権限を確認
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:${SERVICE_ACCOUNT_EMAIL}"

# Artifact Registryリポジトリの確認
gcloud artifacts repositories describe docker-repo \
    --location=asia-northeast1
```

## 最小権限設定例（推奨）

```yaml
# カスタムロール作成
gcloud iam roles create github_actions_deployer \
    --project=$PROJECT_ID \
    --title="GitHub Actions Deployer" \
    --description="Minimal permissions for GitHub Actions deployment" \
    --permissions="storage.buckets.get,storage.objects.create,storage.objects.get,storage.objects.list,container.images.create,container.images.push,artifactregistry.repositories.uploadArtifacts,cloudbuild.builds.create,run.services.create,run.services.get,run.services.update"
```