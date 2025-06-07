#!/bin/bash

# Discord にゃんこエージェント ボット - GCP Compute Engine Docker Compose デプロイスクリプト
# Compute Engine上でdocker-composeを実行

set -e

# 設定
PROJECT_ID="nyanco-bot"
REGION="asia-northeast1"
ZONE="asia-northeast1-a"
INSTANCE_NAME="nyanco-bot-compose"
MACHINE_TYPE="e2-standard-2"  # 2 vCPU, 8GB RAM
BOOT_DISK_SIZE="50GB"
IMAGE_FAMILY="cos-stable"  # Container-Optimized OS

echo "🐱 Discord にゃんこエージェント ボット - GCP Compute Engine デプロイ"
echo "プロジェクト: $PROJECT_ID"
echo "リージョン: $REGION"
echo "ゾーン: $ZONE"
echo "インスタンス: $INSTANCE_NAME"
echo "=" * 70

# 使用方法の表示
show_usage() {
    echo "使用方法:"
    echo "  $0 [コマンド]"
    echo ""
    echo "コマンド:"
    echo "  create        - Compute Engineインスタンスを作成"
    echo "  setup         - インスタンスにdocker-composeをセットアップ"
    echo "  deploy        - ボットをデプロイ"
    echo "  start         - ボットを開始"
    echo "  stop          - ボットを停止"
    echo "  restart       - ボットを再起動"
    echo "  logs          - ログを表示"
    echo "  status        - ステータス確認"
    echo "  ssh           - インスタンスにSSH接続"
    echo "  delete        - インスタンスを削除"
    echo "  all           - create + setup + deploy + start"
    echo ""
    echo "例:"
    echo "  $0 all          # 全てを実行"
    echo "  $0 create       # インスタンスのみ作成"
    echo "  $0 deploy       # デプロイのみ実行"
}

# GCP認証確認
check_gcp_auth() {
    echo "🔐 GCP認証を確認中..."
    
    # プロジェクト設定
    gcloud config set project "$PROJECT_ID"
    
    # 認証確認
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 > /dev/null; then
        echo "❌ GCP認証が必要です"
        gcloud auth login
    fi
    
    # 必要なAPIを有効化
    echo "📡 必要なAPIを有効化中..."
    gcloud services enable compute.googleapis.com
    gcloud services enable container.googleapis.com
    gcloud services enable secretmanager.googleapis.com
    
    echo "✅ GCP認証確認完了"
}

# Secret Manager にシークレットを作成
setup_secrets() {
    echo "🔒 Secret Manager にシークレットを設定中..."
    
    # .env ファイルから環境変数を読み込み
    if [ -f .env ]; then
        source .env
        
        # Discord トークンをSecret Managerに保存
        if [ ! -z "$DISCORD_BOT_TOKEN_MIYA" ]; then
            echo "$DISCORD_BOT_TOKEN_MIYA" | gcloud secrets create discord-bot-token-miya \
                --data-file=- --replication-policy="automatic" || \
            echo "$DISCORD_BOT_TOKEN_MIYA" | gcloud secrets versions add discord-bot-token-miya \
                --data-file=-
        fi
        
        if [ ! -z "$DISCORD_BOT_TOKEN_EVE" ]; then
            echo "$DISCORD_BOT_TOKEN_EVE" | gcloud secrets create discord-bot-token-eve \
                --data-file=- --replication-policy="automatic" || \
            echo "$DISCORD_BOT_TOKEN_EVE" | gcloud secrets versions add discord-bot-token-eve \
                --data-file=-
        fi
        
        # Firebase設定をSecret Managerに保存
        if [ ! -z "$FIREBASE_SERVICE_ACCOUNT" ]; then
            echo "$FIREBASE_SERVICE_ACCOUNT" | gcloud secrets create firebase-service-account \
                --data-file=- --replication-policy="automatic" || \
            echo "$FIREBASE_SERVICE_ACCOUNT" | gcloud secrets versions add firebase-service-account \
                --data-file=-
        fi
        
        # Gemini API KeyをSecret Managerに保存
        if [ ! -z "$GEMINI_API_KEY" ]; then
            echo "$GEMINI_API_KEY" | gcloud secrets create gemini-api-key \
                --data-file=- --replication-policy="automatic" || \
            echo "$GEMINI_API_KEY" | gcloud secrets versions add gemini-api-key \
                --data-file=-
        fi
        
        echo "✅ Secret Manager セットアップ完了"
    else
        echo "⚠️ .env ファイルが見つかりません。手動でSecret Managerを設定してください"
    fi
}

# Compute Engine インスタンス作成
create_instance() {
    echo "🖥️ Compute Engine インスタンスを作成中..."
    
    # ファイアウォールルールを作成
    gcloud compute firewall-rules create nyanco-bot-http \
        --allow tcp:80,tcp:443,tcp:8081,tcp:8082 \
        --source-ranges 0.0.0.0/0 \
        --description "Allow HTTP/HTTPS and bot ports for nyanco-bot" || true
    
    # インスタンス作成
    gcloud compute instances create "$INSTANCE_NAME" \
        --zone="$ZONE" \
        --machine-type="$MACHINE_TYPE" \
        --network-tier=PREMIUM \
        --maintenance-policy=MIGRATE \
        --service-account="$(gcloud config get-value account)" \
        --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append,https://www.googleapis.com/auth/cloud-platform \
        --tags=nyanco-bot,http-server,https-server \
        --image-family="$IMAGE_FAMILY" \
        --image-project=cos-cloud \
        --boot-disk-size="$BOOT_DISK_SIZE" \
        --boot-disk-type=pd-standard \
        --boot-disk-device-name="$INSTANCE_NAME" \
        --labels=app=nyanco-bot,environment=production
    
    echo "✅ インスタンス作成完了"
    
    # インスタンスの準備完了を待機
    echo "⏳ インスタンスの起動を待機中..."
    sleep 30
}

