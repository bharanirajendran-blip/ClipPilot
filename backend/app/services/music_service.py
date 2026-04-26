"""Background music service — generates mood-matched ambient tracks in pure Python."""

import io
import struct
import math
import random
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Mood presets: each defines chord frequencies, tempo, and character
MOOD_PRESETS = {
    "calm": {
        "freqs": [130.81, 164.81, 196.00, 261.63],  # C major (C3, E3, G3, C4)
        "amps": [0.22, 0.15, 0.13, 0.08],
        "vibrato_rate": 0.08,
        "swell_rate": 0.04,
        "brightness": 0.0,
    },
    "inspiring": {
        "freqs": [146.83, 185.00, 220.00, 293.66],  # D major (D3, F#3, A3, D4)
        "amps": [0.20, 0.16, 0.14, 0.10],
        "vibrato_rate": 0.12,
        "swell_rate": 0.06,
        "brightness": 0.3,
    },
    "upbeat": {
        "freqs": [164.81, 207.65, 246.94, 329.63],  # E major (E3, G#3, B3, E4)
        "amps": [0.18, 0.15, 0.15, 0.12],
        "vibrato_rate": 0.15,
        "swell_rate": 0.08,
        "brightness": 0.5,
    },
    "dramatic": {
        "freqs": [110.00, 130.81, 164.81, 220.00],  # A minor (A2, C3, E3, A3)
        "amps": [0.25, 0.18, 0.14, 0.10],
        "vibrato_rate": 0.06,
        "swell_rate": 0.03,
        "brightness": 0.1,
    },
}

# Map video styles to music moods
STYLE_TO_MOOD = {
    "educational": "calm",
    "storytelling": "inspiring",
    "explainer": "upbeat",
    "news": "dramatic",
}


def get_background_music(style: str = "educational", duration: int = 60) -> bytes:
    """Get background music matched to video style.

    Args:
        style: Video style (educational, storytelling, explainer, news)
        duration: Target duration in seconds

    Returns:
        WAV audio bytes
    """
    mood = STYLE_TO_MOOD.get(style, "calm")
    return generate_ambient_music(
        duration_seconds=float(duration + 10),
        mood=mood,
    )


def generate_ambient_music(
    duration_seconds: float = 60.0,
    mood: str = "calm",
    sample_rate: int = 44100,
) -> bytes:
    """Generate a mood-matched ambient background track as WAV.

    Creates layered sine-wave pads with modulation, harmonics,
    and subtle rhythmic pulses for a richer sound.

    Args:
        duration_seconds: Length in seconds
        mood: One of calm, inspiring, upbeat, dramatic
        sample_rate: Audio sample rate

    Returns:
        WAV audio bytes
    """
    try:
        preset = MOOD_PRESETS.get(mood, MOOD_PRESETS["calm"])
        freqs = preset["freqs"]
        amps = preset["amps"]
        vibrato_rate = preset["vibrato_rate"]
        swell_rate = preset["swell_rate"]
        brightness = preset["brightness"]

        num_samples = int(duration_seconds * sample_rate)
        fade_time = 3.0

        # Pre-compute random phase offsets for natural feel
        random.seed(42)  # Deterministic for consistency
        phase_offsets = [random.uniform(0, 2 * math.pi) for _ in freqs]

        samples = []
        for i in range(num_samples):
            t = i / sample_rate
            sample = 0.0

            for j, (freq, amp) in enumerate(zip(freqs, amps)):
                phase = phase_offsets[j]
                # Vibrato
                vibrato = 1.0 + 0.003 * math.sin(2 * math.pi * vibrato_rate * t + phase)
                # Volume swell
                volume_mod = 0.6 + 0.4 * math.sin(2 * math.pi * swell_rate * t + phase * 0.5)

                # Fundamental
                sample += amp * volume_mod * math.sin(2 * math.pi * freq * vibrato * t + phase)

                # Add soft harmonics for richness
                if brightness > 0:
                    sample += amp * brightness * 0.3 * volume_mod * math.sin(
                        2 * math.pi * freq * 2 * vibrato * t + phase
                    )
                    sample += amp * brightness * 0.15 * volume_mod * math.sin(
                        2 * math.pi * freq * 3 * vibrato * t + phase
                    )

            # Subtle rhythmic pulse (very gentle, like breathing)
            pulse = 0.85 + 0.15 * math.sin(2 * math.pi * 0.5 * t)
            sample *= pulse

            # Fade in/out
            if t < fade_time:
                sample *= t / fade_time
            elif t > duration_seconds - fade_time:
                sample *= (duration_seconds - t) / fade_time

            # Soft clamp
            sample = max(-0.8, min(0.8, sample))
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

        wav_bytes = wav_buffer.getvalue()
        logger.info(f"Generated {mood} ambient music: {len(wav_bytes)} bytes, {duration_seconds}s")
        return wav_bytes

    except Exception as e:
        logger.error(f"Music generation failed: {str(e)}")
        raise
