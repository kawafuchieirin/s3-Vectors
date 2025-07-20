"""S3 Vectorsを使用したベクトルストア実装"""
import json
import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from src.core.config import settings
from src.core.embeddings import EmbeddingService


logger = logging.getLogger(__name__)


class S3VectorStore:
    """S3 Vectorsを使用したベクトルストア（ローカルファイルシステム版）"""
    
    def __init__(self):
        # S3クライアントは保持するが、ローカルストレージを優先使用
        try:
            self.s3_client = boto3.client(
                "s3",
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            )
            self.s3_available = True
        except Exception as e:
            logger.warning(f"S3 client initialization failed: {e}. Using local storage only.")
            self.s3_client = None
            self.s3_available = False
        
        self.embedding_service = EmbeddingService()
        self.bucket_name = settings.s3_vector_bucket_name
        self.index_name = settings.s3_vector_index_name
        
        # ローカルストレージの設定
        self.local_storage_path = Path("data/vector_store")
        self.local_storage_path.mkdir(parents=True, exist_ok=True)
        self.vectors_file = self.local_storage_path / "vectors.pkl"
        self.metadata_file = self.local_storage_path / "metadata.json"
    
    def initialize_bucket_and_index(self) -> bool:
        """ベクトルストレージを初期化"""
        try:
            # ローカルストレージの初期化
            self._initialize_local_storage()
            
            # S3が利用可能な場合はS3も初期化を試行
            if self.s3_available:
                try:
                    self._initialize_s3_storage()
                except Exception as e:
                    logger.warning(f"S3 initialization failed, using local storage only: {e}")
                    self.s3_available = False
            
            logger.info("Vector store initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            return False
    
    def _initialize_local_storage(self):
        """ローカルストレージを初期化"""
        if not self.vectors_file.exists():
            # 空のベクトルデータを作成
            with open(self.vectors_file, 'wb') as f:
                pickle.dump({"vectors": [], "ids": []}, f)
        
        if not self.metadata_file.exists():
            # 空のメタデータを作成
            with open(self.metadata_file, 'w') as f:
                json.dump({}, f)
        
        logger.info("Local vector storage initialized")
    
    def _initialize_s3_storage(self):
        """S3ストレージを初期化"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 bucket {self.bucket_name} already exists")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                self._create_vector_bucket()
            else:
                raise
    
    def _create_vector_bucket(self):
        """S3ベクトルバケットを作成（デモ用：通常のS3バケット）"""
        try:
            # S3 Vectorsがプレビュー版のため、デモ用に通常のS3バケットを作成
            if settings.aws_region == 'us-east-1':
                # us-east-1の場合、LocationConstraintは不要
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={
                        'LocationConstraint': settings.aws_region
                    }
                )
            logger.info(f"Created S3 bucket for vector storage: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to create bucket: {e}")
            raise
    
    def _ensure_vector_index(self):
        """ベクトルインデックスを確認または作成"""
        try:
            # 注: 実際のS3 Vectors APIでは、create_vector_indexメソッドを使用
            # 現在のboto3ではまだサポートされていない可能性があるため、
            # 実装時は最新のSDKドキュメントを確認してください
            logger.info(f"Ensuring vector index: {self.index_name}")
            # TODO: 実際のAPIコールに置き換える
        except Exception as e:
            logger.error(f"Failed to ensure vector index: {e}")
            raise
    
    def add_documents(self, chunks: List[Dict[str, Any]]) -> bool:
        """ドキュメントチャンクをベクトル化して保存"""
        try:
            vectors_to_insert = []
            
            for chunk in chunks:
                # テキストをベクトル化
                embedding = self.embedding_service.embed_text(chunk["text"])
                
                # ベクトルデータを準備
                vector_data = {
                    "id": chunk["id"],
                    "vector": embedding,
                    "metadata": {
                        **chunk["metadata"],
                        "source_text": chunk["text"][:1000]  # 最初の1000文字を保存
                    }
                }
                vectors_to_insert.append(vector_data)
            
            # ローカルストレージに保存
            if vectors_to_insert:
                self._save_vectors_locally(vectors_to_insert)
                logger.info(f"Successfully saved {len(vectors_to_insert)} vectors to local storage")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
    
    def _save_vectors_locally(self, vectors: List[Dict[str, Any]]):
        """ベクトルをローカルストレージに保存"""
        try:
            # 既存のデータを読み込み
            with open(self.vectors_file, 'rb') as f:
                data = pickle.load(f)
            
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # 新しいデータを追加
            for vector_data in vectors:
                data["vectors"].append(vector_data["vector"])
                data["ids"].append(vector_data["id"])
                metadata[vector_data["id"]] = vector_data["metadata"]
            
            # ファイルに保存
            with open(self.vectors_file, 'wb') as f:
                pickle.dump(data, f)
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(vectors)} vectors to local storage")
            
        except Exception as e:
            logger.error(f"Failed to save vectors locally: {e}")
            raise
    
    def _insert_vectors(self, vectors: List[Dict[str, Any]]):
        """ベクトルをS3 Vectorsに挿入"""
        try:
            # 注: 実際のS3 Vectors APIでは、put_vectorsメソッドを使用
            # 現在のboto3ではまだサポートされていない可能性があるため、
            # 実装時は最新のSDKドキュメントを確認してください
            
            # バッチサイズを考慮して分割
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                # TODO: 実際のAPIコールに置き換える
                logger.info(f"Inserting batch of {len(batch)} vectors")
                
        except Exception as e:
            logger.error(f"Failed to insert vectors: {e}")
            raise
    
    def search(self, query: str, top_k: int = None, filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """類似ベクトルを検索"""
        try:
            if top_k is None:
                top_k = settings.search_top_k
            
            # クエリテキストをベクトル化
            query_vector = self.embedding_service.embed_text(query)
            
            # 検索を実行
            results = self._query_vectors(
                query_vector=query_vector,
                top_k=top_k,
                filter_metadata=filter_metadata
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            return []
    
    def _query_vectors(self, query_vector: List[float], top_k: int, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """ベクトル検索を実行（ローカルストレージ版）"""
        try:
            # ローカルストレージからデータを読み込み
            with open(self.vectors_file, 'rb') as f:
                data = pickle.load(f)
            
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            if not data["vectors"]:
                return []
            
            # コサイン類似度を計算
            query_vector = np.array(query_vector)
            similarities = []
            
            for i, vector in enumerate(data["vectors"]):
                vector = np.array(vector)
                # コサイン類似度
                dot_product = np.dot(query_vector, vector)
                norms = np.linalg.norm(query_vector) * np.linalg.norm(vector)
                if norms > 0:
                    similarity = dot_product / norms
                else:
                    similarity = 0.0
                
                vector_id = data["ids"][i]
                vector_metadata = metadata.get(vector_id, {})
                
                # フィルタ適用
                if filter_metadata and not self._matches_filter(vector_metadata, filter_metadata):
                    continue
                
                similarities.append({
                    "id": vector_id,
                    "similarity": float(similarity),
                    "metadata": vector_metadata
                })
            
            # 類似度でソートしてtop_kを返す
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to query vectors: {e}")
            return []
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_metadata: Dict[str, Any]) -> bool:
        """メタデータフィルタが一致するかチェック"""
        for key, value in filter_metadata.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
    
    def delete_document(self, doc_id: str) -> bool:
        """ドキュメントに関連するすべてのベクトルを削除"""
        try:
            # TODO: doc_idに関連するすべてのチャンクIDを取得して削除
            logger.info(f"Deleting vectors for document: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False