# インスタンスセットアップ
setup_instance() {
    echo "🔧 インスタンスをセットアップ中..."
    
    # セットアップスクリプト作成
    cat > setup_script.sh << 'EOF'
#!/bin/bash
set -e

echo "📦 必要なパッケージをインストール中..."

# Docker Compose インストール
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 作業ディレクトリ作成
sudo mkdir -p /opt/nyanco-bot/logs
sudo mkdir -p /opt/nyanco-bot/ssl
sudo chown -R $(whoami):$(whoami) /opt/nyanco-bot

# GCPログドライバーのセットアップ
docker plugin install gcplogs || true

echo "✅ セットアップ完了"
EOF

    # スクリプトをインスタンスに送信・実行
    gcloud compute scp setup_script.sh "$INSTANCE_NAME":~/setup.sh --zone="$ZONE"
    gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command="chmod +x ~/setup.sh && ~/setup.sh"
    
    # クリーンアップ
    rm setup_script.sh
    
    echo "✅ インスタンスセットアップ完了"
}

# ボットデプロイ
deploy_bots() {
    echo "🚀 ボットをデプロイ中..."
    
    # 設定ファイルをインスタンスに送信
    gcloud compute scp docker-compose.gcp.yml "$INSTANCE_NAME":~/docker-compose.yml --zone="$ZONE"
    gcloud compute scp nginx.conf "$INSTANCE_NAME":~/nginx.conf --zone="$ZONE"
    
    # 環境変数ファイル作成
    create_env_file() {
        cat > gcp.env << EOF
DISCORD_BOT_TOKEN_MIYA=$(gcloud secrets versions access latest --secret="discord-bot-token-miya" || echo "")
DISCORD_BOT_TOKEN_EVE=$(gcloud secrets versions access latest --secret="discord-bot-token-eve" || echo "")
FIREBASE_SERVICE_ACCOUNT=$(gcloud secrets versions access latest --secret="firebase-service-account" || echo "")
GEMINI_API_KEY=$(gcloud secrets versions access latest --secret="gemini-api-key" || echo "")
EOF
        gcloud compute scp gcp.env "$INSTANCE_NAME":~/.env --zone="$ZONE"
        rm gcp.env
    }
    
    create_env_file
    
    # Docker イメージをプル
    gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command="docker pull gcr.io/$PROJECT_ID/discord-nyanco-agent-miya:latest || echo 'Image not found, please build and push first'"
    gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command="docker pull gcr.io/$PROJECT_ID/discord-nyanco-agent-eve:latest || echo 'Image not found, please build and push first'"
    
    echo "✅ デプロイ完了"
}

# ボット開始
start_bots() {
    echo "▶️ ボットを開始中..."
    gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command="cd ~ && docker-compose up -d"
    echo "✅ ボット開始完了"
}

# ボット停止
stop_bots() {
    echo "⏹️ ボットを停止中..."
    gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command="cd ~ && docker-compose down"
    echo "✅ ボット停止完了"
}

# ボット再起動
restart_bots() {
    echo "🔄 ボットを再起動中..."
    gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command="cd ~ && docker-compose restart"
    echo "✅ ボット再起動完了"
}

# ログ表示
show_logs() {
    echo "📋 ログを表示中..."
    gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command="cd ~ && docker-compose logs -f"
}

# ステータス確認
show_status() {
    echo "📊 ステータス確認中..."
    
    # インスタンスの状態
    echo "🖥️ インスタンス状態:"
    gcloud compute instances describe "$INSTANCE_NAME" --zone="$ZONE" --format="table(status,machineType,selfLink.scope(zones))"
    
    # コンテナの状態
    echo ""
    echo "🐳 コンテナ状態:"
    gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command="cd ~ && docker-compose ps" || echo "Docker Compose not running"
    
    # 外部IP取得
    echo ""
    echo "🌐 アクセス情報:"
    EXTERNAL_IP=$(gcloud compute instances describe "$INSTANCE_NAME" --zone="$ZONE" --format="value(networkInterfaces[0].accessConfigs[0].natIP)")
    echo "External IP: $EXTERNAL_IP"
    echo "Health Check: http://$EXTERNAL_IP/health"
    echo "Miya Bot: http://$EXTERNAL_IP/miya/health"
    echo "Eve Bot: http://$EXTERNAL_IP/eve/health"
}

# SSH接続
ssh_instance() {
    echo "🔗 インスタンスにSSH接続中..."
    gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE"
}

# インスタンス削除
delete_instance() {
    echo "🗑️ インスタンスを削除中..."
    read -p "本当にインスタンス '$INSTANCE_NAME' を削除しますか? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gcloud compute instances delete "$INSTANCE_NAME" --zone="$ZONE" --quiet
        echo "✅ インスタンス削除完了"
    else
        echo "❌ 削除をキャンセルしました"
    fi
}

# 引数の処理
COMMAND="${1:-help}"

# GCP認証確認
check_gcp_auth

case "$COMMAND" in
    "create")
        setup_secrets
        create_instance
        ;;
    
    "setup")
        setup_instance
        ;;
    
    "deploy")
        deploy_bots
        ;;
    
    "start")
        start_bots
        ;;
    
    "stop")
        stop_bots
        ;;
    
    "restart")
        restart_bots
        ;;
    
    "logs")
        show_logs
        ;;
    
    "status")
        show_status
        ;;
    
    "ssh")
        ssh_instance
        ;;
    
    "delete")
        delete_instance
        ;;
    
    "all")
        setup_secrets
        create_instance
        setup_instance
        deploy_bots
        start_bots
        show_status
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