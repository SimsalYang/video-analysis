"""Tests for Ollama client."""
import pytest
from unittest.mock import patch, MagicMock
from video2text.core.ollama_client import list_models, is_ollama_running


def test_list_models_returns_model_names():
    with patch("video2text.core.ollama_client.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "models": [
                {"name": "llama3.2"},
                {"name": "deepseek-r1:7b"},
            ]
        }
        mock_get.return_value = mock_resp

        result = list_models("http://localhost:11434")

        assert result == ["llama3.2", "deepseek-r1:7b"]
        mock_get.assert_called_once_with(
            "http://localhost:11434/api/tags", timeout=5
        )


def test_list_models_returns_empty_on_error():
    with patch("video2text.core.ollama_client.requests.get") as mock_get:
        mock_get.side_effect = Exception("Connection refused")

        result = list_models()

        assert result == []


def test_is_ollama_running_returns_true_when_reachable():
    with patch("video2text.core.ollama_client.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        assert is_ollama_running() is True


def test_is_ollama_running_returns_false_when_unreachable():
    with patch("video2text.core.ollama_client.requests.get") as mock_get:
        mock_get.side_effect = Exception("Connection refused")

        assert is_ollama_running() is False