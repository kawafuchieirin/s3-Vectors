"""FastAPI アプリケーションのメインモジュール"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import os
import tempfile
import logging

from src.core.config import settings
from src.core.document_processor import DocumentProcessor
from src.core.vector_store import S3VectorStore
from src.core.rag_engine import RAGEngine
from src.api.models import (
    ProposalRequest,
    ProposalResponse,
    SearchRequest,
    SearchResponse,
    DocumentUploadResponse
)


# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーションの初期化
app = FastAPI(
    title="営業提案資料RAGシステム",
    description="Amazon S3 Vectorsを活用した営業提案資料生成システム",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# グローバルインスタンス
document_processor = DocumentProcessor()
vector_store = S3VectorStore()
rag_engine = RAGEngine()


@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の初期化処理"""
    logger.info("Initializing S3 Vector store...")
    success = vector_store.initialize_bucket_and_index()
    if not success:
        logger.error("Failed to initialize S3 Vector store")
    else:
        logger.info("S3 Vector store initialized successfully")


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "営業提案資料RAGシステムAPI",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/api/documents/upload",
            "generate": "/api/proposals/generate",
            "search": "/api/documents/search"
        }
    }


@app.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    customer_name: Optional[str] = Form(None),
    industry: Optional[str] = Form(None),
    document_type: Optional[str] = Form(None)
):
    """ドキュメントをアップロードしてベクトル化"""
    try:
        # ファイルの検証
        allowed_extensions = [".pdf", ".docx", ".doc", ".txt", ".md"]
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"サポートされていないファイル形式です。対応形式: {', '.join(allowed_extensions)}"
            )
        
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # メタデータを構築
            metadata = {
                "original_filename": file.filename,
                "file_size": len(content),
                "upload_timestamp": datetime.now().isoformat()
            }
            
            if customer_name:
                metadata["customer_name"] = customer_name
            if industry:
                metadata["industry"] = industry
            if document_type:
                metadata["document_type"] = document_type
            
            # ドキュメントを処理
            document = document_processor.process_file(tmp_file_path, metadata)
            
            # ベクトルストアに追加
            success = vector_store.add_documents(document.chunks)
            
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="ドキュメントの保存に失敗しました"
                )
            
            return DocumentUploadResponse(
                status="success",
                message="ドキュメントが正常にアップロードされました",
                doc_id=document.doc_id,
                chunks_created=len(document.chunks)
            )
            
        finally:
            # 一時ファイルを削除
            os.unlink(tmp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ドキュメントのアップロード中にエラーが発生しました: {str(e)}"
        )


@app.post("/api/proposals/generate", response_model=ProposalResponse)
async def generate_proposal(request: ProposalRequest):
    """営業提案資料を生成"""
    try:
        # コンテキスト情報を構築
        context_info = {}
        if request.customer_name:
            context_info["customer_name"] = request.customer_name
        if request.industry:
            context_info["industry"] = request.industry
        if request.budget:
            context_info["budget"] = request.budget
        
        # 提案を生成
        result = rag_engine.generate_proposal(
            query=request.query,
            context_info=context_info,
            top_k=request.top_k
        )
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=400,
                detail=result["message"]
            )
        
        return ProposalResponse(
            status=result["status"],
            proposal=result["proposal"],
            sources=result.get("sources", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Proposal generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"提案資料の生成中にエラーが発生しました: {str(e)}"
        )


@app.post("/api/documents/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """類似ドキュメントを検索"""
    try:
        results = rag_engine.search_similar_proposals(
            query=request.query,
            top_k=request.top_k
        )
        
        return SearchResponse(
            status="success",
            results=results,
            total_found=len(results)
        )
        
    except Exception as e:
        logger.error(f"Document search error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ドキュメントの検索中にエラーが発生しました: {str(e)}"
        )


@app.get("/api/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    from datetime import datetime
    
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )