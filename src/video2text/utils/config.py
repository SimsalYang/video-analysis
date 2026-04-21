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
