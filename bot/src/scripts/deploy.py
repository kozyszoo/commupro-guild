#!/bin/bash
# Discord にゃんこエージェント ボット - Cloud Run デプロイスクリプト

set -e

# 色付きログ出力用の関数
log_info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

log_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

log_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

# 設定値
PROJECT_ID=${PROJECT_ID:-"nyanco-bot"}
REGION=${REGION:-"asia-northeast1"}
SERVICE_NAME="discord-nyanco-agent"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

log_info "Discord にゃんこエージェント ボットを Cloud Run にデプロイします"
log_info "プロジェクト ID: ${PROJECT_ID}"
log_info "リージョン: ${REGION}"
log_info "サービス名: ${SERVICE_NAME}"

# 環境変数ファイルの確認と作成
ENV_VARS_FILE="env_vars.yaml"
if [ -f "$ENV_VARS_FILE" ]; then
    log_info "既存の環境変数ファイル ($ENV_VARS_FILE) を使用します"
else
    log_info "環境変数ファイルを作成します"
    
    # 必要な環境変数の確認
    if [ -z "$DISCORD_BOT_TOKEN" ]; then
        log_error "DISCORD_BOT_TOKEN 環境変数が設定されていません"
        log_error "環境変数を設定するか、env_vars.yamlファイルを作成してください"
        exit 1
    fi

    if [ -z "$FIREBASE_SERVICE_ACCOUNT" ]; then
        log_error "FIREBASE_SERVICE_ACCOUNT 環境変数が設定されていません"
        log_error "環境変数を設定するか、env_vars.yamlファイルを作成してください"
        exit 1
    fi

    # 環境変数ファイルを作成
    cat > $ENV_VARS_FILE << EOF
DISCORD_BOT_TOKEN: "${DISCORD_BOT_TOKEN}"
FIREBASE_SERVICE_ACCOUNT: '${FIREBASE_SERVICE_ACCOUNT}'
PYTHONUNBUFFERED: "1"
EOF
fi

# Google Cloud プロジェクトの設定
log_info "Google Cloud プロジェクトを設定中..."
gcloud config set project ${PROJECT_ID}

# 必要なAPIの有効化
log_info "必要なAPIを有効化中..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Cloud Build を使用してDocker イメージをビルド（x86_64アーキテクチャ）
log_info "Cloud Build を使用してDocker イメージをビルド中..."
gcloud builds submit --tag ${IMAGE_NAME}:latest .

# Cloud Run にデプロイ
log_info "Cloud Run にデプロイ中..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --concurrency 1 \
    --max-instances 1 \
    --min-instances 1 \
    --port 8080 \
    --timeout 3600 \
    --env-vars-file $ENV_VARS_FILE

# デプロイ結果の確認
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

log_success "デプロイが完了しました！"
log_info "サービス URL: ${SERVICE_URL}"
log_info "ヘルスチェック: ${SERVICE_URL}/health"
log_info "ステータス確認: ${SERVICE_URL}/"

# ログの確認方法を表示
log_info ""
log_info "ログを確認するには以下のコマンドを実行してください:"
log_info "gcloud logs tail --follow --project=${PROJECT_ID} --resource-type=cloud_run_revision --resource-labels=service_name=${SERVICE_NAME}"

log_success "Discord にゃんこエージェント ボットが Cloud Run で稼働中です！"