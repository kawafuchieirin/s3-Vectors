#!/bin/bash

echo "営業提案資料RAGシステムのセットアップを開始します..."

# .envファイルの作成
if [ ! -f .env ]; then
    echo ".envファイルを作成します..."
    cp .env.example .env
    echo ".envファイルが作成されました。AWS認証情報を設定してください。"
fi

# ディレクトリの作成
mkdir -p data/raw data/processed

# Poetry環境のセットアップ
if command -v poetry &> /dev/null; then
    echo "Poetryを使用して依存関係をインストールします..."
    poetry install
else
    echo "Poetryがインストールされていません。pipを使用します..."
    pip install -r requirements.txt
fi

echo ""
echo "セットアップが完了しました！"
echo ""
echo "次のステップ:"
echo "1. .envファイルを編集してAWS認証情報を設定してください"
echo "2. APIサーバーを起動: poetry run uvicorn src.api.main:app --reload"
echo "3. Streamlit UIを起動: poetry run streamlit run streamlit_app.py"
echo ""
echo "または、Docker Composeを使用:"
echo "docker-compose up"