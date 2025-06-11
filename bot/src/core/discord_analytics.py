#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
discord_analytics.py
Discord アクティビティ分析・まとめ生成機能

Discord内のアクションに対するまとめ情報生成、週次レポート作成
"""

import discord
import datetime
import asyncio
import os
import json
import re
from typing import List, Dict, Any, Optional
from firebase_admin import firestore
from collections import Counter, defaultdict
import vertexai
from vertexai.generative_models import GenerativeModel

class DiscordAnalytics:
    """Discord活動データの分析とまとめ生成"""
    
    def __init__(self, firestore_client):
        self.db = firestore_client
        
        # Vertex AIの初期化
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'nyanco-bot')
        location = os.getenv('GOOGLE_CLOUD_LOCATION', 'asia-northeast1')
        vertexai.init(project=project_id, location=location)
        
        # Geminiモデルの設定
        self.model = GenerativeModel("gemini-1.5-flash")
        
        # ボット設定
        self.bot_personas = {
            'bot1': {
                'name': 'みやにゃん',
                'personality': 'フレンドリーで好奇心旺盛、新しい技術や話題に興味津々',
                'speaking_style': 'だにゃ、にゃ〜、だよにゃ',
                'role': 'コミュニティの盛り上げ役'
            },
            'bot2': {
                'name': 'イヴにゃん', 
                'personality': 'クールで分析的、データや統計の解釈が得意',
                'speaking_style': 'ですにゃ、なのにゃ、ですね',
                'role': 'データ分析とインサイト提供'
            },
            'bot3': {
                'name': 'ナレにゃん',
                'personality': '司会進行が得意で、まとめるのが上手',
                'speaking_style': 'ですね、でしょう、ということで',
                'role': 'まとめと進行役'
            }
        }
    
    async def collect_weekly_activities(self, days: int = 7) -> Dict[str, Any]:
        """週間のDiscordアクティビティを収集"""
        cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
        
        activities = {
            'messages': [],
            'reactions': [],
            'voice_activities': [],
            'events': [],
            'user_activities': defaultdict(list),
            'channel_activities': defaultdict(list),
            'summary_stats': {}
        }
        
        try:
            # メッセージアクティビティ収集
            interactions_ref = (self.db.collection('interactions')
                              .where('timestamp', '>=', cutoff_date)
                              .order_by('timestamp', direction=firestore.Query.DESCENDING)
                              .limit(500))
            
            docs = await asyncio.to_thread(interactions_ref.get)
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                activities['messages'].append(data)
                
                # ユーザー別アクティビティ
                username = data.get('username', 'Unknown')
                activities['user_activities'][username].append(data)
                
                # チャンネル別アクティビティ
                channel = data.get('channelName', 'Unknown')
                activities['channel_activities'][channel].append(data)
            
            # イベントデータ収集
            events_ref = (self.db.collection('events')
                         .where('updatedAt', '>=', cutoff_date)
                         .order_by('updatedAt', direction=firestore.Query.DESCENDING))
            
            event_docs = await asyncio.to_thread(events_ref.get)
            for doc in event_docs:
                data = doc.to_dict()
                data['id'] = doc.id
                activities['events'].append(data)
            
            # 統計情報生成
            activities['summary_stats'] = self._generate_summary_stats(activities)
            
            return activities
            
        except Exception as e:
            print(f"❌ アクティビティ収集エラー: {e}")
            return activities
    
    def _generate_summary_stats(self, activities: Dict[str, Any]) -> Dict[str, Any]:
        """アクティビティの統計情報を生成"""
        stats = {
            'total_messages': len(activities['messages']),
            'active_users_count': len(activities['user_activities']),
            'active_channels_count': len(activities['channel_activities']),
            'events_count': len(activities['events']),
            'top_users': [],
            'top_channels': [],
            'popular_keywords': [],
            'time_distribution': defaultdict(int)
        }
        
        # トップユーザー
        user_message_counts = {user: len(msgs) for user, msgs in activities['user_activities'].items()}
        stats['top_users'] = sorted(user_message_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # トップチャンネル
        channel_message_counts = {channel: len(msgs) for channel, msgs in activities['channel_activities'].items()}
        stats['top_channels'] = sorted(channel_message_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # キーワード分析
        all_keywords = []
        for msg in activities['messages']:
            keywords = msg.get('keywords', [])
            all_keywords.extend(keywords)
        
        keyword_counter = Counter(all_keywords)
        stats['popular_keywords'] = keyword_counter.most_common(10)
        
        # 時間分布
        for msg in activities['messages']:
            timestamp = msg.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    hour = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00')).hour
                else:
                    hour = timestamp.hour
                stats['time_distribution'][hour] += 1
        
        return stats
    
    async def generate_weekly_summary_with_ai(self, activities: Dict[str, Any]) -> str:
        """Vertex AI (Gemini)を使用して週次まとめを生成"""
        
        # プロンプト作成
        prompt = self._create_summary_prompt(activities)
        
        try:
            # Geminiで生成
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            
            # レスポンステキスト取得
            summary_text = response.text if hasattr(response, 'text') else str(response)
            
            return summary_text
            
        except Exception as e:
            print(f"❌ AI要約生成エラー: {e}")
            return self._create_fallback_summary(activities)
    
    def _create_summary_prompt(self, activities: Dict[str, Any]) -> str:
        """Gemini用のプロンプトを作成"""
        stats = activities['summary_stats']
        
        prompt = f"""
