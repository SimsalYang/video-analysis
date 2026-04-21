"""Output formatting for markdown and JSON export."""
import json
from datetime import datetime
from typing import List, Optional


def format_markdown(
    source: str,
    segments: List[dict],
    summary: Optional[dict] = None,
    duration: str = "00:00:00",
    transcription_model: str = "base",
    summary_model: str = "",
) -> str:
    """Format result as Markdown document."""
    lines = [
        "# 视频/音频内容提取结果",
        "",
        f"**来源**: {source}",
        f"**时长**: {duration}",
        f"**处理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**转录模型**: {transcription_model}",
    ]
    if summary_model:
        lines.append(f"**摘要模型**: {summary_model}")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 完整转录")
    lines.append("")
    for seg in segments:
        lines.append(f"[{seg['timestamp']}] {seg['text']}")

    if summary:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 内容摘要")
        lines.append("")
        for i, point in enumerate(summary.get("key_points", []), 1):
            lines.append(f"{i}. {point}")

        if summary.get("key_information"):
            lines.append("")
            lines.append("## 关键信息")
            lines.append("")
            for info in summary["key_information"]:
                lines.append(f"- {info}")

    return "\n".join(lines)


def format_json(
    source: str,
    segments: List[dict],
    summary: Optional[dict] = None,
    duration: str = "00:00:00",
    transcription_model: str = "base",
    summary_model: str = "",
) -> str:
    """Format result as JSON document."""
    data = {
        "source": source,
        "duration": duration,
        "processed_at": datetime.now().isoformat(),
        "transcription_model": transcription_model,
        "summary_model": summary_model,
        "full_transcript": segments,
        "summary": summary or {},
    }
    return json.dumps(data, ensure_ascii=False, indent=2)