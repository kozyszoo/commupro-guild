# Firestore データアップロードスクリプト

`public/data` 配下の JSON ファイルを Firestore にアップロードするためのスクリプトです。

## 前提条件

1. **Python 3.7以上** がインストールされていること
2. **Firebase プロジェクト** が設定されていること
3. **サービスアカウントキー** または **Application Default Credentials** が設定されていること

## セットアップ

### 1. 依存関係のインストール

```bash
cd script
pip install -r requirements.txt
```

### 2. Firebase認証の設定

#### 方法A: サービスアカウントキーを使用

1. Firebase Console でサービスアカウントキーを生成
2. JSONファイルをダウンロード
3. 環境変数を設定:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
```

#### 方法B: Application Default Credentials を使用

Google Cloud SDK がインストールされている場合:

```bash
gcloud auth application-default login
```

## 使用方法

### 基本的な使用方法

```bash
cd public
python upload_firestore.py
```

### スクリプトの動作

1. `public/data` ディレクトリ内のすべての `.json` ファイルを検索
2. 各ファイルの構造を解析してコレクション名を決定
3. Firestore にバッチ処理でデータをアップロード
4. 進捗状況とエラーを表示

### サポートされるJSONファイル構造

#### パターン1: ファイル名がコレクション名と一致
```json
// users.json
{
  "users": {
    "user1": { "name": "太郎", "age": 25 },
    "user2": { "name": "花子", "age": 30 }
  }
}
```

#### パターン2: トップレベルキーがコレクション名
```json
// data.json
{
  "topics": {
    "topic1": { "name": "React", "popularity": 85 },
    "topic2": { "name": "Vue", "popularity": 70 }
  }
}
```

#### パターン3: 直接オブジェクト構造
```json
// events.json
{
  "event1": { "title": "勉強会", "date": "2024-01-15" },
  "event2": { "title": "ハッカソン", "date": "2024-02-20" }
}
```

## 機能

- ✅ **バッチ処理**: 大量データを効率的にアップロード（デフォルト500件ずつ）
- ✅ **エラーハンドリング**: 詳細なエラーメッセージと継続処理
- ✅ **進捗表示**: リアルタイムでアップロード状況を表示
- ✅ **柔軟なJSON構造**: 複数のJSONファイル形式に対応
- ✅ **UTF-8対応**: 日本語データの正しい処理

## 注意事項

- 既存のドキュメントは上書きされます
- 大量データの場合、Firestoreの書き込み制限に注意してください
- ネットワークエラーが発生した場合は、再実行してください

## トラブルシューティング

### 認証エラー
```
Firebase初期化エラー: ...
```
- `GOOGLE_APPLICATION_CREDENTIALS` 環境変数が正しく設定されているか確認
- サービスアカウントキーファイルのパスが正しいか確認
- Firebase プロジェクトの権限設定を確認

### ファイル読み込みエラー
```
ファイル読み込みエラー: ...
```
- JSONファイルの構文が正しいか確認
- ファイルの文字エンコーディングがUTF-8か確認

### アップロードエラー
```
バッチアップロードエラー: ...
```
- インターネット接続を確認
- Firestoreの書き込み権限を確認
- データサイズが制限内か確認（1ドキュメント最大1MB）

## 対象ファイル

現在の `public/data` ディレクトリには以下のファイルがあります：

- `admin_users.json` - 管理者ユーザー情報
- `analytics_sessions.json` - 分析セッションデータ
- `bot_actions.json` - ボットアクション履歴
- `events.json` - イベント情報
- `guilds.json` - ギルド情報
- `interactions.json` - ユーザーインタラクション
- `podcasts.json` - ポッドキャスト情報
- `topics.json` - トピック情報
- `user_matches.json` - ユーザーマッチング結果
- `users.json` - ユーザー情報 