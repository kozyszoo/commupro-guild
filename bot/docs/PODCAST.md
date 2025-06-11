# Discord にゃんこエージェント - ポッドキャスト生成スクリプト

## 概要

`make_podcast.py` は、Discordサーバーの最近の活動を分析して、２匹の猫のキャラクター（みやにゃん・イヴにゃん）による週刊ポッドキャストを自動生成するスクリプトです。

## 機能

### 📊 データ分析
- 過去7日間のDiscordインタラクションを分析
- 人気キーワードの抽出
- 技術トピックの特定
- チャンネル別・ユーザー別活動統計
- イベント情報の取得

### 🎭 キャラクター設定
- **みやにゃん** 🐈: フレンドリーで好奇心旺盛、新しい技術に興味津々
- **イヴにゃん** 🐱: クールで分析的、データや統計が得意

### 📝 コンテンツ生成
- 自然な会話形式のポッドキャスト台本
- 統計情報の紹介
- 技術トピックの解説
- イベント情報の案内
- コミュニティへの感謝メッセージ

### 🎵 音声生成（Text-to-Speech）
- 統合音声ファイル（全体）の生成
- キャラクター別音声ファイルの生成
- 日本語音声合成（gTTS使用）

### 💾 データ保存
- Firestoreへの保存
- テキストファイルへの保存
- 音声ファイルの生成

## 必要な依存関係

```bash
# 基本ライブラリ
pip install firebase-admin python-dotenv

# 音声生成ライブラリ
pip install gTTS pydub
```

または、requirements.txtから一括インストール：

```bash
pip install -r requirements.txt
```

## 環境設定

### 1. Firebase設定

以下のいずれかの方法でFirebase認証情報を設定：

#### 方法A: サービスアカウントキーファイル
```bash
# .envファイルに追加
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=./nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json
```

#### 方法B: 環境変数
```bash
# .envファイルに追加
FIREBASE_SERVICE_ACCOUNT='{"type": "service_account", ...}'
```

### 2. ディレクトリ構造
```
bot/
├── make_podcast.py          # メインスクリプト
├── requirements.txt         # 依存関係
├── .env                    # 環境変数
├── nyanco-bot-firebase-adminsdk-fbsvc-d65403c7ca.json  # Firebase認証
└── README_podcast.md       # このファイル
```

## 使用方法

### 基本的な実行

```bash
cd bot
python make_podcast.py
```

### プログラムからの使用

```python
import asyncio
from make_podcast import PodcastGenerator

async def main():
    generator = PodcastGenerator()
    
    # ポッドキャスト生成
    result = await generator.generate_podcast(
        days=7,                    # 分析期間（日数）
        save_to_firestore=True,    # Firestoreに保存
        save_to_file=True,         # ファイルに保存
        generate_audio=True        # 音声ファイル生成
    )
    
    if result['success']:
        print(f"生成完了: {result['filename']}")
        print(f"音声ファイル: {result['audio_file']}")
    else:
        print(f"エラー: {result['error']}")

asyncio.run(main())
```

## 出力ファイル

### テキストファイル
- `podcast_YYYYMMDD_HHMMSS.txt`: ポッドキャスト台本

### 音声ファイル
- `podcast_full_YYYYMMDD_HHMMSS.mp3`: 統合音声ファイル
- `podcast_YYYYMMDD_HHMMSS_miya.mp3`: みやにゃんの音声
- `podcast_YYYYMMDD_HHMMSS_eve.mp3`: イヴにゃんの音声
- `podcast_YYYYMMDD_HHMMSS_narrator.mp3`: ナレーション音声

## ポッドキャスト内容例

```
🐈 **みやにゃん**: みなさん、こんにちはだにゃ！今週のホットトピックをお届けするにゃ！

🐱 **イヴにゃん**: こんにちはですにゃ。今週も活発な議論が繰り広げられていたのにゃ。

🐈 **みやにゃん**: 今週は全部で42件のやり取りがあったにゃ！みんな元気だにゃ〜

🐱 **イヴにゃん**: 分析によると、今週は「React」というキーワードが8回も登場していたのにゃ。

🐈 **みやにゃん**: 技術的な話題では、ReactやTypeScriptについて熱い議論があったにゃ！
```

## カスタマイズ

### 分析期間の変更
```python
result = await generator.generate_podcast(days=14)  # 14日間のデータを分析
```

### 音声生成の無効化
```python
result = await generator.generate_podcast(generate_audio=False)
```

### キャラクター設定の変更
```python
generator.characters['miya']['name'] = 'カスタムにゃん'
generator.characters['miya']['speaking_style'] = 'だよ、です'
```

## トラブルシューティング

### Firebase接続エラー
```
❌ Firebase Firestoreの初期化に失敗しました
```
- サービスアカウントキーファイルのパスを確認
- Firebase認証情報の形式を確認
- ネットワーク接続を確認

### 音声生成エラー
```
❌ 音声ファイル生成エラー
```
- gTTSライブラリがインストールされているか確認
- インターネット接続を確認（gTTSはオンラインサービス）
- ディスク容量を確認

### データ取得エラー
```
⚠️ 分析対象のインタラクションが見つかりませんでした
```
- Firestoreにデータが存在するか確認
- 分析期間を長くしてみる
- Discordボットが正常に動作しているか確認

## 技術仕様

### 使用技術
- **Python 3.8+**
- **Firebase Admin SDK**: Firestoreデータベース接続
- **gTTS**: Google Text-to-Speech API
- **asyncio**: 非同期処理

### データソース
- `interactions`: Discordメッセージ・リアクション等
- `events`: Discordスケジュールイベント
- `users`: ユーザー情報
- `topics`: トピック分析結果

### 音声生成仕様
- **言語**: 日本語 (ja)
- **形式**: MP3
- **品質**: 標準（slow=False）
- **エンコーディング**: UTF-8

## ライセンス

このスクリプトは、Discord にゃんこエージェント プロジェクトの一部です。

## 更新履歴

- **v1.0** (2025/05/31): 初回リリース
  - 基本的なポッドキャスト生成機能
  - Text-to-Speech音声生成
  - Firestore連携
  - キャラクター別音声分離
