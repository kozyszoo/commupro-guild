#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
voice.py
Discord にゃんこエージェント - 音声生成ユーティリティ

音声生成と処理を統合
- SSML生成
- 音声合成
- 音声ファイルの処理
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp
from google.cloud import texttospeech
from dotenv import load_dotenv

class VoiceGenerator:
    """音声生成クラス"""
    
    def __init__(self):
        """初期化"""
        self.client = None
        self.voice_settings = {
            'language_code': 'ja-JP',
            'name': 'ja-JP-Neural2-A',
            'ssml_gender': texttospeech.SsmlVoiceGender.FEMALE,
            'speaking_rate': 1.0,
            'pitch': 0.0
        }
        self.initialize_client()
    
    def initialize_client(self) -> bool:
        """Google Cloud Text-to-Speechクライアントを初期化"""
        try:
            self.client = texttospeech.TextToSpeechClient()
            print("✅ Google Cloud Text-to-Speechクライアントを初期化")
            return True
        except Exception as e:
            print(f"❌ Text-to-Speechクライアントの初期化に失敗: {e}")
            return False
    
    def generate_ssml(self, text: str, settings: Optional[Dict[str, Any]] = None) -> str:
        """SSMLを生成"""
        if settings:
            self.voice_settings.update(settings)
        
        ssml = f"""
        <speak>
            <voice name="{self.voice_settings['name']}">
                <prosody rate="{self.voice_settings['speaking_rate']}" pitch="{self.voice_settings['pitch']}st">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        return ssml.strip()
    
    async def synthesize_speech(self, text: str, output_file: str, settings: Optional[Dict[str, Any]] = None) -> bool:
        """音声を合成"""
        if not self.client:
            return False
        
        try:
            # SSMLの生成
            ssml = self.generate_ssml(text, settings)
            
            # 音声合成リクエストの設定
            synthesis_input = texttospeech.SynthesisInput(ssml=ssml)
            voice = texttospeech.VoiceSelectionParams(
                language_code=self.voice_settings['language_code'],
                name=self.voice_settings['name'],
                ssml_gender=self.voice_settings['ssml_gender']
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=self.voice_settings['speaking_rate'],
                pitch=self.voice_settings['pitch']
            )
            
            # 音声合成の実行
            response = await asyncio.to_thread(
                self.client.synthesize_speech,
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # 音声ファイルの保存
            with open(output_file, 'wb') as out:
                out.write(response.audio_content)
            
            print(f"✅ 音声を生成: {output_file}")
            return True
        except Exception as e:
            print(f"❌ 音声合成エラー: {e}")
            return False
    
    async def generate_podcast(self, script: str, output_dir: str, settings: Optional[Dict[str, Any]] = None) -> bool:
        """ポッドキャストを生成"""
        try:
            # 出力ディレクトリの作成
            os.makedirs(output_dir, exist_ok=True)
            
            # スクリプトを段落に分割
            paragraphs = [p.strip() for p in script.split('\n\n') if p.strip()]
            
            # 各段落の音声を生成
            audio_files = []
            for i, paragraph in enumerate(paragraphs):
                output_file = os.path.join(output_dir, f'segment_{i+1:03d}.mp3')
                if await self.synthesize_speech(paragraph, output_file, settings):
                    audio_files.append(output_file)
            
            if not audio_files:
                return False
            
            # 音声ファイルを結合
            final_output = os.path.join(output_dir, 'podcast.mp3')
            await self.merge_audio_files(audio_files, final_output)
            
            # 一時ファイルの削除
            for file in audio_files:
                os.remove(file)
            
            print(f"✅ ポッドキャストを生成: {final_output}")
            return True
        except Exception as e:
            print(f"❌ ポッドキャスト生成エラー: {e}")
            return False
    
    async def merge_audio_files(self, input_files: list, output_file: str) -> bool:
        """音声ファイルを結合"""
        try:
            # FFmpegを使用して音声ファイルを結合
            input_list = '\n'.join([f"file '{f}'" for f in input_files])
            list_file = 'input_list.txt'
            
            with open(list_file, 'w') as f:
                f.write(input_list)
            
            cmd = f'ffmpeg -f concat -safe 0 -i {list_file} -c copy {output_file}'
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # 一時ファイルの削除
            os.remove(list_file)
            
            if process.returncode == 0:
                print(f"✅ 音声ファイルを結合: {output_file}")
                return True
            else:
                print(f"❌ 音声ファイル結合エラー: {stderr.decode()}")
                return False
        except Exception as e:
            print(f"❌ 音声ファイル結合エラー: {e}")
            return False

async def main():
    """メイン実行関数"""
    # 環境変数の読み込み
    load_dotenv()
    
    # VoiceGeneratorのインスタンス化
    generator = VoiceGenerator()
    
    # テスト用の音声設定
    test_settings = {
        'speaking_rate': 1.2,
        'pitch': 2.0
    }
    
    # テスト用のテキスト
    test_text = "こんにちは！にゃんこエージェントです。"
    
    # 音声の生成
    if await generator.synthesize_speech(test_text, 'test_voice.mp3', test_settings):
        print("✅ テスト音声を生成")
    
    # テスト用のポッドキャストスクリプト
    test_script = """
    こんにちは！にゃんこエージェントです。
    
    今日は素晴らしい天気ですね。
    
    みなさん、お元気ですか？
    """
    
    # ポッドキャストの生成
    if await generator.generate_podcast(test_script, 'test_podcast', test_settings):
        print("✅ テストポッドキャストを生成")

if __name__ == '__main__':
    asyncio.run(main()) 