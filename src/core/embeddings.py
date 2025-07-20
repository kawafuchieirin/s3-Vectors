"""埋め込みベクトル生成サービス"""
import json
from typing import List, Union, Dict, Any
import logging

import boto3
from botocore.exceptions import ClientError

from src.core.config import settings


logger = logging.getLogger(__name__)


class EmbeddingService:
    """Amazon Bedrockを使用した埋め込みベクトル生成サービス"""
    
    def __init__(self):
        try:
            self.bedrock_client = boto3.client(
                "bedrock-runtime",
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            )
            self.model_id = settings.bedrock_model_id
            self.use_bedrock = True
        except Exception as e:
            logger.warning(f"Bedrock client initialization failed: {e}. Using mock embeddings.")
            self.bedrock_client = None
            self.use_bedrock = False
    
    def embed_text(self, text: str) -> List[float]:
        """テキストを埋め込みベクトルに変換"""
        if not self.use_bedrock:
            # モック埋め込みを使用
            return self._create_mock_embedding(text)
        
        try:
            # リクエストボディを準備
            request_body = {
                "inputText": text
            }
            
            # Bedrockモデルを呼び出し
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json"
            )
            
            # レスポンスを解析
            response_body = json.loads(response["body"].read())
            embedding = response_body.get("embedding", [])
            
            if not embedding:
                raise ValueError("No embedding returned from model")
            
            return embedding
            
        except ClientError as e:
            logger.error(f"AWS Client error: {e}")
            # Bedrockでエラーが発生した場合、モック埋め込みにフォールバック
            logger.warning("Falling back to mock embeddings")
            self.use_bedrock = False
            return self._create_mock_embedding(text)
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # その他のエラーでもモック埋め込みにフォールバック
            logger.warning("Falling back to mock embeddings")
            self.use_bedrock = False
            return self._create_mock_embedding(text)
    
    def _create_mock_embedding(self, text: str) -> List[float]:
        """デモ用のモック埋め込みベクトルを生成"""
        import hashlib
        import random
        
        # テキストからハッシュを生成してシード値として使用
        text_hash = hashlib.md5(text.encode()).hexdigest()
        seed = int(text_hash[:8], 16)
        random.seed(seed)
        
        # 1536次元のベクトルを生成（Titan Text Embeddings V2と同じ次元数）
        dimension = settings.vector_dimension
        embedding = [random.normalvariate(0, 1) for _ in range(dimension)]
        
        # 正規化
        norm = sum(x * x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        logger.debug(f"Generated mock embedding of dimension {len(embedding)} for text: '{text[:50]}...'")
        return embedding
    
    def embed_texts(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """複数のテキストを埋め込みベクトルに変換"""
        embeddings = []
        
        # バッチ処理
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = []
            
            for text in batch:
                try:
                    embedding = self.embed_text(text)
                    batch_embeddings.append(embedding)
                except Exception as e:
                    logger.error(f"Failed to embed text: {e}")
                    # エラーが発生した場合は空のベクトルを追加
                    batch_embeddings.append([0.0] * settings.vector_dimension)
            
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    def get_model_info(self) -> Dict[str, Any]:
        """使用中のモデル情報を取得"""
        return {
            "model_id": self.model_id,
            "dimension": settings.vector_dimension,
            "provider": "Amazon Bedrock"
        }