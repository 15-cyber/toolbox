"""
配置管理模块 - 模型预设、路径、系统常量
"""
import os
import sys

# ── 项目路径 ──────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(BASE_DIR, "论文pdf")
CHROMA_DIR = os.path.join(BASE_DIR, ".chroma_db")

# ── PDF 处理参数 ──────────────────────────────────────
CHUNK_SIZE = 1000       # 文本块大小（字符）
CHUNK_OVERLAP = 200     # 块重叠度（字符）
TOP_K = 4               # 检索返回的最相关文本块数
MEMORY_WINDOW = 5       # 对话记忆保留轮数

# ── 模型预设 ──────────────────────────────────────────
# 用户可在 GUI 中选择，也可通过 CLI 参数指定
MODEL_PRESETS = {
    "DeepSeek-V3": {
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com",
        "description": "DeepSeek 通用对话模型，性价比高"
    },
    "DeepSeek-R1": {
        "model": "deepseek-reasoner",
        "base_url": "https://api.deepseek.com",
        "description": "DeepSeek 推理增强模型"
    },
    "OpenAI GPT-4o": {
        "model": "gpt-4o",
        "base_url": "https://api.openai.com/v1",
        "description": "OpenAI 旗舰多模态模型"
    },
    "OpenAI GPT-4o-mini": {
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1",
        "description": "OpenAI 轻量快速模型"
    },
    "通义千问 (Qwen-Max)": {
        "model": "qwen-max",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "description": "阿里通义千问旗舰模型"
    },
    "智谱 GLM-4": {
        "model": "glm-4",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "description": "智谱 AI 通用大模型"
    },
    "Moonshot (Kimi)": {
        "model": "moonshot-v1-8k",
        "base_url": "https://api.moonshot.cn/v1",
        "description": "月之暗面 Kimi 模型"
    },
    "自定义": {
        "model": "",
        "base_url": "",
        "description": "手动输入模型名和 API 地址"
    }
}

# ── 系统 Prompt 模板 ─────────────────────────────────
RAG_SYSTEM_PROMPT = """你是一个精通学术论文深度解析的AI助手。请严格根据以下给出的【已知文献上下文】来回答用户的问题。

严格要求：
1. 如果问题在上下文中没有提及，请直接回答"基于目前加载的文献库，无法提供确切解答"，绝对不允许拼凑或胡编乱造任何观点。
2. 在回答的句末或段落末，必须用 [文件名, 第X页] 标注数据来源。
3. 如果用户要求生成参考文献引用，请严格按照 GB/T 7714-2015 格式输出。

已知文献片段：
{context}

对话历史：
{chat_history}

用户问题：{question}
请严谨回答："""

# ── Prompt Guard 配置 ────────────────────────────────
# 触发自修复的高度不确定性关键词
GUARD_TRIGGER_WORDS = ["我认为", "可能", "也许", "大概", "应该", "估计", "或许", "不太确定"]

# 自修复纠错 Prompt
GUARD_CORRECTION_PROMPT = """检测到您的回答未完全依据已知文档，或包含高度不确定性表述。请根据给定的上下文重新进行严谨、结构化的回答，严格引用文献来源。"""
