# -*- coding: utf-8 -*-
"""
论文助手 Agent - PyQt6 桌面 GUI
双栏布局：左侧文件管理 + 右侧对话窗口，商务风格
"""
import sys
import os
import logging
import asyncio
from typing import Optional

# 项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QTextEdit, QPushButton, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QMessageBox, QProgressBar,
    QStatusBar, QToolBar, QFileDialog, QFrame, QScrollArea,
    QSizePolicy, QSpacerItem, QGroupBox
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize, QMetaObject,
    Q_ARG, QUrl
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QTextCursor,
    QAction, QKeySequence, QTextCharFormat, QSyntaxHighlighter
)
from PyQt6.QtCore import QObject

from src.config import MODEL_PRESETS, PDF_DIR
from src.rag_engine import RAGEngine
from src.citation import enhance_query_for_citation

logger = logging.getLogger("GUI")

# ── 商务风格样式表 ────────────────────────────────────
STYLE_QSS = """
/* 全局 */
QMainWindow {
    background-color: #f5f6fa;
}
QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* 工具栏 */
QToolBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e0e0e0;
    padding: 6px 12px;
    spacing: 10px;
}
QToolBar QLabel {
    color: #2c3e50;
    font-weight: bold;
    font-size: 14px;
}
QToolBar QComboBox {
    background: #ffffff;
    border: 1px solid #d5d8dc;
    border-radius: 4px;
    padding: 4px 8px;
    min-width: 160px;
    color: #2c3e50;
}
QToolBar QComboBox:hover {
    border: 1px solid #3498db;
}
QToolBar QComboBox::drop-down {
    border: none;
}

/* 按钮 */
QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #2980b9;
}
QPushButton:pressed {
    background-color: #2471a3;
}
QPushButton:disabled {
    background-color: #bdc3c7;
    color: #95a5a6;
}
QPushButton#btnSettings {
    background-color: #ffffff;
    color: #2c3e50;
    border: 1px solid #d5d8dc;
}
QPushButton#btnSettings:hover {
    background-color: #ecf0f1;
}
QPushButton#btnLoad {
    background-color: #27ae60;
}
QPushButton#btnLoad:hover {
    background-color: #229954;
}
QPushButton#btnClear {
    background-color: #e74c3c;
}
QPushButton#btnClear:hover {
    background-color: #c0392b;
}

/* 左侧面板 */
#leftPanel {
    background-color: #ffffff;
    border-right: 1px solid #e0e0e0;
}
#leftPanel QLabel {
    color: #2c3e50;
}
#leftPanel QGroupBox {
    border: 1px solid #e8e8e8;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
    background-color: #fafbfc;
}
#leftPanel QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #2c3e50;
    font-weight: bold;
}
#leftPanel QListWidget {
    border: none;
    background: transparent;
    color: #34495e;
    font-size: 12px;
}
#leftPanel QListWidget::item {
    padding: 4px 8px;
    border-bottom: 1px solid #f0f0f0;
}
#leftPanel QListWidget::item:hover {
    background-color: #eaf2f8;
}

/* 聊天区域 */
#chatArea {
    background-color: #f5f6fa;
    border: none;
    font-size: 13px;
    padding: 12px;
    line-height: 1.6;
}

/* 输入区域 */
#inputFrame {
    background-color: #ffffff;
    border-top: 1px solid #e0e0e0;
    padding: 10px;
}
#inputBox {
    background-color: #f8f9fa;
    border: 1px solid #d5d8dc;
    border-radius: 6px;
    padding: 10px;
    font-size: 13px;
    color: #2c3e50;
}
#inputBox:focus {
    border: 1px solid #3498db;
    background-color: #ffffff;
}

/* 进度条 */
QProgressBar {
    border: none;
    background-color: #ecf0f1;
    border-radius: 3px;
    height: 4px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #3498db;
    border-radius: 3px;
}

/* 状态栏 */
QStatusBar {
    background-color: #2c3e50;
    color: #ecf0f1;
    font-size: 11px;
    padding: 4px 10px;
}
QStatusBar QLabel {
    color: #ecf0f1;
}

/* 滚动条 */
QScrollBar:vertical {
    background: #f5f6fa;
    width: 8px;
}
QScrollBar::handle:vertical {
    background: #bdc3c7;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #95a5a6;
}

/* 消息框 */
QMessageBox {
    background-color: #ffffff;
}
QMessageBox QLabel {
    color: #2c3e50;
    font-size: 13px;
}
"""


