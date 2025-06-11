# Gemini API から Vertex AI への移行ガイド

## 概要
このドキュメントでは、Gemini API から Vertex AI への移行手順について説明します。

## 主な変更点

### 1. パッケージの変更
```bash
# 旧: Gemini API
google-generativeai==0.3.2

# 新: Vertex AI
google-cloud-aiplatform==1.38.1
vertexai==1.38.1
```

### 2. インポートの変更
```python
# 旧
import google.generativeai as genai

# 新
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel
```

### 3. 初期化の変更
```python
# 旧: API キーベース
genai.configure(api_key=api_key)
self.gemini_model = genai.GenerativeModel('gemini-1.5-flash-002')

# 新: サービスアカウントベース
aiplatform.init(project=project_id, location=location)
self.gemini_model = GenerativeModel('gemini-1.5-flash-002')
```

### 4. 環境変数の変更
```bash
# 旧
GEMINI_API_KEY=your_gemini_api_key_here

# 新
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1  # または他の利用可能なリージョン
```

## セットアップ手順

### 1. GCPプロジェクトの設定
```bash
# プロジェクトIDを設定
export GCP_PROJECT_ID="your-gcp-project-id"
gcloud config set project $GCP_PROJECT_ID

# Vertex AI APIを有効化
gcloud services enable aiplatform.googleapis.com
```

### 2. サービスアカウントの設定
Vertex AIはFirebaseと同じサービスアカウントを使用できます。既存のFirebaseサービスアカウントに以下の権限を追加してください：

```bash
# サービスアカウントに Vertex AI User ロールを付与
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:your-service-account@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

### 3. 環境変数の設定
`.env` ファイルを更新：
```bash
# GCP設定（Vertex AI用）
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1

# Firebase設定（既存）
FIREBASE_SERVICE_ACCOUNT=...
```

### 4. デプロイメントの更新
Cloud Run / Compute Engine へデプロイする際は、Secret Manager も更新が必要です：

```bash
# 新しいシークレットを作成
echo "your-gcp-project-id" | gcloud secrets create gcp-project-id --data-file=-
echo "us-central1" | gcloud secrets create gcp-location --data-file=-
```

## 利点

1. **統合認証**: Firebase と同じサービスアカウントを使用
2. **エンタープライズグレード**: より高い信頼性とスケーラビリティ
3. **リージョン選択**: データの場所を制御可能
4. **監査ログ**: GCP の統合監査ログ機能
5. **VPC対応**: プライベートエンドポイントのサポート

## 注意事項

1. **料金**: Vertex AI の料金体系は Gemini API と異なります。詳細は[料金ページ](https://cloud.google.com/vertex-ai/pricing)を参照してください。
2. **クォータ**: リージョンごとにクォータが設定されています。
3. **レイテンシ**: 選択したリージョンによってレスポンス時間が変わる可能性があります。

## トラブルシューティング

### 認証エラー
```
Error: 403 Permission denied on resource project
```
→ サービスアカウントに `roles/aiplatform.user` ロールが付与されているか確認

### APIが有効化されていない
```
Error: Vertex AI API has not been used in project
```
→ `gcloud services enable aiplatform.googleapis.com` を実行

### リージョンエラー
```
Error: Invalid location
```
→ [利用可能なリージョン](https://cloud.google.com/vertex-ai/docs/general/locations)を確認