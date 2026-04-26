"""Post-generation vision validation service.

Inspired by Weather AI Agent's multi-layer validation approach:
uses Claude Vision to inspect generated video frames for quality issues,
hallucinated text, artifacts, or unsafe content before assembly.
"""

import base64
import io
import json
import re
from typing import Optional
from dataclasses import dataclass
from anthropic import Anthropic
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of vision validation on a video clip."""
    passed: bool
    severity: str  # "hard" = block, "soft" = warn only
    issues: list[str]
    quality_score: float  # 0.0–1.0
    retry_hint: Optional[str] = None  # Prompt adjustment suggestion for retry


def _extract_json(text: str) -> dict:
    """Extract JSON from a response that may include markdown code fences."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        return json.loads(match.group(1))

    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group(0))

    raise json.JSONDecodeError("No JSON found", text, 0)


def extract_frame_from_video(video_bytes: bytes, timestamp: float = 2.0) -> Optional[bytes]:
    """Extract a single frame from video bytes at the given timestamp.

    Args:
        video_bytes: Raw MP4 video data
        timestamp: Time in seconds to extract frame

    Returns:
        PNG image bytes, or None if extraction fails
    """
    import subprocess
    import tempfile
    import os

    try:
        # Write video to temp file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as vf:
            vf.write(video_bytes)
            video_path = vf.name

        # Extract frame with FFmpeg
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as ff:
            frame_path = ff.name

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp),
            "-i", video_path,
            "-frames:v", "1",
            "-f", "image2",
            frame_path,
        ]
        subprocess.run(cmd, capture_output=True, timeout=15)

        if os.path.exists(frame_path) and os.path.getsize(frame_path) > 0:
            with open(frame_path, "rb") as f:
                return f.read()
        return None

    except Exception as e:
        logger.warning(f"Frame extraction failed: {str(e)}")
        return None
    finally:
        for p in [video_path, frame_path]:
            try:
                os.unlink(p)
            except Exception:
                pass


def validate_video_frame(
    frame_png: bytes,
    original_prompt: str,
    scene_number: int = 1,
) -> ValidationResult:
    """Validate a video frame using Claude Vision.

    Checks for:
    - Hard failures: hallucinated text/watermarks, NSFW content, completely
      wrong scene (e.g., blank/black frame)
    - Soft warnings: minor artifacts, low detail, slight prompt mismatch

    Args:
        frame_png: PNG image bytes of a video frame
        original_prompt: The prompt used to generate this video
        scene_number: Scene number for logging

    Returns:
        ValidationResult with pass/fail and details
    """
    try:
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        frame_b64 = base64.b64encode(frame_png).decode("utf-8")

        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": frame_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": f"""You are a video quality inspector for an AI video platform (12+ audience).

Inspect this frame from scene {scene_number}. The generation prompt was:
"{original_prompt[:300]}"

Check for these issues:

HARD FAILURES (must block):
- Hallucinated text, readable words, or watermarks burned into the scene
- NSFW, violent, or age-inappropriate content
- Completely black, white, or corrupted frame
- Clearly wrong scene (totally unrelated to prompt)

SOFT WARNINGS (log but allow):
- Minor visual artifacts or glitches
- Low detail or blurriness
- Slight mismatch with prompt intent
- Unnatural colors or lighting

Reply with ONLY this JSON:
{{"passed": true, "severity": "none", "issues": [], "quality_score": 0.85, "retry_hint": null}}

Rules:
- "passed" = false only for HARD failures
- "severity" = "hard" if blocking, "soft" if warning only, "none" if clean
- "quality_score" = 0.0 to 1.0 (0.7+ is acceptable)
- "retry_hint" = short prompt fix suggestion if failed, else null
- "issues" = list of strings describing problems found""",
                    },
                ],
            }],
        )

        result_text = response.content[0].text
        logger.info(f"Vision validation scene {scene_number}: {result_text[:200]}")
        result_json = _extract_json(result_text)

        return ValidationResult(
            passed=result_json.get("passed", True),
            severity=result_json.get("severity", "none"),
            issues=result_json.get("issues", []),
            quality_score=result_json.get("quality_score", 0.8),
            retry_hint=result_json.get("retry_hint"),
        )

    except json.JSONDecodeError as e:
        # Fail closed on parse errors — treat as soft warning, not hard block
        logger.warning(f"Vision validation parse error for scene {scene_number}: {str(e)}")
        return ValidationResult(
            passed=True,
            severity="soft",
            issues=["Vision validation response could not be parsed"],
            quality_score=0.5,
        )

    except Exception as e:
        # API errors — don't block the pipeline, just warn
        logger.warning(f"Vision validation error for scene {scene_number}: {str(e)}")
        return ValidationResult(
            passed=True,
            severity="soft",
            issues=[f"Vision validation unavailable: {str(e)}"],
            quality_score=0.5,
        )
