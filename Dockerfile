FROM python:3.9-slim

WORKDIR /app

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Poetryをインストール
RUN pip install poetry

# プロジェクトファイルをコピー
COPY pyproject.toml poetry.lock* ./

# 依存関係をインストール
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# アプリケーションコードをコピー
COPY . .

# デフォルトコマンド
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]