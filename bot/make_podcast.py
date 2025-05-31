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
from gtts import gTTS
import tempfile
import io

# .envファイルから環境変数を読み込み
load_dotenv()

class PodcastGenerator:
    """ポッドキャスト生成クラス"""
    
    def __init__(self):
        self.db = None
        self.initialize_firebase()
        
        # キャラクター設定
        self.characters = {
            'miya': {
                'name': 'みやにゃん',
                'emoji': '🐈',
                'personality': 'フレンドリーで好奇心旺盛、新しい技術に興味津々',
                'speaking_style': 'だにゃ、にゃ〜、だよにゃ',
                'voice_settings': {
                    'lang': 'ja',
                    'tld': 'com',  # アメリカ英語ベース（明るい声）
                    'slow': False
                }
            },
            'eve': {
                'name': 'イヴにゃん',
                'emoji': '🐱',
                'personality': 'クールで分析的、データや統計が得意',
                'speaking_style': 'ですにゃ、なのにゃ、ですね',
                'voice_settings': {
                    'lang': 'ja',
                    'tld': 'co.uk',  # イギリス英語ベース（落ち着いた声）
                    'slow': False
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
        
        # 開始の挨拶（超ハイテンション）
        content = f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: みんなー！今週もキターーー！にゃ〜〜〜！\n\n"
        content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: 週刊にゃんこレポート、スタートですにゃ！今週もヤバかったのにゃ〜！\n\n"
        
        # 統計情報の紹介（超興奮）
        total_interactions = analysis['total_interactions']
        if total_interactions > 100:
            content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: うわあああ！{total_interactions}件って何それ！？バケモノ級だにゃ〜〜〜！\n\n"
            content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: みんなのパワーがハンパないのにゃ！\n\n"
        elif total_interactions > 50:
            content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: {total_interactions}件！すっごーい！みんな超アクティブだにゃ〜！\n\n"
            content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: この勢い、止まらないのにゃ〜！\n\n"
        else:
            content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: {total_interactions}件！質の高い議論がギュッと詰まってるにゃ〜！\n\n"
            content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: 濃密な時間だったのにゃ！\n\n"
        
        # 人気トピックの紹介（爆発的興奮）
        if analysis['popular_keywords']:
            top_keyword = analysis['popular_keywords'][0]
            content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: 今週の大注目は「{top_keyword[0]}」！なんと{top_keyword[1]}回も！\n\n"
            content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: みんなこれに夢中だにゃ〜！熱すぎるにゃ〜〜〜！\n\n"
        
        # 技術トピックの紹介（開発者魂爆発）
        if analysis['tech_mentions']:
            tech_topics = list(analysis['tech_mentions'].keys())
            if len(tech_topics) >= 3:
                content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: 技術トーク祭り開催中！{tech_topics[0]}！{tech_topics[1]}！{tech_topics[2]}！\n\n"
                content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: 開発者のみんな、マジで熱いにゃ〜〜〜！コード書きたくなってきたにゃ！\n\n"
            elif len(tech_topics) >= 2:
                content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: {tech_topics[0]}と{tech_topics[1]}で大盛り上がり！\n\n"
                content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: 技術愛が溢れてるにゃ〜！最高だにゃ〜！\n\n"
            elif len(tech_topics) == 1:
                content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: {tech_topics[0]}について超深掘り！\n\n"
                content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: 専門的すぎて脳みそパンクしそうだにゃ〜！\n\n"
        
        # チャンネル活動の紹介（超活気）
        if analysis['channel_activity']:
            channels = list(analysis['channel_activity'].keys())
            if len(channels) >= 2:
                content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: {channels[0]}チャンネルと{channels[1]}チャンネルが爆発してたにゃ〜！\n\n"
                content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: もうお祭り騒ぎですにゃ〜！\n\n"
            else:
                most_active_channel = channels[0]
                activity_count = analysis['channel_activity'][most_active_channel]
                content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: {most_active_channel}チャンネルで{activity_count}件の嵐！みんな集合してるにゃ〜！\n\n"
        
        # アクティブユーザーの紹介（感謝爆発）
        if analysis['user_activity']:
            active_users = list(analysis['user_activity'].keys())[:3]
            if len(active_users) >= 3:
                content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: {active_users[0]}さん！{active_users[1]}さん！{active_users[2]}さん！\n\n"
                content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: みんな超絶ありがとうにゃ〜〜〜！愛してるにゃ〜！\n\n"
            elif len(active_users) >= 2:
                content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: {active_users[0]}さんと{active_users[1]}さん、神すぎるのにゃ〜！\n\n"
                content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: コミュニティの救世主だにゃ〜！\n\n"
        
        # イベント情報の紹介（期待MAX）
        if events:
            upcoming_events = [e for e in events if e.get('status') in ['scheduled', 'active']]
            if upcoming_events:
                event = upcoming_events[0]
                event_name = event.get('name', 'イベント')
                user_count = event.get('userCount', 0)
                content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: そして！そして！「{event_name}」がやってくるにゃ〜〜〜！\n\n"
                if user_count > 0:
                    content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: すでに{user_count}名が参戦予定！ワクワクが止まらないのにゃ〜！\n\n"
                content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: eventsチャンネル、今すぐチェックだにゃ〜！急げ〜！\n\n"
        
        # 締めの挨拶（愛と感謝爆発）
        content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: みんなのパワーで今週も最高のコミュニティだったのにゃ〜！\n\n"
        content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: 来週はもっともっと盛り上がっちゃうにゃ〜！期待しててにゃ〜〜〜！\n\n"
        content += f"{self.characters['eve']['emoji']} **{self.characters['eve']['name']}**: それじゃあ、また来週〜！みんな大好きだにゃ〜！\n\n"
        content += f"{self.characters['miya']['emoji']} **{self.characters['miya']['name']}**: ばいばーい！にゃ〜〜〜ん！最高だにゃ〜〜〜！"
        
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
        
        # 音声読み上げ用の調整
        content = re.sub(r'にゃ〜ん', 'にゃーん', content)  # 伸ばし音を自然に
        content = re.sub(r'だにゃ〜', 'だにゃー', content)
        content = re.sub(r'ですにゃ〜', 'ですにゃー', content)
        
        # 音声読み上げ用の調整（エネルギッシュな表現を自然に）
        content = re.sub(r'にゃ〜〜〜ん', 'にゃーーーん', content)  # 超長い伸ばし音
        content = re.sub(r'にゃ〜〜', 'にゃーー', content)  # 長い伸ばし音
        content = re.sub(r'だにゃ〜〜〜', 'だにゃーーー', content)
        content = re.sub(r'だにゃ〜〜', 'だにゃーー', content)
        content = re.sub(r'ですにゃ〜〜', 'ですにゃーー', content)
        
        # 興奮表現を自然に
        content = re.sub(r'キターーー', 'きたーーー', content)
        content = re.sub(r'うわあああ', 'うわーーー', content)
        content = re.sub(r'すっごーい', 'すっごーい', content)
        content = re.sub(r'ヤバかった', 'やばかった', content)
        content = re.sub(r'バケモノ級', 'ばけもの級', content)
        content = re.sub(r'ハンパない', 'はんぱない', content)
        content = re.sub(r'マジで', 'まじで', content)
        content = re.sub(r'ワクワク', 'わくわく', content)
        
        # 感嘆符の調整（読み上げ時の自然さのため）
        content = re.sub(r'！{3,}', '！', content)  # 連続感嘆符を1つに
        content = re.sub(r'！{2}', '！', content)
        
        return content.strip()
    
    async def generate_audio(self, content: str, filename: Optional[str] = None, lang: str = 'ja') -> Optional[str]:
        """ポッドキャスト内容を音声ファイルに変換"""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"podcast_{timestamp}.mp3"
        
        try:
            print("🎵 音声ファイル生成中...")
            
            # テキストをTTS用にクリーンアップ（キャラクター名も削除）
            clean_content = self.clean_text_for_tts(content, remove_character_names=True)
            
            # gTTSで音声生成
            tts = gTTS(text=clean_content, lang=lang, slow=False)
            
            # 音声ファイルに保存
            await asyncio.to_thread(tts.save, filename)
            
            print(f"🎵 音声ファイルを生成: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ 音声ファイル生成エラー: {e}")
            return None
    
    async def generate_character_audio(self, content: str, base_filename: Optional[str] = None) -> Dict[str, str]:
        """キャラクター別に音声ファイルを生成"""
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
            
            # 各キャラクターの音声を生成
            for character, lines_list in character_lines.items():
                if lines_list:
                    character_text = ' '.join(lines_list)
                    clean_text = self.clean_text_for_tts(character_text, remove_character_names=True)
                    
                    if clean_text:
                        filename = f"{base_filename}_{character}.mp3"
                        
                        print(f"🎵 {character}の音声生成中...")
                        
                        # キャラクター別の音声設定を使用
                        if character in self.characters:
                            voice_settings = self.characters[character]['voice_settings']
                            tts = gTTS(
                                text=clean_text, 
                                lang=voice_settings['lang'],
                                tld=voice_settings['tld'],
                                slow=voice_settings['slow']
                            )
                        else:
                            # ナレーション用のデフォルト設定
                            tts = gTTS(text=clean_text, lang='ja', tld='com', slow=False)
                        
                        await asyncio.to_thread(tts.save, filename)
                        
                        audio_files[character] = filename
                        print(f"✅ {character}の音声ファイル生成完了: {filename}")
            
            return audio_files
            
        except Exception as e:
            print(f"❌ キャラクター別音声生成エラー: {e}")
            return {}
    
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
                print("\n🎵 音声ファイル生成を開始...")
                
                # 統合音声ファイルを生成
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                audio_filename = await self.generate_audio(content, f"podcast_full_{timestamp}.mp3")
                if audio_filename:
                    result['audio_file'] = audio_filename
                
                # キャラクター別音声ファイルを生成
                character_audio_files = await self.generate_character_audio(content, f"podcast_{timestamp}")
                if character_audio_files:
                    result['character_audio_files'] = character_audio_files
            
            print("✅ ポッドキャスト生成完了！")
            print("\n" + "="*50)
            print("📻 生成されたポッドキャスト内容:")
            print("="*50)
            print(content)
            print("="*50)
            
            return result
            
        except Exception as e:
            print(f"❌ ポッドキャスト生成エラー: {e}")
            return {'success': False, 'error': str(e)}

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
