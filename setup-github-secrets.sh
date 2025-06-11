#!/bin/bash

# GitHub Secrets セットアップスクリプト
# 事前に 'gh auth login' でGitHub CLIにログインしてください

set -e

echo "🔐 GitHub Secrets セットアップを開始します..."

# プロジェクト設定
PROJECT_ID="nyanco-bot"
FIREBASE_KEY_FILE="bot/nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json"

echo "📊 設定内容："
echo "  - GCP Project ID: $PROJECT_ID"
echo "  - Firebase Key File: $FIREBASE_KEY_FILE"

# GitHub CLI認証確認
if ! gh auth status > /dev/null 2>&1; then
    echo "❌ GitHub CLIの認証が必要です。以下のコマンドでログインしてください："
    echo "   gh auth login"
    exit 1
fi

echo "✅ GitHub CLI認証確認完了"

# Firebase関連Secrets
echo "🔥 Firebase関連Secretsを設定中..."

if [ -f "$FIREBASE_KEY_FILE" ]; then
    echo "  - FIREBASE_SERVICE_ACCOUNT"
    gh secret set FIREBASE_SERVICE_ACCOUNT < "$FIREBASE_KEY_FILE"
    
    echo "  - FIREBASE_PROJECT_ID"
    gh secret set FIREBASE_PROJECT_ID -b "$PROJECT_ID"
    
    echo "✅ Firebase Secrets設定完了"
else
    echo "❌ Firebase キーファイルが見つかりません: $FIREBASE_KEY_FILE"
    exit 1
fi

# GCP関連Secrets
echo "☁️ GCP関連Secretsを設定中..."

echo "  - GCP_PROJECT_ID"
gh secret set GCP_PROJECT_ID -b "$PROJECT_ID"

# サービスアカウントキーの作成（存在しない場合）
SERVICE_ACCOUNT_EMAIL="github-actions@${PROJECT_ID}.iam.gserviceaccount.com"
SERVICE_ACCOUNT_KEY_FILE="github-actions-key.json"

echo "  - サービスアカウントの確認/作成: $SERVICE_ACCOUNT_EMAIL"

# サービスアカウントが存在するかチェック
if ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" > /dev/null 2>&1; then
    echo "    サービスアカウントを作成中..."
    gcloud iam service-accounts create github-actions \
        --display-name="GitHub Actions CI/CD" \
        --description="CI/CD用のサービスアカウント"
else
    echo "    サービスアカウントは既に存在します"
fi

# 必要な権限の付与
echo "  - 権限の付与中..."
ROLES=(
    "roles/run.admin"
    "roles/storage.admin"
    "roles/secretmanager.secretAccessor"
    "roles/firebase.admin"
    "roles/aiplatform.user"
)

for ROLE in "${ROLES[@]}"; do
    echo "    - $ROLE"
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="$ROLE" \
        --quiet
done

# サービスアカウントキーの生成
echo "  - サービスアカウントキーを生成中..."
gcloud iam service-accounts keys create "$SERVICE_ACCOUNT_KEY_FILE" \
    --iam-account="$SERVICE_ACCOUNT_EMAIL" \
    --quiet

echo "  - GCP_SERVICE_ACCOUNT_KEY"
gh secret set GCP_SERVICE_ACCOUNT_KEY < "$SERVICE_ACCOUNT_KEY_FILE"

# セキュリティのためローカルキーファイルを削除
rm "$SERVICE_ACCOUNT_KEY_FILE"
echo "    ローカルキーファイルを削除しました"

echo "✅ GCP Secrets設定完了"

# Secret Managerにボット用設定を保存
echo "🤖 Secret Managerにボット設定を保存中..."

# 環境変数ファイルから値を読み込み
if [ -f "bot/.env" ]; then
    source bot/.env
    
    # Discord Bot Token (Miya)
    if [ ! -z "$DISCORD_BOT_TOKEN_MIYA" ] && [ "$DISCORD_BOT_TOKEN_MIYA" != "your_miya_discord_bot_token_here" ]; then
        echo "  - discord-bot-token-miya"
        echo "$DISCORD_BOT_TOKEN_MIYA" | gcloud secrets create discord-bot-token-miya \
            --data-file=- --replication-policy="automatic" 2>/dev/null || \
        echo "$DISCORD_BOT_TOKEN_MIYA" | gcloud secrets versions add discord-bot-token-miya \
            --data-file=- 2>/dev/null || echo "    既に設定済み"
    fi
    
    # Discord Bot Token (Eve)
    if [ ! -z "$DISCORD_BOT_TOKEN_EVE" ] && [ "$DISCORD_BOT_TOKEN_EVE" != "your_eve_discord_bot_token_here" ]; then
        echo "  - discord-bot-token-eve"
        echo "$DISCORD_BOT_TOKEN_EVE" | gcloud secrets create discord-bot-token-eve \
            --data-file=- --replication-policy="automatic" 2>/dev/null || \
        echo "$DISCORD_BOT_TOKEN_EVE" | gcloud secrets versions add discord-bot-token-eve \
            --data-file=- 2>/dev/null || echo "    既に設定済み"
    fi
    
    echo "✅ Discord Bot Tokens設定完了"
else
    echo "⚠️ bot/.env ファイルが見つかりません。手動でDiscord Bot Tokensを設定してください"
fi

# Firebase設定をSecret Managerに保存
echo "  - firebase-service-account"
gcloud secrets create firebase-service-account \
    --data-file="$FIREBASE_KEY_FILE" --replication-policy="automatic" 2>/dev/null || \
gcloud secrets versions add firebase-service-account \
    --data-file="$FIREBASE_KEY_FILE" 2>/dev/null || echo "    既に設定済み"

# Vertex AI設定
echo "  - gcp-project-id"
echo "$PROJECT_ID" | gcloud secrets create gcp-project-id \
    --data-file=- --replication-policy="automatic" 2>/dev/null || \
echo "$PROJECT_ID" | gcloud secrets versions add gcp-project-id \
    --data-file=- 2>/dev/null || echo "    既に設定済み"

echo "  - gcp-location"
echo "asia-northeast1" | gcloud secrets create gcp-location \
    --data-file=- --replication-policy="automatic" 2>/dev/null || \
echo "asia-northeast1" | gcloud secrets versions add gcp-location \
    --data-file=- 2>/dev/null || echo "    既に設定済み"

echo "✅ Secret Manager設定完了"

# 設定内容の確認
echo ""
echo "🎉 GitHub Secrets セットアップが完了しました！"
echo ""
echo "📋 設定されたSecrets："
gh secret list

echo ""
echo "📋 設定されたSecret Manager："
gcloud secrets list --filter="name:discord-bot-token OR name:firebase OR name:gcp"

echo ""
echo "🚀 次のステップ："
echo "1. プルリクエストを作成してCI/CDパイプラインをテスト"
echo "2. mainブランチにマージして本番デプロイをテスト"
echo "3. 必要に応じてSlack通知の設定"

echo ""
echo "📖 詳細情報："
echo "- CI/CD設定ガイド: docs/CI_CD_SETUP.md"
echo "- Secrets設定ガイド: docs/GITHUB_SECRETS_SETUP.md"
echo "- 動作確認レポート: docs/CI_CD_VERIFICATION_REPORT.md"