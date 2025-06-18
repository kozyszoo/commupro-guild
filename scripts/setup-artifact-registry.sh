#!/bin/bash
set -euo pipefail

# 色付き出力用の関数
print_info() {
    echo -e "\033[0;36m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

# プロジェクトIDの確認
if [ -z "${GCP_PROJECT_ID:-}" ]; then
    print_error "GCP_PROJECT_ID環境変数が設定されていません"
    echo "使用方法: GCP_PROJECT_ID=your-project-id ./scripts/setup-artifact-registry.sh"
    exit 1
fi

LOCATION="asia-northeast1"
REPOSITORY="docker-repo"

print_info "プロジェクト: $GCP_PROJECT_ID"
print_info "リージョン: $LOCATION"
print_info "リポジトリ名: $REPOSITORY"

# 現在のプロジェクトを設定
print_info "Google Cloudプロジェクトを設定中..."
gcloud config set project "$GCP_PROJECT_ID"

# Artifact Registry APIを有効化
print_info "Artifact Registry APIを有効化中..."
gcloud services enable artifactregistry.googleapis.com

# リポジトリの存在確認
print_info "既存のリポジトリを確認中..."
if gcloud artifacts repositories describe "$REPOSITORY" \
    --location="$LOCATION" &>/dev/null; then
    print_success "リポジトリ '$REPOSITORY' は既に存在します"
else
    # リポジトリの作成
    print_info "Artifact Registryリポジトリを作成中..."
    gcloud artifacts repositories create "$REPOSITORY" \
        --repository-format=docker \
        --location="$LOCATION" \
        --description="Docker images for Discord bots" \
        --async
    
    # 作成完了を待機
    print_info "リポジトリ作成の完了を待機中..."
    sleep 10
    
    # 作成確認
    if gcloud artifacts repositories describe "$REPOSITORY" \
        --location="$LOCATION" &>/dev/null; then
        print_success "リポジトリ '$REPOSITORY' を作成しました"
    else
        print_error "リポジトリの作成に失敗しました"
        exit 1
    fi
fi

# サービスアカウントの権限確認
SERVICE_ACCOUNT="${SERVICE_ACCOUNT_EMAIL:-github-actions@${GCP_PROJECT_ID}.iam.gserviceaccount.com}"
print_info "サービスアカウント: $SERVICE_ACCOUNT"

# 必要な権限を付与
print_info "サービスアカウントに権限を付与中..."

# Artifact Registry Writer権限
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/artifactregistry.writer" \
    --condition=None 2>/dev/null || true

# Storage Admin権限（レガシーGCR互換性のため）
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/storage.admin" \
    --condition=None 2>/dev/null || true

# Service Account Token Creator権限
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/iam.serviceAccountTokenCreator" \
    --condition=None 2>/dev/null || true

# Cloud Run Admin権限
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/run.admin" \
    --condition=None 2>/dev/null || true

# Service Account User権限（actAs権限のため）
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/iam.serviceAccountUser" \
    --condition=None 2>/dev/null || true

# Compute Service Account User権限（デフォルトCompute Engine SAを使用するため）
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/compute.serviceAgent" \
    --condition=None 2>/dev/null || true

print_success "GitHub Actionsサービスアカウントの権限付与が完了しました"

# Cloud Run用のデフォルトCompute Engine サービスアカウントの権限設定
COMPUTE_SA="${GCP_PROJECT_ID//-/}@developer.gserviceaccount.com"
if [[ "$GCP_PROJECT_ID" =~ ^[0-9]+$ ]]; then
    # プロジェクトIDが数値の場合
    COMPUTE_SA="${GCP_PROJECT_ID}-compute@developer.gserviceaccount.com"
else
    # プロジェクトIDが文字列の場合、数値部分を抽出
    PROJECT_NUMBER=$(gcloud projects describe "$GCP_PROJECT_ID" --format="value(projectNumber)" 2>/dev/null || echo "")
    if [ -n "$PROJECT_NUMBER" ]; then
        COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
    fi
fi

print_info "Cloud Run用Compute Engine サービスアカウント: $COMPUTE_SA"

# Secret Manager Secret Accessor権限をCompute Engine SAに付与
print_info "Secret Manager権限をCompute Engine サービスアカウントに付与中..."
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --condition=None 2>/dev/null || true

print_success "全ての権限の付与が完了しました"

# リポジトリ情報の表示
print_info "リポジトリ情報:"
echo "----------------------------------------"
echo "Docker push先:"
echo "  ${LOCATION}-docker.pkg.dev/${GCP_PROJECT_ID}/${REPOSITORY}/[IMAGE_NAME]:[TAG]"
echo ""
echo "Docker認証設定:"
echo "  gcloud auth configure-docker ${LOCATION}-docker.pkg.dev"
echo "----------------------------------------"

# 認証設定の確認
print_info "Docker認証を設定しますか？ (y/N)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    gcloud auth configure-docker "${LOCATION}-docker.pkg.dev" --quiet
    print_success "Docker認証設定が完了しました"
fi

print_success "Artifact Registryのセットアップが完了しました！"