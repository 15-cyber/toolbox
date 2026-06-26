<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/LangChain-RAG-green?logo=langchain" alt="LangChain">
  <img src="https://img.shields.io/badge/GUI-PyQt6-purple?logo=qt" alt="PyQt6">
  <img src="https://img.shields.io/badge/license-MIT-orange" alt="License">
</p>

<h1 align="center">📚 论文助手 Agent</h1>
<h3 align="center">基于 RAG 的科研文献智能解析桌面系统</h3>

<p align="center">
  <b>拖入论文 → 自动分析 → 智能问答 → 一键引用</b><br>
  让 AI 替你读懂每一篇论文，秒级检索、精准对比、自动生成标准引用。
</p>

---

## 🤔 为什么需要这个工具？

科研工作者每天面对海量 PDF 论文，传统方式逐个打开、手动翻阅、自行归纳的流程低效且容易遗漏关键信息。**论文助手 Agent** 将你本地的论文文献库变成一个「可对话的知识库」——

- 📖 **不用翻 PDF**，直接问「这篇论文用了什么方法？精度多少？」
- 🔍 **秒级跨论文对比**，「对比这三篇论文在土壤分类方法上的异同」
- 📝 **自动生成引用**，「帮我生成徐翰懿那篇论文的 GB/T 7714 引用」
- 🛡️ **拒绝胡编**，严格基于文献上下文回答，找不到就说找不到

## ✨ 核心能力

| 能力 | 说明 |
|---|---|
| 🗂️ **批量文献摄入** | 一键加载文件夹下所有 PDF，自动提取文本、清洗杂行、智能重叠切分 |
| 🧠 **向量语义检索** | 文本块 Embedding 存入 Chroma 本地向量库，Top-K 精准召回相关段落 |
| 💬 **多轮深度对话** | 带记忆的检索增强生成，5 轮对话窗口，追问不丢上下文 |
| 🎯 **严格反幻觉** | 强制约束 System Prompt + 关键词检测护栏，杜绝「我认为」「可能」式臆造 |
| 📄 **GB/T 7714 引用** | 对话中自动识别引用意图，内置 Few-Shot 规范，LLM 排版输出标准学术引用 |
| 🌐 **多模型自由切换** | DeepSeek / GPT-4o / 通义千问 / GLM-4 / Kimi 等即选即用，也支持自定义兼容 API |
| 🖥️ **商务级桌面 GUI** | PyQt6 双栏布局，左侧文件管理、右侧聊天气泡，即装即用的专业体验 |
| ⚡ **流式逐字输出** | 打字机式实时渲染，交互流畅不等待 |
| 📦 **单文件 EXE 分发** | PyInstaller 一键打包，Windows 双击运行，无需 Python 环境 |

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────┐
│                  PyQt6 Desktop GUI                    │
│           ┌──────────────┬──────────────────┐        │
│           │  文件管理面板  │   对话交互面板     │        │
│           └──────────────┴──────────────────┘        │
├─────────────────────────────────────────────────────┤
│              LangChain Agent Engine                  │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │  Memory   │  │  Prompt  │  │  Prompt Guard     │  │
│  │ (Window=5)│  │  Template│  │ (关键词+自修复)    │  │
│  └──────────┘  └──────────┘  └───────────────────┘  │
│  ┌──────────────────────────────────────────────┐   │
│  │  ConversationalRetrievalChain (k=4)           │   │
│  └──────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────┤
│                Chroma Vector Store                   │
│         持久化 .chroma_db / ── Top-K 检索            │
├─────────────────────────────────────────────────────┤
│              Data Ingestion Pipeline                 │
│   PDFPlumber → 文本清洗 → RecursiveCharacterTextSplitter │
│               (chunk_size=1000, overlap=200)          │
└─────────────────────────────────────────────────────┘
```

## 🚀 快速上手

### 环境要求

- Python 3.9+
- Windows / macOS / Linux
- 任意兼容 OpenAI API 格式的大模型 API Key

### 安装

```bash
git clone https://github.com/15-cyber/toolbox.git
cd toolbox
pip install -r requirements.txt
```

### 运行

```bash
# 命令行版本（轻量、快速验证）
python cli.py

# 桌面 GUI 版本（完整体验）
python gui.py
```

### 使用流程

1. **配置 API Key** — 点击「⚙ 设置」，填入你的大模型 API Key 并选择模型
2. **加载论文** — 点击「📂 加载论文文件夹」，选择存放 PDF 论文的目录
3. **开始对话** — 在输入框输入问题，Agent 自动检索文献并生成严谨回答

## 💡 对话示例

```
你: 徐翰懿的论文中使用了哪些光谱预处理方法？

Agent: 根据徐翰懿的硕士论文，该研究对比了多种光谱预处理方法，
包括一阶微分、二阶微分、标准正态变量变换(SNV)、多元散射校正(MSC)
以及 Savitzky-Golay(SG)平滑。研究发现 SG 平滑结合吸收率转换
对土壤有机质预测效果最优…… 
[基于剖面Vis-NIR光谱的土壤属性预测与分类研究_徐翰懿.pdf, 第5页]


你: 帮我生成这篇论文的 GB/T 7714 引用

Agent: [1] 徐翰懿. 基于剖面Vis-NIR光谱的土壤属性预测与分类研究[D]. 
杭州: 浙江大学, 2024.
```

## 📁 项目结构

```
toolbox/
├── cli.py                 # CLI 命令行入口
├── gui.py                 # PyQt6 桌面 GUI 入口
├── build.spec             # PyInstaller 打包配置
├── requirements.txt       # Python 依赖清单
├── src/
│   ├── config.py          # 模型预设、Prompt 模板、Guard 规则
│   ├── ingestion.py       # PDF 数据摄入管道
│   ├── vector_store.py    # Chroma 向量库管理
│   ├── rag_engine.py      # RAG 引擎核心编排
│   └── citation.py        # GB/T 7714 学术引用生成
└── 论文pdf/               # 论文文献目录（示例）
```

## 🛠️ 打包分发

```bash
pyinstaller build.spec
# 输出文件位于 dist/论文助手Agent.exe
```

## 📋 技术栈

| 层级 | 技术选型 |
|---|---|
| 大模型框架 | LangChain（ConversationalRetrievalChain） |
| 向量数据库 | Chroma（本地嵌入式持久化） |
| 文档解析 | PDFPlumber + TikToken |
| 桌面 GUI | PyQt6 |
| 打包分发 | PyInstaller |
| 兼容模型 | DeepSeek / GPT-4o / Qwen-Max / GLM-4 / Kimi 等 |

## 🗺️ 路线图

- [x] CLI 核心 RAG 引擎
- [x] PyQt6 桌面 GUI
- [x] 多模型切换
- [x] GB/T 7714 引用生成
- [x] Prompt Guard 反幻觉
- [ ] 对话历史导出（Markdown / Word）
- [ ] 论文关系图谱可视化
- [ ] 本地 Embedding 模型支持（免 API 向量化）
- [ ] 论文元数据自动提取（标题、作者、年份）

## 📄 License

MIT © 2025
