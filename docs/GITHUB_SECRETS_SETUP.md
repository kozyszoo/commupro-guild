# GitHub Secrets セットアップガイド

このドキュメントでは、CI/CDパイプラインに必要なGitHub Secretsの設定方法について説明します。

## 必要なSecrets一覧

### Firebase関連
```
FIREBASE_SERVICE_ACCOUNT    # Firebase Admin SDKのJSON (必須)
FIREBASE_PROJECT_ID         # FirebaseプロジェクトID (必須)
```

### Google Cloud Platform関連
```
GCP_PROJECT_ID             # GCPプロジェクトID (必須)
GCP_SERVICE_ACCOUNT_KEY    # GCPサービスアカウントのJSON (必須)
```

### 通知関連 (オプション)
```
SLACK_WEBHOOK_URL          # Slack通知用WebhookURL
CODECOV_TOKEN             # Codecovトークン（パブリックリポジトリでは不要）
```

## セットアップ手順

### 1. GitHub CLI を使用した設定（推奨）

```bash
# Firebase関連
gh secret set FIREBASE_SERVICE_ACCOUNT < firebase-service-account.json
gh secret set FIREBASE_PROJECT_ID -b "your-firebase-project-id"

# Google Cloud関連
gh secret set GCP_PROJECT_ID -b "your-gcp-project-id"
gh secret set GCP_SERVICE_ACCOUNT_KEY < gcp-service-account.json

# 通知関連（オプション）
gh secret set SLACK_WEBHOOK_URL -b "https://hooks.slack.com/services/..."
gh secret set CODECOV_TOKEN -b "your-codecov-token"
```

### 2. GitHub Web UIを使用した設定

1. GitHubリポジトリのページを開く
2. **Settings** タブをクリック
3. 左サイドバーで **Secrets and variables** > **Actions** をクリック
4. **New repository secret** をクリック
5. Secret名と値を入力して **Add secret** をクリック

## Firebase Service Account の取得

1. [Firebase Console](https://console.firebase.google.com/) を開く
2. プロジェクトを選択
3. **プロジェクト設定** (歯車アイコン) をクリック
4. **サービスアカウント** タブを選択
5. **新しい秘密鍵の生成** をクリック
6. ダウンロードしたJSONファイルの内容をコピー
7. `FIREBASE_SERVICE_ACCOUNT` として設定

## GCP Service Account の設定

### 1. サービスアカウントの作成

```bash
# プロジェクトIDを設定
export PROJECT_ID="your-gcp-project-id"

# サービスアカウントの作成
gcloud iam service-accounts create github-actions \
    --display-name="GitHub Actions CI/CD" \
    --description="CI/CD用のサービスアカウント"

# サービスアカウントのメールアドレス
SERVICE_ACCOUNT_EMAIL="github-actions@${PROJECT_ID}.iam.gserviceaccount.com"
```

### 2. 必要な権限の付与

```bash
# Cloud Run Admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/run.admin"

# Container Registry Admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/storage.admin"

# Secret Manager Secret Accessor
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"

# Firebase Admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/firebase.admin"

# Vertex AI User
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/aiplatform.user"
```

### 3. キーファイルの生成

```bash
# キーファイルの生成
gcloud iam service-accounts keys create github-actions-key.json \
    --iam-account="${SERVICE_ACCOUNT_EMAIL}"

# キーファイルの内容をGitHub Secretsに設定
gh secret set GCP_SERVICE_ACCOUNT_KEY < github-actions-key.json

# セキュリティのためローカルファイルを削除
rm github-actions-key.json
```

## Secret Manager の設定

### ボット用のトークンとAPIキーを保存

```bash
# Discord Bot トークン
echo "your-miya-bot-token" | gcloud secrets create discord-bot-token-miya --data-file=-
echo "your-eve-bot-token" | gcloud secrets create discord-bot-token-eve --data-file=-

# Firebase サービスアカウント
gcloud secrets create firebase-service-account --data-file=firebase-service-account.json

# Vertex AI用プロジェクト設定
echo "your-gcp-project-id" | gcloud secrets create gcp-project-id --data-file=-
echo "us-central1" | gcloud secrets create gcp-location --data-file=-
```

## Slack 通知の設定 (オプション)

### 1. Slack Webhook URL の取得

1. [Slack API](https://api.slack.com/) にアクセス
2. **Create an app** をクリック
3. **From scratch** を選択
4. アプリ名とワークスペースを選択
5. **Incoming Webhooks** を有効化
6. **Add New Webhook to Workspace** をクリック
7. 通知先チャンネルを選択
8. 生成されたWebhook URLをコピー

### 2. GitHub Secrets に設定

```bash
gh secret set SLACK_WEBHOOK_URL -b "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
```

## セキュリティのベストプラクティス

### 1. 最小権限の原則
- 必要最小限の権限のみを付与
- 定期的な権限の見直し
- 未使用のサービスアカウントの削除

### 2. 定期的なローテーション
- サービスアカウントキーの定期的な更新
- アクセストークンの定期的な更新

### 3. 監査とモニタリング
- Cloud Audit Logs の有効化
- 異常なアクセスパターンの監視

## トラブルシューティング

### よくあるエラーと解決方法

#### 1. 認証エラー
```
Error: Could not load the default credentials
```
**解決方法**: `GCP_SERVICE_ACCOUNT_KEY` が正しく設定されているか確認

#### 2. 権限エラー
```
Error: Permission denied
```
**解決方法**: サービスアカウントに必要な権限が付与されているか確認

#### 3. Secret Manager エラー
```
Error: Secret not found
```
**解決方法**: Secret Manager にシークレットが正しく作成されているか確認

### デバッグ方法

1. **GitHub Actions ログの確認**
   - Actions タブでワークフロー実行結果を確認
   - エラーメッセージの詳細を確認

2. **GCP ログの確認**
   ```bash
   # Cloud Logging でエラーログを確認
   gcloud logging read "resource.type=cloud_run_revision" --limit=50
   ```

3. **ローカルでの認証テスト**
   ```bash
   # gcloud CLI での認証確認
   gcloud auth activate-service-account --key-file=service-account.json
   gcloud projects list
   ```

## 参考リンク

- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-for-github-actions/using-secrets-in-github-actions)
- [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)
- [Google Cloud Service Accounts](https://cloud.google.com/iam/docs/service-accounts-create)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)