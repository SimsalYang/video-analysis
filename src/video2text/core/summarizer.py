from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def summarize(self, text: str) -> str:
        """Generate a summary of the given text."""
        pass


class OllamaProvider(LLMProvider):
    """Ollama LLM provider."""

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model

    def summarize(self, text: str) -> str:
        # TODO: implement
        return ""


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model

    def summarize(self, text: str) -> str:
        # TODO: implement
        return ""


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""

    def __init__(self, api_key: str, model: str = "gemini-pro"):
        self.api_key = api_key
        self.model = model

    def summarize(self, text: str) -> str:
        # TODO: implement
        return ""


def create_provider(provider_type: str, **kwargs) -> LLMProvider:
    """Factory function to create LLM provider instances."""
    providers = {
        "ollama": OllamaProvider,
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
    }
    provider_class = providers.get(provider_type.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider type: {provider_type}")
    return provider_class(**kwargs)
