"""MCP HTTP transport routes.

Exposes the MCP tool server over HTTP via JSON-RPC 2.0,
following the Streamable HTTP transport from the MCP spec.

Endpoints:
    POST /mcp/rpc  — JSON-RPC 2.0 endpoint for MCP protocol messages
    GET  /mcp/tools — Convenience endpoint to list available tools (non-standard)
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.mcp.server import mcp_server
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.post("/rpc")
async def mcp_jsonrpc(request: Request) -> JSONResponse:
    """Handle MCP JSON-RPC 2.0 requests.

    Supports: initialize, tools/list, tools/call

    Args:
        request: Raw JSON-RPC 2.0 request

    Returns:
        JSON-RPC 2.0 response
    """
    try:
        body = await request.json()
        logger.info(f"MCP RPC request: {body.get('method', 'unknown')}")

        response = mcp_server.handle_jsonrpc(body)
        return JSONResponse(content=response)

    except Exception as e:
        logger.error(f"MCP RPC error: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"},
            },
            status_code=400,
        )


@router.get("/tools")
async def list_tools() -> dict:
    """List available MCP tools (convenience endpoint).

    Returns:
        Dict with tools list and count
    """
    tools = mcp_server.tools_list()
    return {"tools": tools, "count": len(tools)}
