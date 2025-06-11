#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scheduler.py
週次コンテンツ制作スケジューラー

毎週決まった時間に自動でエンタメコンテンツを生成・投稿するスケジューラー
"""

import asyncio
import datetime
import os
from typing import Optional, Dict, Any, List
import schedule
import time
import threading
from firebase_admin import firestore
from .content_creator import ContentCreator

class WeeklyContentScheduler:
    """週次コンテンツ制作スケジューラー"""
    
    def __init__(self, firestore_client, discord_bot=None):
        self.db = firestore_client
        self.bot = discord_bot
        self.content_creator = ContentCreator(firestore_client, discord_bot)
        
        # スケジュール設定
        self.schedule_day = os.getenv('WEEKLY_SCHEDULE_DAY', 'monday')  # デフォルト: 月曜日
        self.schedule_time = os.getenv('WEEKLY_SCHEDULE_TIME', '09:00')  # デフォルト: 9:00
        
        # スケジューラーの状態
        self.is_running = False
        self.scheduler_thread = None
        
        print(f"📅 スケジューラー設定: 毎週{self.schedule_day} {self.schedule_time}")
    
    def setup_schedule(self):
        """スケジュールを設定"""
        try:
            # 既存のスケジュールをクリア
            schedule.clear()
            
            # 曜日に応じてスケジュール設定
            day_methods = {
                'monday': schedule.every().monday,
                'tuesday': schedule.every().tuesday,
                'wednesday': schedule.every().wednesday,
                'thursday': schedule.every().thursday,
                'friday': schedule.every().friday,
                'saturday': schedule.every().saturday,
                'sunday': schedule.every().sunday
            }
            
            if self.schedule_day.lower() in day_methods:
                day_schedule = day_methods[self.schedule_day.lower()]
                day_schedule.at(self.schedule_time).do(self._run_weekly_task)
                print(f"✅ スケジュール設定完了: 毎週{self.schedule_day} {self.schedule_time}")
            else:
                print(f"❌ 無効な曜日設定: {self.schedule_day}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ スケジュール設定エラー: {e}")
            return False
    
    def _run_weekly_task(self):
        """週次タスクの実行（同期ラッパー）"""
        print("📅 定期実行: 週次コンテンツ制作を開始...")
        
        try:
            # 非同期タスクを同期実行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._async_weekly_task())
            loop.close()
            
            return result
            
        except Exception as e:
            print(f"❌ 週次タスク実行エラー: {e}")
            return False
    
    async def _async_weekly_task(self) -> Dict[str, Any]:
        """非同期週次タスクの実行"""
        try:
            # 実行ログ記録
            await self._log_execution_start()
            
            # コンテンツ制作実行
            result = await self.content_creator.create_weekly_content()
            
            # 実行結果記録
            await self._log_execution_result(result)
            
            if result['success']:
                print("✅ 定期実行完了: 週次コンテンツ制作成功")
            else:
                print(f"❌ 定期実行完了: コンテンツ制作失敗 - {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            error_result = {'success': False, 'error': str(e)}
            await self._log_execution_result(error_result)
            print(f"❌ 週次タスクエラー: {e}")
            return error_result
    
    async def _log_execution_start(self):
        """実行開始ログ"""
        try:
            log_data = {
                'type': 'weekly_scheduler_start',
                'timestamp': datetime.datetime.now(datetime.timezone.utc),
                'scheduled_day': self.schedule_day,
                'scheduled_time': self.schedule_time
            }
            
            await asyncio.to_thread(self.db.collection('scheduler_logs').add, log_data)
            
        except Exception as e:
            print(f"⚠️ 実行開始ログエラー: {e}")
    
    async def _log_execution_result(self, result: Dict[str, Any]):
        """実行結果ログ"""
        try:
            log_data = {
                'type': 'weekly_scheduler_result',
                'timestamp': datetime.datetime.now(datetime.timezone.utc),
                'success': result.get('success', False),
                'error': result.get('error'),
                'summary_id': result.get('summary_id'),
                'discord_posted': result.get('discord_posted', False),
                'stats': result.get('stats', {})
            }
            
            await asyncio.to_thread(self.db.collection('scheduler_logs').add, log_data)
            
        except Exception as e:
            print(f"⚠️ 実行結果ログエラー: {e}")
    
    def start_scheduler(self):
        """スケジューラーを開始"""
        if self.is_running:
            print("⚠️ スケジューラーは既に実行中です")
            return False
        
        if not self.setup_schedule():
            print("❌ スケジュール設定に失敗しました")
            return False
        
        self.is_running = True
        
        def run_scheduler():
            """スケジューラー実行ループ"""
            print("🚀 スケジューラー開始...")
            while self.is_running:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # 1分間隔でチェック
                except Exception as e:
                    print(f"❌ スケジューラーループエラー: {e}")
                    time.sleep(60)
            
            print("⏹️ スケジューラー停止")
        
        # 別スレッドでスケジューラーを実行
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        print("✅ スケジューラー開始完了")
        return True
    
    def stop_scheduler(self):
        """スケジューラーを停止"""
        if not self.is_running:
            print("⚠️ スケジューラーは実行されていません")
            return False
        
        self.is_running = False
        
        # スケジュールをクリア
        schedule.clear()
        
        # スレッドの終了を待機（最大10秒）
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=10)
        
        print("✅ スケジューラー停止完了")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """スケジューラーの状態を取得"""
        next_run = None
        if self.is_running and schedule.jobs:
            next_run = schedule.next_run()
            if next_run:
                next_run = next_run.isoformat()
        
        return {
            'is_running': self.is_running,
            'schedule_day': self.schedule_day,
            'schedule_time': self.schedule_time,
            'next_run': next_run,
            'jobs_count': len(schedule.jobs)
        }
    
    async def run_manual_task(self) -> Dict[str, Any]:
        """手動でコンテンツ制作タスクを実行"""
        print("🔧 手動実行: 週次コンテンツ制作を開始...")
        
        try:
            # 手動実行ログ
            log_data = {
                'type': 'weekly_manual_execution',
                'timestamp': datetime.datetime.now(datetime.timezone.utc)
            }
            await asyncio.to_thread(self.db.collection('scheduler_logs').add, log_data)
            
            # コンテンツ制作実行
            result = await self.content_creator.create_weekly_content()
            
            # 結果ログ
            await self._log_execution_result(result)
            
            if result['success']:
                print("✅ 手動実行完了: 週次コンテンツ制作成功")
            else:
                print(f"❌ 手動実行失敗: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            error_result = {'success': False, 'error': str(e)}
            await self._log_execution_result(error_result)
            print(f"❌ 手動実行エラー: {e}")
            return error_result
    
    async def get_recent_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """最近のスケジューラーログを取得"""
        try:
            logs_ref = (self.db.collection('scheduler_logs')
                       .order_by('timestamp', direction=firestore.Query.DESCENDING)
                       .limit(limit))
            
            docs = await asyncio.to_thread(logs_ref.get)
            logs = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                logs.append(data)
            
            return logs
            
        except Exception as e:
            print(f"❌ ログ取得エラー: {e}")
            return []
    
    def update_schedule(self, day: Optional[str] = None, time: Optional[str] = None) -> bool:
        """スケジュール設定を更新"""
        try:
            if day:
                self.schedule_day = day
            if time:
                self.schedule_time = time
            
            print(f"📅 スケジュール更新: 毎週{self.schedule_day} {self.schedule_time}")
            
            # 実行中の場合は再設定
            if self.is_running:
                self.setup_schedule()
            
            return True
            
        except Exception as e:
            print(f"❌ スケジュール更新エラー: {e}")
            return False


class SchedulerManager:
    """スケジューラー管理クラス（Bot統合用）"""
    
    def __init__(self, firestore_client, discord_bot=None):
        self.scheduler = WeeklyContentScheduler(firestore_client, discord_bot)
        self.commands_enabled = True
    
    async def handle_scheduler_command(self, message, command_parts: List[str]) -> str:
        """スケジューラー関連のコマンドを処理"""
        if not self.commands_enabled:
            return "スケジューラーコマンドは無効です"
        
        if len(command_parts) < 2:
            return self._get_help_message()
        
        action = command_parts[1].lower()
        
        try:
            if action == 'start':
                success = self.scheduler.start_scheduler()
                return "✅ スケジューラーを開始しました" if success else "❌ スケジューラー開始に失敗しました"
            
            elif action == 'stop':
                success = self.scheduler.stop_scheduler()
                return "✅ スケジューラーを停止しました" if success else "❌ スケジューラー停止に失敗しました"
            
            elif action == 'status':
                status = self.scheduler.get_status()
                return self._format_status(status)
            
            elif action == 'run':
                result = await self.scheduler.run_manual_task()
                return "✅ 手動実行完了" if result['success'] else f"❌ 手動実行失敗: {result.get('error', 'Unknown error')}"
            
            elif action == 'logs':
                logs = await self.scheduler.get_recent_logs(5)
                return self._format_logs(logs)
            
            elif action == 'set' and len(command_parts) >= 4:
                day = command_parts[2]
                time = command_parts[3]
                success = self.scheduler.update_schedule(day, time)
                return f"✅ スケジュール更新: 毎週{day} {time}" if success else "❌ スケジュール更新に失敗しました"
            
            else:
                return self._get_help_message()
                
        except Exception as e:
            return f"❌ コマンド実行エラー: {e}"
    
    def _get_help_message(self) -> str:
        """ヘルプメッセージを生成"""
        return """📅 スケジューラーコマンド:
