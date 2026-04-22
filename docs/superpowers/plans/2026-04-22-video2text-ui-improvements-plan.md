# Video2Text UI 改进实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现三大改进：Ollama 模型动态加载、任务进度显示、NSIS 安装包打包

**Architecture:**
1. Ollama 懒加载：`ollama_client.py` 提供 API 调用，Worker 线程异步加载模型到下拉框
2. 进度显示：`transcriber.py` 新增 progress callback，`Worker` 信号驱动进度条在 indeterminate/percentage 模式间切换
3. 打包：PyInstaller 单目录模式 + bundled FFmpeg + NSIS 安装向导

**Tech Stack:** PyInstaller, NSIS, requests (新增), faster-whisper

---

## File Impact Map

| 文件 | 操作 | 职责 |
|------|------|------|
| `src/video2text/core/ollama_client.py` | 新增 | Ollama API 调用（list_models, is_ollama_running） |
| `src/video2text/core/transcriber.py` | 修改 | 新增 `transcribe_with_progress()` 支持进度回调 |
| `src/video2text/core/file_handler.py` | 修改 | FFmpeg 路径解析支持 bundled 模式 |
| `src/video2text/ui/main_window.py` | 修改 | Ollama 懒加载 + progress/pct/mode 三信号 + 进度条模式切换 |
| `src/video2text/utils/config.py` | 修改 | 新增 `get_ffmpeg_path()` 返回 bundled FFmpeg 路径 |
| `requirements.txt` | 修改 | 新增 `requests` |
| `video2text.spec` | 新增 | PyInstaller 打包配置 |
| `installer.nsi` | 新增 | NSIS 安装脚本 |
| `scripts/prepare-ffmpeg.ps1` | 新增 | 下载 bundled FFmpeg |
| `CLAUDE.md` | 修改 | 更新打包命令 |

---

## Task 1: Ollama 模型动态加载

**Files:**
- Create: `src/video2text/core/ollama_client.py`
- Modify: `src/video2text/ui/main_window.py:282-289`（`_update_model_list`）
- Modify: `src/video2text/ui/main_window.py`（新增 `_load_ollama_models_async`）
- Modify: `requirements.txt`（新增 `requests`）
- Test: `tests/test_ollama_client.py`

- [ ] **Step 1: 添加 requests 依赖**

Modify `requirements.txt`:
```
requests>=2.31.0
```

- [ ] **Step 2: 写测试**

Create `tests/test_ollama_client.py`:
```python
"""Tests for Ollama client."""
import pytest
from unittest.mock import patch, MagicMock
from video2text.core.ollama_client import list_models, is_ollama_running


def test_list_models_returns_model_names():
    with patch("video2text.core.ollama_client.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "models": [
                {"name": "llama3.2"},
                {"name": "deepseek-r1:7b"},
            ]
        }
        mock_get.return_value = mock_resp

        result = list_models("http://localhost:11434")

        assert result == ["llama3.2", "deepseek-r1:7b"]
        mock_get.assert_called_once_with(
            "http://localhost:11434/api/tags", timeout=5
        )


def test_list_models_returns_empty_on_error():
    with patch("video2text.core.ollama_client.requests.get") as mock_get:
        mock_get.side_effect = Exception("Connection refused")

        result = list_models()

        assert result == []


def test_is_ollama_running_returns_true_when_reachable():
    with patch("video2text.core.ollama_client.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        assert is_ollama_running() is True


def test_is_ollama_running_returns_false_when_unreachable():
    with patch("video2text.core.ollama_client.requests.get") as mock_get:
        mock_get.side_effect = Exception("Connection refused")

        assert is_ollama_running() is False
```

