"""ドキュメント処理モジュール"""
import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import hashlib

import pypdf
import docx2txt
from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.core.config import settings


@dataclass
class Document:
    """ドキュメントのデータクラス"""
    content: str
    metadata: Dict[str, Any]
    doc_id: str
    chunks: Optional[List[Dict[str, Any]]] = None


class DocumentProcessor:
    """ドキュメント処理クラス"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "．", " ", ""]
        )
    
    def process_file(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Document:
        """ファイルを処理してDocumentオブジェクトを返す"""
        if metadata is None:
            metadata = {}
        
        # ファイル情報をメタデータに追加
        metadata.update({
            "file_name": os.path.basename(file_path),
            "file_path": file_path,
            "file_size": os.path.getsize(file_path)
        })
        
        # ファイルタイプに応じてテキストを抽出
        content = self._extract_text(file_path)
        
        # ドキュメントIDを生成
        doc_id = self._generate_doc_id(file_path, content)
        
        # Documentオブジェクトを作成
        document = Document(
            content=content,
            metadata=metadata,
            doc_id=doc_id
        )
        
        # チャンクに分割
        document.chunks = self._create_chunks(document)
        
        return document
    
    def _extract_text(self, file_path: str) -> str:
        """ファイルからテキストを抽出"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == ".pdf":
            return self._extract_pdf_text(file_path)
        elif file_extension in [".docx", ".doc"]:
            return self._extract_docx_text(file_path)
        elif file_extension in [".txt", ".md"]:
            return self._extract_plain_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """PDFからテキストを抽出"""
        text = ""
        with open(file_path, "rb") as file:
            pdf_reader = pypdf.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
        return self._clean_text(text)
    
    def _extract_docx_text(self, file_path: str) -> str:
        """Word文書からテキストを抽出"""
        text = docx2txt.process(file_path)
        return self._clean_text(text)
    
    def _extract_plain_text(self, file_path: str) -> str:
        """プレーンテキストファイルを読み込み"""
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()
        return self._clean_text(text)
    
    def _clean_text(self, text: str) -> str:
        """テキストをクリーニング"""
        # 余分な空白を削除
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        
        # 特殊文字を正規化
        text = text.replace('\u3000', ' ')  # 全角スペースを半角に
        
        return text.strip()
    
    def _generate_doc_id(self, file_path: str, content: str) -> str:
        """ドキュメントIDを生成"""
        # ファイルパスとコンテンツの一部からハッシュを生成
        hash_input = f"{file_path}:{content[:1000]}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def _create_chunks(self, document: Document) -> List[Dict[str, Any]]:
        """ドキュメントをチャンクに分割"""
        chunks = self.text_splitter.split_text(document.content)
        
        # 最大チャンク数を制限
        if len(chunks) > settings.max_chunks_per_document:
            chunks = chunks[:settings.max_chunks_per_document]
        
        chunk_data = []
        for i, chunk_text in enumerate(chunks):
            chunk_id = f"{document.doc_id}:chunk_{i}"
            chunk_metadata = document.metadata.copy()
            chunk_metadata.update({
                "chunk_index": i,
                "chunk_id": chunk_id,
                "doc_id": document.doc_id,
                "total_chunks": len(chunks)
            })
            
            chunk_data.append({
                "id": chunk_id,
                "text": chunk_text,
                "metadata": chunk_metadata
            })
        
        return chunk_data