import os
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount

# Import the FastMCP instance that already has all your tools registered
from mcp_massive.server import poly_mcp  # this exists in your server.py

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))

    # What transport to expose publicly
    # chat-data.com may try SSE; streamable-http is newer.
    transport = os.environ.get("MCP_TRANSPORT", "streamable-http").strip().lower()

    # Build an ASGI app that exposes the MCP server at the standard paths.
    # Per MCP Python SDK defaults:
    # - Streamable HTTP: /mcp
    # - SSE:            /sse
    #  [oai_citation:1‡GitHub](https://github.com/modelcontextprotocol/python-sdk?utm_source=chatgpt.com)
    if transport in ("sse",):
        app = Starlette(routes=[Mount("/", app=poly_mcp.sse_app())])
    else:
        # streamable-http (default)
        app = Starlette(routes=[Mount("/", app=poly_mcp.streamable_http_app())])

    uvicorn.run(app, host=host, port=port, log_level="info")