Run: `pytest tests/test_ollama_client.py -v`
Expected: FAIL (ollama_client doesn't exist yet)

- [ ] **Step 3: 实现 ollama_client.py**

Create `src/video2text/core/ollama_client.py`:
```python
"""Ollama API client for model discovery."""
from typing import List
import requests


def list_models(base_url: str = "http://localhost:11434") -> List[str]:
    """Fetch available models from local Ollama instance.
    Returns list of model names. Empty list on error.
    """
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=5)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        return [m["name"] for m in models]
    except Exception:
        return []


def is_ollama_running(base_url: str = "http://localhost:11434") -> bool:
    """Check if Ollama service is reachable."""
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ollama_client.py -v`
Expected: PASS

- [ ] **Step 5: 修改 _update_model_list() 懒加载 Ollama**

当前 `main_window.py` 的 `_update_model_list` 直接 addItems。改为：当 provider == "ollama" 时，启动异步加载。

在 MainWindow 的 `_setup_ui` 末尾（或者在 `_update_model_list` 调用前），确保 ollama_rb 的 toggle 信号连接正确。

Locate the current `_update_model_list` method at line 282-289 and replace it:

```python
def _update_model_list(self, provider: str):
    self.model_combo.clear()
    if provider == "ollama":
        self._load_ollama_models_async()
    elif provider == "openai":
        self.model_combo.addItems(["gpt-4o", "gpt-4o-mini", "o3", "o3-mini"])
    elif provider == "gemini":
        self.model_combo.addItems(["gemini-2.0-flash", "gemini-1.5-pro", "gemini-2.5-pro"])
```

- [ ] **Step 6: 实现 _load_ollama_models_async()**

在 MainWindow 类中新增方法，放在 `_load_config` 后面：

```python
def _load_ollama_models_async(self):
    """Load Ollama models asynchronously when Ollama tab is selected."""
    self.model_combo.clear()
    self.model_combo.addItem("加载中...")
    self.model_combo.setEnabled(False)

    # Run in background thread
    def fetch():
        from video2text.core.ollama_client import list_models, is_ollama_running
        from video2text.utils.config import get_ollama_base_url

        running = is_ollama_running(get_ollama_base_url())
        if not running:
            return None, "Ollama 服务未运行，已使用默认列表"

        models = list_models(get_ollama_base_url())
        return models, None

    def on_result(async_result):
        models, err = async_result
        self.model_combo.setEnabled(True)
        if err:
            QMessageBox.warning(self, "Ollama 连接失败", err)
            self.model_combo.clear()
            self.model_combo.addItems(["llama3.2", "deepseek-r1:7b"])
        elif not models:
            self.model_combo.clear()
            self.model_combo.addItems(["llama3.2", "deepseek-r1:7b"])
        else:
            self.model_combo.clear()
            self.model_combo.addItems(models)
            # Restore previously selected model
            saved = get_ollama_model()
            idx = self.model_combo.findText(saved)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)

    self._run_async(fetch, on_result)
```

- [ ] **Step 7: 实现通用异步工具 _run_async**

在 MainWindow 类中（`__init__` 之后）新增：

```python
from PyQt6.QtCore import QEvent

# Module-level custom event type for async results
ASYNC_RESULT_TYPE = QEvent.Type(QEvent.registerEventType())

class _AsyncResultEvent(QEvent):
    """Custom event carrying an async result to be processed in the main thread."""
    def __init__(self, async_result, callback):
        super().__init__(ASYNC_RESULT_TYPE)
        self.async_result = async_result
        self.callback = callback


def _run_async(self, work_fn, result_fn):
    """Run work_fn in background thread, call result_fn in main thread."""
    def thread_target():
        work_result = work_fn()
        QApplication.instance().postEvent(
            self,
            _AsyncResultEvent(work_result, result_fn)
        )
    import threading
    t = threading.Thread(target=thread_target, daemon=True)
    t.start()
```

Add `from PyQt6.QtCore import QEvent` to the imports at the top of main_window.py.

- [ ] **Step 8: 处理 MainWindow 的 event() 接收异步结果**

In MainWindow class, add override:

```python
def event(self, e):
    """Handle async result events delivered from background threads."""
    if isinstance(e, _AsyncResultEvent):
        e.callback(e.async_result)
        return True
    return super().event(e)
```

- [ ] **Step 9: 验证 import**

Run: `python -c "from video2text.core.ollama_client import list_models, is_ollama_running; print('OK')"`
Expected: OK

- [ ] **Step 10: Commit**

```bash
git add src/video2text/core/ollama_client.py tests/test_ollama_client.py src/video2text/ui/main_window.py requirements.txt
git commit -m "feat: add Ollama dynamic model loading on tab switch"
```

---

## Task 2: 任务进度显示

**Files:**
- Modify: `src/video2text/core/transcriber.py`
- Modify: `src/video2text/ui/main_window.py`（Worker class）
- Test: `tests/test_transcriber.py`

- [ ] **Step 1: 写测试**

Update `tests/test_transcriber.py` — append these test functions:

```python
def test_transcribe_with_progress_callback():
    """Test transcribe_with_progress calls callback with segment index."""
    mock_segments = [
        MagicMock(start=0.0, text="Hello world"),
        MagicMock(start=5.0, text="This is a test"),
    ]

    progress_calls = []

    def progress_cb(current, total):
        progress_calls.append((current, total))

    with patch("video2text.core.transcriber.WhisperModel") as mock_model_class:
        mock_model = MagicMock()
        mock_model.transcribe.return_value = (mock_segments, MagicMock())
        mock_model_class.return_value = mock_model

        result = transcribe_with_progress("/fake/audio.mp3", model="base",
                                          progress_callback=progress_cb)

        assert len(result) == 2
        # Callback should have been called at least once
        assert len(progress_calls) >= 1
```

Run: `pytest tests/test_transcriber.py::test_transcribe_with_progress_callback -v`
Expected: FAIL (transcribe_with_progress doesn't exist yet)

- [ ] **Step 2: 实现 transcribe_with_progress()**

In `src/video2text/core/transcriber.py`, add after the existing `transcribe()` function:

```python
def transcribe_with_progress(audio_path: str, model: str = "base",
                             progress_callback=None) -> List[dict]:
    """Transcribe audio file with progress callback.

    Args:
        audio_path: Path to audio file.
        model: Whisper model size.
        progress_callback: Callable(current: int, total: int) called per segment.
                          current is 0-indexed segment index, total is total segments.

    Returns:
        List of {'timestamp': 'HH:MM:SS', 'text': '...'}
    """
    if model not in WHISPER_MODELS:
        raise ValueError(f"Invalid model: {model}. Available: {WHISPER_MODELS}")

    from faster_whisper import WhisperModel

    model_instance = WhisperModel(model, device="cpu", compute_type="int8")
    segments, info = model_instance.transcribe(
        audio_path, beam_size=5, word_timestamps=True
    )

    # Convert generator to list so we know total count
    segments_list = list(segments)
    total = len(segments_list)

    result = []
    for i, seg in enumerate(segments_list):
        if progress_callback:
            progress_callback(i, total)

        hours = int(seg.start // 3600)
        minutes = int((seg.start % 3600) // 60)
        seconds = int(seg.start % 60)
        timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        result.append({"timestamp": timestamp, "text": seg.text.strip()})

    if progress_callback:
        progress_callback(total, total)

    return result
```

- [ ] **Step 3: Run test to verify it passes**

Run: `pytest tests/test_transcriber.py::test_transcribe_with_progress_callback -v`
Expected: PASS

- [ ] **Step 4: 修改 Worker 类 — 添加 progress_mode/pct 信号**

Locate the `Worker` class at line 24 in `main_window.py`. Replace the signal declarations and `__init__`:

```python
class Worker(QThread):
    progress = pyqtSignal(str)      # status text
    progress_pct = pyqtSignal(int)  # percentage 0-100
    progress_mode = pyqtSignal(str) # "indeterminate" | "percentage"

    def __init__(self, source_type, source_path, generate_summary, llm_provider,
                 whisper_model, summary_model, parent=None):
        super().__init__(parent)
        self.source_type = source_type
        self.source_path = source_path
        self.generate_summary = generate_summary
        self.llm_provider = llm_provider
        self.whisper_model = whisper_model
        self.summary_model = summary_model
```

- [ ] **Step 5: 重写 Worker.run() 实现步骤化进度**

Replace the entire `run()` method body (lines 39-97) with step-based progress:

```python
def run(self):
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    logger = logging.getLogger(__name__)

    try:
        result = {
            "transcript": [], "summary": None, "duration": "00:00:00",
            "source": self.source_path, "error": None
        }
        audio_path = None

        # Step 0: Prepare
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

        from video2text.core.transcriber import transcribe_with_progress
        segments = transcribe_with_progress(
            audio_path, model=self.whisper_model,
            progress_callback=on_progress
        )
        result["transcript"] = segments
        logger.info(f"转录完成，共 {len(segments)} 个片段")

        # Summary step
        if self.generate_summary and self.llm_provider:
            self.progress_mode.emit("indeterminate")
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
```

- [ ] **Step 6: 修改 MainWindow — 进度条槽连接**

Find where `self.worker.progress.connect(self._on_progress)` is connected (around line 341-344). Add the new signal connections:

```python
self.worker.progress.connect(self._on_progress)
self.worker.progress_pct.connect(self._on_progress_pct)
self.worker.progress_mode.connect(self._on_progress_mode)
self.worker.finished.connect(self._on_finished)
self.worker.error.connect(self._on_error)
```

Add the new slot methods in MainWindow class (after `_on_progress`):

```python
def _on_progress_pct(self, pct: int):
    self.progress_bar.setValue(pct)

def _on_progress_mode(self, mode: str):
    if mode == "indeterminate":
        self.progress_bar.setMaximum(0)
        self.progress_bar.setValue(0)
    else:
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
```

- [ ] **Step 7: Run tests**

Run: `pytest tests/test_transcriber.py -v`
Expected: PASS (all tests including new one)

- [ ] **Step 8: 验证 import**

Run: `python -c "from video2text.core.transcriber import transcribe_with_progress; print('OK')"`
Expected: OK

- [ ] **Step 9: Commit**

```bash
git add src/video2text/core/transcriber.py src/video2text/ui/main_window.py tests/test_transcriber.py
git commit -m "feat: add step-based progress display with Whisper percentage"
```

---

## Task 3: Bundled FFmpeg 和路径解析

**Files:**
- Create: `scripts/prepare-ffmpeg.ps1`
- Create: `vendor/ffmpeg/` (directory with ffmpeg.exe + ffprobe.exe)
- Modify: `src/video2text/core/file_handler.py`
- Modify: `src/video2text/utils/config.py`

- [ ] **Step 1: 创建 prepare-ffmpeg.ps1 脚本**

Create `scripts/prepare-ffmpeg.ps1`:

```powershell
# Download and extract minimal FFmpeg binaries for bundling
$url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
$dest = "vendor/ffmpeg.zip"

if (!(Test-Path "vendor")) { New-Item -ItemType Directory -Path "vendor" | Out-Null }

Write-Host "Downloading FFmpeg..."
Invoke-WebRequest -Uri $url -OutFile $dest

Write-Host "Extracting..."
Expand-Archive -Path $dest -DestinationPath "vendor/ffmpeg-tmp" -Force

# Find the extracted directory (ffmpeg-master-latest-win64-gpl)
$extractedDir = Get-ChildItem "vendor/ffmpeg-tmp" | Where-Object { $_.PSIsContainer } | Select-Object -First 1
$binDir = Join-Path $extractedDir.FullName "bin"

if (!(Test-Path "vendor/ffmpeg")) { New-Item -ItemType Directory -Path "vendor/ffmpeg" | Out-Null }

Copy-Item (Join-Path $binDir "ffmpeg.exe") "vendor/ffmpeg/ffmpeg.exe"
Copy-Item (Join-Path $binDir "ffprobe.exe") "vendor/ffmpeg/ffprobe.exe"

Remove-Item $dest -Force -EA SilentlyContinue
Remove-Item "vendor/ffmpeg-tmp" -Recurse -Force -EA SilentlyContinue

Write-Host "Done. FFmpeg binaries in vendor/ffmpeg/"
```

- [ ] **Step 2: 写测试**

Create `tests/test_file_handler.py` additional tests:

```python
def test_get_duration_returns_timestamp():
    import subprocess
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "123.456\n"
        mock_run.return_value.returncode = 0
        from video2text.core.file_handler import get_duration
        result = get_duration("/fake/file.mp4")
        assert result == "00:02:03"
```

Add to existing `test_file_handler.py` and run.

- [ ] **Step 3: 实现 get_ffmpeg_path()**

Add to `src/video2text/utils/config.py`:

```python
def get_ffmpeg_path() -> str:
    """Get the path to bundled FFmpeg directory.
    When running as PyInstaller bundle, returns the _MEIPASS directory.
    Otherwise returns 'vendor/ffmpeg' relative to project root.
    """
    import sys
    import os

    # PyInstaller frozen: files extracted to sys._MEIPASS
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
        ffmpeg_dir = os.path.join(base, "ffmpeg")
    else:
        # Development mode: vendor/ffmpeg next to project root
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        ffmpeg_dir = os.path.join(base, "vendor", "ffmpeg")

    return ffmpeg_dir


def get_ffmpeg_bin(name: str) -> str:
    """Get full path to a bundled FFmpeg binary."""
    return os.path.join(get_ffmpeg_path(), name)
```

- [ ] **Step 4: 修改 file_handler.py 使用 bundled FFmpeg**

Replace the `subprocess.run` calls in `file_handler.py` to use bundled FFmpeg binaries.

First, add import after existing imports:

```python
from video2text.utils.config import get_ffmpeg_bin
```

Then replace ffprobe call (line 26-30):

```python
    result = subprocess.run(
        [
            get_ffmpeg_bin("ffprobe"), "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ],
        capture_output=True, text=True, check=True
    )
```

Replace ffmpeg call (line 44-52):

```python
    result = subprocess.run(
        [
            get_ffmpeg_bin("ffmpeg"), "-y", "-i", video_path,
            "-vn", "-acodec", "libmp3lame", "-q:a", "2",
            output_path
        ],
        capture_output=True,
        text=True,
    )
```

- [ ] **Step 5: 验证 config 和 file_handler import**

Run: `python -c "from video2text.utils.config import get_ffmpeg_path, get_ffmpeg_bin; print(get_ffmpeg_bin('ffmpeg'))"`
Expected: prints path to vendor/ffmpeg/ffmpeg.exe (may not exist yet, that's ok for now)

- [ ] **Step 6: Commit**

```bash
git add scripts/prepare-ffmpeg.ps1 src/video2text/utils/config.py src/video2text/core/file_handler.py
git commit -m "feat: support bundled FFmpeg with PyInstaller path resolution"
```

---

## Task 4: PyInstaller 打包配置

**Files:**
- Create: `video2text.spec`
- Create: `assets/icon.ico` (placeholder — note in spec)
- Modify: `src/video2text/__main__.py`（确认入口正确）

- [ ] **Step 1: 确认 __main__.py 入口**

Read `src/video2text/__main__.py` — it should just call `main()`. Verify it doesn't need changes.

Current content:
```python
"""Entry point for running: python -m video2text"""
from video2text.main import main

if __name__ == "__main__":
    main()
```
This is correct for PyInstaller.

- [ ] **Step 2: 写 video2text.spec**

Create `video2text.spec` in project root:

```spec
# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

a = Analysis(
    ['src/video2text/__main__.py'],
    pathex=[],
    binaries=[
        # Bundled FFmpeg — binaries extracted to dist/video2text/ffmpeg/
        ('vendor/ffmpeg', 'ffmpeg',),
    ],
    datas=[
        # .env file for defaults (contains no secrets by design)
        ('.env', '.',),
    ],
    hiddenimports=[
        # PyQt6
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'PyQt6',
        # Core dependencies
        'faster_whisper',
        'yt_dlp',
        'ollama',
        'openai',
        'google.genai',
        'dotenv',
        'requests',
        # Internal
        'video2text',
        'video2text.core',
        'video2text.ui',
        'video2text.utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'test', 'pytest', 'distutils', 'venv',
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
    [],
    exclude_binaries=True,
    name='Video2Text',
    debug=False,
    bootloader_ignore_signals=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',  # uncomment when icon exists
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='video2text',
)
```

- [ ] **Step 3: 验证 spec 语法**

Run: `python -c "import ast; ast.parse(open('video2text.spec').read())" ; echo "spec syntax OK"`
This parses the spec as Python AST to catch syntax errors.

- [ ] **Step 4: Commit**

```bash
git add video2text.spec
git commit -m "feat: add PyInstaller spec for single-directory bundle"
```

---

## Task 5: NSIS 安装脚本

**Files:**
- Create: `installer.nsi`

- [ ] **Step 1: 写 installer.nsi**

Create `installer.nsi` in project root:

```nsis
; Video2Text NSIS Installer Script
; Requires NSIS 3.x

!include "MUI2.nsh"
!include "FileFunc.nsh"

; ----- General -----
Name "Video2Text"
OutFile "dist\Video2Text-Setup.exe"
InstallDir "$PROGRAMFILES64\Video2Text"
InstallDirRegKey HKLM "Software\Video2Text" "InstallDir"
RequestExecutionLevel admin

; ----- Interface Settings -----
!define MUI_ABORTWARNING
!define MUI_ICON "assets\icon.ico"
!define MUI_UNICON "assets\icon.ico"

; ----- Pages -----
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; ----- Languages -----
!insertmacro MUI_LANGUAGE "SimpChinese"

; ----- Installer Sections -----
Section "Install"
    SetOutPath "$INSTDIR"

    ; Copy all files from PyInstaller output
    File /r "dist\video2text\*.*"

    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\Video2Text"
    CreateShortcut "$SMPROGRAMS\Video2Text\Video2Text.lnk" "$INSTDIR\Video2Text.exe"
    CreateShortcut "$SMPROGRAMS\Video2Text\卸载 Video2Text.lnk" "$INSTDIR\Uninstall.exe"

    ; Create Desktop shortcut
    CreateShortcut "$DESKTOP\Video2Text.lnk" "$INSTDIR\Video2Text.exe"

    ; Write uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Registry keys for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Video2Text" "DisplayName" "Video2Text"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Video2Text" "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Video2Text" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Video2Text" "Publisher" "Video2Text"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Video2Text" "DisplayVersion" "0.1.0"

    ; Estimate installed size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Video2Text" "EstimatedSize" "$0"
SectionEnd

; ----- Uninstaller Section -----
Section "Uninstall"
    ; Remove files and directory
    RMDir /r "$INSTDIR"

    ; Remove shortcuts
    Delete "$DESKTOP\Video2Text.lnk"
    RMDir /r "$SMPROGRAMS\Video2Text"

    ; Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Video2Text"
SectionEnd
```

- [ ] **Step 2: 创建 LICENSE.txt**

Create `LICENSE.txt` in project root (required by NSIS MUI_LICENSE page):

```
Video2Text
Copyright (c) 2026
```

- [ ] **Step 3: Commit**

```bash
git add installer.nsi LICENSE.txt
git commit -m "feat: add NSIS installer script"
```

---

## Task 6: 更新 CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

Add to the "Common Commands" section:

```bash
# Build bundled FFmpeg (Windows PowerShell)
.\scripts\prepare-ffmpeg.ps1

# Package with PyInstaller
pip install pyinstaller
pyinstaller video2text.spec --clean

# Build NSIS installer
makensis installer.nsi
```

Add a "Bundled Dependencies" note:

```
## Bundled Dependencies

FFmpeg binaries (ffmpeg.exe, ffprobe.exe) are bundled in `vendor/ffmpeg/`.
At runtime, config.py resolves the correct path:
- PyInstaller bundle: sys._MEIPASS/ffmpeg/
- Development: project_root/vendor/ffmpeg/
```

---

## Task 7: 端到端验证

- [ ] **Step 1: 运行所有测试**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 2: 验证 PyInstaller spec 可以解析**

Run: `python -c "import PyInstaller; print('OK')"`
Then review spec manually for correctness.

- [ ] **Step 3: 最终 commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with build commands"
```

---

## Spec Coverage Check

| Spec Requirement | Task |
|------|------|
| Ollama tab switch → async load models | Task 1 |
| Fallback list on Ollama error | Task 1 |
| Worker progress/pct/mode signals | Task 2 |
| indeterminate → percentage mode switch | Task 2 |
| Whisper percentage progress | Task 2 |
| Bundled FFmpeg path resolution | Task 3 |
| PyInstaller spec | Task 4 |
| NSIS installer | Task 5 |
| CLAUDE.md update | Task 6 |
