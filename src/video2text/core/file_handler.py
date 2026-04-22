"""File handling and audio extraction using FFmpeg."""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from video2text.utils.config import get_ffmpeg_bin

SUPPORTED_VIDEO_FORMATS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}
SUPPORTED_AUDIO_FORMATS = {".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg"}
SUPPORTED_FORMATS = SUPPORTED_VIDEO_FORMATS | SUPPORTED_AUDIO_FORMATS


def validate_file(path: str) -> Tuple[bool, Optional[str]]:
    """Check if file exists and has supported extension. Returns (valid, error_message)."""
    if not os.path.isfile(path):
        return False, f"文件不存在: {path}"
    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        return False, f"不支持的格式: {ext}。支持的格式: {', '.join(SUPPORTED_FORMATS)}"
    return True, None


def get_duration(file_path: str) -> str:
    """Get duration of video/audio file using ffprobe. Returns HH:MM:SS string."""
    result = subprocess.run(
        [
            get_ffmpeg_bin("ffprobe"), "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ],
        capture_output=True, text=True, check=True
    )
    seconds = float(result.stdout.strip())
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def extract_audio(video_path: str, output_path: Optional[str] = None) -> str:
    """Extract audio from video file using FFmpeg. Returns output audio path."""
    if output_path is None:
        output_path = tempfile.mktemp(suffix=".mp3")

    result = subprocess.run(
        [
            get_ffmpeg_bin("ffmpeg"), "-y", "-i", video_path,
            "-vn", "-acodec", "libmp3lame", "-q:a", "2",
            output_path
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")
    return output_path


def is_audio_file(path: str) -> bool:
    """Check if file is an audio file (not video)."""
    ext = os.path.splitext(path)[1].lower()
    return ext in SUPPORTED_AUDIO_FORMATS
