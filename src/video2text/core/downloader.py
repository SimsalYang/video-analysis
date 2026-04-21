"""Video downloading with yt-dlp."""
import os
import tempfile
from typing import Optional


def get_video_info(url: str, cookies: Optional[str] = None) -> dict:
    """Get video info without downloading. Returns dict with title, duration, etc."""
    import yt_dlp

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }
    if cookies:
        ydl_opts["cookies"] = cookies

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info


def download_video(
    url: str,
    output_dir: Optional[str] = None,
    cookies: Optional[str] = None,
) -> str:
    """Download video from URL. Returns path to downloaded video file."""
    import yt_dlp

    if output_dir is None:
        output_dir = tempfile.gettempdir()

    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "quiet": False,
    }
    if cookies:
        ydl_opts["cookies"] = cookies

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename


def is_supported_url(url: str) -> bool:
    """Check if URL is supported by yt-dlp."""
    from yt_dlp import gen_extractor_classes
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if not parsed.netloc:
        return False

    host = parsed.netloc.lower()
    for extractor in gen_extractor_classes():
        if extractor.IE_NAME.lower() in host or any(h in host for h in extractor.IE_NAME.lower().split()):
            return True
    return False
