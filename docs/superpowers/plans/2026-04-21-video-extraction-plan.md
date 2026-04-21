# Video2Text Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a PyQt desktop app that extracts audio from video files/URLs, transcribes with Whisper, and generates summaries with Ollama/OpenAI/Gemini LLM.

**Architecture:** PyQt6 UI layer → Business logic layer (FileHandler, VideoDownloader, TranscriptionEngine, SummaryEngine) → Tool layer (FFmpeg, yt-dlp, Whisper). Clean separation of concerns with each module independently testable.

**Tech Stack:** PyQt6, faster-whisper, yt-dlp, openai, google-genai, python-dotenv, FFmpeg

---

## File Structure

```
src/video2text/
├── __init__.py
├── main.py                    # PyQt app entry point
├── ui/
│   ├── __init__.py
│   └── main_window.py        # Main window UI (all panels in one file for PyQt simplicity)
├── core/
│   ├── __init__.py
│   ├── file_handler.py        # Local file validation + FFmpeg audio extraction
│   ├── downloader.py          # yt-dlp video download
│   ├── transcriber.py         # Whisper transcription
│   └── summarizer.py          # LLM providers (Ollama, OpenAI, Gemini)
└── utils/
    ├── __init__.py
    └── config.py              # .env config management
tests/
├── __init__.py
├── test_file_handler.py
├── test_downloader.py
├── test_transcriber.py
└── test_summarizer.py
.env.example
requirements.txt
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `src/video2text/__init__.py`
- Create: `src/video2text/main.py`
- Create: `src/video2text/ui/__init__.py`
- Create: `src/video2text/ui/main_window.py`
- Create: `src/video2text/core/__init__.py`
- Create: `src/video2text/core/file_handler.py`
- Create: `src/video2text/core/downloader.py`
- Create: `src/video2text/core/transcriber.py`
- Create: `src/video2text/core/summarizer.py`
- Create: `src/video2text/utils/__init__.py`
- Create: `src/video2text/utils/config.py`
- Create: `tests/__init__.py`
- Create: `tests/test_file_handler.py`
- Create: `tests/test_downloader.py`
- Create: `tests/test_transcriber.py`
- Create: `tests/test_summarizer.py`

- [ ] **Step 1: Create requirements.txt**

```txt
PyQt6>=6.6.0
faster-whisper>=1.0.0
yt-dlp>=2024.0.0
openai>=1.0.0
google-genai>=0.8.0
python-dotenv>=1.0.0
```

- [ ] **Step 2: Create .env.example**

```env
# Ollama (local, free)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# OpenAI (cloud, paid)
OPENAI_API_KEY=sk-...

# Google Gemini (cloud, paid)
GEMINI_API_KEY=...

