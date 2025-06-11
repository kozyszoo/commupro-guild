#!/bin/bash

# Discord にゃんこエージェント ボット - GCP個別デプロイスクリプト
# 各ボットを別々のCloud Runサービスとしてデプロイ

set -e

# 設定
PROJECT_ID="nyanco-bot"
REGION="asia-northeast1"
IMAGE_PREFIX="gcr.io/${PROJECT_ID}/discord-nyanco"

echo "🐱 Discord にゃんこエージェント ボット - 個別デプロイ"
echo "プロジェクト: $PROJECT_ID"
echo "リージョン: $REGION"
echo "=" * 60

# 使用方法の表示
show_usage() {
    echo "使用方法:"
    echo "  $0 [コマンド] [ボット]"
    echo ""
    echo "コマンド:"
    echo "  build     - Dockerイメージをビルド"
    echo "  push      - Dockerイメージをpush"
    echo "  deploy    - Cloud Runにデプロイ"
    echo "  all       - build + push + deploy"
    echo ""
    echo "ボット:"
    echo "  miya      - みやにゃんのみ"
    echo "  eve       - イヴにゃんのみ"
    echo "  both      - 両方（デフォルト）"
    echo ""
    echo "例:"
    echo "  $0 all both      # 両方をビルド・プッシュ・デプロイ"
    echo "  $0 deploy miya   # みやにゃんのみデプロイ"
    echo "  $0 build eve     # イヴにゃんのみビルド"
}

# Docker認証設定
setup_docker_auth() {
    echo "🔐 Docker認証を設定中..."
    gcloud auth configure-docker --quiet
}

# Dockerイメージをビルド
build_image() {
    local bot_name=$1
    local image_tag="${IMAGE_PREFIX}-${bot_name}:latest"
    
    echo "🔨 ${bot_name}ボットのイメージをビルド中..."
    echo "タグ: $image_tag"
    
    docker build -f Dockerfile.single -t "$image_tag" .
    
    echo "✅ ${bot_name}ボットのビルド完了"
}

# Dockerイメージをpush
push_image() {
    local bot_name=$1
    local image_tag="${IMAGE_PREFIX}-${bot_name}:latest"
    
    echo "📦 ${bot_name}ボットのイメージをpush中..."
    echo "タグ: $image_tag"
    
    docker push "$image_tag"
    
    echo "✅ ${bot_name}ボットのpush完了"
}

# Cloud Runにデプロイ
deploy_service() {
    local bot_name=$1
    local service_name="discord-nyanco-agent-${bot_name}"
    local image_tag="${IMAGE_PREFIX}-${bot_name}:latest"
    
    echo "🚀 ${bot_name}ボットをCloud Runにデプロイ中..."
    echo "サービス名: $service_name"
    echo "イメージ: $image_tag"
    
    gcloud run deploy "$service_name" \
        --image="$image_tag" \
        --region="$REGION" \
        --platform=managed \
        --allow-unauthenticated \
        --memory=1Gi \
        --cpu=1 \
        --concurrency=1 \
        --max-instances=1 \
        --min-instances=1 \
        --port=8080 \
        --set-env-vars="BOT_CHARACTER=${bot_name}" \
        --set-env-vars="PYTHONUNBUFFERED=1" \
        --timeout=3600 \
        --quiet
    
    echo "✅ ${bot_name}ボットのデプロイ完了"
    
    # サービスURLを表示
    local service_url=$(gcloud run services describe "$service_name" --region="$REGION" --format="value(status.url)")
    echo "📱 サービスURL: $service_url"
}

# すべての処理を実行
deploy_all() {
    local bot_name=$1
    
    echo "🎯 ${bot_name}ボットの完全デプロイを開始..."
    
    build_image "$bot_name"
    push_image "$bot_name"
    deploy_service "$bot_name"
    
    echo "🎉 ${bot_name}ボットの完全デプロイ完了！"
}

# 引数の処理
COMMAND="${1:-all}"
BOT="${2:-both}"

# Docker認証を設定
setup_docker_auth

case "$COMMAND" in
    "build")
        case "$BOT" in
            "miya")
                build_image "miya"
                ;;
            "eve")
                build_image "eve"
                ;;
            "both")
                build_image "miya"
                build_image "eve"
                ;;
            *)
                echo "❌ 不正なボット指定: $BOT"
                show_usage
                exit 1
                ;;
        esac
        ;;
    
    "push")
        case "$BOT" in
            "miya")
                push_image "miya"
                ;;
            "eve")
                push_image "eve"
                ;;
            "both")
                push_image "miya"
                push_image "eve"
                ;;
            *)
                echo "❌ 不正なボット指定: $BOT"
                show_usage
                exit 1
                ;;
        esac
        ;;
    
    "deploy")
        case "$BOT" in
            "miya")
                deploy_service "miya"
                ;;
            "eve")
                deploy_service "eve"
                ;;
            "both")
                deploy_service "miya"
                deploy_service "eve"
                ;;
            *)
                echo "❌ 不正なボット指定: $BOT"
                show_usage
                exit 1
                ;;
        esac
        ;;
    
    "all")
        case "$BOT" in
            "miya")
                deploy_all "miya"
                ;;
            "eve")
                deploy_all "eve"
                ;;
            "both")
                deploy_all "miya"
                deploy_all "eve"
                ;;
            *)
                echo "❌ 不正なボット指定: $BOT"
                show_usage
                exit 1
                ;;
        esac
        ;;
    
    "help"|"-h"|"--help")
        show_usage
        ;;
    
    *)
        echo "❌ 不正なコマンド: $COMMAND"
        show_usage
        exit 1
        ;;
esac

echo ""
echo "🎊 処理が完了しました！"