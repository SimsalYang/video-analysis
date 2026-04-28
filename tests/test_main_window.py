"""GUI behavior tests for the main window."""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QMessageBox  # noqa: E402

import video2text.ui.main_window as main_window_module  # noqa: E402
from video2text.ui.main_window import MainWindow  # noqa: E402


class DummySignal:
    def __init__(self):
        self._callbacks = []

    def connect(self, fn):
        self._callbacks.append(fn)

    def emit(self, *args, **kwargs):
        for callback in list(self._callbacks):
            callback(*args, **kwargs)


class SuccessWorker:
    def __init__(self, source_type, source_path, generate_summary, llm_provider,
                 whisper_model, summary_model, parent=None):
        self.source_path = source_path
        self.generate_summary = generate_summary
        self.progress = DummySignal()
        self.progress_pct = DummySignal()
        self.progress_mode = DummySignal()
        self.finished = DummySignal()
        self.error = DummySignal()

    def start(self):
        self.finished.emit({
            "transcript": [{"timestamp": "00:00:00", "text": "ok"}],
            "summary": {"key_points": ["summary"], "key_information": []} if self.generate_summary else None,
            "duration": "00:00:01",
            "source": self.source_path,
            "error": None,
        })


class PendingWorker:
    def __init__(self, *args, **kwargs):
        self.progress = DummySignal()
        self.progress_pct = DummySignal()
        self.progress_mode = DummySignal()
        self.finished = DummySignal()
        self.error = DummySignal()

    def start(self):
        self.progress.emit("处理中...")


class ErrorWorker:
    def __init__(self, *args, **kwargs):
        self.progress = DummySignal()
        self.progress_pct = DummySignal()
        self.progress_mode = DummySignal()
        self.finished = DummySignal()
        self.error = DummySignal()

    def start(self):
        self.error.emit("boom")


def sync_run_async(self, work_fn, result_fn):
    result_fn(work_fn())


def create_window(ollama_status=None, openai_key=None, gemini_key=None):
    app = QApplication.instance() or QApplication([])
    patches = [
        patch.object(MainWindow, "_run_async", sync_run_async),
        patch.object(MainWindow, "_check_whisper_models", lambda self: None),
        patch.object(MainWindow, "_get_ollama_status", lambda self: ollama_status or {
            "installed": True,
            "running": True,
            "models": ["llama3.2"],
            "message": "",
        }),
        patch.object(QMessageBox, "warning", return_value=QMessageBox.StandardButton.Ok),
        patch.object(QMessageBox, "critical", return_value=QMessageBox.StandardButton.Ok),
        patch.object(main_window_module, "get_openai_api_key", return_value=openai_key),
        patch.object(main_window_module, "get_gemini_api_key", return_value=gemini_key),
    ]
    for item in patches:
        item.start()

    window = MainWindow()
    window.show()
    app.processEvents()
    return app, window, patches


def destroy_window(app, window, patches):
    window.close()
    app.processEvents()
    for item in reversed(patches):
        item.stop()


def test_transcribe_toggle_preserves_disabled_model_combo_without_ollama():
    app, window, patches = create_window(ollama_status={
        "installed": False,
        "running": False,
        "models": [],
        "message": "missing",
    })
    try:
        assert window.model_combo.isEnabled() is False
        window.transcribe_only_cb.setChecked(True)
        app.processEvents()
        window.transcribe_only_cb.setChecked(False)
        app.processEvents()
        assert window.model_combo.isEnabled() is False
    finally:
        destroy_window(app, window, patches)


def test_openai_requires_api_key_before_processing():
    app, window, patches = create_window(openai_key=None)
    try:
        window.openai_rb.setChecked(True)
        app.processEvents()
        window.selected_file = str(Path(tempfile.gettempdir()) / "sample.mp3")

        with patch.object(main_window_module, "Worker", SuccessWorker), \
             patch.object(main_window_module, "create_provider") as create_provider:
            window._on_process()
            app.processEvents()

        create_provider.assert_not_called()
        assert window.current_result is None
        assert window.process_btn.isEnabled() is True
    finally:
        destroy_window(app, window, patches)


def test_processing_locks_inputs_until_worker_finishes():
    app, window, patches = create_window()
    try:
        window.selected_file = str(Path(tempfile.gettempdir()) / "sample.mp3")
        with patch.object(main_window_module, "Worker", PendingWorker):
            window._on_process()
            app.processEvents()

        assert window.process_btn.isEnabled() is False
        assert window.tab_widget.isEnabled() is False
        assert window.browse_btn.isEnabled() is False
        assert window.ollama_rb.isEnabled() is False
        assert window.model_combo.isEnabled() is False
    finally:
        destroy_window(app, window, patches)


def test_error_clears_stale_result_and_disables_export():
    app, window, patches = create_window()
    try:
        window.selected_file = str(Path(tempfile.gettempdir()) / "sample.mp3")
        with patch.object(main_window_module, "Worker", SuccessWorker):
            window.transcribe_only_cb.setChecked(True)
            app.processEvents()
            window._on_process()
            app.processEvents()

        assert window.current_result is not None
        assert window.export_md_btn.isEnabled() is True

        with patch.object(main_window_module, "Worker", ErrorWorker):
            window._on_process()
            app.processEvents()

        assert window.current_result is None
        assert window.export_md_btn.isEnabled() is False
        assert window.export_json_btn.isEnabled() is False
    finally:
        destroy_window(app, window, patches)


def test_finished_result_uses_models_from_process_start():
    app, window, patches = create_window()
    try:
        window.selected_file = str(Path(tempfile.gettempdir()) / "sample.mp3")
        window.model_combo.setCurrentText("llama3.2")
        with patch.object(main_window_module, "Worker", SuccessWorker):
            window._on_process()
            app.processEvents()

        window.model_combo.clear()
        window.model_combo.addItems(["deepseek-r1:7b"])
        window.model_combo.setCurrentText("deepseek-r1:7b")

        assert window.current_result["summary_model"] == "llama3.2"
        assert "llama3.2" in window.result_text.toPlainText()
    finally:
        destroy_window(app, window, patches)
