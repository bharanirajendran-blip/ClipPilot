"""MCP Client for the worker pipeline.

Instead of calling services directly, the worker uses this MCP client
to call tools through the MCP protocol. This demonstrates the
MCP architecture pattern from the course:

    Worker (Agent Runtime)
         ↓  mcp_client.call_tool("runway_generate_video", {...})
    MCP Client (this file)
         ↓  tools/call
    MCP Server (server.py)
         ↓  delegates to
    Service Layer (runway_service.py, etc.)

In production, the MCP server could run as a separate process
connected via stdio or HTTP. Here we use in-process calls
for simplicity while maintaining the protocol interface.
"""

import base64
import time
from app.mcp.server import mcp_server
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MCPClient:
    """MCP client that communicates with the local MCP tool server.

    Follows the MCP client lifecycle:
    1. initialize() — exchange capabilities
    2. list_tools() — discover available tools
    3. call_tool() — execute tools by name
    """

    def __init__(self):
        self._initialized = False
        self._available_tools: list[dict] = []

    def initialize(self) -> dict:
        """Initialize the MCP connection.

        Returns:
            Server capabilities and info
        """
        result = mcp_server.initialize(
            client_info={"name": "clippilot-worker", "version": "1.0.0"}
        )
        self._initialized = True
        self._available_tools = mcp_server.tools_list()
        logger.info(
            f"MCP client initialized — {len(self._available_tools)} tools available: "
            f"{[t['name'] for t in self._available_tools]}"
        )
        return result

    def list_tools(self) -> list[dict]:
        """List available MCP tools.

        Returns:
            Tool definitions with input schemas
        """
        if not self._initialized:
            self.initialize()
        return self._available_tools

    def call_tool(self, name: str, arguments: dict | None = None) -> dict:
        """Call an MCP tool by name.

        Args:
            name: Tool name (e.g., "runway_generate_video")
            arguments: Tool arguments matching the inputSchema

        Returns:
            Parsed tool result (dict)

        Raises:
            Exception: If tool call fails
        """
        if not self._initialized:
            self.initialize()

        start_time = time.time()
        logger.info(f"MCP call: {name}")

        result = mcp_server.tools_call(name=name, arguments=arguments or {})

        elapsed = time.time() - start_time

        # Parse the content
        content = result.get("content", [])
        is_error = result.get("isError", False)

        if is_error:
            error_text = content[0]["text"] if content else "Unknown error"
            logger.error(f"MCP tool {name} returned error in {elapsed:.1f}s: {error_text}")
            raise Exception(f"MCP tool {name} failed: {error_text}")

        import json
        parsed = json.loads(content[0]["text"]) if content else {}
        logger.info(f"MCP tool {name} completed in {elapsed:.1f}s")

        return parsed

    def generate_video(self, prompt: str, duration: int = 10) -> bytes:
        """Convenience: Generate video via MCP tool.

        Args:
            prompt: Visual scene description
            duration: Clip duration in seconds

        Returns:
            Raw video bytes
        """
        result = self.call_tool("runway_generate_video", {
            "prompt": prompt,
            "duration": duration,
        })
        return base64.b64decode(result["data_base64"])

    def text_to_speech(self, text: str) -> bytes:
        """Convenience: Generate speech via MCP tool.

        Args:
            text: Narration text

        Returns:
            MP3 audio bytes
        """
        result = self.call_tool("elevenlabs_text_to_speech", {"text": text})
        return base64.b64decode(result["data_base64"])

    def transcribe(self, audio_bytes: bytes) -> list[dict]:
        """Convenience: Transcribe audio via MCP tool.

        Args:
            audio_bytes: Raw audio data

        Returns:
            List of words with timestamps
        """
        result = self.call_tool("deepgram_transcribe", {
            "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
        })
        return result["words"]

    def check_safety(self, text: str, check_type: str = "input") -> dict:
        """Convenience: Check content safety via MCP tool.

        Args:
            text: Content to check
            check_type: "input" or "output"

        Returns:
            Safety result dict with is_safe, category, reason
        """
        return self.call_tool("content_safety_check", {
            "text": text,
            "check_type": check_type,
        })


# Singleton
mcp_client = MCPClient()
