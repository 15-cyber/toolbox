"""
CLI 命令行交互入口 - 论文助手 Agent
用法: python cli.py
"""
import os
import sys
import logging
import asyncio

# 将项目根目录加入 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import MODEL_PRESETS, PDF_DIR
from src.rag_engine import RAGEngine
from src.citation import enhance_query_for_citation

# ── 日志配置 ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("CLI")

# ── 终端颜色（Windows 兼容）───────────────────────────
os.system("")  # 启用 Windows 终端 ANSI 颜色支持

C = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "cyan": "\033[36m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "red": "\033[31m",
    "blue": "\033[34m",
    "magenta": "\033[35m"
}


def print_banner():
    """打印启动横幅"""
    print(f"""
{C['cyan']}{C['bold']}╔══════════════════════════════════════════════════════╗
║       科研论文深度解析 Agent - CLI 验证版              ║
║       LangChain + Chroma RAG + 多模型兼容               ║
╚══════════════════════════════════════════════════════╝{C['reset']}
""")


def select_model() -> dict:
    """交互式选择模型"""
    print(f"\n{C['bold']}请选择大模型（输入序号）:{C['reset']}\n")
    presets = list(MODEL_PRESETS.items())

    for i, (name, cfg) in enumerate(presets, 1):
        print(f"  {C['green']}[{i}]{C['reset']} {name} - {cfg['description']}")

    while True:
        try:
            choice = input(f"\n{C['yellow']}请输入序号 (1-{len(presets)}): {C['reset']}").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(presets):
                name, cfg = presets[idx]
                print(f"{C['green']}✓ 已选择: {name}{C['reset']}")
                return {"name": name, **cfg}
        except ValueError:
            pass
        print(f"{C['red']}无效输入，请重试{C['reset']}")


def get_api_key() -> str:
    """获取 API Key"""
    key = os.environ.get("OPENAI_API_KEY", "")
    if key:
        print(f"{C['green']}✓ 从环境变量读取 API Key{C['reset']}")
        return key

    print(f"\n{C['yellow']}请输入 API Key (输入后不可见):{C['reset']}")
    # Windows 下模拟密码输入
    import msvcrt
    key = ""
    while True:
        ch = msvcrt.getch()
        if ch == b'\r' or ch == b'\n':
            break
        if ch == b'\x08':  # 退格
            if key:
                key = key[:-1]
                sys.stdout.write('\b \b')
                sys.stdout.flush()
        else:
            char = ch.decode('utf-8', errors='ignore')
            key += char
            sys.stdout.write('*')
            sys.stdout.flush()
    print()
    return key


def format_source_docs(source_docs: list) -> str:
    """格式化源文档引用"""
    if not source_docs:
        return ""
    sources = set()
    for doc in source_docs:
        meta = doc.metadata
        fname = meta.get("source", "未知")
        page = meta.get("page", "?")
        sources.add(f"  📄 {fname}, 第{page}页")
    return "\n".join(sorted(sources))


def main():
    """CLI 主入口"""
    print_banner()

    # 1. 选择模型
    model_cfg = select_model()

    # 2. 获取 API Key
    api_key = get_api_key()
    if not api_key:
        print(f"{C['red']}✗ API Key 不能为空，退出.{C['reset']}")
        return

    # 3. 初始化 RAG 引擎
    print(f"\n{C['cyan']}⏳ 初始化 RAG 引擎...{C['reset']}")
    engine = RAGEngine(
        api_key=api_key,
        base_url=model_cfg["base_url"],
        model_name=model_cfg["model"],
        embedding_model="text-embedding-ada-002"  # 嵌入也可后续配置
    )
    print(f"{C['green']}✓ 引擎初始化完成 (模型: {model_cfg['name']}){C['reset']}")

    # 4. 文献摄入
    pdf_dir = PDF_DIR
    if not os.path.isdir(pdf_dir) or not any(f.endswith('.pdf') for f in os.listdir(pdf_dir)):
        print(f"{C['yellow']}⚠ 论文目录无 PDF 文件: {pdf_dir}{C['reset']}")
        alt = input("请输入论文文件夹路径 (回车跳过): ").strip()
        if alt:
            pdf_dir = alt

    print(f"\n{C['cyan']}⏳ 正在摄入文献: {pdf_dir}{C['reset']}")
    result = engine.ingest_pdfs(pdf_dir)
    print(f"{C['green']}{result}{C['reset']}")

    # 5. 交互式问答循环
    print(f"\n{C['bold']}{C['magenta']}════════════ 开始对话 (输入 /quit 退出, /clear 清空记忆, /status 查看状态) ════════════{C['reset']}\n")

    while True:
        try:
            question = input(f"{C['bold']}{C['cyan']}你: {C['reset']}").strip()

            if not question:
                continue

            # 命令处理
            if question.lower() in ("/quit", "/exit", "/q"):
                print(f"{C['yellow']}再见！{C['reset']}")
                break
            elif question.lower() in ("/clear", "/c"):
                engine.clear_memory()
                print(f"{C['green']}✓ 对话记忆已清空{C['reset']}")
                continue
            elif question.lower() in ("/status", "/s"):
                status = engine.get_status()
                print(f"{C['blue']}引擎状态: {status}{C['reset']}")
                print(f"{C['blue']}记忆: {engine.get_memory_summary()}{C['reset']}")
                continue

            # 增强引用请求
            enhanced_question = enhance_query_for_citation(question)

            # 查询
            print(f"\n{C['bold']}{C['green']}Agent: {C['reset']}", end="", flush=True)
            response = engine.query(enhanced_question)

            # 打印回答
            print(response["answer"])

            # 打印源文档
            sources = format_source_docs(response.get("source_documents", []))
            if sources:
                print(f"\n{C['blue']}📚 参考来源:{C['reset']}")
                print(sources)

            print()

        except KeyboardInterrupt:
            print(f"\n{C['yellow']}再见！{C['reset']}")
            break
        except Exception as e:
            print(f"\n{C['red']}✗ 错误: {e}{C['reset']}")
            logger.exception("CLI 异常")


if __name__ == "__main__":
    main()
