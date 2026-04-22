# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Video2Text is a PyQt6 desktop application that extracts audio from video files or online URLs, transcribes it to text using Whisper, and generates summaries using LLM providers (Ollama, OpenAI, or Google Gemini).

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python -m video2text

# Run tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_transcriber.py -v
```

## Architecture

**Processing Pipeline:**
```
Local File/URL → FFmpeg (audio extraction) → faster-whisper (transcription) → LLM (summary) → Markdown/JSON output
```

**Key Components:**
- `src/video2text/core/file_handler.py` — File validation and FFmpeg audio extraction. Audio files go directly to transcription; video files have audio extracted first.
- `src/video2text/core/downloader.py` — Video downloading via yt-dlp for URL sources.
- `src/video2text/core/transcriber.py` — Whisper-based transcription using faster-whisper with int8 CPU quantization. Models: tiny, base, small, medium, large.
- `src/video2text/core/summarizer.py` — LLM provider abstraction with three implementations: OllamaProvider (local, free), OpenAIProvider, GeminiProvider. All use a `create_provider()` factory.
- `src/video2text/core/output_formatter.py` — Exports results as Markdown or JSON.
- `src/video2text/ui/main_window.py` — PyQt6 main window. The `Worker` QThread handles the pipeline asynchronously. The `_parse_summary()` method parses unstructured LLM output into structured key_points/key_information.
- `src/video2text/utils/config.py` — Reads from `.env` file. Defaults: Ollama at `localhost:11434`, Whisper model `base`.

**Entry Points:**
- `python -m video2text` — uses `src/video2text/__main__.py` → `main.py`
- `src/video2text/main.py` — creates QApplication and shows MainWindow

**External Dependencies:**
- FFmpeg and ffprobe must be installed and in PATH (used by file_handler for audio extraction and duration)
- Ollama must be running for local LLM summarization (optional; cloud APIs work without it)

**Configuration (.env):**
```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
WHISPER_MODEL=base
```

## UI Language

The application UI is in Chinese. Whisper model sizes are "tiny", "base", "small", "medium", "large".
