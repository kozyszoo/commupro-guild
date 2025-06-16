#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
daily_analytics.py
日次アナリティクスデータの収集と保存

Discordの日次活動データを収集してFirestoreに保存
"""

import discord
import datetime
import asyncio
import os
from typing import Dict, Any, List, Optional
from firebase_admin import firestore
from collections import Counter, defaultdict
import json

class DailyAnalytics:
    """日次アナリティクスデータの収集と管理"""
    
    def __init__(self, bot: discord.Client, firestore_client):
        self.bot = bot
        self.db = firestore_client
        
    async def collect_daily_analytics(self, date: Optional[datetime.date] = None) -> Dict[str, Any]:
        """指定日（デフォルトは今日）のアナリティクスデータを収集"""
        
        if date is None:
            date = datetime.date.today()
        
        # 対象日の開始と終了時刻（UTC）
        start_time = datetime.datetime.combine(date, datetime.time.min, tzinfo=datetime.timezone.utc)
        end_time = datetime.datetime.combine(date, datetime.time.max, tzinfo=datetime.timezone.utc)
        
        analytics_data = {
            'date': date.isoformat(),
            'timestamp': datetime.datetime.now(datetime.timezone.utc),
            'activeUsers': 0,
            'messageCount': 0,
            'newMembers': 0,
            'reengagements': 0,
            'topTopics': [],
            'channelActivity': {},
            'userActivity': {},
            'hourlyActivity': defaultdict(int),
            'topUsers': [],
            'reactions': {
                'total': 0,
                'types': defaultdict(int)
            }
        }
        
        try:
            # 1. メッセージデータの収集
            messages_ref = (self.db.collection('interactions')
                          .where('timestamp', '>=', start_time)
                          .where('timestamp', '<=', end_time)
                          .where('type', '==', 'message'))
            
            messages = await asyncio.to_thread(messages_ref.get)
            active_users = set()
            channel_messages = defaultdict(int)
            user_messages = defaultdict(int)
            keywords_counter = Counter()
            
            for doc in messages:
                data = doc.to_dict()
                analytics_data['messageCount'] += 1
                
                # アクティブユーザー
                user_id = data.get('userId')
                if user_id:
                    active_users.add(user_id)
                    user_messages[user_id] += 1
                
                # チャンネル別
                channel_name = data.get('channelName', 'Unknown')
                channel_messages[channel_name] += 1
                
                # 時間別アクティビティ
                timestamp = data.get('timestamp')
                if timestamp:
                    hour = timestamp.hour
                    analytics_data['hourlyActivity'][hour] += 1
                
                # キーワード収集
                keywords = data.get('keywords', [])
                for keyword in keywords:
                    keywords_counter[keyword] += 1
            
            analytics_data['activeUsers'] = len(active_users)
            
            # 2. チャンネルアクティビティ
            analytics_data['channelActivity'] = dict(channel_messages)
            
            # 3. トップユーザー（メッセージ数順）
            top_users = sorted(user_messages.items(), key=lambda x: x[1], reverse=True)[:10]
            analytics_data['topUsers'] = [
                {'userId': user_id, 'messageCount': count} 
                for user_id, count in top_users
            ]
            
            # 4. トップトピック（キーワード頻度順）
            top_keywords = keywords_counter.most_common(10)
            analytics_data['topTopics'] = [
                {'topic': keyword, 'count': count}
                for keyword, count in top_keywords
            ]
            
            # 5. 新規メンバー数（実際のGuildメンバー情報から取得）
            new_members_count = await self._count_new_members(start_time, end_time)
            analytics_data['newMembers'] = new_members_count
            
            # 6. リアクション統計
            reactions_ref = (self.db.collection('interactions')
                           .where('timestamp', '>=', start_time)
                           .where('timestamp', '<=', end_time)
                           .where('type', '==', 'reaction'))
            
            reactions = await asyncio.to_thread(reactions_ref.get)
            for doc in reactions:
                data = doc.to_dict()
                analytics_data['reactions']['total'] += 1
                reaction_type = data.get('reactionType', 'unknown')
                analytics_data['reactions']['types'][reaction_type] += 1
            
            # 7. 再エンゲージメント数（Bot Actions から）
            reengagements = await self._count_reengagements(start_time, end_time)
            analytics_data['reengagements'] = reengagements
            
            # 時間別アクティビティを通常の辞書に変換
            analytics_data['hourlyActivity'] = dict(analytics_data['hourlyActivity'])
            analytics_data['reactions']['types'] = dict(analytics_data['reactions']['types'])
            
            return analytics_data
            
        except Exception as e:
            print(f"❌ アナリティクスデータ収集エラー: {e}")
            return analytics_data
    
    async def _count_new_members(self, start_time: datetime.datetime, end_time: datetime.datetime) -> int:
        """新規メンバー数をカウント"""
        try:
            # Guildメンバー情報から新規参加者を取得
            new_members_ref = (self.db.collection('guild_members')
                             .where('joinedAt', '>=', start_time)
                             .where('joinedAt', '<=', end_time))
            
            new_members = await asyncio.to_thread(new_members_ref.get)
            return len(new_members)
            
        except Exception as e:
            print(f"新規メンバー数取得エラー: {e}")
            return 0
    
    async def _count_reengagements(self, start_time: datetime.datetime, end_time: datetime.datetime) -> int:
        """再エンゲージメント数をカウント"""
        try:
            # Bot Actionsから再エンゲージメントアクションを取得
            reengagement_ref = (self.db.collection('bot_actions')
                              .where('timestamp', '>=', start_time)
                              .where('timestamp', '<=', end_time)
                              .where('actionType', '==', 'reengagement_dm'))
            
            reengagements = await asyncio.to_thread(reengagement_ref.get)
            return len(reengagements)
            
        except Exception as e:
            print(f"再エンゲージメント数取得エラー: {e}")
            return 0
    
    async def save_daily_analytics(self, analytics_data: Dict[str, Any]) -> str:
        """日次アナリティクスデータをFirestoreに保存"""
        try:
            # analytics_sessions コレクションに保存
            doc_ref = await asyncio.to_thread(
                self.db.collection('analytics_sessions').add,
                analytics_data
            )
            
            analytics_id = doc_ref[1].id
            print(f"✅ 日次アナリティクスデータを保存: {analytics_id}")
            print(f"   日付: {analytics_data['date']}")
            print(f"   アクティブユーザー: {analytics_data['activeUsers']}")
            print(f"   メッセージ数: {analytics_data['messageCount']}")
            
            return analytics_id
            
        except Exception as e:
            print(f"❌ アナリティクスデータ保存エラー: {e}")
            return None
    
    async def run_daily_analytics(self) -> Dict[str, Any]:
        """日次アナリティクスの実行（収集と保存）"""
        print("📊 日次アナリティクスを開始...")
        
        # 今日のデータを収集
        analytics_data = await self.collect_daily_analytics()
        
        # データを保存
        analytics_id = await self.save_daily_analytics(analytics_data)
        
        result = {
            'success': analytics_id is not None,
            'analytics_id': analytics_id,
            'date': analytics_data['date'],
            'summary': {
                'activeUsers': analytics_data['activeUsers'],
                'messageCount': analytics_data['messageCount'],
                'newMembers': analytics_data['newMembers'],
                'reengagements': analytics_data['reengagements'],
                'topChannels': list(analytics_data['channelActivity'].keys())[:3]
            }
        }
        
        print("✅ 日次アナリティクス完了")
        return result
    
    async def get_analytics_for_date(self, date: datetime.date) -> Optional[Dict[str, Any]]:
        """指定日のアナリティクスデータを取得"""
        try:
            date_str = date.isoformat()
            
            # analytics_sessions から指定日のデータを取得
            analytics_ref = (self.db.collection('analytics_sessions')
                           .where('date', '==', date_str)
                           .limit(1))
            
            docs = await asyncio.to_thread(analytics_ref.get)
            
            if docs:
                return docs[0].to_dict()
            else:
                return None
                
        except Exception as e:
            print(f"❌ アナリティクスデータ取得エラー: {e}")
            return None