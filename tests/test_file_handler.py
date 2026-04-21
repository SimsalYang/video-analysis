"""tests/test_file_handler.py"""
import os
import tempfile
import pytest
from video2text.core.file_handler import validate_file, extract_audio, get_duration, SUPPORTED_FORMATS


def test_validate_file_accepts_supported_formats():
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(b"fake video content")
        path = f.name
    try:
        valid, err = validate_file(path)
        assert valid is True
        assert err is None
    finally:
        os.unlink(path)


def test_validate_file_rejects_unsupported_format():
    with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
        f.write(b"data")
        path = f.name
    try:
        valid, err = validate_file(path)
        assert valid is False
        assert err is not None
    finally:
        os.unlink(path)


def test_validate_file_rejects_nonexistent():
    valid, err = validate_file("/nonexistent/path/video.mp4")
    assert valid is False
    assert "不存在" in err


def test_supported_formats_includes_common_formats():
    expected = {".mp4", ".mkv", ".avi", ".mov", ".mp3", ".wav", ".m4a"}
    assert expected.issubset(SUPPORTED_FORMATS)


def test_extract_audio_raises_on_invalid_input():
    with pytest.raises(Exception):
        extract_audio("/nonexistent/video.mp4", "/tmp/output.mp3")
