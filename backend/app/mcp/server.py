"""MCP Tool Server for ClipPilot Lite.

Implements the Model Context Protocol (MCP) pattern from the course:
- tools/list: Discover available tools and their schemas
- tools/call: Execute a tool by name with validated arguments

This server wraps external services as MCP tools:
1. generate_video — AI video generation (Veo 2.0 primary, Runway fallback)
2. elevenlabs_text_to_speech — Text-to-speech narration (ElevenLabs)
3. deepgram_transcribe — Audio transcription with word timestamps (Deepgram)
4. content_safety_check — Content moderation (Claude)

Architecture (from Week 9 MCP Lab):
    Agent Runtime (tasks.py)
         ↓  tools/call
    MCP Tool Server (this file)
         ↓  delegates to
    Service Layer (runway_service.py, elevenlabs_service.py, etc.)
"""

import json
import base64
from typing import Any
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ─── Tool Definitions (tools/list) ───────────────────────────────────

TOOL_REGISTRY = [
    {
        "name": "generate_video",
        "description": (
            "Generate a short video clip from a text prompt. "
            "Uses Google Veo 2.0 (primary) or Runway (fallback). "
            "Returns raw video bytes in 9:16 vertical format."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Detailed visual description of the scene to generate. Should describe real, filmable scenes with specific subjects, environments, lighting, and camera motion.",
                    "maxLength": 512,
                },
                "duration": {
                    "type": "integer",
                    "description": "Clip duration in seconds (4-10)",
                    "default": 8,
                },
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "elevenlabs_text_to_speech",
        "description": (
            "Convert text to natural-sounding speech audio using ElevenLabs. "
            "Returns MP3 audio bytes. Uses the Rachel voice with Turbo v2.5 model."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The narration text to convert to speech",
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "deepgram_transcribe",
        "description": (
            "Transcribe audio to text with word-level timestamps using Deepgram Nova-2. "
            "Returns a list of words with start/end times for caption generation."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "audio_base64": {
                    "type": "string",
                    "description": "Base64-encoded audio data (MP3 or WAV)",
                },
            },
            "required": ["audio_base64"],
        },
    },
    {
        "name": "content_safety_check",
        "description": (
            "Check if text content is safe for a 12+ audience. "
            "Uses Claude to classify content against blocked categories: "
            "violence, explicit content, hate speech, dangerous activities, etc. "
            "Returns is_safe boolean with category and reason if unsafe."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text content to check for safety",
                },
                "check_type": {
                    "type": "string",
                    "description": "Whether this is an input topic or generated output",
                    "enum": ["input", "output"],
                    "default": "input",
                },
            },
            "required": ["text"],
        },
    },
]


# ─── Tool Handlers (tools/call) ─────────────────────────────────────

def _handle_generate_video(arguments: dict) -> dict:
    """Execute video generation tool.

    Routes to Veo 2.0 (primary) or Runway (fallback) based on config.
    """
    from app.config import settings

    prompt = arguments["prompt"]
    duration = arguments.get("duration", 10)
    provider = settings.VIDEO_PROVIDER  # "veo" or "runway"

    if provider == "veo" and settings.GOOGLE_CLOUD_PROJECT:
        from app.services.veo_service import VeoService
        service = VeoService()
        video_bytes = service.generate_video(prompt, duration=duration)
    else:
        from app.services.runway_service import RunwayService
        service = RunwayService()
        video_bytes = service.generate_video(prompt, duration=duration)

    return {
        "type": "video",
        "provider": provider,
        "size_bytes": len(video_bytes),
        "duration_requested": duration,
        "data_base64": base64.b64encode(video_bytes).decode("utf-8"),
    }


def _handle_elevenlabs_tts(arguments: dict) -> dict:
    """Execute elevenlabs_text_to_speech tool."""
    from app.services.elevenlabs_service import ElevenLabsService

    text = arguments["text"]

    service = ElevenLabsService()
    audio_bytes = service.generate_speech(text)

    return {
        "type": "audio",
        "format": "mp3",
        "size_bytes": len(audio_bytes),
        "data_base64": base64.b64encode(audio_bytes).decode("utf-8"),
    }