`!scheduler start` - スケジューラー開始
`!scheduler stop` - スケジューラー停止  
`!scheduler status` - 状態確認
`!scheduler run` - 手動実行
`!scheduler logs` - 実行ログ表示
`!scheduler set <曜日> <時刻>` - スケジュール設定
例: `!scheduler set monday 09:00`"""
    
    def _format_status(self, status: Dict[str, Any]) -> str:
        """状態情報をフォーマット"""
        running_text = "✅ 実行中" if status['is_running'] else "⏹️ 停止中"
        next_run_text = status['next_run'] if status['next_run'] else "未設定"
        
        return f"""📅 スケジューラー状態:
状態: {running_text}
設定: 毎週{status['schedule_day']} {status['schedule_time']}
次回実行: {next_run_text}
登録ジョブ数: {status['jobs_count']}"""
    
    def _format_logs(self, logs: List[Dict[str, Any]]) -> str:
        """ログ情報をフォーマット"""
        if not logs:
            return "📋 実行ログがありません"
        
        log_lines = ["📋 最近の実行ログ:"]
        for log in logs[:5]:
            timestamp = log.get('timestamp', 'Unknown')
            log_type = log.get('type', 'unknown')
            success = log.get('success')
            
            if success is not None:
                status_icon = "✅" if success else "❌"
                log_lines.append(f"{status_icon} {timestamp} - {log_type}")
            else:
                log_lines.append(f"📝 {timestamp} - {log_type}")
        
        return "\n".join(log_lines)