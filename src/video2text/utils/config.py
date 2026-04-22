"""Configuration management via .env file."""
import os


def get_ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def get_ollama_model() -> str:
    return os.getenv("OLLAMA_MODEL", "llama3.2")


def get_openai_api_key():
    return os.getenv("OPENAI_API_KEY") or None


def get_gemini_api_key():
    return os.getenv("GEMINI_API_KEY") or None


def get_whisper_model() -> str:
    return os.getenv("WHISPER_MODEL", "base")


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
