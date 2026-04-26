"""Google Vertex AI Veo video generation service.

Uses the official google-genai SDK which handles:
- Authentication via Application Default Credentials
- Long-running operation polling automatically

Video download uses httpx directly to avoid SDK stdout binary dump.

Requires:
- pip install google-genai google-auth
- Google Cloud project with Vertex AI API enabled
- Application Default Credentials (gcloud auth application-default login)
"""

import time
import os
import sys
import httpx
from google import genai
from google.genai import types
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VeoService:
    """Service for generating videos using Google Veo via Vertex AI."""

    POLL_INTERVAL = 20  # seconds between status checks (recommended by Google)
    MAX_POLL_TIME = 600  # 10 minutes max wait

    def __init__(self):
        self.project_id = settings.GOOGLE_CLOUD_PROJECT
        self.location = settings.GOOGLE_CLOUD_LOCATION
        self.model = settings.VEO_MODEL
        self.bucket = settings.GCS_BUCKET

        # Initialize the genai client for Vertex AI
        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location,
        )

    def _get_access_token(self) -> str:
        """Get OAuth2 access token for GCS download."""
        import google.auth
        import google.auth.transport.requests

        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        credentials.refresh(google.auth.transport.requests.Request())
        return credentials.token

    def generate_video(self, prompt: str, duration: int = 8) -> bytes:
        """Generate a video from a text prompt using Veo.

        Args:
            prompt: Visual scene description
            duration: Clip duration in seconds (4, 6, or 8)

        Returns:
            Raw MP4 video bytes
        """
        # Veo supports 4, 6, or 8 second durations
        allowed_durations = [4, 6, 8]
        veo_duration = min(allowed_durations, key=lambda x: abs(x - duration))

        logger.info(
            f"Veo request: model={self.model}, duration={veo_duration}s, "
            f"prompt={prompt[:100]}..."
        )

        try:
            # Submit the video generation request
            # Suppress stdout at fd level — SDK sometimes writes binary to fd 1
            stdout_fd = sys.stdout.fileno()
            saved_fd = os.dup(stdout_fd)
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, stdout_fd)
            os.close(devnull)

            try:
                operation = self.client.models.generate_videos(
                    model=self.model,
                    prompt=prompt[:480],
                    config=types.GenerateVideosConfig(
                        aspect_ratio="9:16",
                        number_of_videos=1,
                        duration_seconds=veo_duration,
                    ),
                )

                logger.info("Veo operation submitted, polling for completion...")

                # Poll until done
                start_time = time.time()
                while not operation.done:
                    elapsed = time.time() - start_time
                    if elapsed > self.MAX_POLL_TIME:
                        raise Exception(
                            f"Veo operation timed out after {int(elapsed)}s"
                        )

                    logger.info(
                        f"Veo operation in progress... "
                        f"({int(elapsed)}s elapsed)"
                    )
                    time.sleep(self.POLL_INTERVAL)
                    operation = self.client.operations.get(operation)
            finally:
                # Restore stdout
                os.dup2(saved_fd, stdout_fd)
                os.close(saved_fd)

            logger.info("Veo operation complete!")

            # Check for errors
            if operation.error:
                raise Exception(
                    f"Veo generation failed: {operation.error}"
                )

            # Extract the generated video
            result = operation.result
            if not result or not result.generated_videos:
                raise Exception(
                    f"No videos in Veo result: {result}"
                )

            generated_video = result.generated_videos[0]
            video_file = generated_video.video

            # Log what we got back
            logger.info(f"Video file type: {type(video_file)}")
            logger.info(f"Video file attrs: {[a for a in dir(video_file) if not a.startswith('_')]}")

            # Download the video bytes
            video_bytes = self._download_video(video_file)
            logger.info(f"Downloaded Veo video: {len(video_bytes)} bytes")
            return video_bytes

        except Exception as e:
            logger.error(f"Veo generation error: {str(e)}")
            raise Exception(f"Veo video generation failed: {str(e)}")

    def _download_video(self, video_file) -> bytes:
        """Download generated video bytes.

        Priority:
        1. video_bytes attribute (direct bytes from SDK)
        2. GCS URI download via httpx
        3. SDK save-to-file (with stdout suppressed)
        """
        # Method 1: Direct bytes attribute (fastest, no network call)
        video_bytes = getattr(video_file, 'video_bytes', None)
        if video_bytes:
            logger.info(f"Got video_bytes directly: {len(video_bytes)} bytes")
            return video_bytes

        # Method 2: Download from GCS URI
        gcs_uri = getattr(video_file, 'uri', None)
        logger.info(f"Video URI: {gcs_uri}")

        if gcs_uri and gcs_uri.startswith("gs://"):
            return self._download_from_gcs_http(gcs_uri)

        if gcs_uri and gcs_uri.startswith("http"):
            token = self._get_access_token()
            with httpx.Client(timeout=120.0) as client:
                resp = client.get(gcs_uri, headers={"Authorization": f"Bearer {token}"})
                resp.raise_for_status()
                return resp.content

        # Method 3: Save to temp file via SDK (suppress stdout at fd level)
        if hasattr(video_file, 'save'):
            logger.info("Using save() method to write to temp file")
            tmp_path = '/tmp/veo_temp_video.mp4'
            stdout_fd = sys.stdout.fileno()
            saved_fd = os.dup(stdout_fd)
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, stdout_fd)
            os.close(devnull)
            try:
                video_file.save(tmp_path)
            finally:
                os.dup2(saved_fd, stdout_fd)
                os.close(saved_fd)
            with open(tmp_path, 'rb') as f:
                data = f.read()
            os.remove(tmp_path)
            logger.info(f"Saved via SDK: {len(data)} bytes")
            return data

        raise Exception(
            f"Cannot download video. "
            f"Type: {type(video_file)}, "
            f"attrs: {[a for a in dir(video_file) if not a.startswith('_')]}"
        )

    def _download_from_gcs_http(self, gcs_uri: str) -> bytes:
        """Download from GCS using the JSON API with httpx.

        This avoids both the google-cloud-storage SDK and the genai SDK,
        neither of which behave well with stdout.
        """
        from urllib.parse import quote

        # Parse gs://bucket/path
        parts = gcs_uri.replace("gs://", "").split("/", 1)
        bucket_name = parts[0]
        object_path = parts[1] if len(parts) > 1 else ""

        token = self._get_access_token()

        download_url = (
            f"https://storage.googleapis.com/storage/v1/b/{bucket_name}"
            f"/o/{quote(object_path, safe='')}?alt=media"
        )

        logger.info(f"Downloading from GCS: {download_url[:100]}...")

        with httpx.Client(timeout=120.0) as client:
            response = client.get(
                download_url,
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            logger.info(f"GCS download complete: {len(response.content)} bytes")
            return response.content
