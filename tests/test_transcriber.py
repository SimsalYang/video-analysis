"""Tests for transcription module."""
import pytest
from unittest.mock import patch, MagicMock
from video2text.core.transcriber import transcribe, format_transcript, get_transcript_text, WHISPER_MODELS


def test_whisper_models_available():
    assert "tiny" in WHISPER_MODELS
    assert "base" in WHISPER_MODELS
    assert "large" in WHISPER_MODELS


def test_format_transcript_creates_timestamped_output():
    segments = [
        {"timestamp": "00:00:00", "text": "Hello world"},
        {"timestamp": "00:00:05", "text": "This is a test"},
    ]
    result = format_transcript(segments)
    assert "[00:00:00] Hello world" in result
    assert "[00:00:05] This is a test" in result


def test_format_transcript_without_timestamps():
    segments = [
        {"timestamp": "00:00:00", "text": "Hello world"},
        {"timestamp": "00:00:05", "text": "This is a test"},
    ]
    result = format_transcript(segments, include_timestamps=False)
    assert "Hello world" in result
    assert "This is a test" in result
    assert "[00:00:00]" not in result


def test_get_transcript_text():
    segments = [
        {"timestamp": "00:00:00", "text": "Hello"},
        {"timestamp": "00:00:05", "text": "World"},
    ]
    result = get_transcript_text(segments)
    assert result == "Hello World"


def test_transcribe_with_mock():
    """Test transcribe function with mocked WhisperModel."""
    mock_segments = [
        MagicMock(start=0.0, text="Hello world"),
        MagicMock(start=5.0, text="This is a test"),
    ]

    with patch("faster_whisper.WhisperModel") as mock_model_class:
        mock_model = MagicMock()
        mock_model.transcribe.return_value = (mock_segments, None)
        mock_model_class.return_value = mock_model

        result = transcribe("/fake/audio.mp3", model="base")

        assert len(result) == 2
        assert result[0]["timestamp"] == "00:00:00"
        assert result[0]["text"] == "Hello world"
        mock_model_class.assert_called_once_with("base", device="cpu", compute_type="int8")


def test_transcribe_invalid_model():
    with pytest.raises(ValueError):
        transcribe("/fake/audio.mp3", model="invalid_model")


def test_transcribe_with_progress_callback():
    """Test transcribe_with_progress calls callback with segment index."""
    from video2text.core.transcriber import transcribe_with_progress
    mock_segments = [
        MagicMock(start=0.0, text="Hello world"),
        MagicMock(start=5.0, text="This is a test"),
    ]

    progress_calls = []

    def progress_cb(current, total):
        progress_calls.append((current, total))

    with patch("faster_whisper.WhisperModel") as mock_model_class:
        mock_model = MagicMock()
        mock_model.transcribe.return_value = (mock_segments, MagicMock())
        mock_model_class.return_value = mock_model

        result = transcribe_with_progress("/fake/audio.mp3", model="base",
                                         progress_callback=progress_cb)

        assert len(result) == 2
        assert len(progress_calls) >= 1