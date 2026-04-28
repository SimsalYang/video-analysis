"""Ollama API client for model discovery."""
import shutil
from typing import List
import requests


def is_ollama_installed() -> bool:
    """Check whether the Ollama CLI is available on PATH."""
    return shutil.which("ollama") is not None


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
