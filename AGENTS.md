# Repository Guidelines

## Project Structure & Module Organization
The application uses a `src` layout. Core runtime code lives in `src/video2text/`: `core/` contains the processing pipeline, `ui/` contains the PyQt6 desktop interface, and `utils/` holds configuration helpers. Tests live in `tests/` and mirror the runtime modules with files such as `test_transcriber.py` and `test_downloader.py`. Packaging assets are split across `assets/` for icons, `vendor/` for bundled FFmpeg binaries, and root-level installer files such as `video2text.spec` and `installer.nsi`. Design notes and implementation plans live under `docs/superpowers/`.

## Build, Test, and Development Commands
Install dependencies with `pip install -r requirements.txt`.
Run the desktop app with `python -m video2text`.
Run the full test suite with `pytest tests/ -v`.
Run one test file while iterating with `pytest tests/test_transcriber.py -v`.
Prepare bundled FFmpeg on Windows with `.\scripts\prepare-ffmpeg.ps1`.
Build the packaged app with `pyinstaller video2text.spec --clean`.
Create the Windows installer with `makensis installer.nsi`.

## Coding Style & Naming Conventions
Target Python 3.10+ and follow the existing code style: 4-space indentation, module docstrings where helpful, `snake_case` for functions and variables, `PascalCase` for Qt widgets such as `MainWindow`, and small focused modules under `core/` and `ui/`. Keep imports explicit and grouped cleanly. No formatter or linter is configured in the repository today, so match surrounding code and keep changes narrow.

## Testing Guidelines
Use `pytest` for unit coverage. Name tests `test_<behavior>` and keep files in `tests/` named after the module under test. Prefer mocks for external systems such as Whisper, Ollama, network downloads, and FFmpeg so tests stay deterministic and local. Add or update tests whenever changing pipeline behavior, provider selection, export formatting, or file handling.

## Commit & Pull Request Guidelines
Current history uses short conventional prefixes: `feat:`, `fix:`, `docs:`, and `chore:`. Keep commits focused and written in the imperative, for example `fix: handle missing ffprobe path`. Pull requests should summarize the user-visible change, note any packaging or dependency impact, link related issues, and include screenshots when UI text, layout, or workflow changes.

## Configuration & Packaging Notes
Use `.env.example` as the template for local `.env` values. Do not commit API keys or generated build output from `build/` and `dist/`. When changing FFmpeg resolution or packaging behavior, verify both local runs and the PyInstaller bundle path handling in `src/video2text/utils/config.py`.
