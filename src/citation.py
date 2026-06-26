"""
GB/T 7714-2015 参考文献引用生成模块
"""
import re
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# ── GB/T 7714-2015 格式 Few-Shot 示例 ────────────────
GB_T7714_FEWSHOT = """
【GB/T 7714-2015 参考文献格式规范】

期刊论文格式：
[序号] 作者. 题名[J]. 刊名, 出版年, 卷号(期号): 起止页码.
示例：[1] 张三, 李四, 王五. 基于深度学习的土壤分类方法研究[J]. 遥感学报, 2023, 27(3): 456-468.

学位论文格式：
[序号] 作者. 题名[D]. 出版地: 出版者, 出版年.
示例：[2] 徐翰懿. 基于剖面Vis-NIR光谱的土壤属性预测与分类研究[D]. 北京: 中国科学院大学, 2024.

会议论文格式：
[序号] 作者. 题名[C]// 会议名称. 出版地: 出版者, 出版年: 起止页码.
示例：[3] 杨瑞清. 基于深度学习与RGB图像的土壤类型识别[C]// 中国土壤学会年会论文集. 南京: 中国土壤学会, 2023: 123-130.

注意事项：
- 作者超过3人时，列出前3人后加", 等"或", et al"
- 无明确页码时标注总页数或省略
- 严格使用半角标点符号
"""


def build_citation_prompt(question: str) -> str:
    """
    如果用户询问引用相关问题，将 GB/T 7714 规范注入到问题上下文中。
    这样 LLM 会自动按照规范格式输出。
    """
    return f"{GB_T7714_FEWSHOT}\n\n请根据以上格式规范，回答以下问题：\n{question}"


def detect_citation_request(question: str) -> bool:
    """检测用户是否在请求参考文献引用"""
    keywords = [
        "引用", "参考文献", "reference", "cite", "citation",
        "GB/T", "7714", "格式", "标注来源", "列出文献"
    ]
    question_lower = question.lower()
    return any(kw.lower() in question_lower for kw in keywords)


def enhance_query_for_citation(question: str) -> str:
    """
    增强查询：如果检测到引用请求，自动注入 GB/T 7714 格式规范。
    """
    if detect_citation_request(question):
        return build_citation_prompt(question)
    return question


# ── 基础 PDF 元数据提取 ───────────────────────────────
def extract_pdf_metadata(file_path: str) -> Dict[str, str]:
    """从 PDF 文件提取基础元数据（标题、作者推测等）"""
    metadata = {
        "filename": "",
        "title": "",
        "authors": "",
        "year": ""
    }

    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            # 文件名
            metadata["filename"] = file_path

            # 尝试从文档信息提取
            if pdf.metadata:
                info = pdf.metadata
                metadata["title"] = info.get("Title", "") or ""
                metadata["authors"] = info.get("Author", "") or ""

            # 从第一页文本推测标题和作者
            if not metadata["title"] and len(pdf.pages) > 0:
                first_page_text = pdf.pages[0].extract_text() or ""
                lines = first_page_text.strip().split('\n')
                # 取前几行作为标题候选
                for line in lines[:10]:
                    clean = line.strip()
                    if len(clean) > 10 and not clean.startswith(('http', 'DOI', '第', '摘 要', '关键')):
                        metadata["title"] = clean
                        break

            # 尝试提取年份
            if not metadata["year"] and metadata.get("title"):
                year_match = re.search(r'(20\d{2})', metadata["title"])
                if year_match:
                    metadata["year"] = year_match.group(1)

    except Exception as e:
        logger.warning(f"提取元数据失败: {file_path} - {e}")

    return metadata