# ── API Key 设置对话框 ───────────────────────────────
class SettingsDialog(QDialog):
    """API Key 与模型配置对话框"""

    def __init__(self, parent=None, current_key="", current_model="", current_base=""):
        super().__init__(parent)
        self.setWindowTitle("⚙ 设置 - API 配置")
        self.setMinimumWidth(500)
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QLabel { color: #2c3e50; font-size: 13px; }
            QLineEdit {
                border: 1px solid #d5d8dc; border-radius: 4px;
                padding: 8px; font-size: 13px; background: #f8f9fa;
            }
            QLineEdit:focus { border: 1px solid #3498db; background: #ffffff; }
            QComboBox {
                border: 1px solid #d5d8dc; border-radius: 4px;
                padding: 8px; font-size: 13px; background: #ffffff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 标题
        title = QLabel("API 配置")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        # API Key
        self.key_input = QLineEdit(current_key)
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("输入您的 API Key...")
        form.addRow("API Key:", self.key_input)

        # 模型选择
        self.model_combo = QComboBox()
        for name in MODEL_PRESETS.keys():
            self.model_combo.addItem(name)
        if current_model:
            idx = self.model_combo.findText(current_model)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        form.addRow("模型:", self.model_combo)

        # Base URL
        self.base_url_input = QLineEdit(current_base)
        self.base_url_input.setPlaceholderText("https://api.openai.com/v1")
        form.addRow("API 地址:", self.base_url_input)

        layout.addLayout(form)

        # 提示
        hint = QLabel("支持所有兼容 OpenAI API 格式的大模型服务")
        hint.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(hint)

        layout.addStretch()

        # 按钮
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self._on_model_changed(self.model_combo.currentText())

    def _on_model_changed(self, name):
        """切换模型时自动填充 Base URL"""
        cfg = MODEL_PRESETS.get(name, {})
        if cfg.get("base_url") and name != "自定义":
            self.base_url_input.setText(cfg["base_url"])
        if cfg.get("model") and name != "自定义":
            pass  # 模型名在引擎初始化时使用

    def get_values(self):
        return {
            "api_key": self.key_input.text().strip(),
            "model_name": self.model_combo.currentText(),
            "base_url": self.base_url_input.text().strip()
        }


# ── RAG 工作线程 ──────────────────────────────────────
class RAGWorker(QThread):
    """后台执行 RAG 查询，避免阻塞 UI"""
    token_signal = pyqtSignal(str)       # 逐 token 流式输出
    finished_signal = pyqtSignal(dict)    # 查询完成信号
    error_signal = pyqtSignal(str)        # 错误信号

    def __init__(self, engine: RAGEngine, question: str):
        super().__init__()
        self.engine = engine
        self.question = question

    def run(self):
        try:
            # 增强引用请求
            enhanced = enhance_query_for_citation(self.question)

            # 非流式查询（在子线程中）
            response = self.engine.query(enhanced)
            answer = response.get("answer", "")
            sources = response.get("source_documents", [])

            # 模拟流式输出
            for char in answer:
                self.token_signal.emit(char)
                self.msleep(15)  # 模拟打字效果

            self.finished_signal.emit({
                "answer": answer,
                "source_documents": sources
            })
        except Exception as e:
            self.error_signal.emit(str(e))


# ── 主窗口 ────────────────────────────────────────────
class MainWindow(QMainWindow):
    """论文助手主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("论文助手 Agent - 科研文献深度解析")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)

        # 状态
        self.api_key = ""
        self.model_preset_name = "DeepSeek-V3"
        self.base_url = MODEL_PRESETS["DeepSeek-V3"]["base_url"]
        self.model_name = MODEL_PRESETS["DeepSeek-V3"]["model"]
        self.engine: Optional[RAGEngine] = None
        self.is_ingesting = False
        self.worker: Optional[RAGWorker] = None

        self._init_ui()
        self._apply_style()

    def _init_ui(self):
        """初始化 UI 组件"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 工具栏 ────────────────────────────────────
        self._create_toolbar()

        # ── 主分割区 ──────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        # 左侧面板
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # 右侧聊天区
        right_panel = self._create_chat_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)  # 左侧 1 份
        splitter.setStretchFactor(1, 3)  # 右侧 3 份
        splitter.setSizes([320, 1080])

        main_layout.addWidget(splitter)

        # ── 状态栏 ────────────────────────────────────
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status("就绪 - 请先配置 API Key 并加载文献")

    def _create_toolbar(self):
        """创建顶部工具栏"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setObjectName("mainToolbar")
        self.addToolBar(toolbar)

        # 标题
        title_label = QLabel("📚 论文助手 Agent")
        toolbar.addWidget(title_label)
        toolbar.addSeparator()

        # 模型选择
        toolbar.addWidget(QLabel("模型:"))
        self.model_selector = QComboBox()
        for name in MODEL_PRESETS.keys():
            self.model_selector.addItem(name)
        self.model_selector.currentTextChanged.connect(self._on_model_changed)
        toolbar.addWidget(self.model_selector)
        toolbar.addSeparator()

        # 设置按钮
        btn_settings = QPushButton("⚙ 设置")
        btn_settings.setObjectName("btnSettings")
        btn_settings.clicked.connect(self._show_settings)
        toolbar.addWidget(btn_settings)

        toolbar.addSeparator()

        # 清空对话
        btn_clear = QPushButton("🗑 清空对话")
        btn_clear.setObjectName("btnClear")
        btn_clear.clicked.connect(self._clear_conversation)
        toolbar.addWidget(btn_clear)

        # 弹性空间
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # 版本
        version_label = QLabel("v1.0")
        version_label.setStyleSheet("color: #95a5a6; font-size: 11px;")
        toolbar.addWidget(version_label)

    def _create_left_panel(self) -> QWidget:
        """创建左侧文件管理面板"""
        panel = QWidget()
        panel.setObjectName("leftPanel")
        panel.setMinimumWidth(280)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # 加载文献按钮
        self.btn_load = QPushButton("📂 加载论文文件夹")
        self.btn_load.setObjectName("btnLoad")
        self.btn_load.clicked.connect(self._load_pdf_folder)
        layout.addWidget(self.btn_load)

        # 论文目录显示
        self.folder_label = QLabel("未加载")
        self.folder_label.setStyleSheet("color: #7f8c8d; font-size: 11px; padding: 4px;")
        self.folder_label.setWordWrap(True)
        layout.addWidget(self.folder_label)

        # PDF 文件列表
        pdf_group = QGroupBox("📄 已加载文献")
        pdf_layout = QVBoxLayout(pdf_group)
        self.pdf_list = QListWidget()
        self.pdf_list.setMaximumHeight(180)
        pdf_layout.addWidget(self.pdf_list)
        layout.addWidget(pdf_group)

        # 向量库统计
        stats_group = QGroupBox("📊 向量库状态")
        stats_layout = QVBoxLayout(stats_group)
        self.stats_label = QLabel("文本块: 0\n向量库: 未初始化")
        self.stats_label.setStyleSheet("color: #7f8c8d; font-size: 12px; padding: 4px;")
        stats_layout.addWidget(self.stats_label)
        layout.addWidget(stats_group)

        # 摄入进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 使用提示
        tips_group = QGroupBox("💡 使用提示")
        tips_layout = QVBoxLayout(tips_group)
        tips = QLabel(
            "1. 点击「设置」配置 API Key\n"
            "2. 加载论文 PDF 文件夹\n"
            "3. 在右侧输入问题开始对话\n"
            "4. 支持多轮对话记忆 (5轮)\n"
            "5. 引用格式遵循 GB/T 7714"
        )
        tips.setStyleSheet("color: #7f8c8d; font-size: 11px; padding: 4px; line-height: 1.8;")
        tips_layout.addWidget(tips)
        layout.addWidget(tips_group)

        layout.addStretch()
        return panel

    def _create_chat_panel(self) -> QWidget:
        """创建右侧聊天面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 聊天显示区
        self.chat_display = QTextEdit()
        self.chat_display.setObjectName("chatArea")
        self.chat_display.setReadOnly(True)
        self.chat_display.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(self.chat_display, stretch=1)

        # 输入区域
        input_frame = QWidget()
        input_frame.setObjectName("inputFrame")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(12, 8, 12, 8)
        input_layout.setSpacing(8)

        self.input_box = QTextEdit()
        self.input_box.setObjectName("inputBox")
        self.input_box.setPlaceholderText("输入您的问题... (Enter 发送, Shift+Enter 换行)")
        self.input_box.setMaximumHeight(100)
        self.input_box.setMinimumHeight(40)
        self.input_box.installEventFilter(self)
        input_layout.addWidget(self.input_box)

        self.btn_send = QPushButton("发送 ➤")
        self.btn_send.clicked.connect(self._send_message)
        self.btn_send.setMinimumWidth(90)
        input_layout.addWidget(self.btn_send)

        layout.addWidget(input_frame)
        return panel

    def _apply_style(self):
        """应用全局样式"""
        self.setStyleSheet(STYLE_QSS)

    # ── 事件处理 ──────────────────────────────────────
    def eventFilter(self, obj, event):
        """拦截输入框的 Enter 键"""
        from PyQt6.QtCore import QEvent
        if obj == self.input_box and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not (
                event.modifiers() & Qt.KeyboardModifier.ShiftModifier
            ):
                self._send_message()
                return True
        return super().eventFilter(obj, event)

    def _on_model_changed(self, name):
        """模型切换"""
        cfg = MODEL_PRESETS.get(name, {})
        self.model_preset_name = name
        if name != "自定义":
            self.base_url = cfg.get("base_url", "")
            self.model_name = cfg.get("model", "")
        self._update_status(f"模型已切换: {name}")

    def _show_settings(self):
        """显示设置对话框"""
        dlg = SettingsDialog(
            self,
            current_key=self.api_key,
            current_model=self.model_preset_name,
            current_base=self.base_url
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            values = dlg.get_values()
            self.api_key = values["api_key"]
            self.model_preset_name = values["model_name"]
            self.base_url = values["base_url"]

            cfg = MODEL_PRESETS.get(self.model_preset_name, {})
            if self.model_preset_name != "自定义":
                self.model_name = cfg.get("model", self.model_name)

            # 更新模型选择器
            idx = self.model_selector.findText(self.model_preset_name)
            if idx >= 0:
                self.model_selector.blockSignals(True)
                self.model_selector.setCurrentIndex(idx)
                self.model_selector.blockSignals(False)

            self._init_engine()
            self._update_status(f"✓ 配置已更新: {self.model_preset_name}")

    def _init_engine(self):
        """初始化 RAG 引擎"""
        if not self.api_key or not self.base_url:
            return
        try:
            self.engine = RAGEngine(
                api_key=self.api_key,
                base_url=self.base_url,
                model_name=self.model_name
            )
            self._update_stats()
            self._update_status(f"✓ 引擎就绪: {self.model_preset_name}")
        except Exception as e:
            QMessageBox.warning(self, "引擎初始化失败", str(e))

    def _load_pdf_folder(self):
        """加载论文文件夹"""
        if not self.api_key:
            QMessageBox.information(self, "提示", "请先在「设置」中配置 API Key")
            self._show_settings()
            if not self.api_key:
                return

        folder = QFileDialog.getExistingDirectory(
            self, "选择论文 PDF 文件夹",
            PDF_DIR if os.path.isdir(PDF_DIR) else os.path.expanduser("~")
        )
        if not folder:
            return

        if self.engine is None:
            self._init_engine()

        if self.engine is None:
            return

        self.is_ingesting = True
        self.btn_load.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度

        self._update_status("⏳ 正在解析论文...")
        self.folder_label.setText(folder)
        QApplication.processEvents()

        try:
            result = self.engine.ingest_pdfs(folder)
            self._update_pdf_list(folder)
            self._update_stats()
            self._update_status(f"✓ {result}")
            self._append_system_message(f"📚 {result}")
        except Exception as e:
            QMessageBox.critical(self, "加载失败", str(e))
            self._update_status(f"✗ 加载失败: {e}")
        finally:
            self.is_ingesting = False
            self.btn_load.setEnabled(True)
            self.progress_bar.setVisible(False)

    def _update_pdf_list(self, folder):
        """更新 PDF 文件列表"""
        self.pdf_list.clear()
        if os.path.isdir(folder):
            for f in sorted(os.listdir(folder)):
                if f.lower().endswith('.pdf'):
                    item = QListWidgetItem(f"📕 {f}")
                    item.setToolTip(f)
                    self.pdf_list.addItem(item)

    def _update_stats(self):
        """更新向量库统计"""
        if self.engine:
            status = self.engine.get_status()
            self.stats_label.setText(
                f"模型: {status['model']}\n"
                f"文本块: {status['vector_count']}\n"
                f"记忆窗口: {status['memory_rounds']} 轮"
            )
        else:
            self.stats_label.setText("文本块: 0\n向量库: 未初始化")

    def _send_message(self):
        """发送消息"""
        question = self.input_box.toPlainText().strip()
        if not question:
            return

        if self.engine is None or not self.engine.is_ready:
            QMessageBox.information(self, "提示", "请先加载文献库后再提问。")
            return

        # 禁用输入
        self.input_box.clear()
        self.input_box.setEnabled(False)
        self.btn_send.setEnabled(False)

        # 显示用户消息
        self._append_user_message(question)

        # 显示 AI 消息占位
        self._append_ai_header()
        self.ai_cursor = self.chat_display.textCursor()
        self.ai_answer_buffer = ""

        # 启动工作线程
        self.worker = RAGWorker(self.engine, question)
        self.worker.token_signal.connect(self._on_token)
        self.worker.finished_signal.connect(self._on_query_finished)
        self.worker.error_signal.connect(self._on_query_error)
        self.worker.start()

        self._update_status("⏳ 思考中...")

    def _on_token(self, token: str):
        """接收流式 token"""
        self.ai_answer_buffer += token
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(token)
        self.chat_display.ensureCursorVisible()

    def _on_query_finished(self, result: dict):
        """查询完成"""
        answer = result.get("answer", "")
        sources = result.get("source_documents", [])

        # 添加来源引用
        if sources:
            source_lines = ["\n\n---\n📚 **参考来源:**"]
            seen = set()
            for doc in sources:
                meta = doc.metadata
                fname = meta.get("source", "未知")
                page = meta.get("page", "?")
                key = f"{fname}:{page}"
                if key not in seen:
                    seen.add(key)
                    source_lines.append(f"\n📄 {fname}, 第{page}页")

            for line in source_lines:
                cursor = self.chat_display.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                cursor.insertText(line)

        self.chat_display.append("\n")

        # 恢复输入
        self.input_box.setEnabled(True)
        self.btn_send.setEnabled(True)
        self.input_box.setFocus()
        self.worker = None

        doc_count = len(self.engine.vector_manager.get_document_count()) if self.engine else 0
        self._update_status(f"✓ 就绪 | 模型: {self.model_preset_name} | 文献块: {doc_count}")

    def _on_query_error(self, error: str):
        """查询出错"""
        self.chat_display.append(f"\n❌ 查询出错: {error}\n")
        self.input_box.setEnabled(True)
        self.btn_send.setEnabled(True)
        self.worker = None
        self._update_status(f"✗ 错误: {error}")

    def _clear_conversation(self):
        """清空对话"""
        if self.engine:
            self.engine.clear_memory()
        self.chat_display.clear()
        self._append_system_message("🗑 对话已清空")
        self._update_status("对话已清空")

    # ── 消息显示 ──────────────────────────────────────
    def _append_user_message(self, text: str):
        """添加用户消息"""
        self.chat_display.append(
            f'<div style="text-align:right; margin:8px 0;">'
            f'<span style="background-color:#3498db; color:white; '
            f'padding:10px 16px; border-radius:12px 12px 0 12px; '
            f'display:inline-block; max-width:80%; text-align:left; '
            f'font-size:13px;">{text}</span></div>'
        )

    def _append_ai_header(self):
        """添加 AI 回答头部"""
        self.chat_display.append(
            f'<div style="text-align:left; margin:8px 0;">'
            f'<span style="background-color:#ffffff; color:#2c3e50; '
            f'padding:10px 16px; border-radius:12px 12px 12px 0; '
            f'display:inline-block; max-width:85%; text-align:left; '
            f'font-size:13px; border:1px solid #e8e8e8;">'
        )

    def _append_system_message(self, text: str):
        """添加系统消息"""
        self.chat_display.append(
            f'<div style="text-align:center; margin:8px 0;">'
            f'<span style="color:#95a5a6; font-size:11px;">{text}</span></div>'
        )

    def _update_status(self, message: str):
        """更新状态栏"""
        self.status_bar.showMessage(message)


# ── 主入口 ────────────────────────────────────────────
def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

    app = QApplication(sys.argv)
    app.setApplicationName("论文助手 Agent")
    app.setOrganizationName("PaperAssistant")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
