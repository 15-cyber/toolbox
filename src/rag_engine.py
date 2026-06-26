"""
RAG 核心引擎 - LangChain 业务编排层
集成：ConversationalRetrievalChain + Memory + Streaming + Prompt Guard
"""
import logging
from typing import Optional, Callable, AsyncGenerator, Dict, Any

from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler

from .config import (
    RAG_SYSTEM_PROMPT, MEMORY_WINDOW, TOP_K,
    GUARD_TRIGGER_WORDS, GUARD_CORRECTION_PROMPT
)
from .vector_store import VectorStoreManager
from .ingestion import ingest_pdf_folder

logger = logging.getLogger(__name__)


# ── 流式回调处理器 ────────────────────────────────────
class StreamCallbackHandler(BaseCallbackHandler):
    """将 LLM 的流式 token 逐字传递给外部回调函数"""

    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.buffer = ""

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.callback(token)


class RAGEngine:
    """RAG 检索增强生成引擎"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str = "deepseek-chat",
        embedding_model: str = "text-embedding-ada-002",
        persist_directory: Optional[str] = None
    ):
        """
        初始化 RAG 引擎。

        Args:
            api_key: 大模型 API 密钥
            base_url: API 基础地址
            model_name: 对话模型名称
            embedding_model: 嵌入模型名称
            persist_directory: 向量库路径
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name

        # 初始化 LLM（开启流式输出）
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            streaming=True,
            temperature=0.3  # 低温度保证学术严谨性
        )

        # 初始化向量库管理器
        self.vector_manager = VectorStoreManager(
            api_key=api_key,
            base_url=base_url,
            persist_directory=persist_directory or "",
            embedding_model=embedding_model
        )

        # 初始化滑动窗口记忆
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            output_key="answer",
            return_messages=True,
            k=MEMORY_WINDOW
        )

        # RAG 链条（在摄入文档后构建）
        self.retrieval_chain: Optional[ConversationalRetrievalChain] = None
        self.is_ready = False

        # 尝试加载已有向量库
        self._try_load_existing()

    def _try_load_existing(self):
        """尝试加载已有向量库并构建检索链"""
        if self.vector_manager.get_document_count() > 0:
            self._build_chain()
            self.is_ready = True
            logger.info("✓ RAG 引擎就绪 (已有向量库)")

    def _build_chain(self):
        """构建 ConversationalRetrievalChain"""
        retriever = self.vector_manager.get_retriever(k=TOP_K)

        qa_prompt = PromptTemplate(
            input_variables=["context", "chat_history", "question"],
            template=RAG_SYSTEM_PROMPT
        )

        self.retrieval_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": qa_prompt},
            return_source_documents=True,
            verbose=False
        )
        self.is_ready = True

    # ── 文献摄入 ──────────────────────────────────────
    def ingest_pdfs(self, folder_path: Optional[str] = None) -> str:
        """
        摄入 PDF 文献库：加载 → 切分 → 向量化 → 构建检索链
        """
        chunks = ingest_pdf_folder(folder_path)
        if not chunks:
            return "未找到有效 PDF 文献，请检查论文目录。"

        count = self.vector_manager.build_from_documents(chunks)
        self._build_chain()

        return f"✓ 成功加载文献库：{count} 个文本块已向量化，引擎就绪。"

    # ── 查询接口（非流式）──────────────────────────────
    def query(self, question: str) -> Dict[str, Any]:
        """
        同步查询（非流式）。

        Returns:
            {"answer": str, "source_documents": List[Document]}
        """
        if not self.is_ready or self.retrieval_chain is None:
            return {"answer": "请先加载您的文献库。", "source_documents": []}

        try:
            response = self.retrieval_chain.invoke({"question": question})
            answer = response.get("answer", "")

            # Prompt Guard: 检测 + 自动重试一次
            if self._needs_correction(answer):
                logger.warning("检测到不确定回答，触发自修复重试...")
                answer = self._retry_with_correction(question)

            return {
                "answer": answer,
                "source_documents": response.get("source_documents", [])
            }
        except Exception as e:
            logger.error(f"查询异常: {e}")
            return {"answer": f"系统异常: {str(e)}", "source_documents": []}

    # ── 流式查询接口 ──────────────────────────────────
    async def query_stream(
        self,
        question: str,
        callback: Callable[[str], None]
    ) -> Dict[str, Any]:
        """
        异步流式查询，token 逐字回调。

        Args:
            question: 用户问题
            callback: 接收每个 token 的回调函数

        Returns:
            {"answer": str, "source_documents": List[Document]}
        """
        if not self.is_ready or self.retrieval_chain is None:
            callback("请先加载您的文献库。")
            return {"answer": "请先加载您的文献库。", "source_documents": []}

        try:
            # 构建带流式回调的临时 LLM
            stream_handler = StreamCallbackHandler(callback)
            stream_llm = ChatOpenAI(
                model=self.model_name,
                api_key=self.api_key,
                base_url=self.base_url,
                streaming=True,
                temperature=0.3,
                callbacks=[stream_handler]
            )

            # 临时替换链条中的 LLM
            original_llm = self.retrieval_chain.combine_docs_chain.llm_chain.llm
            self.retrieval_chain.combine_docs_chain.llm_chain.llm = stream_llm

            response = await self.retrieval_chain.ainvoke({"question": question})

            # 恢复原始 LLM
            self.retrieval_chain.combine_docs_chain.llm_chain.llm = original_llm

            answer = response.get("answer", "")
            source_docs = response.get("source_documents", [])

            # Prompt Guard
            if self._needs_correction(answer):
                callback("\n\n[自修复重试中...]\n")
                answer = self._retry_with_correction(question)
                callback(answer)

            return {"answer": answer, "source_documents": source_docs}

        except Exception as e:
            logger.error(f"流式查询异常: {e}")
            error_msg = f"系统异常: {str(e)}"
            callback(error_msg)
            return {"answer": error_msg, "source_documents": []}

    # ── Prompt Guard（简单版）──────────────────────────
    def _needs_correction(self, answer: str) -> bool:
        """检测回答是否包含高度不确定性关键词"""
        for word in GUARD_TRIGGER_WORDS:
            if word in answer:
                return True
        return False

    def _retry_with_correction(self, original_question: str) -> str:
        """触发自修复：附加纠错 Prompt 后重新查询"""
        corrected_question = (
            f"{GUARD_CORRECTION_PROMPT}\n\n"
            f"原始问题：{original_question}"
        )
        try:
            response = self.retrieval_chain.invoke({"question": corrected_question})
            return response.get("answer", "自修复失败，请重新提问。")
        except Exception as e:
            return f"自修复异常: {str(e)}"

    # ── 对话管理 ──────────────────────────────────────
    def clear_memory(self):
        """清空对话记忆"""
        self.memory.clear()
        logger.info("对话记忆已清空")

    def get_memory_summary(self) -> str:
        """获取当前对话记忆摘要"""
        msgs = self.memory.load_memory_variables({}).get("chat_history", [])
        if not msgs:
            return "无对话历史"
        return f"当前记忆 {len(msgs)} 条消息，窗口大小 {MEMORY_WINDOW} 轮"

    def get_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            "ready": self.is_ready,
            "model": self.model_name,
            "base_url": self.base_url,
            "vector_count": self.vector_manager.get_document_count(),
            "memory_rounds": MEMORY_WINDOW
        }
