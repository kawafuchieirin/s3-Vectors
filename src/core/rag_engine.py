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
        try:
            self.bedrock_client = boto3.client(
                "bedrock-runtime",
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            )
            self.generation_model_id = settings.bedrock_generation_model_id
            self.use_bedrock = True
        except Exception as e:
            logger.warning(f"Bedrock client initialization failed: {e}. Using mock generation.")
            self.bedrock_client = None
            self.use_bedrock = False
    
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
            if self.use_bedrock:
                proposal = self._generate_with_bedrock(prompt)
            else:
                proposal = self._generate_mock_proposal(query, context, context_info)
            
            return {
                "status": "success",
                "proposal": proposal,
                "sources": [
                    {
                        "file_name": result["metadata"].get("file_name", "Unknown"),
                        "chunk_id": result["id"],
                        "relevance_score": result.get("similarity", 0)
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
                # Titan等の他のモデル用
                generated_text = response_body["results"][0]["outputText"]
            
            return generated_text.strip()
            
        except ClientError as e:
            logger.error(f"Bedrock API error: {e}")
            # Bedrockでエラーが発生した場合、モック生成にフォールバック
            logger.warning("Falling back to mock proposal generation")
            self.use_bedrock = False
            return self._generate_mock_proposal("", "", {})
        except Exception as e:
            logger.error(f"Failed to generate with Bedrock: {e}")
            # その他のエラーでもモック生成にフォールバック
            logger.warning("Falling back to mock proposal generation")
            self.use_bedrock = False
            return self._generate_mock_proposal("", "", {})
    
    def _generate_mock_proposal(self, query: str, context: str, context_info: Optional[Dict[str, Any]] = None) -> str:
        """デモ用のモック提案を生成"""
        customer_name = context_info.get("customer_name", "お客様") if context_info else "お客様"
        industry = context_info.get("industry", "") if context_info else ""
        budget = context_info.get("budget", "") if context_info else ""
        
        # 業界別のカスタマイズ
        industry_solutions = {
            "製造業": {
                "solutions": ["AI品質管理システム", "予知保全ソリューション", "生産最適化AI"],
                "benefits": ["品質向上", "コスト削減", "効率化"]
            },
            "金融業": {
                "solutions": ["セキュリティ強化", "コンプライアンス対応", "リスク管理システム"],
                "benefits": ["セキュリティ向上", "規制対応", "リスク軽減"]
            },
            "IT・通信": {
                "solutions": ["クラウド移行", "DX推進", "データ分析基盤"],
                "benefits": ["スケーラビリティ", "コスト最適化", "データ活用"]
            }
        }
        
        current_solutions = industry_solutions.get(industry, {
            "solutions": ["デジタル変革", "業務効率化", "コスト最適化"],
            "benefits": ["生産性向上", "コスト削減", "競争力強化"]
        })
        
        proposal = f"""# 営業提案書

{customer_name} 御中

平素よりお世話になっております。
お客様のご要望「{query}」について、以下のとおりご提案させていただきます。

## 1. 課題認識

{industry}業界では、以下のような課題が重要視されています：
- デジタル変革への対応
- 業務効率化の推進
- コスト最適化の実現

## 2. 提案ソリューション

弊社では以下のソリューションをご提案いたします：

### 主要な機能・サービス
"""

        for i, solution in enumerate(current_solutions["solutions"], 1):
            proposal += f"\n{i}. **{solution}**\n   - 最新技術による効果的な解決策\n   - 実証済みの導入実績\n"

        proposal += f"""
## 3. 期待される効果

導入により以下の効果が期待できます：
"""

        for benefit in current_solutions["benefits"]:
            proposal += f"- {benefit}\n"

        if budget:
            proposal += f"""
## 4. 投資効果

ご予算：{budget}
投資回収期間：12-18ヶ月を想定
"""

        proposal += """
## 5. 導入スケジュール

- フェーズ1（1-2ヶ月）：要件定義・設計
- フェーズ2（2-3ヶ月）：開発・導入
- フェーズ3（1ヶ月）：運用開始・サポート

## 6. サポート体制

- 24時間365日のサポート
- 専任担当者によるプロジェクト管理
- 定期的な効果測定とフォローアップ

ご不明な点やご質問がございましたら、お気軽にお申し付けください。

---
※この提案書はRAGシステムのデモ機能で生成されました。
実際のAWS Bedrock環境では、より高品質な提案が生成されます。
"""

        return proposal
    
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
                    "relevance_score": result.get("similarity", 0),
                    "metadata": metadata
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search similar proposals: {e}")
            return []