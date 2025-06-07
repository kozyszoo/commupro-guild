#!/bin/bash

# Discord にゃんこエージェント ボット - 起動スクリプト
# 複数のボットを別々のDockerコンテナで起動

set -e

echo "🐱 Discord にゃんこエージェント ボット - 複数ボット起動"
echo "=" * 50

# .env ファイルの存在確認
if [ ! -f .env ]; then
    echo "❌ エラー: .env ファイルが見つかりません"
    echo "   .env.example を参考に .env ファイルを作成してください"
    exit 1
fi

# Docker Compose の存在確認
if ! command -v docker-compose &> /dev/null; then
    echo "❌ エラー: docker-compose が見つかりません"
    echo "   Docker Compose をインストールしてください"
    exit 1
fi

# 使用方法の表示
show_usage() {
    echo "使用方法:"
    echo "  $0 [コマンド]"
    echo ""
    echo "コマンド:"
    echo "  start     - すべてのボットを起動"
    echo "  stop      - すべてのボットを停止"
    echo "  restart   - すべてのボットを再起動"
    echo "  logs      - ログを表示"
    echo "  status    - ステータスを表示"
    echo "  build     - イメージを再ビルド"
    echo "  miya      - みやにゃんのみ起動"
    echo "  eve       - イヴにゃんのみ起動"
    echo ""
    echo "例:"
    echo "  $0 start    # すべてのボットを起動"
    echo "  $0 miya     # みやにゃんのみ起動"
    echo "  $0 logs     # ログを表示"
}

# 引数の処理
case "${1:-start}" in
    "start")
        echo "🚀 すべてのボットを起動中..."
        docker-compose up -d
        echo "✅ 起動完了"
        echo "📊 ステータス確認: $0 status"
        echo "📋 ログ確認: $0 logs"
        ;;
    
    "stop")
        echo "🛑 すべてのボットを停止中..."
        docker-compose down
        echo "✅ 停止完了"
        ;;
    
    "restart")
        echo "🔄 すべてのボットを再起動中..."
        docker-compose restart
        echo "✅ 再起動完了"
        ;;
    
    "logs")
        echo "📋 ログを表示中... (Ctrl+C で終了)"
        docker-compose logs -f
        ;;
    
    "status")
        echo "📊 ボットのステータス:"
        docker-compose ps
        ;;
    
    "build")
        echo "🔨 イメージを再ビルド中..."
        docker-compose build --no-cache
        echo "✅ ビルド完了"
        ;;
    
    "miya")
        echo "🐈 みやにゃんのみ起動中..."
        docker-compose up -d miya-bot
        echo "✅ みやにゃん起動完了"
        ;;
    
    "eve")
        echo "🐱 イヴにゃんのみ起動中..."
        docker-compose up -d eve-bot
        echo "✅ イヴにゃん起動完了"
        ;;
    
    "help"|"-h"|"--help")
        show_usage
        ;;
    
    *)
        echo "❌ 不正なコマンド: $1"
        show_usage
        exit 1
        ;;
esac