def _handle_deepgram_transcribe(arguments: dict) -> dict:
    """Execute deepgram_transcribe tool."""
    from app.services.deepgram_service import DeepgramService

    audio_bytes = base64.b64decode(arguments["audio_base64"])

    service = DeepgramService()
    words = service.transcribe_with_timestamps(audio_bytes)

    return {
        "type": "transcription",
        "word_count": len(words),
        "words": words,
    }


def _handle_content_safety_check(arguments: dict) -> dict:
    """Execute content_safety_check tool."""
    from app.services.guardrails import check_input_safety, check_output_safety

    text = arguments["text"]
    check_type = arguments.get("check_type", "input")

    if check_type == "output":
        result = check_output_safety(text)
    else:
        result = check_input_safety(text)

    return {
        "type": "safety_result",
        "is_safe": result.is_safe,
        "category": result.category,
        "reason": result.reason,
        "severity": result.severity,
        "warnings": result.warnings,
    }


# Map tool names to handlers
_TOOL_HANDLERS = {
    "generate_video": _handle_generate_video,
    "runway_generate_video": _handle_generate_video,  # Backward compat alias
    "elevenlabs_text_to_speech": _handle_elevenlabs_tts,
    "deepgram_transcribe": _handle_deepgram_transcribe,
    "content_safety_check": _handle_content_safety_check,
}


# ─── MCP Protocol Interface ─────────────────────────────────────────

class MCPToolServer:
    """MCP-compliant tool server for ClipPilot Lite.

    Implements the standard MCP protocol methods:
    - initialize(): Exchange capabilities
    - tools_list(): Return available tools with schemas
    - tools_call(): Execute a tool by name

    This follows the JSON-RPC 2.0 pattern taught in Week 9.
    """

    SERVER_INFO = {
        "name": "clippilot-tools",
        "version": "1.0.0",
    }

    CAPABILITIES = {
        "tools": {"listChanged": False},
    }

    def initialize(self, client_info: dict | None = None) -> dict:
        """Handle MCP initialize request.

        Args:
            client_info: Client identification (name, version)

        Returns:
            Server info and capabilities
        """
        logger.info(f"MCP initialize from client: {client_info}")
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": self.SERVER_INFO,
            "capabilities": self.CAPABILITIES,
        }

    def tools_list(self) -> list[dict]:
        """Handle tools/list request.

        Returns:
            List of available tools with their input schemas
        """
        logger.info(f"MCP tools/list — returning {len(TOOL_REGISTRY)} tools")
        return TOOL_REGISTRY

    def tools_call(self, name: str, arguments: dict | None = None) -> dict:
        """Handle tools/call request.

        Args:
            name: Tool name to execute
            arguments: Tool arguments matching the inputSchema

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool name is unknown
            Exception: If tool execution fails
        """
        if name not in _TOOL_HANDLERS:
            available = ", ".join(_TOOL_HANDLERS.keys())
            raise ValueError(f"Unknown tool: {name}. Available: {available}")

        arguments = arguments or {}
        logger.info(f"MCP tools/call: {name} with {list(arguments.keys())}")

        try:
            result = _TOOL_HANDLERS[name](arguments)
            logger.info(f"MCP tool {name} succeeded")
            return {"content": [{"type": "text", "text": json.dumps(result)}]}
        except Exception as e:
            logger.error(f"MCP tool {name} failed: {str(e)}")
            return {
                "content": [{"type": "text", "text": json.dumps({"error": str(e)})}],
                "isError": True,
            }

    def handle_jsonrpc(self, request: dict) -> dict:
        """Handle a JSON-RPC 2.0 request (full protocol implementation).

        Args:
            request: JSON-RPC 2.0 request object

        Returns:
            JSON-RPC 2.0 response object
        """
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id")

        try:
            if method == "initialize":
                result = self.initialize(params.get("clientInfo"))
            elif method == "tools/list":
                result = {"tools": self.tools_list()}
            elif method == "tools/call":
                result = self.tools_call(
                    name=params.get("name", ""),
                    arguments=params.get("arguments"),
                )
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }

            return {"jsonrpc": "2.0", "id": req_id, "result": result}

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": str(e)},
            }


# Singleton instance
mcp_server = MCPToolServer()
