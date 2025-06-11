#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_podcast.py
Discord にゃんこエージェント - ポッドキャスト生成スクリプト

最近のトピックを解説するポッドキャストを生成するスクリプト
登場人物：みやにゃん、イヴにゃん（２匹の猫のキャラクター）
"""

import os
import json
import datetime
import asyncio
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
from collections import Counter
import re
from typing import List, Dict, Any, Optional
from google.cloud import texttospeech
from google.oauth2 import service_account
import tempfile
import io

# .envファイルから環境変数を読み込み
load_dotenv()

class PodcastGenerator:
    """ポッドキャスト生成クラス"""
    
    def __init__(self):
        self.db = None
        self.initialize_firebase()
        
        # キャラクター設定（改善版）
        self.characters = {
            'miya': {
                'name': 'みやにゃん',
                'emoji': '🐈',
                'personality': 'フレンドリーで好奇心旺盛、新しい技術に興味津々',
                'speaking_style': 'だにゃ、にゃ〜、だよにゃ',
                'voice_settings': {
                    'language_code': 'ja-JP',
                    'name': 'ja-JP-Neural2-B',  # 明るい女性の声
                    'ssml_gender': texttospeech.SsmlVoiceGender.FEMALE,
                    'speaking_rate': 1.2,  # 速めで元気な印象
                    'pitch': 0.5,  # 軽く高めで掠れ防止（さらに調整）
                    'volume_gain_db': 0.5,  # 少し大きめで活発な印象
                    'sample_rate_hertz': 24000
                },
                'gender': 'female',
                'emotions': {
                    'excited': {'pitch': 1.5, 'speaking_rate': 1.3},  # 興奮時も掠れない範囲で
                    'calm': {'pitch': 0.2, 'speaking_rate': 1.15},    # 落ち着き時も自然に
                    'curious': {'pitch': 1.0, 'speaking_rate': 1.25} # 好奇心は少し高めで速め
                }
            },
            'eve': {
                'name': 'イヴにゃん',
                'emoji': '🐱',
                'personality': 'クールで分析的、データや統計が得意',
                'speaking_style': 'ですにゃ、なのにゃ、ですね',
                'voice_settings': {
                    'language_code': 'ja-JP',
                    'name': 'ja-JP-Neural2-C',  # 低めの男性の声
                    'ssml_gender': texttospeech.SsmlVoiceGender.MALE,
                    'speaking_rate': 1.0,  # 標準的な速さで落ち着いた印象
                    'pitch': -1.5,  # 低めで男性らしく、適度な差
                    'volume_gain_db': 0.0,  # 標準的な音量で落ち着いた印象
                    'sample_rate_hertz': 24000
                },
                'gender': 'male',
                'emotions': {
                    'analytical': {'pitch': -2.0, 'speaking_rate': 0.95},  # 分析時は少し低くゆっくり
                    'pleased': {'pitch': -1.0, 'speaking_rate': 1.05},      # 喜び時は少し明るめ
                    'thoughtful': {'pitch': -1.8, 'speaking_rate': 0.9}    # 思考時は少し低くゆっくり
                }
            }
        }
    
    def initialize_firebase(self):
        """Firebase Firestoreを初期化"""
        try:
            if not firebase_admin._apps:
                # サービスアカウントキーファイルのパス
                key_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH', 
                                   './nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json')
                
                if os.path.exists(key_path):
                    print(f"🔑 Firebaseサービスアカウントキーファイルを読み込み中: {key_path}")
                    cred = credentials.Certificate(key_path)
                elif os.getenv('FIREBASE_SERVICE_ACCOUNT'):
                    print("🔑 環境変数からFirebaseサービスアカウント情報を読み込み中...")
                    service_account_info = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT'))
                    cred = credentials.Certificate(service_account_info)
                else:
                    raise FileNotFoundError("Firebaseサービスアカウントキーが見つかりません")
                
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            print("✅ Firebase Firestoreへの接続準備ができました。")
            return True
            
        except Exception as e:
            print(f"❌ Firebase Firestoreの初期化に失敗しました: {e}")
            return False
    
    async def get_recent_interactions(self, days: int = 7, limit: int = 100) -> List[Dict]:
        """最近のインタラクションデータを取得"""
        if not self.db:
            return []
        
        try:
            # 指定日数前の日時を計算
            cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
            
            # Firestoreクエリ
            interactions_ref = (self.db.collection('interactions')
                              .where('timestamp', '>=', cutoff_date)
                              .order_by('timestamp', direction=firestore.Query.DESCENDING)
                              .limit(limit))
            
            docs = await asyncio.to_thread(interactions_ref.get)
            interactions = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                interactions.append(data)
            
            print(f"📊 最近{days}日間のインタラクション: {len(interactions)}件取得")
            return interactions
            
        except Exception as e:
            print(f"❌ インタラクションデータ取得エラー: {e}")
            return []
    
    async def get_recent_events(self, days: int = 14) -> List[Dict]:
        """最近のイベントデータを取得"""
        if not self.db:
            return []
        
        try:
            # 指定日数前の日時を計算
            cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
            
            # Firestoreクエリ
            events_ref = (self.db.collection('events')
                         .where('updatedAt', '>=', cutoff_date)
                         .order_by('updatedAt', direction=firestore.Query.DESCENDING))
            
            docs = await asyncio.to_thread(events_ref.get)
            events = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                events.append(data)
            
            print(f"📅 最近{days}日間のイベント: {len(events)}件取得")
            return events
            
        except Exception as e:
            print(f"❌ イベントデータ取得エラー: {e}")
            return []
    
    def analyze_topics(self, interactions: List[Dict]) -> Dict[str, Any]:
        """インタラクションからトピックを分析"""
        # キーワード集計
        all_keywords = []
        channel_activity = Counter()
        user_activity = Counter()
        message_types = Counter()
        
        for interaction in interactions:
            # キーワード収集
            keywords = interaction.get('keywords', [])
            all_keywords.extend(keywords)
            
            # チャンネル別活動
            channel_name = interaction.get('channelName', 'Unknown')
            channel_activity[channel_name] += 1
            
            # ユーザー別活動
            username = interaction.get('username', 'Unknown')
            user_activity[username] += 1
            
            # メッセージタイプ別
            msg_type = interaction.get('type', 'unknown')
            message_types[msg_type] += 1
        
        # 人気キーワード（上位10個）
        popular_keywords = Counter(all_keywords).most_common(10)
        
        # 技術関連キーワードの検出
        tech_keywords = [
            'react', 'typescript', 'javascript', 'python', 'node', 'firebase', 
            'discord', 'api', 'database', 'frontend', 'backend', 'web', 'app',
            'github', 'git', 'docker', 'aws', 'gcp', 'azure', 'ai', 'ml',
            'figma', 'design', 'ui', 'ux', 'css', 'html', 'vue', 'angular'
        ]
        
        tech_mentions = Counter()
        for keyword, count in popular_keywords:
            if keyword.lower() in tech_keywords:
                tech_mentions[keyword] = count
        
        return {
            'popular_keywords': popular_keywords,
            'tech_mentions': dict(tech_mentions.most_common(5)),
            'channel_activity': dict(channel_activity.most_common(5)),
            'user_activity': dict(user_activity.most_common(5)),
            'message_types': dict(message_types),
            'total_interactions': len(interactions)
        }
    
    def generate_podcast_content(self, analysis: Dict[str, Any], events: List[Dict]) -> str:
        """分析結果とイベント情報からポッドキャスト内容を生成"""
        
        # 開始の挨拶（落ち着いたテンポ良く）
        content = f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: こんにちは！今週のレポートをお届けするにゃ〜\n\n"
        content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: 週刊にゃんこレポート、始めましょうにゃ。今週も興味深いデータが集まりましたにゃ\n\n"
        
        # 統計情報の紹介（数字を魅力的に、でも落ち着いて）
        total_interactions = analysis['total_interactions']
        if total_interactions > 100:
            content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: 今週は{total_interactions}件のやり取り！とても活発だったにゃ〜\n\n"
            content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: 素晴らしい参加率ですにゃ。コミュニティの活気を感じますにゃ\n\n"
        elif total_interactions > 50:
            content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: {total_interactions}件の投稿がありましたにゃ！良いペースだにゃ〜\n\n"
            content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: 安定した活動量ですにゃ。質の高い議論が多かったようですにゃ\n\n"
        else:
            content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: {total_interactions}件の投稿。深い議論が中心だったにゃ〜\n\n"
            content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: 少数精鋭の濃密な交流でしたにゃ\n\n"
        
        # 人気トピックの紹介（興味深く）
        if analysis['popular_keywords']:
            top_keyword = analysis['popular_keywords'][0]
            content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: 今週の注目キーワードは「{top_keyword[0]}」。{top_keyword[1]}回登場しましたにゃ\n\n"
            content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: みんなの関心が集まってるトピックだにゃ〜\n\n"
        
        # 技術トピックの紹介（専門的に）
        if analysis['tech_mentions']:
            tech_topics = list(analysis['tech_mentions'].keys())
            if len(tech_topics) >= 3:
                content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: 技術面では{tech_topics[0]}、{tech_topics[1]}、{tech_topics[2]}について活発な議論がありましたにゃ\n\n"
                content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: 開発者のみんなの知識共有が素晴らしいにゃ〜\n\n"
            elif len(tech_topics) >= 2:
                content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: {tech_topics[0]}と{tech_topics[1]}の技術トピックで盛り上がりましたにゃ\n\n"
                content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: 実践的な情報交換ができてるにゃ〜\n\n"
            elif len(tech_topics) == 1:
                content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: {tech_topics[0]}について詳しい議論が展開されましたにゃ\n\n"
                content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: 専門的で勉強になる内容だったにゃ〜\n\n"
        
        # チャンネル活動の紹介（分析的に）
        if analysis['channel_activity']:
            channels = list(analysis['channel_activity'].keys())
            if len(channels) >= 2:
                content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: {channels[0]}チャンネルと{channels[1]}チャンネルが特に活発でしたにゃ\n\n"
                content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: それぞれ違った話題で盛り上がってたにゃ〜\n\n"
            else:
                most_active_channel = channels[0]
                activity_count = analysis['channel_activity'][most_active_channel]
                content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: {most_active_channel}チャンネルで{activity_count}件の投稿がありましたにゃ\n\n"
                content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: みんなが集まる人気スポットだにゃ〜\n\n"
        
        # アクティブユーザーの紹介（感謝を込めて）
        if analysis['user_activity']:
            active_users = list(analysis['user_activity'].keys())[:3]
            if len(active_users) >= 3:
                content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: {active_users[0]}さん、{active_users[1]}さん、{active_users[2]}さん、今週もありがとうにゃ〜\n\n"
                content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: 皆さんの積極的な参加に感謝ですにゃ\n\n"
            elif len(active_users) >= 2:
                content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: {active_users[0]}さんと{active_users[1]}さん、いつも盛り上げてくれてありがとうにゃ〜\n\n"
                content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: コミュニティの中心的存在ですにゃ\n\n"
        
        # イベント情報の紹介（期待感を込めて）
        if events:
            upcoming_events = [e for e in events if e.get('status') in ['scheduled', 'active']]
            if upcoming_events:
                event = upcoming_events[0]
                event_name = event.get('name', 'イベント')
                user_count = event.get('userCount', 0)
                content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: 「{event_name}」の開催が予定されていますにゃ\n\n"
                if user_count > 0:
                    content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: すでに{user_count}名の方が参加予定だにゃ〜楽しみだにゃ〜\n\n"
                content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: 詳細はeventsチャンネルでご確認くださいにゃ\n\n"
        
        # 締めの挨拶（温かく）
        content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: 今週もみんなの活発な交流で素敵なコミュニティでしたにゃ〜\n\n"
        content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: 来週もどんな話題が生まれるか楽しみですにゃ\n\n"
        content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: それでは、また来週お会いしましょうにゃ〜\n\n"
        content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: さようなら、良い一週間をお過ごしくださいにゃ"
        
        return content
    
    async def save_podcast_to_firestore(self, content: str, analysis: Dict[str, Any]) -> str:
        """生成したポッドキャストをFirestoreに保存"""
        if not self.db:
            print("⚠️ Firebase Firestoreが初期化されていません。")
            return None
        
        try:
            # ポッドキャストデータの作成
            podcast_data = {
                'content': content,
                'publishedAt': datetime.datetime.now(datetime.timezone.utc),
                'type': 'weekly_summary',
                'characters': ['みやにゃん', 'イヴにゃん'],
                'topics': list(analysis.get('tech_mentions', {}).keys()),
                'keywords': [kw[0] for kw in analysis.get('popular_keywords', [])[:5]],
                'statistics': {
                    'totalInteractions': analysis.get('total_interactions', 0),
                    'topChannels': list(analysis.get('channel_activity', {}).keys())[:3],
                    'topUsers': list(analysis.get('user_activity', {}).keys())[:3]
                },
                'metadata': {
                    'generatedBy': 'make_podcast.py',
                    'version': '1.0',
                    'analysisDate': datetime.datetime.now(datetime.timezone.utc).isoformat()
                }
            }
            
            # Firestoreに保存
            doc_ref = await asyncio.to_thread(self.db.collection('podcasts').add, podcast_data)
            podcast_id = doc_ref[1].id
            
            print(f"✅ ポッドキャストをFirestoreに保存: {podcast_id}")
            return podcast_id
            
        except Exception as e:
            print(f"❌ ポッドキャスト保存エラー: {e}")
            return None
    
    def save_podcast_to_file(self, content: str, filename: Optional[str] = None) -> str:
        """ポッドキャスト内容をファイルに保存"""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"podcast_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# Discord にゃんこエージェント - 週刊ポッドキャスト\n")
                f.write(f"# 生成日時: {datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n\n")
                f.write(content)
            
            print(f"📝 ポッドキャストをファイルに保存: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ ファイル保存エラー: {e}")
            return None
    
    def clean_text_for_tts(self, content: str, remove_character_names: bool = True) -> str:
        """Text-to-Speech用にテキストをクリーンアップ"""
        # Markdownの太字記法を削除
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
        
        # キャラクター名と話者表記を削除（音声読み上げには不要）
        if remove_character_names:
            content = re.sub(f"{self.characters['miya']['emoji']} {self.characters['miya']['name']}: ", '', content)
            content = re.sub(f"{self.characters['eve']['emoji']} {self.characters['eve']['name']}: ", '', content)
            content = re.sub(f"{self.characters['miya']['name']}: ", '', content)
            content = re.sub(f"{self.characters['eve']['name']}: ", '', content)
        
        # 絵文字を削除（音声読み上げには不要）
        content = re.sub(r'[🐈🐱😺👋👥🗑️📅📊📝🔥🎉❌⚠️✅]', '', content)
        
        # チャンネル名の#を削除
        content = re.sub(r'#(\w+)', r'\1チャンネル', content)
        
        # @メンションを読みやすく
        content = re.sub(r'@(\w+)', r'\1', content)
        
        # 改行を適切な間隔に変換
        content = re.sub(r'\n\n+', '。 ', content)
        content = re.sub(r'\n', '、', content)
        
        # 連続する句読点を整理
        content = re.sub(r'[。、]+', '。', content)
        
        # 音声読み上げ用の調整（落ち着いたトーン）
        content = re.sub(r'にゃ〜ん', 'にゃーん', content)  # 伸ばし音を自然に
        content = re.sub(r'だにゃ〜', 'だにゃー', content)
        content = re.sub(r'ですにゃ〜', 'ですにゃー', content)
        content = re.sub(r'にゃ〜', 'にゃー', content)
        
        # 感嘆符の調整（読み上げ時の自然さのため）
        content = re.sub(r'！{2,}', '！', content)  # 連続感嘆符を1つに
        
        # 読み上げ速度を上げるための調整
        content = re.sub(r'。\s+', '。', content)  # 句点後の余分な空白を削除
        content = re.sub(r'、\s+', '、', content)  # 読点後の余分な空白を削除
        
        return content.strip()
    
    def create_ssml_content(self, text: str, character: str = None, emotion: str = None) -> str:
        """SSML（Speech Synthesis Markup Language）を使用した高品質な音声用テキスト生成"""
        # 基本的なクリーンアップ
        clean_text = self.clean_text_for_tts(text, remove_character_names=True)
        
        # SSMLの開始タグ
        ssml = '<speak>'
        
        # キャラクター別の基本音声設定
        if character == 'miya':
            # みやにゃん：明るく活発な設定
            ssml += '<prosody rate="1.2" pitch="+0.5st" volume="medium">'
        elif character == 'eve':
            # イヴにゃん：落ち着いて低い設定
            ssml += '<prosody rate="1.0" pitch="-1.5st" volume="medium">'
        
        # キャラクター別の感情設定を追加適用
        if character and character in self.characters and emotion and emotion in self.characters[character].get('emotions', {}):
            emotion_settings = self.characters[character]['emotions'][emotion]
            
            # 感情による追加調整
            if character == 'miya':
                if emotion == 'excited':
                    ssml += '<prosody rate="1.3" pitch="+1.5st">'
                elif emotion == 'curious':
                    ssml += '<prosody rate="1.25" pitch="+1.0st">'
                elif emotion == 'calm':
                    ssml += '<prosody rate="1.15" pitch="+0.2st">'
            elif character == 'eve':
                if emotion == 'analytical':
                    ssml += '<prosody rate="0.95" pitch="-2.0st">'
                elif emotion == 'thoughtful':
                    ssml += '<prosody rate="0.9" pitch="-1.8st">'
                elif emotion == 'pleased':
                    ssml += '<prosody rate="1.05" pitch="-1.0st">'
        
        # テキストを文に分割して、キャラクター別の特徴を強化
        sentences = re.split(r'([。！？])', clean_text)
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
            
            # キャラクター別の表現調整
            if character == 'miya':
                # みやにゃん：明るく元気な表現を強調
                if '！' in sentence or 'ありがとう' in sentence or '楽しみ' in sentence or 'すごい' in sentence:
                    ssml += f'<emphasis level="strong"><prosody rate="1.6" pitch="+7.0st">{sentence}</prosody></emphasis>'
                elif 'にゃー' in sentence or 'にゃん' in sentence:
                    ssml += f'<prosody pitch="+5.5st" rate="1.4">{sentence}</prosody>'
                elif '数字' in sentence or '件' in sentence:
                    ssml += f'<emphasis level="moderate">{sentence}</emphasis>'
                else:
                    ssml += sentence
            elif character == 'eve':
                # イヴにゃん：分析的で落ち着いた表現を強調
                if '数字' in sentence or '統計' in sentence or '分析' in sentence or 'データ' in sentence:
                    ssml += f'<emphasis level="moderate"><prosody rate="0.75" pitch="-10.5st">{sentence}</prosody></emphasis>'
                elif 'にゃー' in sentence or 'にゃん' in sentence:
                    ssml += f'<prosody pitch="-7.5st" rate="0.8">{sentence}</prosody>'
                elif 'すばらしい' in sentence or '良い' in sentence:
                    ssml += f'<prosody rate="0.95" pitch="-6.5st">{sentence}</prosody>'
                else:
                    ssml += sentence
            else:
                # その他のキャラクター（ナレーション等）
                if '！' in sentence or 'ありがとう' in sentence or '楽しみ' in sentence:
                    ssml += f'<emphasis level="moderate">{sentence}</emphasis>'
                elif '数字' in sentence or '統計' in sentence or '分析' in sentence:
                    ssml += f'<prosody rate="0.8">{sentence}</prosody>'
                else:
                    ssml += sentence
            
            # 文の間に適切な休止を追加（キャラクター別調整）
            if sentence.endswith(('。', '！', '？')) and i < len(sentences) - 2:
                if character == 'miya':
                    # みやにゃん：短めの休止で活発さを表現
                    if '。' in sentence:
                        ssml += '<break time="600ms"/>'
                    elif '！' in sentence:
                        ssml += '<break time="400ms"/>'
                    elif '？' in sentence:
                        ssml += '<break time="500ms"/>'
                elif character == 'eve':
                    # イヴにゃん：長めの休止で落ち着きを表現
                    if '。' in sentence:
                        ssml += '<break time="1000ms"/>'
                    elif '！' in sentence:
                        ssml += '<break time="800ms"/>'
                    elif '？' in sentence:
                        ssml += '<break time="900ms"/>'
                else:
                    # デフォルト
                    if '。' in sentence:
                        ssml += '<break time="800ms"/>'
                    elif '！' in sentence:
                        ssml += '<break time="600ms"/>'
                    elif '？' in sentence:
                        ssml += '<break time="700ms"/>'
        
        # 特別な表現の調整（キャラクター別）
        if character == 'miya':
            ssml = re.sub(r'にゃー+', '<phoneme alphabet="ipa" ph="ɲaː"><prosody pitch="+3.0st">にゃー</prosody></phoneme>', ssml)
        elif character == 'eve':
            ssml = re.sub(r'にゃー+', '<phoneme alphabet="ipa" ph="ɲaː"><prosody pitch="-2.0st">にゃー</prosody></phoneme>', ssml)
        
        # 感情設定の終了タグ
        if character and character in self.characters and emotion and emotion in self.characters[character].get('emotions', {}):
            ssml += '</prosody>'
        
        # キャラクター別基本設定の終了タグ
        if character in ['miya', 'eve']:
            ssml += '</prosody>'
        
        # SSMLの終了タグ
        ssml += '</speak>'
        
        return ssml
    
    def detect_emotion_from_content(self, text: str, character: str) -> str:
        """テキスト内容からキャラクターに適した感情を検出"""
        if character not in self.characters:
            return None
        
        emotions = self.characters[character].get('emotions', {})
        if not emotions:
            return None
        
        # キーワードベースの感情検出
        excited_keywords = ['！', 'すごい', 'すばらしい', '楽しい', 'ありがとう', '活発', '盛り上がり']
        analytical_keywords = ['統計', '分析', 'データ', '数字', '件', '割合', '比較']
        calm_keywords = ['落ち着い', '安定', 'ゆっくり', '深い']
        
        text_lower = text.lower()
        
        if character == 'miya':
            # みやにゃんの感情検出
            if any(keyword in text for keyword in excited_keywords):
                return 'excited'
            else:
                curious_keywords = ['新しい', '興味', '気になる', '知りたい']
                if any(keyword in text for keyword in curious_keywords):
                    return 'curious'
                else:
                    return 'calm'
        elif character == 'eve':
            # イヴにゃんの感情検出
            if any(keyword in text for keyword in analytical_keywords):
                return 'analytical'
            elif any(keyword in text for keyword in ['良い', 'すばらしい', '素晴らしい']):
                return 'pleased'
            else:
                return 'thoughtful'
        
        return None
    
    async def generate_audio(self, content: str, filename: Optional[str] = None, voice_settings: Optional[Dict] = None, character: str = None, use_ssml: bool = True) -> Optional[str]:
        """ポッドキャスト内容を音声ファイルに変換（SSML対応、高品質版）"""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"podcast_{timestamp}.mp3"
        
        try:
            print("🎵 高品質音声ファイル生成中...")
            
            # Google Cloud Text-to-Speech クライアントを初期化
            key_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH', 
                               './nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json')
            
            if os.path.exists(key_path):
                client = texttospeech.TextToSpeechClient.from_service_account_json(key_path)
            elif os.getenv('FIREBASE_SERVICE_ACCOUNT'):
                service_account_info = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT'))
                credentials = service_account.Credentials.from_service_account_info(service_account_info)
                client = texttospeech.TextToSpeechClient(credentials=credentials)
            else:
                print("⚠️ サービスアカウントキーが見つかりません。デフォルトクレデンシャルを使用します。")
                client = texttospeech.TextToSpeechClient()
            
            # デフォルトの音声設定（高品質版）
            default_voice_settings = {
                'language_code': 'ja-JP',
                'name': 'ja-JP-Neural2-B',
                'ssml_gender': texttospeech.SsmlVoiceGender.FEMALE,
                'speaking_rate': 1.15,
                'pitch': 0.0,
                'volume_gain_db': 2.0,
                'sample_rate_hertz': 24000
            }
            
            # 音声設定をマージ
            if voice_settings:
                default_voice_settings.update(voice_settings)
            
            # SSML対応のテキスト準備
            if use_ssml and character:
                # 感情を検出
                emotion = self.detect_emotion_from_content(content, character)
                # SSMLコンテンツ生成
                synthesis_input = texttospeech.SynthesisInput(
                    ssml=self.create_ssml_content(content, character, emotion)
                )
                print(f"📢 {character}キャラクターの{emotion}感情でSSML音声生成中...")
            else:
                # 通常のテキスト処理
                clean_content = self.clean_text_for_tts(content, remove_character_names=True)
                synthesis_input = texttospeech.SynthesisInput(text=clean_content)
                print("📢 通常のテキスト音声生成中...")
            
            # 音声設定
            voice = texttospeech.VoiceSelectionParams(
                language_code=default_voice_settings['language_code'],
                name=default_voice_settings['name'],
                ssml_gender=default_voice_settings['ssml_gender']
            )
            
            # 高品質音声設定
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=default_voice_settings['speaking_rate'],
                pitch=default_voice_settings['pitch'],
                volume_gain_db=default_voice_settings.get('volume_gain_db', 0.0),
                sample_rate_hertz=default_voice_settings.get('sample_rate_hertz', 24000),
                effects_profile_id=['telephony-class-application']  # 音質改善プロファイル
            )
            
            # 音声合成を実行
            response = await asyncio.to_thread(
                client.synthesize_speech,
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # 音声ファイルに保存
            with open(filename, 'wb') as out:
                out.write(response.audio_content)
            
            print(f"🎵 高品質音声ファイルを生成: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ 音声ファイル生成エラー: {e}")
            return None
    
    async def generate_character_audio(self, content: str, base_filename: Optional[str] = None) -> Dict[str, str]:
        """キャラクター別に音声ファイルを生成（SSML対応、高品質版）"""
        if not base_filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"podcast_{timestamp}"
        
        audio_files = {}
        
        try:
            # キャラクター別にセリフを分割
            lines = content.split('\n')
            character_lines = {'miya': [], 'eve': [], 'narrator': []}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if self.characters['miya']['name'] in line:
                    # みやにゃんのセリフを抽出
                    speech = re.sub(f".*{self.characters['miya']['name']}.*?:\s*", '', line)
                    if speech:
                        character_lines['miya'].append(speech)
                elif self.characters['eve']['name'] in line:
                    # イヴにゃんのセリフを抽出
                    speech = re.sub(f".*{self.characters['eve']['name']}.*?:\s*", '', line)
                    if speech:
                        character_lines['eve'].append(speech)
                else:
                    # ナレーション
                    character_lines['narrator'].append(line)
            
            # 各キャラクターの音声を生成（高品質版）
            for character, lines_list in character_lines.items():
                if lines_list:
                    character_text = ' '.join(lines_list)
                    
                    if character_text.strip():
                        filename = f"{base_filename}_{character}.mp3"
                        
                        print(f"🎵 {character}の高品質音声生成中...")
                        
                        # キャラクター別の音声設定を使用
                        if character in self.characters:
                            voice_settings = self.characters[character]['voice_settings']
                            # SSML対応で音声生成
                            audio_file = await self.generate_audio(
                                character_text, 
                                filename, 
                                voice_settings,
                                character=character,
                                use_ssml=True
                            )
                            if audio_file:
                                audio_files[character] = audio_file
                                print(f"✅ {character}の高品質音声ファイル生成完了: {filename}")
                        else:
                            # ナレーション用の高品質設定（キャラクターとの区別を明確化）
                            default_narrator_settings = {
                                'language_code': 'ja-JP',
                                'name': 'ja-JP-Neural2-D',  # ナレーション用の中性的な声
                                'ssml_gender': texttospeech.SsmlVoiceGender.NEUTRAL,
                                'speaking_rate': 1.15,  # みやにゃんとイヴにゃんの中間
                                'pitch': 0.0,  # 中性的な高さ
                                'volume_gain_db': 2.0,  # 適度な音量
                                'sample_rate_hertz': 24000
                            }
                            # ナレーションはSSMLなしで生成
                            audio_file = await self.generate_audio(
                                character_text, 
                                filename, 
                                default_narrator_settings,
                                character=None,
                                use_ssml=False
                            )
                            if audio_file:
                                audio_files[character] = audio_file
                                print(f"✅ {character}の高品質音声ファイル生成完了: {filename}")
            
            return audio_files
            
        except Exception as e:
            print(f"❌ キャラクター別音声生成エラー: {e}")
            return {}
    
    async def create_conversation_audio(self, content: str, base_filename: Optional[str] = None) -> Optional[str]:
        """会話形式で統合された高品質音声を生成（キャラクター切り替え対応）"""
        if not base_filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"podcast_conversation_{timestamp}"
        
        try:
            print("🎭 会話形式音声生成中...")
            
            # 各キャラクターの個別音声を生成
            character_audios = await self.generate_character_audio(content, base_filename)
            
            if len(character_audios) > 1:
                # 複数の音声ファイルが生成された場合は、統合処理の準備
                print("🔄 複数キャラクターの音声統合準備完了")
                print("💡 音声統合には外部ツール（ffmpeg等）の使用を推奨します")
                
                # 統合用のメタデータファイルを作成
                metadata_filename = f"{base_filename}_metadata.json"
                metadata = {
                    'total_characters': len(character_audios),
                    'audio_files': character_audios,
                    'suggestion': 'Use ffmpeg or similar tool to concatenate audio files in conversation order',
                    'generated_at': datetime.datetime.now().isoformat()
                }
                
                with open(metadata_filename, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                
                print(f"📋 音声統合メタデータを生成: {metadata_filename}")
                return metadata_filename
            elif character_audios:
                # 単一キャラクターの場合はそのまま返す
                return list(character_audios.values())[0]
            else:
                print("⚠️ 音声ファイルが生成されませんでした")
                return None
                
        except Exception as e:
            print(f"❌ 会話形式音声生成エラー: {e}")
            return None
    
    def create_full_conversation_ssml(self, content: str) -> str:
        """会話全体をキャラクター別音声設定でSSML化"""
        lines = content.split('\n')
        ssml = '<speak>'
        
        for line in lines:
            line = line.strip()
            if not line:
                # 空行は短い休止
                ssml += '<break time="300ms"/>'
                continue
            
            # キャラクター判定とセリフ抽出
            if self.characters['miya']['name'] in line:
                # みやにゃんのセリフ
                speech = re.sub(f".*{self.characters['miya']['name']}.*?:\s*", '', line)
                speech = self.clean_text_for_tts(speech, remove_character_names=False)
                if speech:
                    emotion = self.detect_emotion_from_content(speech, 'miya')
                    
                    # みやにゃんの基本設定
                    ssml += '<prosody rate="1.2" pitch="+0.5st" volume="medium">'
                    
                    # 感情による調整
                    if emotion == 'excited':
                        ssml += '<prosody rate="1.3" pitch="+1.5st">'
                    elif emotion == 'curious':
                        ssml += '<prosody rate="1.25" pitch="+1.0st">'
                    elif emotion == 'calm':
                        ssml += '<prosody rate="1.15" pitch="+0.2st">'
                    
                    # 特別な表現の調整
                    speech_adjusted = re.sub(r'にゃー+', '<prosody pitch="+1.0st">にゃー</prosody>', speech)
                    if '！' in speech or 'ありがとう' in speech or '楽しみ' in speech:
                        ssml += f'<emphasis level="strong">{speech_adjusted}</emphasis>'
                    else:
                        ssml += speech_adjusted
                    
                    # 感情調整の終了
                    if emotion in ['excited', 'curious', 'calm']:
                        ssml += '</prosody>'
                    
                    # 基本設定の終了
                    ssml += '</prosody>'
                    
                    # みやにゃん用の休止（短め）
                    ssml += '<break time="500ms"/>'
                    
            elif self.characters['eve']['name'] in line:
                # イヴにゃんのセリフ
                speech = re.sub(f".*{self.characters['eve']['name']}.*?:\s*", '', line)
                speech = self.clean_text_for_tts(speech, remove_character_names=False)
                if speech:
                    emotion = self.detect_emotion_from_content(speech, 'eve')
                    
                    # イヴにゃんの基本設定
                    ssml += '<prosody rate="1.0" pitch="-1.5st" volume="medium">'
                    
                    # 感情による調整
                    if emotion == 'analytical':
                        ssml += '<prosody rate="0.95" pitch="-2.0st">'
                    elif emotion == 'thoughtful':
                        ssml += '<prosody rate="0.9" pitch="-1.8st">'
                    elif emotion == 'pleased':
                        ssml += '<prosody rate="1.05" pitch="-1.0st">'
                    
                    # 特別な表現の調整
                    speech_adjusted = re.sub(r'にゃー+', '<prosody pitch="-0.5st">にゃー</prosody>', speech)
                    if '数字' in speech or '統計' in speech or '分析' in speech:
                        ssml += f'<emphasis level="moderate">{speech_adjusted}</emphasis>'
                    else:
                        ssml += speech_adjusted
                    
                    # 感情調整の終了
                    if emotion in ['analytical', 'thoughtful', 'pleased']:
                        ssml += '</prosody>'
                    
                    # 基本設定の終了
                    ssml += '</prosody>'
                    
                    # イヴにゃん用の休止（長め）
                    ssml += '<break time="800ms"/>'
            
            else:
                # ナレーション（中間的な設定）
                speech = self.clean_text_for_tts(line, remove_character_names=False)
                if speech:
                    ssml += f'<prosody rate="1.0" pitch="0st" volume="medium">{speech}</prosody>'
                    ssml += '<break time="800ms"/>'
        
        ssml += '</speak>'
        return ssml
    
    async def generate_podcast(self, days: int = 7, save_to_firestore: bool = True, save_to_file: bool = True, generate_audio: bool = True) -> Dict[str, Any]:
        """ポッドキャストを生成するメイン関数"""
        print(f"🎙️ ポッドキャスト生成を開始（過去{days}日間のデータを分析）...")
        
        try:
            # データ取得
            print("📊 データ取得中...")
            interactions = await self.get_recent_interactions(days=days)
            events = await self.get_recent_events(days=days*2)  # イベントは少し長めの期間で取得
            
            if not interactions:
                print("⚠️ 分析対象のインタラクションが見つかりませんでした。")
                return {'success': False, 'error': 'No interactions found'}
            
            # トピック分析
            print("🔍 トピック分析中...")
            analysis = self.analyze_topics(interactions)
            
            # ポッドキャスト内容生成
            print("✍️ ポッドキャスト内容生成中...")
            content = self.generate_podcast_content(analysis, events)
            
            # 結果の保存
            result = {
                'success': True,
                'content': content,
                'analysis': analysis,
                'events_count': len(events),
                'generated_at': datetime.datetime.now().isoformat()
            }
            
            # Firestoreに保存
            if save_to_firestore:
                podcast_id = await self.save_podcast_to_firestore(content, analysis)
                result['firestore_id'] = podcast_id
            
            # ファイルに保存
            if save_to_file:
                filename = self.save_podcast_to_file(content)
                result['filename'] = filename
            
            # 音声ファイル生成
            if generate_audio:
                print("\n🎵 高品質音声ファイル生成を開始...")
                
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # 統合音声ファイルを生成（キャラクター別SSML対応版）
                print("🎭 統合音声ファイル生成中（キャラクター別音声設定適用）...")
                
                # キャラクター別SSML生成
                full_ssml = self.create_full_conversation_ssml(content)
                
                # SSML対応で統合音声生成
                audio_filename = await self.generate_audio_with_ssml(
                    full_ssml,
                    f"podcast_full_{timestamp}.mp3",
                    voice_settings={
                        'language_code': 'ja-JP',
                        'name': 'ja-JP-Neural2-B',  # 基本はみやにゃんの声をベース
                        'ssml_gender': texttospeech.SsmlVoiceGender.FEMALE,
                        'speaking_rate': 1.15,  # 中間値
                        'pitch': 0.0,  # SSMLで制御するので基本値
                        'volume_gain_db': 2.0,
                        'sample_rate_hertz': 24000
                    }
                )
                if audio_filename:
                    result['audio_file'] = audio_filename
                    print(f"✅ キャラクター別音声対応の統合ファイル生成: {audio_filename}")
                
                # キャラクター別音声ファイルを生成（SSML対応）
                character_audio_files = await self.generate_character_audio(content, f"podcast_{timestamp}")
                if character_audio_files:
                    result['character_audio_files'] = character_audio_files
                
                # 会話形式音声を生成（新機能）
                conversation_audio = await self.create_conversation_audio(content, f"podcast_conversation_{timestamp}")
                if conversation_audio:
                    result['conversation_metadata'] = conversation_audio
            
            print("✅ ポッドキャスト生成完了！")
            print("\n" + "="*50)
            print("📻 生成されたポッドキャスト内容:")
            print("="*50)
            print(content)
            print("="*50)
            
            # 音声ファイル情報の表示
            if 'audio_file' in result:
                print(f"🎵 統合音声ファイル: {result['audio_file']}")
            if 'character_audio_files' in result:
                print(f"🎭 キャラクター別音声ファイル:")
                for character, filename in result['character_audio_files'].items():
                    print(f"   - {character}: {filename}")
            if 'conversation_metadata' in result:
                print(f"💬 会話形式音声メタデータ: {result['conversation_metadata']}")
                print("💡 ヒント: 会話形式の音声統合にはffmpegなどの外部ツールをご利用ください")
            
            return result
            
        except Exception as e:
            print(f"❌ ポッドキャスト生成エラー: {e}")
            return {'success': False, 'error': str(e)}

    async def generate_audio_with_ssml(self, ssml_content: str, filename: Optional[str] = None, voice_settings: Optional[Dict] = None) -> Optional[str]:
        """SSML専用の音声ファイル生成関数"""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"podcast_ssml_{timestamp}.mp3"
        
        try:
            print("🎵 SSML対応音声ファイル生成中...")
            
            # Google Cloud Text-to-Speech クライアントを初期化
            key_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH', 
                               './nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json')
            
            if os.path.exists(key_path):
                client = texttospeech.TextToSpeechClient.from_service_account_json(key_path)
            elif os.getenv('FIREBASE_SERVICE_ACCOUNT'):
                service_account_info = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT'))
                credentials = service_account.Credentials.from_service_account_info(service_account_info)
                client = texttospeech.TextToSpeechClient(credentials=credentials)
            else:
                print("⚠️ サービスアカウントキーが見つかりません。デフォルトクレデンシャルを使用します。")
                client = texttospeech.TextToSpeechClient()
            
            # デフォルトの音声設定
            default_voice_settings = {
                'language_code': 'ja-JP',
                'name': 'ja-JP-Neural2-B',
                'ssml_gender': texttospeech.SsmlVoiceGender.FEMALE,
                'speaking_rate': 1.15,
                'pitch': 0.0,
                'volume_gain_db': 2.0,
                'sample_rate_hertz': 24000
            }
            
            # 音声設定をマージ
            if voice_settings:
                default_voice_settings.update(voice_settings)
            
            # SSMLコンテンツで音声合成
            synthesis_input = texttospeech.SynthesisInput(ssml=ssml_content)
            
            # 音声設定
            voice = texttospeech.VoiceSelectionParams(
                language_code=default_voice_settings['language_code'],
                name=default_voice_settings['name'],
                ssml_gender=default_voice_settings['ssml_gender']
            )
            
            # 高品質音声設定
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=default_voice_settings['speaking_rate'],
                pitch=default_voice_settings['pitch'],
                volume_gain_db=default_voice_settings.get('volume_gain_db', 0.0),
                sample_rate_hertz=default_voice_settings.get('sample_rate_hertz', 24000),
                effects_profile_id=['telephony-class-application']
            )
            
            # 音声合成を実行
            response = await asyncio.to_thread(
                client.synthesize_speech,
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # 音声ファイルに保存
            with open(filename, 'wb') as out:
                out.write(response.audio_content)
            
            print(f"🎵 SSML対応音声ファイルを生成: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ SSML音声ファイル生成エラー: {e}")
            return None

async def main():
    """メイン実行関数"""
    print("🎙️ Discord にゃんこエージェント - ポッドキャスト生成スクリプト")
    print("="*60)
    
    # ポッドキャスト生成器を初期化
    generator = PodcastGenerator()
    
    # ポッドキャストを生成
    result = await generator.generate_podcast(
        days=7,  # 過去7日間のデータを分析
        save_to_firestore=True,  # Firestoreに保存
        save_to_file=True  # ファイルにも保存
    )
    
    if result['success']:
        print(f"\n🎉 ポッドキャスト生成成功！")
        if 'filename' in result:
            print(f"📝 ファイル: {result['filename']}")
        if 'firestore_id' in result:
            print(f"🔥 Firestore ID: {result['firestore_id']}")
        
        # 音声ファイル情報の表示
        if 'audio_file' in result:
            print(f"🎵 統合音声ファイル: {result['audio_file']}")
        if 'character_audio_files' in result:
            print(f"🎭 キャラクター別音声ファイル:")
            for character, filename in result['character_audio_files'].items():
                print(f"   - {character}: {filename}")
        if 'conversation_metadata' in result:
            print(f"💬 会話形式音声メタデータ: {result['conversation_metadata']}")
            print("💡 ヒント: 会話形式の音声統合にはffmpegなどの外部ツールをご利用ください")
        
        # 統計情報の表示
        analysis = result.get('analysis', {})
        print(f"\n📊 分析統計:")
        print(f"   - 総インタラクション数: {analysis.get('total_interactions', 0)}件")
        print(f"   - 人気キーワード数: {len(analysis.get('popular_keywords', []))}個")
        print(f"   - 技術トピック数: {len(analysis.get('tech_mentions', {}))}個")
        print(f"   - アクティブチャンネル数: {len(analysis.get('channel_activity', {}))}個")
        print(f"   - イベント数: {result.get('events_count', 0)}件")
    else:
        print(f"❌ ポッドキャスト生成失敗: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    # 非同期実行
    asyncio.run(main())
