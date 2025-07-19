"""APIのリクエスト/レスポンスモデル"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ProposalRequest(BaseModel):
    """提案生成リクエスト"""
    query: str = Field(..., description="提案内容の要求・質問")
    customer_name: Optional[str] = Field(None, description="顧客名")
    industry: Optional[str] = Field(None, description="業界")
    budget: Optional[str] = Field(None, description="予算")
    top_k: Optional[int] = Field(10, description="検索する参考資料の数")


class SourceDocument(BaseModel):
    """参照元ドキュメント情報"""
    file_name: str
    chunk_id: str
    relevance_score: float


class ProposalResponse(BaseModel):
    """提案生成レスポンス"""
    status: str
    proposal: Optional[str]
    sources: List[SourceDocument] = []


class SearchRequest(BaseModel):
    """ドキュメント検索リクエスト"""
    query: str = Field(..., description="検索クエリ")
    top_k: int = Field(5, description="返す結果の最大数")
    filter_metadata: Optional[Dict[str, Any]] = Field(None, description="メタデータフィルター")


class SearchResult(BaseModel):
    """検索結果"""
    file_name: str
    excerpt: str
    relevance_score: float
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    """ドキュメント検索レスポンス"""
    status: str
    results: List[SearchResult]
    total_found: int


class DocumentUploadResponse(BaseModel):
    """ドキュメントアップロードレスポンス"""
    status: str
    message: str
    doc_id: str
    chunks_created: int