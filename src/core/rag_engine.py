"""RAGエンジン - 検索と生成を統合"""
import json
from typing import List, Dict, Any, Optional
import logging

import boto3
from botocore.exceptions import ClientError

from src.core.config import settings
from src.core.vector_store import S3VectorStore


logger = logging.getLogger(__name__)


class RAGEngine:
    """検索拡張生成（RAG）エンジン"""
    
    def __init__(self):
        self.vector_store = S3VectorStore()
        self.bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        self.generation_model_id = settings.bedrock_generation_model_id
    
    def generate_proposal(
        self,
        query: str,
        context_info: Optional[Dict[str, Any]] = None,
        top_k: int = None
    ) -> Dict[str, Any]:
        """営業提案資料を生成"""
        try:
            # 関連するドキュメントを検索
            search_results = self.vector_store.search(query, top_k=top_k)
            
            if not search_results:
                return {
                    "status": "error",
                    "message": "関連する資料が見つかりませんでした。",
                    "proposal": None
                }
            
            # コンテキストを構築
            context = self._build_context(search_results)
            
            # プロンプトを構築
            prompt = self._build_proposal_prompt(query, context, context_info)
            
            # 提案を生成
            proposal = self._generate_with_bedrock(prompt)
            
            return {
                "status": "success",
                "proposal": proposal,
                "sources": [
                    {
                        "file_name": result["metadata"].get("file_name", "Unknown"),
                        "chunk_id": result["id"],
                        "relevance_score": result.get("score", 0)
                    }
                    for result in search_results[:5]  # 上位5件のソースを返す
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to generate proposal: {e}")
            return {
                "status": "error",
                "message": str(e),
                "proposal": None
            }
    
    def _build_context(self, search_results: List[Dict[str, Any]]) -> str:
        """検索結果からコンテキストを構築"""
        context_parts = []
        
        for i, result in enumerate(search_results):
            metadata = result.get("metadata", {})
            source_text = metadata.get("source_text", "")
            file_name = metadata.get("file_name", "Unknown")
            
            context_parts.append(f"【参考資料{i+1} - {file_name}】\n{source_text}\n")
        
        return "\n".join(context_parts)
    
    def _build_proposal_prompt(
        self,
        query: str,
        context: str,
        context_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """提案生成用のプロンプトを構築"""
        base_prompt = f"""あなたは優秀な営業担当者です。以下の参考資料を基に、お客様のニーズに合わせた営業提案資料を作成してください。

【お客様の要望】
{query}

【参考資料】
{context}

【作成要件】
1. お客様の課題や要望を明確に理解し、それに対する解決策を提示してください
2. 参考資料の内容を活用し、具体的な提案を行ってください
3. 分かりやすく、説得力のある構成にしてください
4. 必要に応じて、価格や導入スケジュールの目安も含めてください

"""
        
        # 追加のコンテキスト情報があれば含める
        if context_info:
            additional_info = []
            if "customer_name" in context_info:
                additional_info.append(f"顧客名: {context_info['customer_name']}")
            if "industry" in context_info:
                additional_info.append(f"業界: {context_info['industry']}")
            if "budget" in context_info:
                additional_info.append(f"予算: {context_info['budget']}")
            
            if additional_info:
                base_prompt += "【顧客情報】\n" + "\n".join(additional_info) + "\n\n"
        
        base_prompt += "【提案資料】\n"
        
        return base_prompt
    
    def _generate_with_bedrock(self, prompt: str) -> str:
        """Amazon Bedrockを使用してテキストを生成"""
        try:
            # モデルに応じてリクエストボディを構築
            if "claude" in self.generation_model_id:
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            else:
                # Titan等の他のモデル用
                request_body = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": 4000,
                        "temperature": 0.7,
                        "topP": 0.9
                    }
                }
            
            # モデルを呼び出し
            response = self.bedrock_client.invoke_model(
                modelId=self.generation_model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json"
            )
            
            # レスポンスを解析
            response_body = json.loads(response["body"].read())
            
            # モデルに応じて生成されたテキストを取得
            if "claude" in self.generation_model_id:
                generated_text = response_body["content"][0]["text"]
            else:
                # Titan等の他のモデル
                generated_text = response_body.get("results", [{}])[0].get("outputText", "")
            
            return generated_text
            
        except ClientError as e:
            logger.error(f"AWS Client error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to generate text: {e}")
            raise
    
    def search_similar_proposals(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """類似の提案資料を検索"""
        try:
            results = self.vector_store.search(query, top_k=top_k)
            
            formatted_results = []
            for result in results:
                metadata = result.get("metadata", {})
                formatted_results.append({
                    "file_name": metadata.get("file_name", "Unknown"),
                    "excerpt": metadata.get("source_text", "")[:200] + "...",
                    "relevance_score": result.get("score", 0),
                    "metadata": metadata
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search similar proposals: {e}")
            return []