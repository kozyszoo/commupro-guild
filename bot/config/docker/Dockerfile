# Discord エンタメコンテンツ制作ボット - Dockerfile
FROM python:3.10-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージの更新とffmpeg追加（音声生成用）
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    build-essential \
    tzdata \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime

# Python依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーション全体をコピー
COPY . .

# 環境変数の設定
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV BOT_CHARACTER=miya
EXPOSE 8080

# 非rootユーザーを作成
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Discord Botを起動
CMD ["python3", "run_entertainment_bot.py"]