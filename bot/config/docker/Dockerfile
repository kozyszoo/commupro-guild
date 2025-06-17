# Discord にゃんこエージェント ボット - Dockerfile
# Python 3.10 ベースイメージを使用
FROM python:3.10-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージの更新、ビルドツール、タイムゾーン設定
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    build-essential \
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime

# 依存関係ファイルをコピー
COPY bot/requirements.txt .

# Python依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY bot/run_entertainment_bot.py .
COPY bot/src/ ./src/

# 環境変数の設定（デフォルト値）
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# ポート設定（Cloud Runで必要）
ENV PORT=8080
EXPOSE 8080

# 非rootユーザーを作成してセキュリティを向上
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# アプリケーションを起動（存在するファイルを実行）
CMD ["python3", "run_entertainment_bot.py"]