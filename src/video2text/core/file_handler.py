from pathlib import Path

SUPPORTED_FORMATS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv"}


def validate_file(file_path: str) -> bool:
    """Validate if the file is a supported video format."""
    path = Path(file_path)
    return path.exists() and path.suffix.lower() in SUPPORTED_FORMATS