あなたは、Discordコミュニティの週次活動をまとめる3匹の猫キャラクターです。
以下のデータを基に、楽しく分かりやすい対話形式で今週のまとめを作成してください。

## キャラクター設定:
- **みやにゃん**: {self.bot_personas['bot1']['personality']} ({self.bot_personas['bot1']['speaking_style']})
- **イヴにゃん**: {self.bot_personas['bot2']['personality']} ({self.bot_personas['bot2']['speaking_style']})  
- **ナレにゃん**: {self.bot_personas['bot3']['personality']} ({self.bot_personas['bot3']['speaking_style']})

## 今週の活動データ:
- 総メッセージ数: {stats['total_messages']}件
- アクティブユーザー数: {stats['active_users_count']}名
- アクティブチャンネル数: {stats['active_channels_count']}個
- イベント数: {stats['events_count']}件

### トップアクティブユーザー:
{self._format_top_users(stats['top_users'])}

### 人気チャンネル:
{self._format_top_channels(stats['top_channels'])}

### 人気キーワード:
{self._format_keywords(stats['popular_keywords'])}

## 出力形式:
キャラクター名: セリフ の形式で、3匹が自然に会話する形で出力してください。
各キャラクターが最低2-3回は発言し、データの分析と感想を述べてください。
"""
        
        return prompt
    
    def _format_top_users(self, top_users: List[tuple]) -> str:
        """トップユーザーをフォーマット"""
        if not top_users:
            return "なし"
        
        formatted = []
        for user, count in top_users:
            formatted.append(f"- {user}: {count}メッセージ")
        return "\n".join(formatted)
    
    def _format_top_channels(self, top_channels: List[tuple]) -> str:
        """トップチャンネルをフォーマット"""
        if not top_channels:
            return "なし"
        
        formatted = []
        for channel, count in top_channels:
            formatted.append(f"- {channel}: {count}メッセージ")
        return "\n".join(formatted)
    
    def _format_keywords(self, keywords: List[tuple]) -> str:
        """キーワードをフォーマット"""
        if not keywords:
            return "なし"
        
        formatted = []
        for keyword, count in keywords[:5]:  # 上位5個
            formatted.append(f"- {keyword}: {count}回")
        return "\n".join(formatted)
    
    def _create_fallback_summary(self, activities: Dict[str, Any]) -> str:
        """AIが失敗した場合のフォールバック要約"""
        stats = activities['summary_stats']
        
        summary = f"""ナレにゃん: 今週のDiscordコミュニティ活動をまとめますね

みやにゃん: 今週は{stats['total_messages']}件のメッセージがあったにゃ〜！とても活発だったにゃ！

イヴにゃん: {stats['active_users_count']}名のユーザーが参加し、{stats['active_channels_count']}のチャンネルでアクティビティがありましたにゃ

ナレにゃん: 素晴らしい参加率ですね。今週もコミュニティが盛り上がりました

みやにゃん: 来週も楽しい話題がたくさん生まれそうだにゃ〜

イヴにゃん: 継続的な活動を期待していますにゃ

ナレにゃん: それでは、また来週お会いしましょう"""
        
        return summary
    
    async def save_weekly_summary(self, summary_text: str, activities: Dict[str, Any]) -> str:
        """週次まとめをFirestoreに保存"""
        try:
            summary_data = {
                'content': summary_text,
                'type': 'weekly_summary_ai',
                'generatedAt': datetime.datetime.now(datetime.timezone.utc),
                'activities_analyzed': {
                    'total_messages': activities['summary_stats']['total_messages'],
                    'active_users': activities['summary_stats']['active_users_count'],
                    'active_channels': activities['summary_stats']['active_channels_count'],
                    'events': activities['summary_stats']['events_count']
                },
                'ai_generated': True,
                'characters': ['みやにゃん', 'イヴにゃん', 'ナレにゃん'],
                'metadata': {
                    'generator': 'discord_analytics.py',
                    'model_used': 'gemini-1.5-flash',
                    'version': '2.0'
                }
            }
            
            doc_ref = await asyncio.to_thread(self.db.collection('weekly_summaries').add, summary_data)
            summary_id = doc_ref[1].id
            
            print(f"✅ 週次まとめをFirestoreに保存: {summary_id}")
            return summary_id
            
        except Exception as e:
            print(f"❌ 週次まとめ保存エラー: {e}")
            return None
    
    async def generate_and_save_weekly_summary(self, days: int = 7) -> Dict[str, Any]:
        """週次まとめ生成・保存のメイン処理"""
        print("📊 週次アクティビティ分析を開始...")
        
        # アクティビティ収集
        activities = await self.collect_weekly_activities(days)
        
        # AI要約生成
        print("🤖 AI による要約生成中...")
        summary_text = await self.generate_weekly_summary_with_ai(activities)
        
        # 保存
        summary_id = await self.save_weekly_summary(summary_text, activities)
        
        result = {
            'success': True,
            'summary_id': summary_id,
            'summary_text': summary_text,
            'activities_stats': activities['summary_stats'],
            'generated_at': datetime.datetime.now().isoformat()
        }
        
        print("✅ 週次まとめ生成完了")
        return result