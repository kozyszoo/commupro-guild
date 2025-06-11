# Discord にゃんこエージェント ボット

## プロジェクト構造

```
bot/
├── src/                    # メインのソースコード
│   ├── core/              # コア機能
│   │   ├── bot.py        # メインボット
│   │   ├── podcast.py    # ポッドキャスト機能
│   │   └── manager.py    # ボット管理機能
│   ├── utils/            # ユーティリティ
│   │   ├── firestore.py  # Firestore関連
│   │   └── voice.py      # 音声関連
│   └── scripts/          # スクリプト
│       ├── deploy.py     # デプロイスクリプト
│       └── test.py       # テストスクリプト
├── config/               # 設定ファイル
│   ├── nginx.conf
│   └── docker/
│       ├── Dockerfile
│       └── docker-compose.yml
├── docs/                # ドキュメント
│   ├── README.md
│   ├── DEPLOYMENT.md
│   └── TUTORIAL.md
└── tests/              # テスト
    ├── test_voice.py
    └── test_data.py
```

## セットアップ

1. 環境変数の設定
```bash
cp env_example.txt .env
# .envファイルを編集して必要な環境変数を設定
```

2. 依存関係のインストール
```bash
pip install -r requirements.txt
```

3. ボットの起動
```bash
python src/scripts/start_bots.py
```

## 主要機能

- Discordボット機能
- ポッドキャスト生成
- マルチボット管理
- ヘルスチェック
- Firestoreデータ管理

## デプロイメント

詳細は [DEPLOYMENT.md](docs/DEPLOYMENT.md) を参照してください。

## ドキュメント

- [Discord Bot](docs/DISCORD_BOT.md)
- [Podcast](docs/PODCAST.md)
- [Upload](docs/UPLOAD.md)
- [Onboarding](docs/ONBOARDING.md)

## テスト

```bash
python -m pytest tests/
```

## ライセンス

MIT License