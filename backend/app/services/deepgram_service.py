"""Deepgram speech-to-text service."""

import httpx
import json
from typing import List, Dict
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DeepgramService:
    """Service for transcribing audio using Deepgram Nova-2."""

    BASE_URL = "https://api.deepgram.com/v1"

    def __init__(self):
        """Initialize Deepgram service."""
        self.api_key = settings.DEEPGRAM_API_KEY

    def transcribe_with_timestamps(self, audio_bytes: bytes) -> List[Dict]:
        """Transcribe audio and return word-level timestamps.

        Args:
            audio_bytes: Audio file bytes (MP3 or WAV)

        Returns:
            List of dicts with keys: word, start (seconds), end (seconds)

        Raises:
            Exception: If transcription fails
        """
        try:
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "audio/mpeg",
            }

            params = {
                "model": "nova-2",
                "detect_language": True,
                "punctuate": True,
            }

            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{self.BASE_URL}/listen",
                    content=audio_bytes,
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

            # Extract words with timestamps from Deepgram response
            words = []
            if "results" in data and "channels" in data["results"]:
                channels = data["results"]["channels"]
                if channels and "alternatives" in channels[0]:
                    alternatives = channels[0]["alternatives"]
                    if alternatives and "words" in alternatives[0]:
                        for word_data in alternatives[0]["words"]:
                            words.append({
                                "word": word_data.get("punctuated_word", word_data.get("word", "")),
                                "start": word_data.get("start", 0.0),
                                "end": word_data.get("end", 0.0),
                            })

            if not words:
                logger.warning("No words extracted from transcription")

            logger.info(f"Transcribed {len(words)} words")
            return words

        except httpx.HTTPError as e:
            logger.error(f"Deepgram API error: {str(e)}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse transcription response: {str(e)}")
            raise Exception(f"Invalid transcription response: {str(e)}")
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise

    def get_transcript_text(self, audio_bytes: bytes) -> str:
        """Get full transcript text from audio.

        Args:
            audio_bytes: Audio file bytes

        Returns:
            Full transcript text

        Raises:
            Exception: If transcription fails
        """
        try:
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "audio/mpeg",
            }

            params = {
                "model": "nova-2",
                "detect_language": True,
                "punctuate": True,
            }

            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{self.BASE_URL}/listen",
                    content=audio_bytes,
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

            # Extract transcript
            if "results" in data and "channels" in data["results"]:
                channels = data["results"]["channels"]
                if channels and "alternatives" in channels[0]:
                    alternatives = channels[0]["alternatives"]
                    if alternatives and "transcript" in alternatives[0]:
                        transcript = alternatives[0]["transcript"]
                        logger.info(f"Transcript length: {len(transcript)} chars")
                        return transcript

            logger.warning("No transcript in response")
            return ""

        except httpx.HTTPError as e:
            logger.error(f"Deepgram API error: {str(e)}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise
