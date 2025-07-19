"""Streamlit WebUIアプリケーション"""
import streamlit as st
import requests
import json
from datetime import datetime
import os
from typing import Dict, Any, Optional

# ページ設定
st.set_page_config(
    page_title="営業提案資料RAGシステム",
    page_icon="📄",
    layout="wide"
)

# APIエンドポイントの設定
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def upload_document(file, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """ドキュメントをアップロード"""
    files = {"file": (file.name, file, file.type)}
    data = {
        "customer_name": metadata.get("customer_name", ""),
        "industry": metadata.get("industry", ""),
        "document_type": metadata.get("document_type", "")
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/documents/upload",
        files=files,
        data=data
    )
    
    return response.json()


def generate_proposal(query: str, context_info: Dict[str, Any]) -> Dict[str, Any]:
    """提案を生成"""
    payload = {
        "query": query,
        "customer_name": context_info.get("customer_name"),
        "industry": context_info.get("industry"),
        "budget": context_info.get("budget"),
        "top_k": context_info.get("top_k", 10)
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/proposals/generate",
        json=payload
    )
    
    return response.json()


def search_documents(query: str, top_k: int = 5) -> Dict[str, Any]:
    """ドキュメントを検索"""
    payload = {
        "query": query,
        "top_k": top_k
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/documents/search",
        json=payload
    )
    
    return response.json()


def main():
    st.title("📄 営業提案資料RAGシステム")
    st.markdown("Amazon S3 Vectorsを活用した営業提案資料生成システム")
    
    # サイドバー
    with st.sidebar:
        st.header("設定")
        
        # 顧客情報入力
        st.subheader("顧客情報")
        customer_name = st.text_input("顧客名")
        industry = st.selectbox(
            "業界",
            ["", "製造業", "小売業", "金融業", "IT・通信", "医療・福祉", "建設業", "その他"]
        )
        budget = st.text_input("予算")
        
        # 検索設定
        st.subheader("検索設定")
        top_k = st.slider("参照する資料数", 1, 20, 10)
    
    # メインコンテンツ
    tab1, tab2, tab3 = st.tabs(["💡 提案生成", "📤 資料アップロード", "🔍 資料検索"])
    
    # 提案生成タブ
    with tab1:
        st.header("営業提案の生成")
        
        # 要望入力
        query = st.text_area(
            "お客様の要望・課題を入力してください",
            height=150,
            placeholder="例：製造業向けのAIを活用した品質管理システムの提案をお願いします。"
        )
        
        if st.button("提案を生成", type="primary"):
            if query:
                with st.spinner("提案を生成中..."):
                    try:
                        # コンテキスト情報を構築
                        context_info = {
                            "customer_name": customer_name,
                            "industry": industry,
                            "budget": budget,
                            "top_k": top_k
                        }
                        
                        # 提案を生成
                        result = generate_proposal(query, context_info)
                        
                        if result["status"] == "success":
                            st.success("提案が生成されました！")
                            
                            # 提案内容を表示
                            st.subheader("生成された提案")
                            st.markdown(result["proposal"])
                            
                            # 参照元を表示
                            if result.get("sources"):
                                st.subheader("参照した資料")
                                for source in result["sources"]:
                                    st.write(f"- **{source['file_name']}** (関連度: {source['relevance_score']:.2f})")
                        else:
                            st.error(f"エラー: {result.get('message', '不明なエラー')}")
                            
                    except Exception as e:
                        st.error(f"エラーが発生しました: {str(e)}")
            else:
                st.warning("要望を入力してください。")
    
    # 資料アップロードタブ
    with tab2:
        st.header("営業資料のアップロード")
        
        # ファイルアップロード
        uploaded_file = st.file_uploader(
            "ファイルを選択してください",
            type=["pdf", "docx", "doc", "txt", "md"],
            help="PDF、Word文書、テキストファイルがアップロード可能です"
        )
        
        if uploaded_file:
            # メタデータ入力
            col1, col2 = st.columns(2)
            with col1:
                doc_customer = st.text_input("関連顧客名（オプション）", key="doc_customer")
                doc_type = st.selectbox(
                    "資料タイプ",
                    ["", "提案書", "カタログ", "事例紹介", "価格表", "その他"],
                    key="doc_type"
                )
            
            with col2:
                doc_industry = st.selectbox(
                    "関連業界（オプション）",
                    ["", "製造業", "小売業", "金融業", "IT・通信", "医療・福祉", "建設業", "その他"],
                    key="doc_industry"
                )
            
            if st.button("アップロード", type="primary"):
                with st.spinner("アップロード中..."):
                    try:
                        # メタデータを構築
                        metadata = {
                            "customer_name": doc_customer,
                            "industry": doc_industry,
                            "document_type": doc_type
                        }
                        
                        # アップロード実行
                        result = upload_document(uploaded_file, metadata)
                        
                        if result["status"] == "success":
                            st.success(result["message"])
                            st.info(f"ドキュメントID: {result['doc_id']}")
                            st.info(f"作成されたチャンク数: {result['chunks_created']}")
                        else:
                            st.error(f"エラー: {result.get('message', '不明なエラー')}")
                            
                    except Exception as e:
                        st.error(f"アップロードエラー: {str(e)}")
    
    # 資料検索タブ
    with tab3:
        st.header("営業資料の検索")
        
        # 検索クエリ入力
        search_query = st.text_input(
            "検索キーワードを入力してください",
            placeholder="例：クラウドセキュリティ"
        )
        
        search_top_k = st.slider("検索結果数", 1, 20, 5, key="search_top_k")
        
        if st.button("検索", type="primary"):
            if search_query:
                with st.spinner("検索中..."):
                    try:
                        # 検索実行
                        result = search_documents(search_query, search_top_k)
                        
                        if result["status"] == "success":
                            st.success(f"{result['total_found']}件の結果が見つかりました")
                            
                            # 検索結果を表示
                            for idx, doc in enumerate(result["results"]):
                                with st.expander(f"📄 {doc['file_name']} (関連度: {doc['relevance_score']:.2f})"):
                                    st.write(doc["excerpt"])
                                    
                                    # メタデータ表示
                                    metadata = doc["metadata"]
                                    if metadata.get("customer_name"):
                                        st.write(f"**顧客:** {metadata['customer_name']}")
                                    if metadata.get("industry"):
                                        st.write(f"**業界:** {metadata['industry']}")
                                    if metadata.get("document_type"):
                                        st.write(f"**資料タイプ:** {metadata['document_type']}")
                        else:
                            st.error("検索に失敗しました")
                            
                    except Exception as e:
                        st.error(f"検索エラー: {str(e)}")
            else:
                st.warning("検索キーワードを入力してください。")
    
    # フッター
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
        Powered by Amazon S3 Vectors & Amazon Bedrock
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()