# Whisper model (tiny, base, small, medium, large)
WHISPER_MODEL=base
```

- [ ] **Step 3: Create src/video2text/__init__.py**

```python
"""Video2Text - Video/Audio content extraction and summarization tool."""
__version__ = "0.1.0"
```

- [ ] **Step 4: Create src/video2text/main.py (minimal stub)**

```python
"""PyQt6 application entry point."""
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from video2text.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Video2Text")

    try:
        window = MainWindow()
        window.show()
    except Exception as e:
        QMessageBox.critical(None, "Startup Error", str(e))
        sys.exit(1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Create src/video2text/ui/__init__.py**

```python
"""UI package."""
```

- [ ] **Step 6: Create src/video2text/ui/main_window.py (minimal stub with import check)**

```python
"""Main window UI - minimal stub to verify PyQt6 import."""
from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video2Text")
        self.setMinimumSize(900, 700)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel("Video2Text - Loading..."))
        self.setCentralWidget(central)
```

- [ ] **Step 7: Create src/video2text/core/__init__.py**

```python
"""Core business logic package."""
```

- [ ] **Step 8: Create src/video2text/core/file_handler.py (stub)**

```python
"""File handling and audio extraction."""
SUPPORTED_FORMATS = {".mp4", ".mkv", ".avi", ".mov", ".mp3", ".wav", ".m4a"}


def validate_file(path: str) -> bool:
    """Check if file exists and has supported extension."""
    import os
    ext = os.path.splitext(path)[1].lower()
    return os.path.isfile(path) and ext in SUPPORTED_FORMATS


def extract_audio(video_path: str, output_path: str) -> str:
    """Extract audio from video file using FFmpeg. Returns output audio path."""
    import subprocess
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "libmp3lame", "-q:a", "2",
        output_path
    ], check=True, capture_output=True)
    return output_path
```

- [ ] **Step 9: Create src/video2text/core/downloader.py (stub)**

```python
"""Video downloading with yt-dlp."""
from typing import Optional


def download_video(url: str, output_dir: str, cookies: Optional[str] = None) -> str:
    """Download video from URL. Returns path to downloaded video file."""
    import yt_dlp

    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
        "quiet": False,
    }
    if cookies:
        ydl_opts["cookies"] = cookies

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)
```

- [ ] **Step 10: Create src/video2text/core/transcriber.py (stub)**

```python
"""Whisper-based transcription."""
from typing import List


def transcribe(audio_path: str, model: str = "base") -> List[dict]:
    """Transcribe audio file. Returns list of {'timestamp': 'HH:MM:SS', 'text': '...'}.
    Uses faster-whisper for speed.
    """
    from faster_whisper import WhisperModel

    model_instance = WhisperModel(model, device="cpu", compute_type="int8")
    segments, _ = model_instance.transcribe(audio_path, beam_size=5)

    result = []
    for seg in segments:
        hours = int(seg.start // 3600)
        minutes = int((seg.start % 3600) // 60)
        seconds = int(seg.start % 60)
        timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        result.append({"timestamp": timestamp, "text": seg.text.strip()})

    return result
```

- [ ] **Step 11: Create src/video2text/core/summarizer.py (stub)**

```python
"""LLM-based summarization with multiple provider support."""
from abc import ABC, abstractmethod
from typing import Literal


class LLMProvider(ABC):
    @abstractmethod
    def generate_summary(self, text: str) -> str:
        pass

    @abstractmethod
    def name(self) -> str:
        pass


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model

    def name(self) -> str:
        return f"Ollama ({self.model})"

    def generate_summary(self, text: str) -> str:
        import ollama

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes text. Provide a concise summary with key points.",
                },
                {"role": "user", "content": f"Summarize this:\n\n{text}"},
            ],
        )
        return response["message"]["content"]


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model

    def name(self) -> str:
        return f"OpenAI ({self.model})"

    def generate_summary(self, text: str) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes text. Provide a concise summary with key points.",
                },
                {"role": "user", "content": f"Summarize this:\n\n{text}"},
            ],
        )
        return response.choices[0].message.content


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model

    def name(self) -> str:
        return f"Gemini ({self.model})"

    def generate_summary(self, text: str) -> str:
        import google.genai as genai

        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=self.model,
            contents=f"Summarize this:\n\n{text}",
            config={
                "system_instruction": "You are a helpful assistant that summarizes text. Provide a concise summary with key points."
            },
        )
        return response.text


def create_provider(
    provider_type: Literal["ollama", "openai", "gemini"],
    api_key: str = "",
    model: str = "",
) -> LLMProvider:
    """Factory function to create LLM provider."""
    if provider_type == "ollama":
        return OllamaProvider(model=model or "llama3")
    elif provider_type == "openai":
        return OpenAIProvider(api_key=api_key, model=model or "gpt-4o")
    elif provider_type == "gemini":
        return GeminiProvider(api_key=api_key, model=model or "gemini-2.0-flash")
    else:
        raise ValueError(f"Unknown provider: {provider_type}")
```

- [ ] **Step 12: Create src/video2text/utils/__init__.py**

```python
"""Utilities package."""
```

- [ ] **Step 13: Create src/video2text/utils/config.py**

```python
"""Configuration management via .env file."""
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_env_path)


def get_ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def get_ollama_model() -> str:
    return os.getenv("OLLAMA_MODEL", "llama3")


def get_openai_api_key() -> Optional[str]:
    return os.getenv("OPENAI_API_KEY") or None


def get_gemini_api_key() -> Optional[str]:
    return os.getenv("GEMINI_API_KEY") or None


def get_whisper_model() -> str:
    return os.getenv("WHISPER_MODEL", "base")
```

- [ ] **Step 14: Create test files (empty)**

```python
# tests/__init__.py
```

```python
# tests/test_file_handler.py
# (filled in Task 2)
```

```python
# tests/test_downloader.py
# (filled in Task 3)
```

```python
# tests/test_transcriber.py
# (filled in Task 4)
```

```python
# tests/test_summarizer.py
# (filled in Task 5)
```

- [ ] **Step 15: Run scaffold verification**

```bash
cd H:/WORKSPACE/Projects/video-analysis
pip install -e . 2>&1 | tail -5
python -c "from video2text.ui.main_window import MainWindow; print('Import OK')"
```

Expected: "Import OK"

- [ ] **Step 16: Commit**

```bash
git add -A
git commit -m "feat: project scaffold - initial structure and stubs"
```

---

## Task 2: FileHandler Implementation

**Files:**
- Modify: `src/video2text/core/file_handler.py`
- Test: `tests/test_file_handler.py`

- [ ] **Step 1: Write test**

```python
"""tests/test_file_handler.py"""
import os
import tempfile
import pytest
from video2text.core.file_handler import validate_file, extract_audio, get_duration, SUPPORTED_FORMATS


def test_validate_file_accepts_supported_formats():
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(b"fake video content")
        path = f.name
    try:
        assert validate_file(path) is True
    finally:
        os.unlink(path)


def test_validate_file_rejects_unsupported_format():
    with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
        f.write(b"data")
        path = f.name
    try:
        assert validate_file(path) is False
    finally:
        os.unlink(path)


def test_validate_file_rejects_nonexistent():
    assert validate_file("/nonexistent/path/video.mp4") is False


def test_supported_formats_includes_common_formats():
    expected = {".mp4", ".mkv", ".avi", ".mov", ".mp3", ".wav", ".m4a"}
    assert expected.issubset(SUPPORTED_FORMATS)


def test_extract_audio_raises_on_invalid_input():
    with pytest.raises(Exception):
        extract_audio("/nonexistent/video.mp4", "/tmp/output.mp3")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd H:/WORKSPACE/Projects/video-analysis
pytest tests/test_file_handler.py -v
```

Expected: FAIL (file doesn't exist, etc.)

- [ ] **Step 3: Write full file_handler.py implementation**

```python
"""File handling and audio extraction using FFmpeg."""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

SUPPORTED_VIDEO_FORMATS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}
SUPPORTED_AUDIO_FORMATS = {".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg"}
SUPPORTED_FORMATS = SUPPORTED_VIDEO_FORMATS | SUPPORTED_AUDIO_FORMATS


def validate_file(path: str) -> Tuple[bool, Optional[str]]:
    """Check if file exists and has supported extension. Returns (valid, error_message)."""
    if not os.path.isfile(path):
        return False, f"文件不存在: {path}"
    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        return False, f"不支持的格式: {ext}。支持的格式: {', '.join(SUPPORTED_FORMATS)}"
    return True, None


def get_duration(file_path: str) -> str:
    """Get duration of video/audio file using ffprobe. Returns HH:MM:SS string."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ],
        capture_output=True, text=True, check=True
    )
    seconds = float(result.stdout.strip())
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def extract_audio(video_path: str, output_path: Optional[str] = None) -> str:
    """Extract audio from video file using FFmpeg. Returns output audio path."""
    if output_path is None:
        output_path = tempfile.mktemp(suffix=".mp3")

    result = subprocess.run(
        [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "libmp3lame", "-q:a", "2",
            output_path
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")
    return output_path


def is_audio_file(path: str) -> bool:
    """Check if file is an audio file (not video)."""
    ext = os.path.splitext(path)[1].lower()
    return ext in SUPPORTED_AUDIO_FORMATS
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd H:/WORKSPACE/Projects/video-analysis
pytest tests/test_file_handler.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/video2text/core/file_handler.py tests/test_file_handler.py
git commit -m "feat: implement FileHandler with FFmpeg audio extraction"
```

---

## Task 3: VideoDownloader Implementation

**Files:**
- Modify: `src/video2text/core/downloader.py`
- Test: `tests/test_downloader.py`

- [ ] **Step 1: Write test**

```python
"""tests/test_downloader.py"""
import tempfile
import os
import pytest
from unittest.mock import patch, MagicMock
from video2text.core.downloader import download_video, get_video_info


def test_download_video_with_mock():
    """Test download_video calls yt-dlp correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("video2text.core.downloader.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = MagicMock()
            mock_instance.extract_info.return_value = {"title": "Test Video", "ext": "mp4"}
            mock_instance.prepare_filename.return_value = os.path.join(tmpdir, "Test Video.mp4")
            mock_ydl.return_value.__enter__ = MagicMock(return_value=mock_instance)
            mock_ydl.return_value.__exit__ = MagicMock(return_value=False)

            url = "https://youtube.com/watch?v=test"
            result = download_video(url, tmpdir)

            assert "Test Video" in result
            mock_instance.extract_info.assert_called_once_with(url, download=True)


def test_download_video_uses_cookies():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("video2text.core.downloader.yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = MagicMock()
            mock_instance.extract_info.return_value = {"title": "Test", "ext": "mp4"}
            mock_instance.prepare_filename.return_value = os.path.join(tmpdir, "Test.mp4")
            mock_ydl.return_value.__enter__ = MagicMock(return_value=mock_instance)
            mock_ydl.return_value.__exit__ = MagicMock(return_value=False)

            download_video("https://youtube.com/watch?v=test", tmpdir, cookies="/path/to/cookies.txt")

            call_kwargs = mock_ydl.call_args[1]["ydl_opts"]
            assert call_kwargs.get("cookies") == "/path/to/cookies.txt"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd H:/WORKSPACE/Projects/video-analysis
pytest tests/test_downloader.py -v
```

Expected: FAIL

- [ ] **Step 3: Write full downloader.py implementation**

```python
"""Video downloading with yt-dlp."""
import os
import tempfile
from typing import Optional


def get_video_info(url: str, cookies: Optional[str] = None) -> dict:
    """Get video info without downloading. Returns dict with title, duration, etc."""
    import yt_dlp

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }
    if cookies:
        ydl_opts["cookies"] = cookies

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info


def download_video(
    url: str,
    output_dir: Optional[str] = None,
    cookies: Optional[str] = None,
) -> str:
    """Download video from URL. Returns path to downloaded video file."""
    import yt_dlp

    if output_dir is None:
        output_dir = tempfile.gettempdir()

    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "quiet": False,
    }
    if cookies:
        ydl_opts["cookies"] = cookies

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename


def is_supported_url(url: str) -> bool:
    """Check if URL is supported by yt-dlp."""
    from yt_dlp import gen_extractor_classes
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if not parsed.netloc:
        return False

    host = parsed.netloc.lower()
    for extractor in gen_extractor_classes():
        if extractor.IE_NAME.lower() in host or any(h in host for h in extractor.IE_NAME.lower().split()):
            return True
    return False
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd H:/WORKSPACE/Projects/video-analysis
pytest tests/test_downloader.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/video2text/core/downloader.py tests/test_downloader.py
git commit -m "feat: implement VideoDownloader with yt-dlp"
```

---

## Task 4: TranscriptionEngine Implementation

**Files:**
- Modify: `src/video2text/core/transcriber.py`
- Test: `tests/test_transcriber.py`

- [ ] **Step 1: Write test**

```python
"""tests/test_transcriber.py"""
import pytest
from unittest.mock import patch, MagicMock
from video2text.core.transcriber import transcribe, format_transcript, WHISPER_MODELS


def test_whisper_models_available():
    assert "tiny" in WHISPER_MODELS
    assert "base" in WHISPER_MODELS
    assert "large" in WHISPER_MODELS


def test_format_transcript_creates_timestamped_output():
    segments = [
        {"timestamp": "00:00:00", "text": "Hello world"},
        {"timestamp": "00:00:05", "text": "This is a test"},
    ]
    result = format_transcript(segments)
    assert "[00:00:00] Hello world" in result
    assert "[00:00:05] This is a test" in result


def test_transcribe_with_mock():
    """Test transcribe function with mocked WhisperModel."""
    mock_segments = [
        MagicMock(start=0.0, text="Hello world"),
        MagicMock(start=5.0, text="This is a test"),
    ]

    with patch("video2text.core.transcriber.WhisperModel") as mock_model_class:
        mock_model = MagicMock()
        mock_model.transcribe.return_value = (mock_segments, None)
        mock_model_class.return_value = mock_model

        result = transcribe("/fake/audio.mp3", model="base")

        assert len(result) == 2
        assert result[0]["timestamp"] == "00:00:00"
        assert result[0]["text"] == "Hello world"
        mock_model_class.assert_called_once_with("base", device="cpu", compute_type="int8")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd H:/WORKSPACE/Projects/video-analysis
pytest tests/test_transcriber.py -v
```

Expected: FAIL

- [ ] **Step 3: Write full transcriber.py implementation**

```python
"""Whisper-based transcription using faster-whisper."""
from typing import List

WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]


def transcribe(audio_path: str, model: str = "base") -> List[dict]:
    """Transcribe audio file using faster-whisper. Returns list of {'timestamp': 'HH:MM:SS', 'text': '...'}.
    Uses int8 quantization for faster CPU inference.
    """
    if model not in WHISPER_MODELS:
        raise ValueError(f"Invalid model: {model}. Available: {WHISPER_MODELS}")

    from faster_whisper import WhisperModel

    model_instance = WhisperModel(model, device="cpu", compute_type="int8")
    segments, _ = model_instance.transcribe(audio_path, beam_size=5)

    result = []
    for seg in segments:
        hours = int(seg.start // 3600)
        minutes = int((seg.start % 3600) // 60)
        seconds = int(seg.start % 60)
        timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        result.append({"timestamp": timestamp, "text": seg.text.strip()})

    return result


def format_transcript(segments: List[dict], include_timestamps: bool = True) -> str:
    """Format transcript segments into a readable string."""
    if include_timestamps:
        return "\n".join(f"[{seg['timestamp']}] {seg['text']}" for seg in segments)
    return "\n".join(seg["text"] for seg in segments)


def get_transcript_text(segments: List[dict]) -> str:
    """Get plain text from transcript segments without timestamps."""
    return " ".join(seg["text"] for seg in segments)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd H:/WORKSPACE/Projects/video-analysis
pytest tests/test_transcriber.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/video2text/core/transcriber.py tests/test_transcriber.py
git commit -m "feat: implement TranscriptionEngine with faster-whisper"
```

---

## Task 5: SummaryEngine (LLM Providers) Implementation

**Files:**
- Modify: `src/video2text/core/summarizer.py`
- Test: `tests/test_summarizer.py`

- [ ] **Step 1: Write test**

```python
"""tests/test_summarizer.py"""
import pytest
from unittest.mock import patch, MagicMock
from video2text.core.summarizer import (
    OllamaProvider,
    OpenAIProvider,
    GeminiProvider,
    create_provider,
)


def test_ollama_provider_generate_summary():
    with patch("video2text.core.summarizer.ollama") as mock_ollama:
        mock_ollama.chat.return_value = {
            "message": {"content": "This is a summary."}
        }
        provider = OllamaProvider(model="llama3")
        result = provider.generate_summary("Long text to summarize")
        assert result == "This is a summary."
        mock_ollama.chat.assert_called_once()


def test_openai_provider_generate_summary():
    with patch("video2text.core.summarizer.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "GPT summary."
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        provider = OpenAIProvider(api_key="sk-test", model="gpt-4o")
        result = provider.generate_summary("Long text to summarize")
        assert result == "GPT summary."


def test_gemini_provider_generate_summary():
    with patch("video2text.core.summarizer.genai") as mock_genai:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Gemini summary."
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        provider = GeminiProvider(api_key="gemini-key", model="gemini-2.0-flash")
        result = provider.generate_summary("Long text to summarize")
        assert result == "Gemini summary."


def test_create_provider_ollama():
    provider = create_provider("ollama", model="llama3")
    assert isinstance(provider, OllamaProvider)
    assert provider.model == "llama3"


def test_create_provider_openai():
    provider = create_provider("openai", api_key="sk-test", model="gpt-4o")
    assert isinstance(provider, OpenAIProvider)


def test_create_provider_gemini():
    provider = create_provider("gemini", api_key="gemini-key", model="gemini-2.0-flash")
    assert isinstance(provider, GeminiProvider)


def test_create_provider_invalid():
    with pytest.raises(ValueError):
        create_provider("invalid_provider")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd H:/WORKSPACE/Projects/video-analysis
pytest tests/test_summarizer.py -v
```

Expected: FAIL

- [ ] **Step 3: Run test to verify it passes (stub already exists)**

```bash
cd H:/WORKSPACE/Projects/video-analysis
pytest tests/test_summarizer.py -v
```

Expected: PASS (stub implementation works with mocks)

- [ ] **Step 4: Commit**

```bash
git add src/video2text/core/summarizer.py tests/test_summarizer.py
git commit -m "feat: implement SummaryEngine with Ollama/OpenAI/Gemini providers"
```

---

## Task 6: Output Formatting

**Files:**
- Create: `src/video2text/core/output_formatter.py`
- Test: `tests/test_output_formatter.py`

- [ ] **Step 1: Write test**

```python
"""tests/test_output_formatter.py"""
import json
from datetime import datetime
from video2text.core.output_formatter import format_markdown, format_json


def test_format_markdown_with_transcript_and_summary():
    segments = [
        {"timestamp": "00:00:00", "text": "Hello world"},
        {"timestamp": "00:00:05", "text": "This is a test"},
    ]
    summary = {
        "key_points": ["Point 1", "Point 2"],
        "key_information": ["Info 1"],
    }

    md = format_markdown(
        source="/path/to/video.mp4",
        segments=segments,
        summary=summary,
        duration="00:01:00",
        transcription_model="base",
        summary_model="gpt-4o",
    )

    assert "**来源**:" in md
    assert "完整转录" in md
    assert "[00:00:00] Hello world" in md
    assert "内容摘要" in md
    assert "Point 1" in md
    assert "关键信息" in md


def test_format_json_output():
    segments = [
        {"timestamp": "00:00:00", "text": "Hello world"},
    ]
    summary = {
        "key_points": ["Point 1"],
        "key_information": ["Info 1"],
    }

    result = format_json(
        source="/path/to/video.mp4",
        segments=segments,
        summary=summary,
        duration="00:01:00",
        transcription_model="base",
        summary_model="gpt-4o",
    )

    data = json.loads(result)
    assert data["source"] == "/path/to/video.mp4"
    assert data["duration"] == "00:01:00"
    assert len(data["full_transcript"]) == 1
    assert data["summary"]["key_points"] == ["Point 1"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd H:/WORKSPACE/Projects/video-analysis
pytest tests/test_output_formatter.py -v
```

Expected: FAIL

- [ ] **Step 3: Write output_formatter.py**

```python
"""Output formatting for markdown and JSON export."""
import json
from datetime import datetime
from typing import List, Optional


def format_markdown(
    source: str,
    segments: List[dict],
    summary: Optional[dict] = None,
    duration: str = "00:00:00",
    transcription_model: str = "base",
    summary_model: str = "",
) -> str:
    """Format result as Markdown document."""
    lines = [
        "# 视频/音频内容提取结果",
        "",
        f"**来源**: {source}",
        f"**时长**: {duration}",
        f"**处理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**转录模型**: {transcription_model}",
    ]
    if summary_model:
        lines.append(f"**摘要模型**: {summary_model}")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 完整转录")
    lines.append("")
    for seg in segments:
        lines.append(f"[{seg['timestamp']}] {seg['text']}")

    if summary:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 内容摘要")
        lines.append("")
        for i, point in enumerate(summary.get("key_points", []), 1):
            lines.append(f"{i}. {point}")

        if summary.get("key_information"):
            lines.append("")
            lines.append("## 关键信息")
            lines.append("")
            for info in summary["key_information"]:
                lines.append(f"- {info}")

    return "\n".join(lines)


def format_json(
    source: str,
    segments: List[dict],
    summary: Optional[dict] = None,
    duration: str = "00:00:00",
    transcription_model: str = "base",
    summary_model: str = "",
) -> str:
    """Format result as JSON document."""
    data = {
        "source": source,
        "duration": duration,
        "processed_at": datetime.now().isoformat(),
        "transcription_model": transcription_model,
        "summary_model": summary_model,
        "full_transcript": segments,
        "summary": summary or {},
    }
    return json.dumps(data, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd H:/WORKSPACE/Projects/video-analysis
pytest tests/test_output_formatter.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/video2text/core/output_formatter.py tests/test_output_formatter.py
git commit -m "feat: add output formatting for markdown and JSON export"
```

---

## Task 7: Config Management

**Files:**
- Modify: `src/video2text/utils/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write test**

```python
"""tests/test_config.py"""
import os
import pytest
from video2text.utils.config import (
    get_ollama_base_url,
    get_ollama_model,
    get_openai_api_key,
    get_gemini_api_key,
    get_whisper_model,
)


def test_get_ollama_base_url_returns_default():
    url = get_ollama_base_url()
    assert "localhost" in url or "ollama" in url.lower()


def test_get_whisper_model_returns_valid_model():
    model = get_whisper_model()
    assert model in ["tiny", "base", "small", "medium", "large"]
```

- [ ] **Step 2: Run test**

```bash
cd H:/WORKSPACE/Projects/video-analysis
pytest tests/test_config.py -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/video2text/utils/config.py tests/test_config.py
git commit -m "feat: implement config management"
```

---

## Task 8: PyQt6 Main Window UI

**Files:**
- Modify: `src/video2text/ui/main_window.py`
- Modify: `src/video2text/main.py`

- [ ] **Step 1: Write the complete main_window.py**

```python
"""Main window UI for Video2Text application."""
import os
import tempfile
import traceback
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar,
    QFileDialog, QMessageBox, QGroupBox, QRadioButton, QComboBox,
    QCheckBox, QSpinBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from video2text.core.file_handler import validate_file, extract_audio, is_audio_file, get_duration
from video2text.core.downloader import download_video
from video2text.core.transcriber import transcribe, format_transcript
from video2text.core.summarizer import create_provider
from video2text.core.output_formatter import format_markdown, format_json
from video2text.utils.config import (
    get_ollama_model, get_openai_api_key, get_gemini_api_key, get_whisper_model,
)


class Worker(QThread):
    progress = pyqtSignal(str)
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
        try:
            result = {"transcript": [], "summary": None, "duration": "00:00:00",
                      "source": self.source_path, "error": None}
            audio_path = None

            self.progress.emit("正在准备文件...")
            if self.source_type == "file":
                valid, err = validate_file(self.source_path)
                if not valid:
                    raise ValueError(err)

                if is_audio_file(self.source_path):
                    audio_path = self.source_path
                    result["duration"] = get_duration(audio_path)
                else:
                    self.progress.emit("正在提取音频...")
                    audio_path = extract_audio(self.source_path)
                    result["duration"] = get_duration(audio_path)
            else:
                self.progress.emit("正在下载视频...")
                audio_path = download_video(self.source_path, tempfile.gettempdir())
                result["duration"] = get_duration(audio_path)

            self.progress.emit("正在转录音频...")
            segments = transcribe(audio_path, model=self.whisper_model)
            result["transcript"] = segments

            if self.generate_summary and self.llm_provider:
                self.progress.emit("正在生成摘要...")
                full_text = " ".join(seg["text"] for seg in segments)
                summary_text = self.llm_provider.generate_summary(full_text)
                result["summary"] = self._parse_summary(summary_text)

            self.finished.emit(result)
        except Exception as e:
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

        self._setup_ui()
        self._load_config()

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
        self.model_combo.addItems(["llama3", "qwen2.5", "mistral"])
        self.ollama_rb.toggled.connect(lambda: self._update_model_list("ollama"))
        self.openai_rb.toggled.connect(lambda: self._update_model_list("openai"))
        self.gemini_rb.toggled.connect(lambda: self._update_model_list("gemini"))
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
        ollama_model = get_ollama_model()
        if ollama_model:
            idx = self.model_combo.findText(ollama_model)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
        api_key = get_openai_api_key()
        if api_key:
            self.openai_rb.setEnabled(True)
        api_key = get_gemini_api_key()
        if api_key:
            self.gemini_rb.setEnabled(True)

    def _update_model_list(self, provider: str):
        self.model_combo.clear()
        if provider == "ollama":
            self.model_combo.addItems(["llama3", "qwen2.5", "mistral", "phi3"])
        elif provider == "openai":
            self.model_combo.addItems(["gpt-4o", "gpt-4o-mini", "o3", "o3-mini"])
        elif provider == "gemini":
            self.model_combo.addItems(["gemini-2.0-flash", "gemini-1.5-pro", "gemini-2.5-pro"])

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
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, msg: str):
        self.status_label.setText(msg)
        self.progress_bar.repaint()

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
```

- [ ] **Step 2: Run to verify it starts**

```bash
cd H:/WORKSPACE/Projects/video-analysis
python -c "from video2text.ui.main_window import MainWindow; print('UI import OK')"
```

Expected: UI import OK

- [ ] **Step 3: Commit**

```bash
git add src/video2text/ui/main_window.py
git commit -m "feat: implement PyQt6 main window UI"
```

---

## Task 9: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README**

```markdown
# Video2Text

视频/音频内容提取与摘要工具。从本地视频文件或在线视频 URL 中提取音频、转换为文字，并使用 LLM 生成内容摘要。

## 功能

- 支持本地视频文件 (MP4, MKV, AVI, MOV) 和音频文件 (MP3, WAV, M4A)
- 支持 YouTube、Bilibili 等在线视频 URL
- 使用 Whisper (开源版) 进行语音识别，完全免费
- 支持三种 LLM Provider:
  - Ollama (本地免费)
  - OpenAI GPT (云端付费)
  - Google Gemini (云端付费)
- 导出为 Markdown 或 JSON 格式

## 安装

### 1. 安装 FFmpeg

Windows: `winget install FFmpeg` 或从 https://ffmpeg.org 下载

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 (可选)

复制 `.env.example` 为 `.env`，填入 API 密钥：

```env
OLLAMA_MODEL=llama3
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
WHISPER_MODEL=base
```

### 4. 运行

```bash
python -m video2text.main
```

## 使用方法

1. 选择本地文件或输入 URL
2. 配置 Whisper 模型（默认 base）
3. 选择是否生成摘要
4. 选择 LLM Provider 和模型
5. 点击"开始处理"
6. 预览结果并导出
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README"
```

---

## Task 10: Verification

**Run all tests:**

```bash
cd H:/WORKSPACE/Projects/video-analysis
pytest tests/ -v
```

**Verify imports:**

```bash
python -c "
from video2text.main import main
from video2text.ui.main_window import MainWindow
from video2text.core.file_handler import validate_file, extract_audio
from video2text.core.downloader import download_video
from video2text.core.transcriber import transcribe
from video2text.core.summarizer import create_provider
from video2text.core.output_formatter import format_markdown, format_json
print('All imports OK')
"
```

---

**Plan complete.** Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
