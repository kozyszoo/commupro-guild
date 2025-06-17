# GitHub Actions デプロイメント権限設定

## 必要なGoogle Cloud IAM権限

GitHub ActionsでDockerイメージをGCRにプッシュするためのサービスアカウント権限：

### 基本権限
```
roles/storage.admin
roles/cloudbuild.builds.builder
roles/container.developer
roles/artifactregistry.writer
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

# Cloud Runデプロイ権限
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/iam.serviceAccountUser"
```

## トラブルシューティング

### "Permission denied" エラーの場合
1. サービスアカウントキーが正しく設定されているか確認
2. 上記の権限が全て付与されているか確認
3. Artifact Registryが有効化されているか確認

### 権限確認コマンド
```bash
# 現在の権限を確認
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:${SERVICE_ACCOUNT_EMAIL}"
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