"""SRT (SubRip) subtitle format utilities."""

from typing import List, Dict
from dataclasses import dataclass


@dataclass
class TimePoint:
    """A point in time with hour, minute, second, millisecond."""
    hours: int
    minutes: int
    seconds: int
    milliseconds: int

    def __str__(self) -> str:
        """Format as SRT time string (HH:MM:SS,mmm)."""
        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d},{self.milliseconds:03d}"

    @classmethod
    def from_seconds(cls, total_seconds: float) -> "TimePoint":
        """Create TimePoint from total seconds."""
        hours = int(total_seconds // 3600)
        remaining = total_seconds - (hours * 3600)
        minutes = int(remaining // 60)
        remaining = remaining - (minutes * 60)
        seconds = int(remaining)
        milliseconds = int((remaining - seconds) * 1000)
        return cls(hours, minutes, seconds, milliseconds)


def words_to_srt(words: List[Dict[str, float]], text: str) -> str:
    """Convert word-level timestamps to SRT format.

    Args:
        words: List of dicts with keys: word, start (seconds), end (seconds)
        text: Full transcript text for reference

    Returns:
        SRT formatted string
    """
    if not words:
        return ""

    srt_lines = []
    seq_num = 1

    # Group words into subtitle chunks (roughly 5-10 words per subtitle)
    chunk_size = 7
    for i in range(0, len(words), chunk_size):
        chunk = words[i:i + chunk_size]
        if not chunk:
            continue

        start_time = TimePoint.from_seconds(chunk[0]["start"])
        end_time = TimePoint.from_seconds(chunk[-1]["end"])

        subtitle_text = " ".join([w["word"] for w in chunk])

        srt_lines.append(str(seq_num))
        srt_lines.append(f"{start_time} --> {end_time}")
        srt_lines.append(subtitle_text)
        srt_lines.append("")

        seq_num += 1

    return "\n".join(srt_lines)


def create_simple_srt(text: str, start_time: float = 0.0, end_time: float = None) -> str:
    """Create simple SRT with entire text as one subtitle.

    Args:
        text: Subtitle text
        start_time: Start time in seconds
        end_time: End time in seconds (if None, defaults to start_time + 5)

    Returns:
        SRT formatted string
    """
    if end_time is None:
        end_time = start_time + 5.0

    start = TimePoint.from_seconds(start_time)
    end = TimePoint.from_seconds(end_time)

    return f"""1
{start} --> {end}
{text}
"""
