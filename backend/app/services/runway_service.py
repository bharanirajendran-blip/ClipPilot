"""Runway video generation service (supports Gen-3 and Gen-4 models)."""

import httpx
import time
import base64
import io
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RunwayService:
    """Service for generating videos using Runway Gen-3 Alpha Turbo.

    Tries text-to-video first for best quality.
    Falls back to image-to-video with rich starter images.
    """

    BASE_URL = "https://api.dev.runwayml.com/v1"
    POLL_INTERVAL = settings.RUNWAY_POLL_INTERVAL
    MAX_RETRIES = settings.RUNWAY_MAX_RETRIES

    def __init__(self):
        self.api_key = settings.RUNWAY_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": "2024-11-06",
        }

    def generate_video(self, prompt: str, duration: int = 10) -> bytes:
        """Generate a video from a text prompt.

        Strategy:
        1. Try text-to-video (best quality — Runway generates from scratch)
        2. Fall back to image-to-video with a rich starter image
        """
        # Always use 10-second clips for best quality — scenes concatenate to full length
        runway_duration = 10

        try:
            # Strategy 1: Try text-to-video (produces the best results)
            task_id = self._try_text_to_video(prompt, runway_duration)
            if task_id:
                logger.info(f"Created Runway text-to-video task: {task_id}")
                task_data = self._wait_for_completion(task_id)
                video_bytes = self._extract_and_download(task_data, task_id)
                return video_bytes
        except Exception as e:
            logger.info(f"Text-to-video not available or failed: {str(e)}, trying image-to-video")

        # Strategy 2: Image-to-video with rich starter image
        try:
            starter_image_b64 = self._create_starter_image(prompt)
            task_id = self._create_image_to_video_task(prompt, starter_image_b64, runway_duration)
            logger.info(f"Created Runway image-to-video task: {task_id}")

            task_data = self._wait_for_completion(task_id)
            video_bytes = self._extract_and_download(task_data, task_id)
            return video_bytes

        except Exception as e:
            logger.error(f"Video generation failed: {str(e)}")
            raise

    def _extract_and_download(self, task_data: dict, task_id: str) -> bytes:
        """Extract video URL from task data and download it."""
        output = task_data.get("output", [])
        if isinstance(output, list) and len(output) > 0:
            video_url = output[0]
        elif isinstance(output, str):
            video_url = output
        else:
            raise Exception(f"Unexpected output format: {output}")

        video_bytes = self._download_video(video_url)
        logger.info(f"Downloaded video: {len(video_bytes)} bytes from task {task_id}")
        return video_bytes

    def _try_text_to_video(self, prompt: str, duration: int) -> str | None:
        """Attempt text-to-video generation. Returns task ID or None."""
        payload = {
            "model": "gen4.5",
            "promptText": prompt[:512],
            "duration": duration,
            "watermark": True,
            "ratio": "720:1280",
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.BASE_URL}/text_to_video",
                    json=payload,
                    headers=self.headers,
                )

                if response.status_code == 404:
                    logger.info("Text-to-video endpoint not available")
                    return None

                if not response.is_success:
                    logger.warning(f"Text-to-video failed {response.status_code}: {response.text[:300]}")
                    return None

                data = response.json()
                return data.get("id")

        except Exception as e:
            logger.warning(f"Text-to-video attempt failed: {str(e)}")
            return None

    def _create_starter_image(self, prompt: str) -> str:
        """Create a visually rich, scene-relevant starter image.

        Uses keyword analysis to create appropriate imagery with
        multiple layers, organic shapes, and cinematic composition.
        """
        import random
        import hashlib

        width, height = 768, 1344
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)

        # Use prompt as seed for deterministic but varied results
        seed = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        prompt_lower = prompt.lower()

        # Scene-appropriate color palettes
        if any(w in prompt_lower for w in ['nature', 'plant', 'forest', 'tree', 'leaf', 'green', 'garden', 'photosynthesis']):
            colors = [(15, 50, 15), (30, 90, 35), (50, 140, 45), (100, 190, 70), (160, 220, 120)]
        elif any(w in prompt_lower for w in ['ocean', 'water', 'sea', 'rain', 'river', 'fish', 'marine']):
            colors = [(5, 20, 60), (15, 50, 110), (30, 90, 170), (70, 150, 220), (140, 200, 245)]
        elif any(w in prompt_lower for w in ['fire', 'sun', 'energy', 'heat', 'warm', 'light', 'solar']):
            colors = [(60, 15, 5), (140, 45, 10), (220, 100, 20), (250, 160, 40), (255, 220, 120)]
        elif any(w in prompt_lower for w in ['space', 'star', 'galaxy', 'cosmos', 'universe', 'night', 'dark']):
            colors = [(3, 3, 15), (10, 8, 35), (25, 15, 65), (50, 30, 100), (80, 60, 150)]
        elif any(w in prompt_lower for w in ['city', 'urban', 'building', 'tech', 'digital', 'computer', 'code']):
            colors = [(15, 20, 35), (30, 40, 65), (50, 70, 110), (80, 110, 170), (130, 160, 210)]
        elif any(w in prompt_lower for w in ['food', 'cook', 'kitchen', 'meal', 'coffee', 'eat', 'drink']):
            colors = [(50, 25, 10), (100, 55, 20), (160, 90, 35), (210, 140, 60), (240, 200, 130)]
        elif any(w in prompt_lower for w in ['medical', 'health', 'body', 'cell', 'brain', 'science', 'lab']):
            colors = [(10, 35, 45), (25, 65, 85), (40, 110, 140), (80, 170, 190), (150, 215, 230)]
        elif any(w in prompt_lower for w in ['music', 'sound', 'instrument', 'concert', 'song']):
            colors = [(40, 10, 50), (80, 20, 100), (130, 50, 160), (180, 90, 200), (220, 150, 240)]
        elif any(w in prompt_lower for w in ['history', 'ancient', 'old', 'past', 'war', 'battle']):
            colors = [(40, 30, 20), (80, 60, 40), (130, 100, 65), (180, 145, 95), (220, 195, 150)]
        else:
            colors = [(25, 15, 35), (50, 35, 65), (85, 60, 100), (130, 100, 145), (190, 160, 200)]

        # Layer 1: Multi-stop gradient
        for y in range(height):
            t = y / height
            idx = t * (len(colors) - 1)
            i = min(int(idx), len(colors) - 2)
            frac = idx - i
            c1, c2 = colors[i], colors[i + 1]
            r = int(c1[0] + (c2[0] - c1[0]) * frac)
            g = int(c1[1] + (c2[1] - c1[1]) * frac)
            b = int(c1[2] + (c2[2] - c1[2]) * frac)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Layer 2: Large soft blurred shapes for depth
        for _ in range(rng.randint(10, 18)):
            cx = rng.randint(-150, width + 150)
            cy = rng.randint(-150, height + 150)
            radius = rng.randint(100, 400)
            c_idx = rng.randint(0, len(colors) - 1)
            base = colors[c_idx]
            alpha = rng.uniform(0.1, 0.3)

            overlay = Image.new('RGB', (width, height), (0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            bright = (
                min(255, int(base[0] * 2.0 + 50)),
                min(255, int(base[1] * 2.0 + 50)),
                min(255, int(base[2] * 2.0 + 50)),
            )
            overlay_draw.ellipse(
                [cx - radius, cy - radius, cx + radius, cy + radius],
                fill=bright,
            )
            # Blur the overlay for soft bokeh effect
            overlay = overlay.filter(ImageFilter.GaussianBlur(radius=40))
            img = Image.blend(img, overlay, alpha)
            draw = ImageDraw.Draw(img)

        # Layer 3: Smaller detailed shapes for texture
        for _ in range(rng.randint(15, 30)):
            cx = rng.randint(0, width)
            cy = rng.randint(0, height)
            radius = rng.randint(10, 60)
            c_idx = rng.randint(len(colors) - 2, len(colors) - 1)
            base = colors[c_idx]
            alpha = rng.uniform(0.05, 0.15)

            overlay = Image.new('RGB', (width, height), (0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            highlight = (
                min(255, base[0] + 100),
                min(255, base[1] + 100),
                min(255, base[2] + 100),
            )
            overlay_draw.ellipse(
                [cx - radius, cy - radius, cx + radius, cy + radius],
                fill=highlight,
            )
            overlay = overlay.filter(ImageFilter.GaussianBlur(radius=15))
            img = Image.blend(img, overlay, alpha)
            draw = ImageDraw.Draw(img)

        # Layer 4: Light rays from top for cinematic depth
        for _ in range(rng.randint(4, 8)):
            x_start = rng.randint(0, width)
            spread = rng.randint(100, 300)
            c_idx = rng.randint(len(colors) - 2, len(colors) - 1)
            ray_color = colors[c_idx]

            overlay = Image.new('RGB', (width, height), (0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            for w_offset in range(-20, 21):
                overlay_draw.line(
                    [(x_start + w_offset, 0), (x_start + w_offset * spread // 20, height)],
                    fill=ray_color,
                )
            overlay = overlay.filter(ImageFilter.GaussianBlur(radius=25))
            img = Image.blend(img, overlay, 0.05)
            draw = ImageDraw.Draw(img)

        # Layer 5: Vignette effect (darken edges)
        vignette = Image.new('RGB', (width, height), (0, 0, 0))
        vignette_draw = ImageDraw.Draw(vignette)
        center_x, center_y = width // 2, height // 2
        max_dist = (center_x ** 2 + center_y ** 2) ** 0.5
        for ring in range(0, int(max_dist), 3):
            alpha_factor = min(1.0, (ring / max_dist) ** 1.5)
            if alpha_factor > 0.05:
                vignette_draw.ellipse(
                    [center_x - ring, center_y - ring, center_x + ring, center_y + ring],
                    outline=(0, 0, 0),
                )
        img = Image.blend(img, vignette, 0.3)

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_b64 = base64.b64encode(buffer.read()).decode('utf-8')

        return f"data:image/png;base64,{img_b64}"

    def _create_image_to_video_task(self, prompt: str, image_b64: str, duration: int) -> str:
        """Create an image-to-video generation task."""
        payload = {
            "model": settings.RUNWAY_MODEL,
            "promptImage": image_b64,
            "promptText": prompt[:512],
            "duration": duration,
            "watermark": True,
            "ratio": "768:1280",
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.BASE_URL}/image_to_video",
                    json=payload,
                    headers=self.headers,
                )

                if not response.is_success:
                    logger.error(f"Runway API error {response.status_code}: {response.text[:500]}")
                    response.raise_for_status()

                data = response.json()
                logger.info(f"Runway create response: {data}")

                task_id = data.get("id")
                if not task_id:
                    raise Exception(f"No task ID in response: {data}")

                return task_id

        except httpx.HTTPStatusError as e:
            raise Exception(f"Runway API error {e.response.status_code}: {e.response.text[:300]}")
        except httpx.HTTPError as e:
            raise Exception(f"Failed to connect to Runway: {str(e)}")

    def _wait_for_completion(self, task_id: str) -> dict:
        """Poll for task completion."""
        for attempt in range(self.MAX_RETRIES):
            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(
                        f"{self.BASE_URL}/tasks/{task_id}",
                        headers=self.headers,
                    )
                    response.raise_for_status()
                    data = response.json()

                    status = data.get("status", "").upper()
                    logger.info(f"Task {task_id} status: {status} (attempt {attempt + 1}/{self.MAX_RETRIES})")

                    if status == "SUCCEEDED":
                        return data
                    elif status == "FAILED":
                        error = data.get("failure", data.get("error", "Unknown"))
                        raise Exception(f"Runway task failed: {error}")
                    else:
                        time.sleep(self.POLL_INTERVAL)

            except httpx.HTTPError as e:
                logger.error(f"Poll error: {str(e)}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.POLL_INTERVAL)
                else:
                    raise

        raise Exception(f"Runway task {task_id} timed out")

    def _download_video(self, video_url: str) -> bytes:
        """Download video file from URL."""
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.get(video_url)
                response.raise_for_status()
                return response.content
        except httpx.HTTPError as e:
            raise Exception(f"Failed to download video: {str(e)}")
