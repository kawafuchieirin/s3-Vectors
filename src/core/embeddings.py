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
        self.bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        self.model_id = settings.bedrock_model_id
    
    def embed_text(self, text: str) -> List[float]:
        """テキストを埋め込みベクトルに変換"""
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
            raise
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
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