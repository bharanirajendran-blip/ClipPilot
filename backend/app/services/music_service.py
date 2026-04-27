"""Background music service — fetches royalty-free mood-matched tracks from Supabase Storage.

Five pre-uploaded MP3 tracks (one per mood) live in the Supabase `audio` bucket.
The worker downloads the matching track at video-assembly time. Falls back to a
simple generated tone if the download fails.
"""

import io
import struct
import math
import httpx
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Map video styles to music moods
STYLE_TO_MOOD = {
    "educational": "calm",
    "storytelling": "inspiring",
    "explainer": "upbeat",
    "documentary": "dramatic",
    "animated": "playful",
}

# Filenames stored in the Supabase `audio` bucket
MOOD_TRACKS = {
    "calm": "mood_calm.mp3",
    "inspiring": "mood_inspiring.mp3",
    "upbeat": "mood_upbeat.mp3",
    "dramatic": "mood_dramatic.mp3",
    "playful": "mood_playful.mp3",
}


def _track_url(filename: str) -> str:
    """Build the public Supabase Storage URL for an audio file."""
    base = settings.SUPABASE_URL.rstrip("/")
    return f"{base}/storage/v1/object/public/audio/{filename}"


async def get_background_music(style: str = "educational", duration: int = 60) -> bytes:
    """Download the royalty-free background track matched to the video style.

    Args:
        style: Video style name (educational, storytelling, etc.)
        duration: Target duration in seconds (unused — tracks are pre-cut,
                  FFmpeg handles looping/trimming at mix time)

    Returns:
        MP3 audio bytes
    """
    mood = STYLE_TO_MOOD.get(style, "calm")
    filename = MOOD_TRACKS.get(mood, MOOD_TRACKS["calm"])
    url = _track_url(filename)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            audio_bytes = resp.content
            logger.info(
                f"Downloaded {mood} background music: {len(audio_bytes)} bytes "
                f"from {filename}"
            )
            return audio_bytes
    except Exception as e:
        logger.warning(f"Failed to download {mood} track ({filename}): {e}. Falling back to generated tone.")
        return _generate_fallback_tone(duration)


def get_background_music_sync(style: str = "educational", duration: int = 60) -> bytes:
    """Synchronous wrapper — downloads the track using httpx sync client.

    Use this when calling from non-async code.
    """
    mood = STYLE_TO_MOOD.get(style, "calm")
    filename = MOOD_TRACKS.get(mood, MOOD_TRACKS["calm"])
    url = _track_url(filename)

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            audio_bytes = resp.content
            logger.info(
                f"Downloaded {mood} background music: {len(audio_bytes)} bytes "
                f"from {filename}"
            )
            return audio_bytes
    except Exception as e:
        logger.warning(f"Failed to download {mood} track ({filename}): {e}. Falling back to generated tone.")
        return _generate_fallback_tone(duration)


def _generate_fallback_tone(duration: int = 60, sample_rate: int = 44100) -> bytes:
    """Generate a minimal soft pad as fallback if Supabase download fails.

    This is intentionally very simple — just a quiet, warm chord so the
    video isn't silent. The real tracks from Supabase are much better.
    """
    duration_seconds = float(duration + 5)
    num_samples = int(duration_seconds * sample_rate)
    fade_time = 3.0

    # Soft C major chord, triangle-ish wave, very quiet
    freqs = [130.81, 164.81, 196.00]
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        sample = 0.0
        for freq in freqs:
            # Triangle wave approximation
            p = (freq * t) % 1.0
            sample += 0.06 * (4.0 * abs(p - 0.5) - 1.0)

        # Gentle swell
        sample *= 0.7 + 0.3 * math.sin(2 * math.pi * 0.03 * t)

        # Fade in/out
        if t < fade_time:
            sample *= t / fade_time
        elif t > duration_seconds - fade_time:
            sample *= (duration_seconds - t) / fade_time

        sample = max(-0.5, min(0.5, sample))
        samples.append(sample)

    # Encode as 16-bit mono WAV
    wav_buffer = io.BytesIO()
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = num_samples * block_align

    wav_buffer.write(b'RIFF')
    wav_buffer.write(struct.pack('<I', 36 + data_size))
    wav_buffer.write(b'WAVE')
    wav_buffer.write(b'fmt ')
    wav_buffer.write(struct.pack('<I', 16))
    wav_buffer.write(struct.pack('<H', 1))
    wav_buffer.write(struct.pack('<H', num_channels))
    wav_buffer.write(struct.pack('<I', sample_rate))
    wav_buffer.write(struct.pack('<I', byte_rate))
    wav_buffer.write(struct.pack('<H', block_align))
    wav_buffer.write(struct.pack('<H', bits_per_sample))
    wav_buffer.write(b'data')
    wav_buffer.write(struct.pack('<I', data_size))

    for sample in samples:
        int_sample = int(sample * 32767)
        int_sample = max(-32768, min(32767, int_sample))
        wav_buffer.write(struct.pack('<h', int_sample))

    logger.info(f"Generated fallback tone: {len(wav_buffer.getvalue())} bytes")
    return wav_buffer.getvalue()
