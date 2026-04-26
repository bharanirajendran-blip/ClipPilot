"""Content guardrail checks using Claude.

Implements a two-tier validation strategy inspired by Weather AI Agent:
- HARD checks: block execution (safety violations, NSFW, hate speech)
- SOFT warnings: log but continue (minor quality issues, borderline tone)
"""

import json
import re
from anthropic import Anthropic
from app.config import settings
from app.models.schemas import GuardrailResult
from app.utils.logger import get_logger

logger = get_logger(__name__)

HARD_CATEGORIES = [
    "violence",
    "explicit_content",
    "hate_speech",
    "dangerous_activities",
    "self_harm",
]

SOFT_CATEGORIES = [
    "health_misinformation",
    "political_misinformation",
    "bullying",
    "mild_language",
    "borderline_tone",
]


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


def check_input_safety(topic: str) -> GuardrailResult:
    """Check if topic is safe for 12+ audience using hard/soft tiers.

    Hard failures block the request. Soft warnings are logged
    but the request proceeds.

    Args:
        topic: Topic string to evaluate

    Returns:
        GuardrailResult with is_safe, severity, and any warnings
    """
    try:
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": f"""You are a content safety classifier for a 12+ audience video platform.

Topic: "{topic}"

Classify this topic into one of these tiers:

HARD BLOCK (is_safe=false, severity="hard") — must reject:
- Violence, gore, weapons instructions
- Explicit/sexual content
- Hate speech, slurs, discrimination
- Dangerous activities (drugs, self-harm instructions)
- Self-harm promotion

SOFT WARNING (is_safe=true, severity="soft") — allow with warning:
- Potentially misleading health claims
- Political bias or one-sided political framing
- Mild bullying or mean-spirited tone
- Borderline age-appropriateness

CLEAN (is_safe=true, severity="none") — fully safe:
- Educational, entertaining, informative content

Reply with ONLY this JSON (no markdown, no extra text):
{{"is_safe": true, "severity": "none", "category": "safe", "reason": "brief reason", "warnings": []}}

For soft warnings, set is_safe=true but include the concern in "warnings" array."""}],
        )

        result_text = response.content[0].text
        logger.info(f"Guardrail raw response: {result_text[:200]}")
        result_json = _extract_json(result_text)

        is_safe = result_json.get("is_safe", True)
        category = result_json.get("category", "safe")
        reason = result_json.get("reason", "")
        severity = result_json.get("severity", "none")
        warnings = result_json.get("warnings", [])

        if severity == "soft":
            logger.warning(f"Input soft warning - Category: {category}, Warnings: {warnings}")
        elif not is_safe:
            logger.warning(f"Input HARD BLOCK - Category: {category}, Reason: {reason}")

        return GuardrailResult(
            is_safe=is_safe,
            category=category if not is_safe else None,
            reason=reason if not is_safe else None,
            severity=severity,
            warnings=warnings,
        )

    except json.JSONDecodeError as e:
        # FAIL CLOSED: if we can't parse the safety response, block the content
        logger.warning(f"Failed to parse guardrail response, blocking as unsafe: {str(e)}")
        return GuardrailResult(
            is_safe=False,
            category="parse_error",
            reason="Safety check could not be completed — content blocked as a precaution",
            severity="hard",
        )
    except Exception as e:
        # FAIL CLOSED: API errors should block, not allow
        logger.error(f"Input guardrail check error: {str(e)}")
        return GuardrailResult(
            is_safe=False,
            category="api_error",
            reason="Safety check unavailable — content blocked as a precaution",
            severity="hard",
        )


def check_output_safety(script: str) -> GuardrailResult:
    """Check if generated script is safe for 12+ audience using hard/soft tiers.

    Args:
        script: Generated script text to evaluate

    Returns:
        GuardrailResult with is_safe, severity, and any warnings
    """
    try:
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        script_preview = script[:2000] if len(script) > 2000 else script

        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": f"""You are a content safety classifier for a 12+ audience video platform.

Script: "{script_preview}"

Classify this script into one of these tiers:

HARD BLOCK (is_safe=false, severity="hard") — must reject:
- Violence, gore, weapons instructions
- Explicit/sexual content
- Hate speech, slurs, discrimination
- Dangerous activities (drugs, self-harm instructions)

SOFT WARNING (is_safe=true, severity="soft") — allow with warning:
- Potentially misleading health/science claims
- One-sided political framing
- Sensationalist or clickbait language
- Minor factual inaccuracies

CLEAN (is_safe=true, severity="none") — fully safe:
- Accurate, educational, entertaining content

Reply with ONLY this JSON (no markdown, no extra text):
{{"is_safe": true, "severity": "none", "category": "safe", "reason": "brief reason", "warnings": []}}

For soft warnings, set is_safe=true but include the concern in "warnings" array."""}],
        )

        result_text = response.content[0].text
        result_json = _extract_json(result_text)

        is_safe = result_json.get("is_safe", True)
        category = result_json.get("category", "safe")
        reason = result_json.get("reason", "")
        severity = result_json.get("severity", "none")
        warnings = result_json.get("warnings", [])

        if severity == "soft":
            logger.warning(f"Output soft warning - Category: {category}, Warnings: {warnings}")
        elif not is_safe:
            logger.warning(f"Output HARD BLOCK - Category: {category}, Reason: {reason}")

        return GuardrailResult(
            is_safe=is_safe,
            category=category if not is_safe else None,
            reason=reason if not is_safe else None,
            severity=severity,
            warnings=warnings,
        )

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse output guardrail response, blocking: {str(e)}")
        return GuardrailResult(
            is_safe=False,
            category="parse_error",
            reason="Output safety check could not be completed — content blocked as a precaution",
            severity="hard",
        )
    except Exception as e:
        logger.error(f"Output guardrail check error: {str(e)}")
        return GuardrailResult(
            is_safe=False,
            category="api_error",
            reason="Output safety check unavailable — content blocked as a precaution",
            severity="hard",
        )
