#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
health.py
Discord にゃんこエージェント - ヘルスチェックユーティリティ

ヘルスチェックと監視を統合
- ヘルスチェックサーバー
- システム状態の監視
- ログ管理
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp
from aiohttp import web
from dotenv import load_dotenv

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('health')

class HealthServer:
    """ヘルスチェックサーバークラス"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8080):
        """初期化"""
        self.host = host
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        self.start_time = datetime.now()
        self.system_status = {
            'status': 'healthy',
            'uptime': 0,
            'last_check': None,
            'errors': []
        }
    
    def setup_routes(self):
        """ルートの設定"""
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/status', self.get_status)
        self.app.router.add_post('/status', self.update_status)
    
    async def health_check(self, request: web.Request) -> web.Response:
        """ヘルスチェックエンドポイント"""
        try:
            # システム状態の更新
            self.update_system_status()
            
            # レスポンスの作成
            response = {
                'status': self.system_status['status'],
                'uptime': self.system_status['uptime'],
                'last_check': self.system_status['last_check'].isoformat() if self.system_status['last_check'] else None
            }
            
            return web.json_response(response)
        except Exception as e:
            logger.error(f"ヘルスチェックエラー: {e}")
            return web.json_response(
                {'error': 'Internal Server Error'},
                status=500
            )
    
    async def get_status(self, request: web.Request) -> web.Response:
        """システム状態の取得"""
        try:
            return web.json_response(self.system_status)
        except Exception as e:
            logger.error(f"状態取得エラー: {e}")
            return web.json_response(
                {'error': 'Internal Server Error'},
                status=500
            )
    
    async def update_status(self, request: web.Request) -> web.Response:
        """システム状態の更新"""
        try:
            data = await request.json()
            
            # 状態の更新
            if 'status' in data:
                self.system_status['status'] = data['status']
            
            if 'errors' in data:
                self.system_status['errors'] = data['errors']
            
            self.system_status['last_check'] = datetime.now()
            
            return web.json_response(self.system_status)
        except Exception as e:
            logger.error(f"状態更新エラー: {e}")
            return web.json_response(
                {'error': 'Internal Server Error'},
                status=500
            )
    
    def update_system_status(self):
        """システム状態の更新"""
        # 稼働時間の計算
        uptime = (datetime.now() - self.start_time).total_seconds()
        self.system_status['uptime'] = uptime
        
        # 最終チェック時間の更新
        self.system_status['last_check'] = datetime.now()
        
        # エラーの確認
        if self.system_status['errors']:
            self.system_status['status'] = 'unhealthy'
        else:
            self.system_status['status'] = 'healthy'
    
    async def start(self):
        """サーバーの起動"""
        try:
            runner = web.AppRunner(self.app)
            await runner.setup()
            site = web.TCPSite(runner, self.host, self.port)
            await site.start()
            
            logger.info(f"ヘルスチェックサーバーを起動: http://{self.host}:{self.port}")
            
            # サーバーを実行し続ける
            while True:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"サーバー起動エラー: {e}")
            raise

class SystemMonitor:
    """システム監視クラス"""
    
    def __init__(self, health_server: HealthServer):
        """初期化"""
        self.health_server = health_server
        self.check_interval = 60  # 秒
    
    async def check_system_resources(self):
        """システムリソースの確認"""
        try:
            # CPU使用率の確認
            cpu_percent = await self.get_cpu_usage()
            
            # メモリ使用率の確認
            memory_percent = await self.get_memory_usage()
            
            # ディスク使用率の確認
            disk_percent = await self.get_disk_usage()
            
            # 結果の記録
            if any(percent > 90 for percent in [cpu_percent, memory_percent, disk_percent]):
                self.health_server.system_status['errors'].append({
                    'type': 'resource_usage',
                    'message': f'リソース使用率が高い: CPU {cpu_percent}%, メモリ {memory_percent}%, ディスク {disk_percent}%',
                    'timestamp': datetime.now().isoformat()
                })
            
            logger.info(f"システムリソース: CPU {cpu_percent}%, メモリ {memory_percent}%, ディスク {disk_percent}%")
        except Exception as e:
            logger.error(f"リソース確認エラー: {e}")
    
    async def get_cpu_usage(self) -> float:
        """CPU使用率の取得"""
        try:
            cmd = "top -l 1 | grep 'CPU usage' | awk '{print $3}' | sed 's/%//'"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return float(stdout.decode().strip())
        except Exception as e:
            logger.error(f"CPU使用率取得エラー: {e}")
            return 0.0
    
    async def get_memory_usage(self) -> float:
        """メモリ使用率の取得"""
        try:
            cmd = "top -l 1 | grep 'PhysMem' | awk '{print $2}' | sed 's/%//'"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return float(stdout.decode().strip())
        except Exception as e:
            logger.error(f"メモリ使用率取得エラー: {e}")
            return 0.0
    
    async def get_disk_usage(self) -> float:
        """ディスク使用率の取得"""
        try:
            cmd = "df -h / | tail -n 1 | awk '{print $5}' | sed 's/%//'"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return float(stdout.decode().strip())
        except Exception as e:
            logger.error(f"ディスク使用率取得エラー: {e}")
            return 0.0
    
    async def start_monitoring(self):
        """監視の開始"""
        try:
            while True:
                await self.check_system_resources()
                await asyncio.sleep(self.check_interval)
        except Exception as e:
            logger.error(f"監視エラー: {e}")
            raise

async def main():
    """メイン実行関数"""
    # 環境変数の読み込み
    load_dotenv()
    
    # ヘルスチェックサーバーの起動
    server = HealthServer()
    monitor = SystemMonitor(server)
    
    # サーバーとモニタリングを並行実行
    await asyncio.gather(
        server.start(),
        monitor.start_monitoring()
    )

if __name__ == '__main__':
    asyncio.run(main()) 