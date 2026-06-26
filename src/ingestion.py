"""
PDF 数据摄入模块 - 多文献批量加载、文本提取、智能重叠切分
"""
import os
import re
import logging
from typing import List, Optional

import pdfplumber
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PDFPlumberLoader

from .config import PDF_DIR, CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)


# ── 文本清洗规则 ──────────────────────────────────────
# 纯页码模式：单独成行的数字
RE_PAGE_NUMBER = re.compile(r'^\s*\d{1,4}\s*$')
# 杂乱抬头（纯符号、短字符串等）
RE_JUNK_LINE = re.compile(r'^\s*[_\-\*=~#]{3,}\s*$')


def clean_text(text: str) -> str:
    """清洗提取的文本：移除纯页码行和杂乱分割线"""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if RE_PAGE_NUMBER.match(stripped):
            continue
        if RE_JUNK_LINE.match(stripped):
            continue
        cleaned.append(line)
    return '\n'.join(cleaned)


def load_pdf_with_metadata(file_path: str) -> List[Document]:
    """
    使用 pdfplumber 逐页提取 PDF 文本，并附加页数元数据。
    返回 LangChain Document 列表（每页一个 Document）。
    """
    docs = []
    file_name = os.path.basename(file_path)

    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if not text or len(text.strip()) < 20:
                    continue  # 跳过内容过少的页面

                text = clean_text(text)
                if len(text.strip()) < 20:
                    continue

                doc = Document(
                    page_content=text,
                    metadata={
                        "source": file_name,
                        "file_path": file_path,
                        "page": page_num,
                        "total_pages": len(pdf.pages)
                    }
                )
                docs.append(doc)

        logger.info(f"✓ {file_name}: 提取 {len(docs)} 页有效内容")
    except Exception as e:
        logger.error(f"✗ 解析失败 {file_name}: {e}")

    return docs


def ingest_pdf_folder(
    folder_path: Optional[str] = None,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP
) -> List[Document]:
    """
    批量摄入文件夹中的所有 PDF 文献：
    1. 逐页提取文本
    2. 用 RecursiveCharacterTextSplitter 重叠切分
    3. 返回切分后的 Document 列表（含 metadata）
    """
    if folder_path is None:
        folder_path = PDF_DIR

    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"论文目录不存在: {folder_path}")

    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    if not pdf_files:
        raise ValueError(f"目录中未找到 PDF 文件: {folder_path}")

    logger.info(f"发现 {len(pdf_files)} 篇 PDF 论文，开始解析...")

    all_docs = []
    for pdf_file in pdf_files:
        file_path = os.path.join(folder_path, pdf_file)
        docs = load_pdf_with_metadata(file_path)
        all_docs.extend(docs)

    logger.info(f"共提取 {len(all_docs)} 个页面文档")

    # 重叠切分
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", ".", "；", ";", " ", ""],
        length_function=len,
        add_start_index=True  # 记录切分起始位置
    )

    chunks = text_splitter.split_documents(all_docs)
    logger.info(f"切分为 {len(chunks)} 个文本块 (chunk_size={chunk_size}, overlap={chunk_overlap})")

    return chunks
