"""LLM-based summarization with multiple provider support."""
from abc import ABC, abstractmethod
from typing import Literal

from video2text.utils.config import get_ollama_base_url


class LLMProvider(ABC):
    @abstractmethod
    def generate_summary(self, text: str) -> str:
        pass

    @abstractmethod
    def name(self) -> str:
        pass


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = None, model: str = "llama3"):
        self.base_url = base_url or get_ollama_base_url()
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
                    "content": "你是一个有用的助手，负责总结文本。提供简洁的摘要和关键要点。",
                },
                {"role": "user", "content": f"请总结以下内容:\n\n{text}"},
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
                    "content": "你是一个有用的助手，负责总结文本。提供简洁的摘要和关键要点。",
                },
                {"role": "user", "content": f"请总结以下内容:\n\n{text}"},
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
            contents=f"请总结以下内容:\n\n{text}",
            config={
                "system_instruction": "你是一个有用的助手，负责总结文本。提供简洁的摘要和关键要点。"
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
        return OllamaProvider(model=model or "llama3.2")
    elif provider_type == "openai":
        return OpenAIProvider(api_key=api_key, model=model or "gpt-4o")
    elif provider_type == "gemini":
        return GeminiProvider(api_key=api_key, model=model or "gemini-2.0-flash")
    else:
        raise ValueError(f"Unknown provider: {provider_type}")
