"""Tests for background music service."""

import pytest
from app.services.music_service import (
    get_background_music_sync,
    _generate_fallback_tone,
    _track_url,
    STYLE_TO_MOOD,
    MOOD_TRACKS,
)


def test_all_styles_have_mood_mapping():
    """Ensure every video style maps to a valid mood."""
    expected_styles = ["educational", "storytelling", "explainer", "documentary", "animated"]
    for style in expected_styles:
        assert style in STYLE_TO_MOOD, f"Style '{style}' missing from STYLE_TO_MOOD"
        mood = STYLE_TO_MOOD[style]
        assert mood in MOOD_TRACKS, f"Mood '{mood}' for style '{style}' not in MOOD_TRACKS"


def test_news_style_removed():
    """Confirm the old 'news' style is no longer in the mapping."""
    assert "news" not in STYLE_TO_MOOD


def test_all_moods_have_tracks():
    """Ensure every mood has a track filename."""
    expected_moods = ["calm", "inspiring", "upbeat", "dramatic", "playful"]
    for mood in expected_moods:
        assert mood in MOOD_TRACKS, f"Mood '{mood}' missing from MOOD_TRACKS"
        assert MOOD_TRACKS[mood].endswith(".mp3"), f"Track for '{mood}' should be an MP3"


def test_track_url_format():
    """Test that track URL is built correctly."""
    url = _track_url("mood_calm.mp3")
    assert "storage/v1/object/public/audio/mood_calm.mp3" in url
    assert url.startswith("http")


def test_fallback_tone_returns_wav():
    """Test that the fallback tone generator produces valid WAV bytes."""
    audio = _generate_fallback_tone(duration=5)
    assert isinstance(audio, bytes)
    assert len(audio) > 0
    # WAV files start with 'RIFF'
    assert audio[:4] == b"RIFF"
    # And contain 'WAVE' at offset 8
    assert audio[8:12] == b"WAVE"


def test_fallback_tone_duration():
    """Test that fallback audio length roughly matches requested duration."""
    duration = 5
    sample_rate = 44100
    audio = _generate_fallback_tone(duration=duration, sample_rate=sample_rate)

    # WAV header is 44 bytes, then 16-bit mono samples
    # Duration is duration + 5 seconds (extra buffer built in)
    data_size = len(audio) - 44
    expected_samples = (duration + 5) * sample_rate
    actual_samples = data_size // 2  # 16-bit = 2 bytes per sample

    # Allow 1% tolerance
    assert abs(actual_samples - expected_samples) < expected_samples * 0.01


def test_get_background_music_sync_falls_back():
    """Test that sync download falls back to generated tone when Supabase is unavailable.

    In test/CI environments there's no live Supabase, so this should
    gracefully fall back to the generated fallback tone.
    """
    # This will fail to connect to Supabase and fall back to generated tone
    audio = get_background_music_sync(style="educational", duration=5)
    assert isinstance(audio, bytes)
    assert len(audio) > 1000
