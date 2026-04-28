# Repository Guidelines

## Project Structure & Module Organization
This project uses a `src` layout. Application code lives in `src/video2text/`: `core/` contains the extraction, transcription, summarization, and export pipeline; `ui/` contains the PyQt6 window and worker orchestration; `utils/` contains configuration and runtime path helpers. Tests live in `tests/`, with module-aligned files such as `test_ollama_client.py` and `test_main_window.py`. Packaging files stay at the repo root (`video2text.spec`, `installer.nsi`), while icons live in `assets/` and bundled runtime binaries live in `vendor/ffmpeg/`.

## Build, Test, and Development Commands
Install dependencies with `pip install -r requirements.txt`.
Run the app from the repo with `$env:PYTHONPATH='src'; python -m video2text`.
Run all tests with `$env:PYTHONPATH='src'; pytest tests/ -v`.
Run a focused GUI regression pass with `$env:PYTHONPATH='src'; pytest tests/test_main_window.py -v`.
Prepare bundled FFmpeg on Windows with `.\scripts\prepare-ffmpeg.ps1`.
Build the portable app with `pyinstaller video2text.spec --clean -y`.
Build the installer with `makensis installer.nsi`.

## Coding Style & Naming Conventions
Target Python 3.10+ and keep to the existing style: 4-space indentation, explicit imports, `snake_case` for functions and variables, and `PascalCase` for Qt classes such as `MainWindow` and `Worker`. Keep UI state logic in `ui/`, processing logic in `core/`, and avoid mixing packaging concerns into runtime modules. No formatter or linter is checked in, so match surrounding code closely.

## Testing Guidelines
Use `pytest` and prefer deterministic tests with mocks for Ollama, OpenAI, Gemini, Whisper, FFmpeg, and file dialogs. Name tests `test_<behavior>` and keep them near the module boundary they validate. Any change to provider selection, GUI state transitions, export behavior, or packaging-sensitive runtime paths should include or update tests.

## Commit & Pull Request Guidelines
Follow the existing conventional prefixes: `feat:`, `fix:`, `docs:`, and `chore:`. Keep commits small and imperative, for example `fix: harden gui processing state`. Pull requests should summarize user-visible behavior, mention packaging impact when relevant, and include screenshots for UI changes.

## Configuration & Packaging Notes
Use `.env.example` as the template for local secrets and model defaults. Do not commit `.env`, `.claude/settings.local.json`, `build/`, `dist/`, `__pycache__/`, or large vendored archives under `scripts/vendor/`. When changing packaging, verify both the PyInstaller bundle and the NSIS installer output.
