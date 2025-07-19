"""設定管理モジュール"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # AWS設定
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    
    # S3 Vectors設定
    s3_vector_bucket_name: str = Field(..., env="S3_VECTOR_BUCKET_NAME")
    s3_vector_index_name: str = Field(default="sales-documents-index", env="S3_VECTOR_INDEX_NAME")
    vector_dimension: int = Field(default=1536, env="VECTOR_DIMENSION")
    
    # Amazon Bedrock設定
    bedrock_model_id: str = Field(
        default="amazon.titan-embed-text-v2:0",
        env="BEDROCK_MODEL_ID"
    )
    bedrock_generation_model_id: str = Field(
        default="anthropic.claude-3-sonnet-20240229-v1:0",
        env="BEDROCK_GENERATION_MODEL_ID"
    )
    
    # API設定
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # ドキュメント処理設定
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    max_chunks_per_document: int = Field(default=100, env="MAX_CHUNKS_PER_DOCUMENT")
    
    # 検索設定
    search_top_k: int = Field(default=10, env="SEARCH_TOP_K")
    similarity_threshold: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# シングルトンインスタンス
settings = Settings()