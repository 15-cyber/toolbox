# 论文助手 Agent - 科研文献深度解析系统

基于 **LangChain + Chroma RAG** 架构的本地桌面端科研论文智能解析工具。

## 功能特性

- **多模型兼容** — 支持 DeepSeek、OpenAI GPT-4o、通义千问、智谱 GLM-4、Kimi 等兼容 OpenAI API 格式的大模型，用户可自由切换
- **本地 PDF 智能摄入** — 批量加载文件夹内 PDF 论文，自动清洗页码/杂乱行，`RecursiveCharacterTextSplitter` 重叠切分（chunk_size=1000, overlap=200）
- **Chroma 向量持久化** — 文本块 Embedding 向量化后存入本地 `.chroma_db/`，启动时自动加载免重复处理
- **RAG 检索增强生成** — `ConversationalRetrievalChain` + `ConversationBufferWindowMemory`（窗口 k=5），严格上下文约束 Prompt 对抗幻觉
- **学术引用自动生成** — 对话中检测引用请求，自动注入 GB/T 7714-2015 格式 Few-Shot 规范，LLM 自动排版输出
- **Prompt Guard 安全护栏** — 关键词检测（"我认为""可能"等）自动触发纠错重试
- **流式逐字输出** — LLM `streaming=True` 回调实时渲染，打字机式交互体验
- **双栏商务风 GUI** — PyQt6 左侧文件管理 + 右侧聊天气泡，现代简约风格
- **PyInstaller 一键打包** — 单文件 EXE 输出，Windows 双击即用

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 CLI 命令行
python cli.py

# 启动桌面 GUI
python gui.py

# 打包 EXE
pyinstaller build.spec
```

## 项目结构

```
论文助手agent开发/
├── cli.py                 # CLI 命令行入口
├── gui.py                 # PyQt6 桌面 GUI
├── build.spec             # PyInstaller 打包配置
├── requirements.txt       # 依赖清单
├── src/
│   ├── config.py          # 模型预设 & Prompt 模板 & Guard 规则
│   ├── ingestion.py       # PDF 摄入：加载→清洗→切分
│   ├── vector_store.py    # Chroma 向量库管理
│   ├── rag_engine.py      # RAG 引擎核心
│   └── citation.py        # GB/T 7714 引用生成
└── 论文pdf/               # 论文文献目录
```

## 技术栈

`Python 3.9+` · `LangChain` · `Chroma` · `PyQt6` · `PDFPlumber` · `TikToken` · `PyInstaller`
