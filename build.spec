# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置 - 论文助手 Agent
用法: pyinstaller build.spec
"""

import sys
from pathlib import Path

block_cipher = None

# 项目根目录
BASE_DIR = Path(__file__).parent.absolute()

# 需要额外包含的隐藏导入
hidden_imports = [
    # LangChain
    'langchain', 'langchain_community', 'langchain_openai', 'langchain_chroma',
    'langchain_core', 'langchain_text_splitters', 'langsmith',
    # ChromaDB
    'chromadb', 'chromadb.config', 'chromadb.db', 'chromadb.api',
    'chromadb.utils.embedding_functions',
    # PDF
    'pdfplumber', 'pdfminer', 'pdfminer.high_level',
    'pypdf', 'pypdfium2',
    # Tokenizer
    'tiktoken', 'tiktoken_ext', 'tiktoken_ext.openai_public',
    # 其他
    'dotenv', 'yaml', 'sqlalchemy', 'pydantic',
    'openai', 'httpx', 'aiohttp',
    # PyQt6
    'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets',
    'PyQt6.sip',
]

# 需要打包的数据文件
datas = []

# ChromaDB 的 SQLite 驱动 (关键!)
# Windows 上 chromadb 使用 duckdb + sqlite3
try:
    import chromadb
    chroma_path = Path(chromadb.__file__).parent
    # 添加 chromadb 的持久化模块
    datas.append((str(chroma_path / 'migrations'), 'chromadb/migrations'))
except ImportError:
    pass

# 添加 src 包
datas.append((str(BASE_DIR / 'src'), 'src'))


a = Analysis(
    ['gui.py'],
    pathex=[str(BASE_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'unittest', 'test', 'tests',
        'matplotlib', 'numpy.testing', 'scipy',
        'IPython', 'jupyter', 'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='论文助手Agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # Windows GUI 模式，不显示控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # 可添加 .ico 图标路径
)
