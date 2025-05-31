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
    """ヘルスチェックサーバーを開始"""
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"ヘルスチェックサーバーを開始: ポート {port}")
    
    # デバッグモードを無効にして本番環境用に設定
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    start_health_server()