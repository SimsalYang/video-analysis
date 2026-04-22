"""Whisper-based transcription using faster-whisper."""
from typing import List

WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]


def transcribe(audio_path: str, model: str = "base") -> List[dict]:
    """Transcribe audio file using faster-whisper. Returns list of {'timestamp': 'HH:MM:SS', 'text': '...'}.
    Uses int8 quantization for faster CPU inference.
    """
    if model not in WHISPER_MODELS:
        raise ValueError(f"Invalid model: {model}. Available: {WHISPER_MODELS}")

    from faster_whisper import WhisperModel

    model_instance = WhisperModel(model, device="cpu", compute_type="int8")
    segments, _ = model_instance.transcribe(audio_path, beam_size=5)

    result = []
    for seg in segments:
        hours = int(seg.start // 3600)
        minutes = int((seg.start % 3600) // 60)
        seconds = int(seg.start % 60)
        timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        result.append({"timestamp": timestamp, "text": seg.text.strip()})

    return result


def transcribe_with_progress(audio_path: str, model: str = "base",
                             progress_callback=None) -> List[dict]:
    """Transcribe audio file with progress callback.

    Args:
        audio_path: Path to audio file.
        model: Whisper model size.
        progress_callback: Callable(current: int, total: int) called per segment.
                          current is 0-indexed segment index, total is total segments.

    Returns:
        List of {'timestamp': 'HH:MM:SS', 'text': '...'}
    """
    if model not in WHISPER_MODELS:
        raise ValueError(f"Invalid model: {model}. Available: {WHISPER_MODELS}")

    from faster_whisper import WhisperModel

    model_instance = WhisperModel(model, device="cpu", compute_type="int8")
    segments, info = model_instance.transcribe(
        audio_path, beam_size=5, word_timestamps=True
    )

    # Convert generator to list so we know total count
    segments_list = list(segments)
    total = len(segments_list)

    result = []
    for i, seg in enumerate(segments_list):
        if progress_callback:
            progress_callback(i, total)

        hours = int(seg.start // 3600)
        minutes = int((seg.start % 3600) // 60)
        seconds = int(seg.start % 60)
        timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        result.append({"timestamp": timestamp, "text": seg.text.strip()})

    if progress_callback:
        progress_callback(total, total)

    return result


def format_transcript(segments: List[dict], include_timestamps: bool = True) -> str:
    """Format transcript segments into a readable string."""
    if include_timestamps:
        return "\n".join(f"[{seg['timestamp']}] {seg['text']}" for seg in segments)
    return "\n".join(seg["text"] for seg in segments)


def get_transcript_text(segments: List[dict]) -> str:
    """Get plain text from transcript segments without timestamps."""
    return " ".join(seg["text"] for seg in segments)
