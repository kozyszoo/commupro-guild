#!/usr/bin/env python3
"""
Cloud Run ヘルスチェック用 HTTP サーバー
Discord ボットと並行して動作し、Cloud Run の要求に応答します
"""

import os
import threading
import time
from flask import Flask, jsonify
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ボットの状態を追跡
bot_status = {
    'is_running': False,
    'last_heartbeat': None,
    'start_time': time.time()
}

@app.route('/')
def health_check():
    """ヘルスチェックエンドポイント"""
    return jsonify({
        'status': 'healthy',
        'service': 'discord-nyanco-agent',
        'uptime': time.time() - bot_status['start_time'],
        'bot_running': bot_status['is_running'],
        'last_heartbeat': bot_status['last_heartbeat']
    })

@app.route('/health')
def health():
    """Cloud Run ヘルスチェック用"""
    return jsonify({'status': 'ok'})

@app.route('/ready')
def ready():
    """レディネスプローブ用"""
    if bot_status['is_running']:
        return jsonify({'status': 'ready'})
    else:
        return jsonify({'status': 'not ready'}), 503

def update_bot_status(is_running: bool):
    """ボットの状態を更新"""
    bot_status['is_running'] = is_running
    bot_status['last_heartbeat'] = time.time()

def start_health_server():
    """ヘルスチェックサーバーを開始（非同期対応）"""
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"ヘルスチェックサーバーを開始: ポート {port}")
    
    try:
        # WSGIサーバーとして実行（本番環境対応）
        from werkzeug.serving import make_server
        server = make_server('0.0.0.0', port, app, threaded=True)
        logger.info(f"HTTPサーバーがポート {port} で待機中...")
        server.serve_forever()
    except ImportError:
        # werkzeugが利用できない場合はFlaskの開発サーバーを使用
        logger.warning("werkzeugが利用できないため、開発サーバーを使用します")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        logger.error(f"ヘルスサーバーの起動に失敗: {e}")
        raise

if __name__ == '__main__':
    start_health_server()