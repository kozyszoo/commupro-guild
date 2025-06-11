#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
content_creator.py
エンタメコンテンツ制作統合システム

週次まとめテキスト・音声ファイル生成、Google Drive保存、Discord投稿の統合処理
"""

import os
import json
import datetime
import asyncio
import tempfile
from typing import Dict, Any, Optional, List
from google.cloud import texttospeech
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from firebase_admin import firestore
import discord
from .discord_analytics import DiscordAnalytics
from .podcast import PodcastGenerator

class ContentCreator:
    """エンタメコンテンツ制作統合クラス"""
    
    def __init__(self, firestore_client, discord_bot: Optional[discord.Client] = None):
        self.db = firestore_client
        self.bot = discord_bot
        
        # Discord分析システム
        self.analytics = DiscordAnalytics(firestore_client)
        
        # Podcast生成システム
        self.podcast_generator = PodcastGenerator()
        
        # Google Drive API初期化
        self.drive_service = None
        self._initialize_drive_service()
        
        # TTS設定
        self.tts_client = None
        self._initialize_tts_client()
        
        # Discord設定
        self.target_channel_id = os.getenv('DISCORD_SUMMARY_CHANNEL_ID')
        
    def _initialize_drive_service(self):
        """Google Drive API サービスを初期化"""
        try:
            key_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH', 
                               './nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json')
            
            if os.path.exists(key_path):
                credentials = service_account.Credentials.from_service_account_file(
                    key_path,
                    scopes=['https://www.googleapis.com/auth/drive.file']
                )
            elif os.getenv('FIREBASE_SERVICE_ACCOUNT'):
                service_account_info = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT'))
                credentials = service_account.Credentials.from_service_account_info(
                    service_account_info,
                    scopes=['https://www.googleapis.com/auth/drive.file']
                )
            else:
                raise FileNotFoundError("Google Cloud認証情報が見つかりません")
            
            self.drive_service = build('drive', 'v3', credentials=credentials)
            print("✅ Google Drive API初期化完了")
            
        except Exception as e:
            print(f"⚠️ Google Drive API初期化エラー: {e}")
            self.drive_service = None
    
    def _initialize_tts_client(self):
        """Text-to-Speech クライアントを初期化"""
        try:
            key_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH', 
                               './nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json')
            
            if os.path.exists(key_path):
                self.tts_client = texttospeech.TextToSpeechClient.from_service_account_json(key_path)
            elif os.getenv('FIREBASE_SERVICE_ACCOUNT'):
                service_account_info = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT'))
                credentials = service_account.Credentials.from_service_account_info(service_account_info)
                self.tts_client = texttospeech.TextToSpeechClient(credentials=credentials)
            else:
                self.tts_client = texttospeech.TextToSpeechClient()
            
            print("✅ Text-to-Speech クライアント初期化完了")
            
        except Exception as e:
            print(f"⚠️ TTS クライアント初期化エラー: {e}")
            self.tts_client = None
    
    async def generate_enhanced_tts_audio(self, content: str, filename: Optional[str] = None) -> Optional[str]:
        """強化されたText-to-Speech音声生成（キャラクター別対応）"""
        if not self.tts_client:
            print("❌ TTS クライアントが初期化されていません")
            return None
        
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"weekly_summary_{timestamp}.mp3"
        
        try:
            print("🎵 強化された音声ファイル生成中...")
            
            # キャラクター別音声生成を使用
            audio_files = await self.podcast_generator.generate_character_audio(content, filename.replace('.mp3', ''))
            
            if audio_files:
                # 最初の音声ファイルを返す（統合版は別途実装可能）
                first_audio = list(audio_files.values())[0]
                print(f"✅ 強化音声ファイル生成完了: {first_audio}")
                return first_audio
            else:
                # フォールバック: 通常のTTS
                return await self._generate_standard_tts(content, filename)
                
        except Exception as e:
            print(f"❌ 強化TTS生成エラー: {e}")
            return await self._generate_standard_tts(content, filename)
    
    async def _generate_standard_tts(self, content: str, filename: str) -> Optional[str]:
        """標準のTTS音声生成"""
        try:
            # テキストクリーンアップ
            clean_content = self.podcast_generator.clean_text_for_tts(content)
            
            # 音声設定
            synthesis_input = texttospeech.SynthesisInput(text=clean_content)
            voice = texttospeech.VoiceSelectionParams(
                language_code='ja-JP',
                name='ja-JP-Neural2-B',
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.15,
                pitch=0.0,
                volume_gain_db=2.0,
                sample_rate_hertz=24000
            )
            
            # 音声合成
            response = await asyncio.to_thread(
                self.tts_client.synthesize_speech,
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # ファイル保存
            with open(filename, 'wb') as out:
                out.write(response.audio_content)
            
            print(f"✅ 標準音声ファイル生成完了: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ 標準TTS生成エラー: {e}")
            return None
    
    async def upload_to_google_drive(self, file_path: str, filename: str, folder_id: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Google Driveにファイルをアップロード"""
        if not self.drive_service:
            print("❌ Google Drive サービスが初期化されていません")
            return None
        
        try:
            print(f"☁️ Google Driveにアップロード中: {filename}")
            
            # ファイルメタデータ
            file_metadata = {
                'name': filename,
                'parents': [folder_id] if folder_id else []
            }
            
            # ファイルの MIME タイプを推定
            if filename.endswith('.mp3'):
                mimetype = 'audio/mpeg'
            elif filename.endswith('.txt'):
                mimetype = 'text/plain'
            elif filename.endswith('.json'):
                mimetype = 'application/json'
            else:
                mimetype = 'application/octet-stream'
            
            # ファイルアップロード
            media = MediaFileUpload(file_path, mimetype=mimetype)
            file = await asyncio.to_thread(
                self.drive_service.files().create,
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,webContentLink'
            )
            
            result = file.execute()
            
            # ファイル共有設定（読み取り専用で誰でもアクセス可能）
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            
            await asyncio.to_thread(
                self.drive_service.permissions().create,
                fileId=result['id'],
                body=permission
            )
            
            print(f"✅ Google Driveアップロード完了")
            print(f"   ファイルID: {result['id']}")
            print(f"   表示リンク: {result['webViewLink']}")
            
            return {
                'file_id': result['id'],
                'filename': result['name'],
                'view_link': result['webViewLink'],
                'download_link': result.get('webContentLink', ''),
                'uploaded_at': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Google Driveアップロードエラー: {e}")
            return None
    
    async def post_to_discord(self, summary_text: str, audio_file_info: Optional[Dict] = None, 
                            text_file_info: Optional[Dict] = None) -> bool:
        """Discordチャンネルに投稿"""
        if not self.bot or not self.target_channel_id:
            print("❌ Discord設定が不完全です")
            return False
        
        try:
            channel = self.bot.get_channel(int(self.target_channel_id))
            if not channel:
                print(f"❌ チャンネルが見つかりません: {self.target_channel_id}")
                return False
            
            print(f"📝 Discord投稿中...")
            
            # 投稿用のメッセージ作成
            embed = discord.Embed(
                title="📻 今週のまとめ",
                description="今週のDiscordコミュニティ活動をお届けします！",
                color=0x00ff00,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            
            # テキスト要約を追加（長すぎる場合は短縮）
            if len(summary_text) > 1000:
                summary_preview = summary_text[:1000] + "..."
            else:
                summary_preview = summary_text
            
            embed.add_field(
                name="今週の活動まとめ",
                value=summary_preview,
                inline=False
            )
            
            # Google Driveリンク追加
            if audio_file_info:
                embed.add_field(
                    name="🎵 音声ファイル",
                    value=f"[音声を聞く]({audio_file_info['view_link']})",
                    inline=True
                )
            
            if text_file_info:
                embed.add_field(
                    name="📄 完全版テキスト",
                    value=f"[テキストを読む]({text_file_info['view_link']})",
                    inline=True
                )
            
            embed.set_footer(text="by にゃんこボット • エンタメコンテンツ制作システム")
            
            # メッセージ送信
            message = await channel.send(embed=embed)
            
            print(f"✅ Discord投稿完了: {message.jump_url}")
            return True
            
        except Exception as e:
            print(f"❌ Discord投稿エラー: {e}")
            return False
    
    async def create_weekly_content(self, days: int = 7) -> Dict[str, Any]:
        """週次コンテンツ制作のメイン処理"""
        print("🎬 週次エンタメコンテンツ制作を開始...")
        
        try:
            # 1. 週次まとめテキスト生成
            print("📊 週次活動分析中...")
            summary_result = await self.analytics.generate_and_save_weekly_summary(days)
            
            if not summary_result['success']:
                return {'success': False, 'error': 'Failed to generate summary'}
            
            summary_text = summary_result['summary_text']
            
            # 2. 音声ファイル生成
            print("🎵 音声ファイル生成中...")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"weekly_summary_{timestamp}.mp3"
            
            audio_file_path = await self.generate_enhanced_tts_audio(summary_text, audio_filename)
            
            # 3. テキストファイル保存
            text_filename = f"weekly_summary_{timestamp}.txt"
            with open(text_filename, 'w', encoding='utf-8') as f:
                f.write("# Discord コミュニティ 今週のまとめ\n")
                f.write(f"# 生成日時: {datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n\n")
                f.write(summary_text)
            
            # 4. Google Driveアップロード
            drive_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
            
            audio_drive_info = None
            text_drive_info = None
            
            if audio_file_path and os.path.exists(audio_file_path):
                audio_drive_info = await self.upload_to_google_drive(
                    audio_file_path, audio_filename, drive_folder_id
                )
            
            if os.path.exists(text_filename):
                text_drive_info = await self.upload_to_google_drive(
                    text_filename, text_filename, drive_folder_id
                )
            
            # 5. Discord投稿
            discord_posted = await self.post_to_discord(
                summary_text, audio_drive_info, text_drive_info
            )
            
            # 6. 結果のまとめ
            result = {
                'success': True,
                'summary_id': summary_result['summary_id'],
                'summary_text': summary_text,
                'audio_file': {
                    'local_path': audio_file_path,
                    'drive_info': audio_drive_info
                },
                'text_file': {
                    'local_path': text_filename,
                    'drive_info': text_drive_info
                },
                'discord_posted': discord_posted,
                'generated_at': datetime.datetime.now().isoformat(),
                'stats': summary_result['activities_stats']
            }
            
            # 7. ローカルファイルクリーンアップ（オプション）
            cleanup_local_files = os.getenv('CLEANUP_LOCAL_FILES', 'true').lower() == 'true'
            if cleanup_local_files:
                try:
                    if audio_file_path and os.path.exists(audio_file_path):
                        os.remove(audio_file_path)
                    if os.path.exists(text_filename):
                        os.remove(text_filename)
                    print("🧹 ローカルファイルクリーンアップ完了")
                except Exception as e:
                    print(f"⚠️ ファイルクリーンアップエラー: {e}")
            
            print("✅ 週次エンタメコンテンツ制作完了！")
            return result
            
        except Exception as e:
            print(f"❌ コンテンツ制作エラー: {e}")
            return {'success': False, 'error': str(e)}
    
    async def save_content_record(self, result: Dict[str, Any]) -> Optional[str]:
        """コンテンツ制作記録をFirestoreに保存"""
        try:
            record_data = {
                'type': 'weekly_entertainment_content',
                'generated_at': datetime.datetime.now(datetime.timezone.utc),
                'summary_id': result.get('summary_id'),
                'files': {
                    'audio': result.get('audio_file', {}),
                    'text': result.get('text_file', {})
                },
                'discord_posted': result.get('discord_posted', False),
                'stats': result.get('stats', {}),
                'success': result.get('success', False),
                'metadata': {
                    'system': 'content_creator.py',
                    'version': '1.0'
                }
            }
            
            doc_ref = await asyncio.to_thread(self.db.collection('content_records').add, record_data)
            record_id = doc_ref[1].id
            
            print(f"✅ コンテンツ記録保存完了: {record_id}")
            return record_id
            
        except Exception as e:
            print(f"❌ コンテンツ記録保存エラー: {e}")
            return None