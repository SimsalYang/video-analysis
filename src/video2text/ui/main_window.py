"""Main window UI for Video2Text application."""
import os
import tempfile
import traceback
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar,
    QFileDialog, QMessageBox, QGroupBox, QRadioButton, QComboBox,
    QCheckBox, QApplication,
)
from PyQt6.QtCore import Qt, QThread, QEvent, pyqtSignal

from video2text.core.file_handler import validate_file, extract_audio, is_audio_file, get_duration
from video2text.core.downloader import download_video
from video2text.core.transcriber import transcribe, transcribe_with_progress, format_transcript
from video2text.core.summarizer import create_provider
from video2text.core.output_formatter import format_markdown, format_json
from video2text.utils.config import (
    get_ollama_base_url, get_ollama_model, get_openai_api_key, get_gemini_api_key, get_whisper_model,
)

ASYNC_RESULT_TYPE = QEvent.Type(QEvent.registerEventType())


class _AsyncResultEvent(QEvent):
    def __init__(self, async_result, callback):
        super().__init__(ASYNC_RESULT_TYPE)
        self.async_result = async_result
        self.callback = callback


class Worker(QThread):
    progress = pyqtSignal(str)      # status text
    progress_pct = pyqtSignal(int)  # percentage 0-100
    progress_mode = pyqtSignal(str) # "indeterminate" | "percentage"
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, source_type, source_path, generate_summary, llm_provider,
                 whisper_model, summary_model, parent=None):
        super().__init__(parent)
        self.source_type = source_type
        self.source_path = source_path
        self.generate_summary = generate_summary
        self.llm_provider = llm_provider
        self.whisper_model = whisper_model
        self.summary_model = summary_model

    def run(self):
        import logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        logger = logging.getLogger(__name__)

        try:
            result = {"transcript": [], "summary": None, "duration": "00:00:00",
                      "source": self.source_path, "error": None}
            audio_path = None

            self.progress_mode.emit("indeterminate")
            self.progress.emit("正在准备文件...")
            logger.info("开始处理文件...")

            if self.source_type == "file":
                valid, err = validate_file(self.source_path)
                if not valid:
                    raise ValueError(err)
                logger.info(f"文件验证通过: {self.source_path}")

                if is_audio_file(self.source_path):
                    audio_path = self.source_path
                    result["duration"] = get_duration(audio_path)
                    logger.info(f"音频文件，直接使用，时长: {result['duration']}")
                else:
                    self.progress.emit("正在提取音频...")
                    logger.info("正在使用 FFmpeg 提取音频...")
                    audio_path = extract_audio(self.source_path)
                    result["duration"] = get_duration(audio_path)
                    logger.info(f"音频提取完成，时长: {result['duration']}")
            else:
                self.progress.emit("正在下载视频...")
                logger.info(f"正在下载视频: {self.source_path}")
                video_path = download_video(self.source_path, tempfile.gettempdir())
                logger.info(f"视频下载完成: {video_path}")
                self.progress.emit("正在提取音频...")
                logger.info("正在使用 FFmpeg 提取音频...")
                audio_path = extract_audio(video_path)
                result["duration"] = get_duration(audio_path)
                logger.info(f"音频提取完成，时长: {result['duration']}")

            # Step: Transcribe with real percentage progress
            self.progress_mode.emit("percentage")
            self.progress_pct.emit(0)
            self.progress.emit("正在转录音频... 0%")
            logger.info(f"正在使用 Whisper ({self.whisper_model}) 转录音频...")

            def on_progress(current, total):
                pct = int(current / total * 100) if total > 0 else 0
                self.progress_pct.emit(pct)
                self.progress.emit(f"正在转录音频... {pct}%")

            segments = transcribe_with_progress(
                audio_path, model=self.whisper_model,
                progress_callback=on_progress
            )
            result["transcript"] = segments
            logger.info(f"转录完成，共 {len(segments)} 个片段")

            self.progress_mode.emit("indeterminate")

            if self.generate_summary and self.llm_provider:
                self.progress.emit("正在生成摘要...")
                logger.info(f"正在使用 {self.llm_provider.name()} 生成摘要...")
                full_text = " ".join(seg["text"] for seg in segments)
                summary_text = self.llm_provider.generate_summary(full_text)
                result["summary"] = self._parse_summary(summary_text)
                logger.info("摘要生成完成")

            logger.info("处理完成！")
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"处理失败: {e}")
            traceback.print_exc()
            self.error.emit(str(e))

    def _parse_summary(self, text: str) -> dict:
        """Parse LLM summary text into structured dict."""
        lines = text.strip().split("\n")
        key_points = []
        key_info = []
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue
            lower = line.lower()
            if "摘要" in lower or "总结" in lower or "要点" in lower:
                current_section = "points"
            elif "关键" in lower or "信息" in lower:
                current_section = "info"
            elif line.startswith(("1.", "2.", "3.", "4.", "5.")):
                if current_section == "points":
                    key_points.append(line.split(".", 1)[1].strip())
            elif line.startswith("-") or line.startswith("*"):
                content = line.lstrip("-*").strip()
                if current_section == "points":
                    key_points.append(content)
                elif current_section == "info":
                    key_info.append(content)
            else:
                if line and len(line) > 10 and current_section == "points":
                    key_points.append(line)

        if not key_points:
            key_points = [text[:200] + "..." if len(text) > 200 else text]

        return {"key_points": key_points, "key_information": key_info}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video2Text - 视频内容提取工具")
        self.setMinimumSize(900, 700)
        self.current_result = None
        self.selected_file = None
        self._ollama_status = None

        self._setup_ui()
        self._load_config()

    def _run_async(self, work_fn, result_fn):
        """Run work function in background thread and deliver result via callback on main thread."""
        def thread_target():
            work_result = work_fn()
            QApplication.instance().postEvent(
                self,
                _AsyncResultEvent(work_result, result_fn)
            )
        import threading
        t = threading.Thread(target=thread_target, daemon=True)
        t.start()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Title
        title = QLabel("<h1>Video2Text - 视频/音频内容提取</h1>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Input tabs (File / URL)
        self.tab_widget = QTabWidget()
        self.file_tab = QWidget()
        self.url_tab = QWidget()
        self.tab_widget.addTab(self.file_tab, "本地文件")
        self.tab_widget.addTab(self.url_tab, "URL 链接")
        layout.addWidget(self.tab_widget)

        self._setup_file_tab()
        self._setup_url_tab()

        # Options
        options_group = QGroupBox("选项")
        options_layout = QHBoxLayout()

        self.transcribe_only_cb = QCheckBox("仅转录（不生成摘要）")
        self.transcribe_only_cb.toggled.connect(self._on_transcribe_mode_changed)
        options_layout.addWidget(self.transcribe_only_cb)

        options_layout.addWidget(QLabel("Whisper 模型:"))
        self.whisper_model_combo = QComboBox()
        self.whisper_model_combo.addItems(["tiny", "base", "small", "medium", "large"])
        self.whisper_model_combo.setCurrentText("base")
        options_layout.addWidget(self.whisper_model_combo)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # LLM Settings
        llm_group = QGroupBox("LLM 设置")
        llm_layout = QVBoxLayout()

        llm_type_layout = QHBoxLayout()
        llm_type_layout.addWidget(QLabel("Provider:"))
        self.ollama_rb = QRadioButton("Ollama (本地免费)")
        self.ollama_rb.setChecked(True)
        self.openai_rb = QRadioButton("OpenAI")
        self.gemini_rb = QRadioButton("Gemini")
        llm_type_layout.addWidget(self.ollama_rb)
        llm_type_layout.addWidget(self.openai_rb)
        llm_type_layout.addWidget(self.gemini_rb)
        llm_type_layout.addStretch()
        llm_layout.addLayout(llm_type_layout)

        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("模型:"))
        self.model_combo = QComboBox()
        self.ollama_rb.toggled.connect(lambda checked: checked and self._update_model_list("ollama"))
        self.openai_rb.toggled.connect(lambda checked: checked and self._update_model_list("openai"))
        self.gemini_rb.toggled.connect(lambda checked: checked and self._update_model_list("gemini"))
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        llm_layout.addLayout(model_layout)

        llm_group.setLayout(llm_layout)
        layout.addWidget(llm_group)

        # Process button
        self.process_btn = QPushButton("开始处理")
        self.process_btn.clicked.connect(self._on_process)
        layout.addWidget(self.process_btn)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # Result preview
        result_group = QGroupBox("结果预览")
        result_layout = QVBoxLayout()
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(250)
        result_layout.addWidget(self.result_text)
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)

        # Export buttons
        export_layout = QHBoxLayout()
        self.export_md_btn = QPushButton("导出 .md")
        self.export_md_btn.clicked.connect(lambda: self._export("md"))
        self.export_json_btn = QPushButton("导出 .json")
        self.export_json_btn.clicked.connect(lambda: self._export("json"))
        self.export_md_btn.setEnabled(False)
        self.export_json_btn.setEnabled(False)
        export_layout.addWidget(self.export_md_btn)
        export_layout.addWidget(self.export_json_btn)
        export_layout.addStretch()
        layout.addLayout(export_layout)

    def _setup_file_tab(self):
        layout = QVBoxLayout(self.file_tab)
        layout.addWidget(QLabel("选择视频或音频文件"))
        btn_layout = QHBoxLayout()
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self._browse_file)
        btn_layout.addWidget(self.browse_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        self.file_label = QLabel("未选择文件")
        layout.addWidget(self.file_label)

    def _setup_url_tab(self):
        layout = QVBoxLayout(self.url_tab)
        layout.addWidget(QLabel("输入视频 URL (YouTube / Bilibili 等)"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://youtube.com/watch?v=...")
        layout.addWidget(self.url_input)

    def _load_config(self):
        self.whisper_model_combo.setCurrentText(get_whisper_model())
        api_key = get_openai_api_key()
        if api_key:
            self.openai_rb.setEnabled(True)
        api_key = get_gemini_api_key()
        if api_key:
            self.gemini_rb.setEnabled(True)
        self._update_model_list("ollama")
        # Check Whisper models on startup
        self._check_whisper_models()

    def _get_ollama_status(self):
        from video2text.core.ollama_client import is_ollama_installed, is_ollama_running, list_models

        if not is_ollama_installed():
            return {
                "installed": False,
                "running": False,
                "models": [],
                "message": "未检测到 Ollama。请先安装 Ollama 后再使用本地模型。",
            }

        base_url = get_ollama_base_url()
        if not is_ollama_running(base_url):
            return {
                "installed": True,
                "running": False,
                "models": [],
                "message": "已检测到 Ollama，但服务未启动。请先启动 Ollama。",
            }

        models = list_models(base_url)
        if not models:
            return {
                "installed": True,
                "running": True,
                "models": [],
                "message": "Ollama 已启动，但未找到任何已安装模型。\n请先执行例如：ollama pull llama3.2",
            }

        return {
            "installed": True,
            "running": True,
            "models": models,
            "message": "",
        }

    def _apply_ollama_status(self, status: dict, show_dialog: bool = True):
        self._ollama_status = status
        self.model_combo.clear()

        if status["models"]:
            self.model_combo.setEnabled(True)
            self.model_combo.addItems(status["models"])
            saved = get_ollama_model()
            idx = self.model_combo.findText(saved)
            self.model_combo.setCurrentIndex(idx if idx >= 0 else 0)
            return

        self.model_combo.setEnabled(False)
        if not status["installed"]:
            self.model_combo.addItem("未安装 Ollama")
        elif not status["running"]:
            self.model_combo.addItem("Ollama 未启动")
        else:
            self.model_combo.addItem("未安装本地模型")

        if show_dialog:
            QMessageBox.warning(self, "Ollama 状态", status["message"])

    def _check_whisper_models(self):
        """Check if Whisper models are available, prompt download if not."""
        from faster_whisper import WhisperModel
        def check():
            try:
                # Try loading the smallest model to check connectivity
                model = WhisperModel("tiny", device="cpu", compute_type="int8")
                return True, None
            except Exception as e:
                return False, str(e)

        def on_result(async_result):
            success, err = async_result
            if not success:
                QMessageBox.warning(
                    self, "Whisper 模型未找到",
                    f"Whisper 模型首次使用需要下载。\n"
                    f"错误: {err}\n\n"
                    f"请确保网络连接，首次运行时会自动下载模型。\n"
                    f"或手动下载: huggingface.co/Systran/faster-whisper-{get_whisper_model()}"
                )

        self._run_async(check, on_result)

    def _load_ollama_models_async(self, show_dialog: bool = True):
        """Load Ollama models asynchronously when Ollama tab is selected."""
        self.model_combo.clear()
        self.model_combo.addItem("加载中...")
        self.model_combo.setEnabled(False)

        def fetch():
            return self._get_ollama_status()

        def on_result(async_result):
            self._apply_ollama_status(async_result, show_dialog=show_dialog)

        self._run_async(fetch, on_result)

    def _load_openai_models_async(self):
        """Load OpenAI models asynchronously."""
        self.model_combo.clear()
        self.model_combo.addItem("加载中...")
        self.model_combo.setEnabled(False)

        def fetch():
            from video2text.utils.config import get_openai_api_key
            api_key = get_openai_api_key()
            if not api_key:
                return None, "请先在 .env 中配置 OPENAI_API_KEY"
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                models = client.models.list()
                model_list = [m.id for m in models.data if "gpt" in m.id.lower()]
                return model_list, None
            except Exception as e:
                return None, f"获取 OpenAI 模型失败: {e}"

        def on_result(async_result):
            models, err = async_result
            self.model_combo.setEnabled(True)
            if err:
                QMessageBox.warning(self, "OpenAI 模型获取失败", err)
                self.model_combo.clear()
                self.model_combo.addItems(["gpt-4o", "gpt-4o-mini", "o3", "o3-mini"])
                return
            if not models:
                self.model_combo.clear()
                self.model_combo.addItems(["gpt-4o", "gpt-4o-mini", "o3", "o3-mini"])
                return
            self.model_combo.clear()
            self.model_combo.addItems(models)

        self._run_async(fetch, on_result)

    def _load_gemini_models_async(self):
        """Load Gemini models asynchronously."""
        self.model_combo.clear()
        self.model_combo.addItem("加载中...")
        self.model_combo.setEnabled(False)

        def fetch():
            from video2text.utils.config import get_gemini_api_key
            api_key = get_gemini_api_key()
            if not api_key:
                return None, "请先在 .env 中配置 GEMINI_API_KEY"
            try:
                import google.genai as genai
                client = genai.Client(api_key=api_key)
                models = client.models.list()
                model_list = [m.name.replace("models/", "") for m in models.models]
                return model_list, None
            except Exception as e:
                return None, f"获取 Gemini 模型失败: {e}"

        def on_result(async_result):
            models, err = async_result
            self.model_combo.setEnabled(True)
            if err:
                QMessageBox.warning(self, "Gemini 模型获取失败", err)
                self.model_combo.clear()
                self.model_combo.addItems(["gemini-2.0-flash", "gemini-1.5-pro", "gemini-2.5-pro"])
                return
            if not models:
                self.model_combo.clear()
                self.model_combo.addItems(["gemini-2.0-flash", "gemini-1.5-pro", "gemini-2.5-pro"])
                return
            self.model_combo.clear()
            self.model_combo.addItems(models)

        self._run_async(fetch, on_result)

    def event(self, e):
        """Handle async result events delivered from background threads."""
        if isinstance(e, _AsyncResultEvent):
            e.callback(e.async_result)
            return True
        return super().event(e)

    def _update_model_list(self, provider: str):
        self.model_combo.clear()
        if provider == "ollama":
            self._load_ollama_models_async(show_dialog=True)
        elif provider == "openai":
            self._load_openai_models_async()
        elif provider == "gemini":
            self._load_gemini_models_async()

    def _on_transcribe_mode_changed(self, checked):
        """Disable LLM settings when in transcribe-only mode."""
        self.ollama_rb.setEnabled(not checked)
        self.openai_rb.setEnabled(not checked)
        self.gemini_rb.setEnabled(not checked)
        self.model_combo.setEnabled(not checked)

    def _browse_file(self):
        filters = "视频文件 (*.mp4 *.mkv *.avi *.mov *.webm);;音频文件 (*.mp3 *.wav *.m4a *.flac);;所有文件 (*.*)"
        path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", filters)
        if path:
            self.selected_file = path
            self.file_label.setText(os.path.basename(path))

    def _get_source(self):
        if self.tab_widget.currentWidget() == self.file_tab:
            return "file", self.selected_file
        else:
            return "url", self.url_input.text().strip()

    def _on_process(self):
        source_type, source_path = self._get_source()

        if not source_path:
            QMessageBox.warning(self, "提示", "请选择文件或输入 URL")
            return

        generate_summary = not self.transcribe_only_cb.isChecked()

        llm_provider = None
        if generate_summary:
            provider_type = "ollama" if self.ollama_rb.isChecked() else ("openai" if self.openai_rb.isChecked() else "gemini")
            model = self.model_combo.currentText()
            if provider_type == "ollama":
                status = self._get_ollama_status()
                self._apply_ollama_status(status, show_dialog=not status["models"])
                if not status["models"]:
                    return
                model = self.model_combo.currentText()
            try:
                llm_provider = create_provider(provider_type, model=model)
            except Exception as e:
                QMessageBox.warning(self, "LLM 错误", f"无法创建 LLM Provider: {e}\n请确保 Ollama 已启动，或配置了 API Key。")
                return

        self.process_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("处理中...")
        self.result_text.clear()

        self.worker = Worker(
            source_type, source_path, generate_summary,
            llm_provider,
            self.whisper_model_combo.currentText(),
            self.model_combo.currentText() if generate_summary else "",
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_pct.connect(self._on_progress_pct)
        self.worker.progress_mode.connect(self._on_progress_mode)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, msg: str):
        self.status_label.setText(msg)
        self.progress_bar.repaint()

    def _on_progress_pct(self, pct: int):
        self.progress_bar.setValue(pct)

    def _on_progress_mode(self, mode: str):
        if mode == "indeterminate":
            self.progress_bar.setMaximum(0)
            self.progress_bar.setValue(0)
        else:
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(0)

    def _on_finished(self, result: dict):
        self.current_result = result
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)

        summary_model = self.model_combo.currentText() if result["summary"] else ""
        md = format_markdown(
            source=result["source"],
            segments=result["transcript"],
            summary=result["summary"],
            duration=result["duration"],
            transcription_model=self.whisper_model_combo.currentText(),
            summary_model=summary_model,
        )
        self.result_text.setPlainText(md)
        self.status_label.setText("处理完成！")
        self.export_md_btn.setEnabled(True)
        self.export_json_btn.setEnabled(True)

    def _on_error(self, err: str):
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        self.status_label.setText("错误")
        QMessageBox.critical(self, "处理错误", err)

    def _export(self, fmt: str):
        if not self.current_result:
            return
        ext = f".{fmt}"
        filters = f"{fmt.upper()} 文件 (*{ext})"
        path, _ = QFileDialog.getSaveFileName(self, "保存文件", f"result{ext}", filters)
        if not path:
            return

        if fmt == "md":
            content = self.result_text.toPlainText()
        else:
            content = format_json(
                source=self.current_result["source"],
                segments=self.current_result["transcript"],
                summary=self.current_result["summary"],
                duration=self.current_result["duration"],
                transcription_model=self.whisper_model_combo.currentText(),
                summary_model=self.model_combo.currentText(),
            )

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        QMessageBox.information(self, "导出成功", f"已保存到: {path}")
