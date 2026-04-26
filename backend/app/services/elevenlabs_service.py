"""ElevenLabs text-to-speech service."""

import httpx
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ElevenLabsService:
    """Service for generating speech using ElevenLabs Turbo v2.5."""

    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self):
        """Initialize ElevenLabs service."""
        self.api_key = settings.ELEVENLABS_API_KEY
        self.voice_id = settings.ELEVENLABS_VOICE_ID
        self.model_id = settings.ELEVENLABS_MODEL_ID

    def generate_speech(self, text: str, voice_id: str = None) -> bytes:
        """Generate speech audio from text.

        Args:
            text: Text to convert to speech
            voice_id: Voice ID (defaults to configured voice)

        Returns:
            Audio bytes (MP3 format)

        Raises:
            Exception: If generation fails
        """
        if voice_id is None:
            voice_id = self.voice_id

        try:
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
            }

            payload = {
                "text": text,
                "model_id": self.model_id,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
            }

            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.BASE_URL}/text-to-speech/{voice_id}",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()

                audio_bytes = response.content
                logger.info(f"Generated speech: {len(audio_bytes)} bytes")

                return audio_bytes

        except httpx.HTTPError as e:
            logger.error(f"ElevenLabs API error: {str(e)}")
            raise Exception(f"Failed to generate speech: {str(e)}")
        except Exception as e:
            logger.error(f"Speech generation error: {str(e)}")
            raise

    def get_voices(self) -> list:
        """Get list of available voices.

        Returns:
            List of voice dicts with id and name

        Raises:
            Exception: If request fails
        """
        try:
            headers = {"xi-api-key": self.api_key}

            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{self.BASE_URL}/voices",
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                voices = data.get("voices", [])
                logger.info(f"Retrieved {len(voices)} voices")

                return [{"id": v.get("voice_id"), "name": v.get("name")} for v in voices]

        except httpx.HTTPError as e:
            logger.error(f"Failed to get voices: {str(e)}")
            raise Exception(f"Failed to retrieve voices: {str(e)}")
