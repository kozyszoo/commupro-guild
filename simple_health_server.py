#!/usr/bin/env python3
"""
簡単なヘルスチェックサーバー（テスト用）
Cloud Run の要求に応答するシンプルなHTTPサーバー
"""

import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def health_check():
    """ヘルスチェックエンドポイント"""
    return jsonify({
        'status': 'healthy',
        'service': 'discord-bot-test'
    })

@app.route('/health')
def health():
    """Cloud Run ヘルスチェック用"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting health server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)