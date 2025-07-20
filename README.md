# s3-Vectors RAG システム

Amazon S3 Vectorsを活用した営業提案資料作成のためのRAGシステム

[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Framework-green)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-red)](https://streamlit.io/)
[![AWS](https://img.shields.io/badge/AWS-S3%20Vectors-orange)](https://aws.amazon.com/)

## 🚀 クイックスタート

**たった3ステップで即座に動作します！**

```bash
git clone <repository-url>
cd s3-Vectors
docker-compose up -d
```

→ http://localhost:8501 でWebUIにアクセス

## 概要

このプロジェクトは、Amazon S3 VectorsとAmazon Bedrockを活用して、営業資料を効率的に管理し、顧客ニーズに合わせた提案書を自動生成するRAG（Retrieval-Augmented Generation）システムです。

**🎯 特徴**: 環境変数の設定なしで、すぐにデモモードで全機能をテストできます。

## 主な機能

### 📄 ドキュメント管理
- PDF、Word、テキストファイルのアップロードと自動処理
- 文書の自動チャンキングとベクトル化
- メタデータ（顧客名、業界、文書タイプ）による分類

### 🔍 インテリジェント検索
- セマンティック検索による関連文書の検索
- 類似度スコアによるランキング
- フィルタリング機能（業界、顧客、文書タイプ）

### 💡 自動提案生成
- 顧客の要望に基づいた営業提案書の自動生成
- 関連する営業資料の自動選択と参照
- 業界特化型の提案内容カスタマイズ

### 🌐 Webインターフェース
- 直感的なStreamlit WebUI
- ドラッグ&ドロップによるファイルアップロード
- リアルタイムでの提案生成と結果表示

## 技術スタック

### バックエンド
- **Python 3.9+**: メインプログラミング言語
- **FastAPI**: REST API フレームワーク
- **Amazon S3 Vectors**: ベクトルストレージ（プレビュー版）
- **Amazon Bedrock**: 埋め込み生成とテキスト生成
- **LangChain**: ドキュメント処理とRAGパイプライン

### フロントエンド
- **Streamlit**: Webインターフェース
- **Docker**: コンテナ化とデプロイメント

### 依存関係管理
- **Poetry**: Pythonパッケージ管理

## アーキテクチャ

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │ ─→ │   FastAPI       │ ─→ │  Amazon S3      │
│                 │    │   Backend       │    │  Vectors        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Amazon Bedrock │
                       │  - Embeddings   │
                       │  - Text Gen     │
                       └─────────────────┘
```

## セットアップとインストール

### 前提条件
- Docker Desktop（macOS/Windows）またはDocker Engine（Linux）

**オプション（本格運用の場合）**：
- AWS アカウントとクレデンシャル
- S3 Vectors対応リージョンのアクセス権限
- Amazon Bedrock利用権限

### 1. リポジトリのクローン
```bash
git clone <repository-url>
cd s3-Vectors
```

### 2. 環境変数の設定（オプション）
```bash
# .env.exampleをコピーして.envファイルを作成（オプション）
cp .env.example .env

# .envファイルを編集して必要な環境変数を設定
```

**重要**: 環境変数の設定は**オプション**です。設定なしでもデモモードで動作します。

#### デモモード（推奨・すぐに試せます）
環境変数を設定せずに起動すると、以下の機能で動作します：
- ローカルファイルシステムでのベクトル保存
- モック埋め込みサービス（ハッシュベース）
- 完全なRAG機能のテスト

#### 本格運用モード
実際のAWSサービスを使用する場合の環境変数：
```env
# AWS設定
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# S3 Vectors設定
S3_VECTOR_BUCKET_NAME=your-vector-bucket-name
S3_VECTOR_INDEX_NAME=sales-documents-index

# Bedrock設定
BEDROCK_MODEL_ID=amazon.titan-embed-text-v2:0
BEDROCK_GENERATION_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

### 3. Dockerコンテナの起動
```bash
# コンテナをビルドして起動
docker-compose up -d

# ログを確認（オプション）
docker-compose logs -f
```

### 4. アプリケーションへのアクセス
- **Streamlit UI**: http://localhost:8501 （メインのWebインターフェース）
- **API**: http://localhost:8000 （REST API）

### 5. クイックテスト
すぐに動作確認したい場合：

1. **WebUIでテスト**:
   - http://localhost:8501 にアクセス
   - サンプルテキストファイルをアップロード
   - 検索機能をテスト

2. **コマンドラインでテスト**:
   ```bash
   # テストファイルを作成
   echo "営業提案資料のサンプルです。クラウドソリューションを提供します。" > test.txt
   
   # アップロード
   curl -X POST -F "file=@test.txt" -F "customer_name=テスト会社" -F "industry=IT" http://localhost:8000/api/documents/upload
   
   # 検索
   curl -X POST -H "Content-Type: application/json" -d '{"query":"クラウド","top_k":3}' http://localhost:8000/api/documents/search
   ```

## 使用方法

### 営業資料のアップロード
1. Streamlit UI（http://localhost:8501）にアクセス
2. 「📤 資料アップロード」タブを選択
3. PDF、Word、テキストファイルをドラッグ&ドロップ
4. メタデータ（顧客名、業界、資料タイプ）を入力
5. 「アップロード」ボタンをクリック

### 提案書の生成
1. 「💡 提案生成」タブを選択
2. 顧客情報（顧客名、業界、予算）を入力
3. 要望・課題を詳細に記述
4. 「提案を生成」ボタンをクリック
5. 生成された提案と参照資料を確認

### 資料の検索
1. 「🔍 資料検索」タブを選択
2. 検索キーワードを入力
3. 「検索」ボタンをクリック
4. 関連度順に表示される結果を確認

## 開発者向け情報

### ローカル開発環境
```bash
# 依存関係のインストール
poetry install

# API サーバーの起動
poetry run uvicorn src.api.main:app --reload

# Streamlit UIの起動
poetry run streamlit run streamlit_app.py

# テストの実行
poetry run pytest

# コードフォーマット
poetry run black src/
poetry run isort src/

# 型チェック
poetry run mypy src/
```

### API エンドポイント
- `POST /api/documents/upload` - ドキュメントアップロード
- `POST /api/documents/search` - ドキュメント検索
- `POST /api/proposals/generate` - 提案生成
- `GET /api/health` - ヘルスチェック

### プロジェクト構造
```
s3-Vectors/
├── src/
│   ├── api/           # FastAPI REST API
│   ├── core/          # コアビジネスロジック
│   │   ├── config.py           # 設定管理
│   │   ├── document_processor.py # ドキュメント処理
│   │   ├── embeddings.py       # 埋め込み生成（Bedrock + モック）
│   │   ├── vector_store.py     # ベクトルストア（S3 + ローカル）
│   │   └── rag_engine.py       # RAG実装
│   ├── utils/         # ユーティリティ関数
│   └── web/           # Webインターフェース
├── tests/             # テストファイル
├── data/              # データ格納
│   └── vector_store/  # ローカルベクトルストレージ
├── streamlit_app.py   # Streamlit UIエントリーポイント
└── docker-compose.yml # Docker設定
```

## 技術的な特徴

### 自動フォールバック機能
システムには以下の自動フォールバック機能が搭載されています：

1. **埋め込みサービス**:
   - Amazon Bedrock（本格運用）
   - ↓ フォールバック ↓
   - モック埋め込み（デモ・開発）

2. **ベクトルストレージ**:
   - Amazon S3 Vectors（本格運用）
   - ↓ フォールバック ↓
   - ローカルファイルシステム（デモ・開発）

3. **テキスト生成**:
   - Amazon Bedrock Claude（本格運用）
   - ↓ フォールバック ↓
   - テンプレートベース生成（デモ・開発）

## デモ vs 本格運用

### デモモード（デフォルト）
**特徴**: 環境変数なしで即座に動作
- ✅ ローカルファイルストレージ
- ✅ モック埋め込み（ハッシュベース）
- ✅ 全機能テスト可能
- ⚠️ 実際のAIモデルは使用しない

**最適な用途**:
- 機能検証・デモンストレーション
- 開発・テスト環境
- AWSアカウントなしでの評価

### 本格運用モード
**特徴**: AWS認証情報設定で有効化
- ✅ Amazon S3 Vectors
- ✅ Amazon Bedrock埋め込み
- ✅ Amazon Bedrock テキスト生成
- ✅ 本番品質の結果

**最適な用途**:
- 本番環境
- 高品質なRAG結果が必要
- 大規模データ処理

## 注意事項

### Amazon S3 Vectors（プレビュー版）
- 現在プレビュー版のため、仕様変更の可能性があります
- 対応リージョンが限定されています
- 特殊なIAM権限が必要です

### セキュリティ
- AWS認証情報を環境変数で管理
- Docker環境での実行を推奨
- 本番環境では追加のセキュリティ対策を実装してください

## トラブルシューティング

### よくある問題

#### デモモード
1. **Docker起動失敗**: Dockerデーモンの起動状態を確認
2. **ポート競合**: 8000, 8501ポートが他のアプリで使用されていないか確認

#### 本格運用モード  
1. **S3バケット作成エラー**: リージョン設定とIAM権限を確認
2. **Bedrock API エラー**: モデルIDと権限設定を確認
3. **Access Denied**: Bedrock利用権限の確認

### ログの確認
```bash
# コンテナログの確認
docker-compose logs api
docker-compose logs streamlit

# リアルタイムログの監視
docker-compose logs -f
```

## 参考資料

- [Amazon S3 Vectors公式ドキュメント](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors.html)
- [Amazon Bedrock開発者ガイド](https://docs.aws.amazon.com/bedrock/)
- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [Streamlit公式ドキュメント](https://docs.streamlit.io/)

## ライセンス

MIT License - 詳細はLICENSEファイルを参照してください。