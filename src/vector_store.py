"""
向量存储与检索模块 - Chroma 本地持久化 + Top-K 混合检索
"""
import os
import logging
from typing import List, Optional, Tuple

from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from .config import CHROMA_DIR, TOP_K

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Chroma 向量库管理器：持久化存储、增量加载、语义检索"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        persist_directory: str = CHROMA_DIR,
        embedding_model: str = "text-embedding-ada-002"
    ):
        """
        初始化向量库管理器。

        Args:
            api_key: API 密钥
            base_url: API 基础地址
            persist_directory: 向量库持久化目录
            embedding_model: 嵌入模型名称
        """
        self.api_key = api_key
        self.base_url = base_url
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model

        # 初始化嵌入模型
        self.embeddings = OpenAIEmbeddings(
            api_key=api_key,
            base_url=base_url,
            model=embedding_model
        )

        self.vector_store: Optional[Chroma] = None
        self._load_or_init()

    def _load_or_init(self):
        """优先加载已有向量库，否则初始化为空"""
        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            try:
                self.vector_store = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                doc_count = self.vector_store._collection.count()
                logger.info(f"✓ 加载已有向量库: {doc_count} 个向量 (路径: {self.persist_directory})")
            except Exception as e:
                logger.warning(f"加载向量库失败，将重建: {e}")
                self.vector_store = None
        else:
            logger.info("未发现已有向量库，将在首次摄入时创建")

    def build_from_documents(self, documents: List[Document]) -> int:
        """
        从 Document 列表构建/重建向量库并持久化。

        Returns:
            存入的向量数量
        """
        os.makedirs(self.persist_directory, exist_ok=True)

        self.vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        count = self.vector_store._collection.count()
        logger.info(f"✓ 向量库已持久化: {count} 个向量 → {self.persist_directory}")
        return count

    def add_documents(self, documents: List[Document]) -> int:
        """增量添加文档到已有向量库"""
        if self.vector_store is None:
            return self.build_from_documents(documents)

        self.vector_store.add_documents(documents)
        count = self.vector_store._collection.count()
        logger.info(f"✓ 增量添加 {len(documents)} 个文本块，总计 {count} 个向量")
        return count

    def similarity_search(
        self,
        query: str,
        k: int = TOP_K
    ) -> List[Tuple[Document, float]]:
        """
        语义相似度检索。

        Returns:
            (Document, score) 列表，按相关度降序
        """
        if self.vector_store is None:
            raise ValueError("向量库为空，请先加载文献。")

        results = self.vector_store.similarity_search_with_relevance_scores(query, k=k)
        return results

    def get_retriever(self, k: int = TOP_K):
        """获取 LangChain Retriever 接口"""
        if self.vector_store is None:
            raise ValueError("向量库为空，请先加载文献。")
        return self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )

    def get_document_count(self) -> int:
        """获取当前向量库中文档数量"""
        if self.vector_store is None:
            return 0
        return self.vector_store._collection.count()

    def clear(self):
        """清空向量库"""
        if self.vector_store is not None:
            self.vector_store.delete_collection()
            self.vector_store = None
        import shutil
        if os.path.exists(self.persist_directory):
            shutil.rmtree(self.persist_directory)
        logger.info("向量库已清空")
