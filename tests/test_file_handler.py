import pytest
from video2text.core.file_handler import validate_file, SUPPORTED_FORMATS


def test_supported_formats():
    assert ".mp4" in SUPPORTED_FORMATS
    assert ".mkv" in SUPPORTED_FORMATS


def test_validate_file(tmp_path):
    # Create a temporary video file for testing
    video_file = tmp_path / "test.mp4"
    video_file.write_text("fake video content")

    assert validate_file(str(video_file)) is True
    assert validate_file(str(tmp_path / "nonexistent.mp4")) is False
    assert validate_file(str(tmp_path / "test.txt")) is False
