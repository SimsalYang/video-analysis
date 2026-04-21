"""LLM-based summarization with multiple provider support."""
from abc import ABC, abstractmethod
from typing import Literal


class LLMProvider(ABC):
    @abstractmethod
    def generate_summary(self, text: str) -> str:
        pass


class OllamaProvider(LLMProvider):
    def name(self) -> str:
        return "Ollama"


class OpenAIProvider(LLMProvider):
    def name(self) -> str:
        return "OpenAI"


class GeminiProvider(LLMProvider):
    def name(self) -> str:
        return "Gemini"


def create_provider(provider_type: Literal["ollama", "openai", "gemini"], api_key: str = "", model: str = "") -> LLMProvider:
    if provider_type == "ollama":
        return OllamaProvider()
    elif provider_type == "openai":
        return OpenAIProvider()
    elif provider_type == "gemini":
        return GeminiProvider()
    raise ValueError(f"Unknown provider: {provider_type}")
