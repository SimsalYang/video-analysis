def get_ollama_base_url() -> str:
    """Get Ollama base URL from config."""
    return "http://localhost:11434"


def get_ollama_model() -> str:
    """Get Ollama model name from config."""
    return "llama3"


def get_whisper_model() -> str:
    """Get Whisper model name from config."""
    return "base"
