#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音声設定の違いをテストするためのスクリプト
みやにゃんとイヴにゃんの音声の違いを確認
"""

import os
import sys
from google.cloud import texttospeech

class VoiceTestGenerator:
    def __init__(self):
        # Google Cloud TTSクライアント
        self.tts_client = texttospeech.TextToSpeechClient()
        
        # キャラクター設定
        self.characters = {
            'miya': {
                'name': 'みやにゃん',
                'voice_settings': {
                    'language_code': 'ja-JP',
                    'name': 'ja-JP-Neural2-B',  # 明るい女性の声
                    'ssml_gender': texttospeech.SsmlVoiceGender.FEMALE,
                    'speaking_rate': 1.2,  # 速めで元気な印象
                    'pitch': 0.5,  # 軽く高めで掠れ防止（さらに調整）
                    'volume_gain_db': 0.5,  # 少し大きめで活発な印象
                    'sample_rate_hertz': 24000
                }
            },
            'eve': {
                'name': 'イヴにゃん',
                'voice_settings': {
                    'language_code': 'ja-JP',
                    'name': 'ja-JP-Neural2-C',  # 低めの男性の声
                    'ssml_gender': texttospeech.SsmlVoiceGender.MALE,
                    'speaking_rate': 1.0,  # 標準的な速さで落ち着いた印象
                    'pitch': -1.5,  # 低めで男性らしく、適度な差
                    'volume_gain_db': 0.0,  # 標準的な音量で落ち着いた印象
                    'sample_rate_hertz': 24000
                }
            }
        }
    
    def create_ssml_content(self, text: str, character: str) -> str:
        """キャラクター別SSML生成"""
        ssml = '<speak>'
        
        if character == 'miya':
            # みやにゃん：明るく元気に
            ssml += '<prosody rate="1.2" pitch="+0.5st" volume="medium">'
        elif character == 'eve':
            # イヴにゃん：落ち着いて低く
            ssml += '<prosody rate="1.0" pitch="-1.5st" volume="medium">'
        
        ssml += text
        
        if character in ['miya', 'eve']:
            ssml += '</prosody>'
        
        ssml += '</speak>'
        return ssml
    
    async def generate_test_audio(self, character: str, test_text: str, filename: str):
        """テスト音声生成"""
        try:
            char_settings = self.characters[character]
            voice_settings = char_settings['voice_settings']
            
            # SSML生成
            ssml_content = self.create_ssml_content(test_text, character)
            
            # 音声合成リクエスト作成
            synthesis_input = texttospeech.SynthesisInput(ssml=ssml_content)
            
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_settings['language_code'],
                name=voice_settings['name'],
                ssml_gender=voice_settings['ssml_gender']
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=voice_settings['speaking_rate'],
                pitch=voice_settings['pitch'],
                volume_gain_db=voice_settings['volume_gain_db'],
                sample_rate_hertz=voice_settings['sample_rate_hertz'],
                effects_profile_id=['telephony-class-application']
            )
            
            # 音声合成実行
            print(f"🎵 {char_settings['name']}の音声を生成中...")
            response = self.tts_client.synthesize_speech(
                input=synthesis_input, 
                voice=voice, 
                audio_config=audio_config
            )
            
            # ファイル保存
            with open(filename, "wb") as out:
                out.write(response.audio_content)
            
            print(f"✅ {filename} に保存しました")
            return filename
            
        except Exception as e:
            print(f"❌ {character}の音声生成エラー: {e}")
            return None

async def main():
    """メイン関数"""
    generator = VoiceTestGenerator()
    
    # テスト用テキスト
    test_text = "こんにちは、今日はDiscordコミュニティについて話しますにゃ。データ分析の結果、とても活発な議論が行われていることがわかりましたにゃ。"
    
    print("🎤 音声の違いテストを開始します...")
    
    # みやにゃんの音声生成
    await generator.generate_test_audio('miya', test_text, 'test_miya_voice.mp3')
    
    # イヴにゃんの音声生成
    await generator.generate_test_audio('eve', test_text, 'test_eve_voice.mp3')
    
    print("\n🎧 音声ファイルが生成されました。聞き比べてみてください：")
    print("📁 test_miya_voice.mp3 - みやにゃん（高音・速め・元気）")
    print("📁 test_eve_voice.mp3 - イヴにゃん（低音・ゆっくり・落ち着き）")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 