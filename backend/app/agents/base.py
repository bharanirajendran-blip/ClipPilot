"""Base agent class."""

import json
import re
from anthropic import Anthropic
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _extract_json(text: str) -> dict:
    """Robustly extract JSON from Claude's response.

    Handles: raw JSON, ```json fences, JSON followed by extra text,
    JSON embedded in prose, etc.
    """
    text = text.strip()

    # 1. Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Try extracting from ```json ... ``` or ``` ... ```
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 3. Try extracting from ```json ... ``` with array
    match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 4. Find the first complete JSON object by brace matching
    start = text.find('{')
    if start != -1:
        depth = 0
        in_string = False
        escape_next = False
        for i in range(start, len(text)):
            c = text[i]
            if escape_next:
                escape_next = False
                continue
            if c == '\\' and in_string:
                escape_next = True
                continue
            if c == '"' and not escape_next:
                in_string = not in_string
                continue
            if in_string:
                continue
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break

    # 5. Find first complete JSON array
    start = text.find('[')
    if start != -1:
        depth = 0
        in_string = False
        escape_next = False
        for i in range(start, len(text)):
            c = text[i]
            if escape_next:
                escape_next = False
                continue
            if c == '\\' and in_string:
                escape_next = True
                continue
            if c == '"' and not escape_next:
                in_string = not in_string
                continue
            if in_string:
                continue
            if c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break

    raise json.JSONDecodeError("No valid JSON found in response", text, 0)


class BaseAgent:
    """Base class for AI agents."""

    def __init__(self, system_prompt: str):
        """Initialize agent.

        Args:
            system_prompt: System prompt for Claude
        """
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.system_prompt = system_prompt
        self.model = settings.ANTHROPIC_MODEL

    def call(self, user_message: str, max_tokens: int = 2000) -> str:
        """Call Claude with a message.

        Args:
            user_message: User message content
            max_tokens: Maximum tokens in response

        Returns:
            Response text

        Raises:
            Exception: If API call fails
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ],
            )

            result = response.content[0].text
            logger.info(f"Agent call succeeded: {len(result)} chars")
            return result

        except Exception as e:
            logger.error(f"Agent call failed: {str(e)}")
            raise

    def call_json(self, user_message: str, max_tokens: int = 2000) -> dict:
        """Call Claude expecting JSON response.

        Args:
            user_message: User message content
            max_tokens: Maximum tokens in response

        Returns:
            Parsed JSON response

        Raises:
            Exception: If API call fails or JSON parsing fails
        """
        response_text = ""
        try:
            response_text = self.call(user_message, max_tokens)
            result = _extract_json(response_text)

            # Ensure we always return a dict — if Claude wrapped it in a list, unwrap
            if isinstance(result, list):
                if len(result) == 1 and isinstance(result[0], dict):
                    result = result[0]
                else:
                    result = {"items": result}

            logger.info(f"Agent JSON call succeeded: {len(json.dumps(result))} chars")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {str(e)}")
            logger.error(f"Raw response was: {response_text[:500]}")
            raise Exception(f"Invalid JSON response from agent: {str(e)}")
        except Exception as e:
            logger.error(f"Agent JSON call failed: {str(e)}")
            raise
