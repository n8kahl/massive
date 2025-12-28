import os
import json
import uvicorn

from mcp_massive.server import poly_mcp  # your FastMCP instance with tools registered


def json_response(status_code: int, payload: dict):
    body = json.dumps(payload).encode("utf-8")
    headers = [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]
    return status_code, headers, body


def make_health_wrapped_app(mcp_asgi_app):
    async def app(scope, receive, send):
        # Health endpoints should always respond 200 so we can verify Railway routing.
        if scope["type"] == "http" and scope.get("path") in ("/", "/healthz", "/health"):
            status, headers, body = json_response(200, {"status": "ok"})
            await send({"type": "http.response.start", "status": status, "headers": headers})
            await send({"type": "http.response.body", "body": body})
            return

        # Everything else goes to MCP ASGI app
        await mcp_asgi_app(scope, receive, send)

    return app


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    transport = os.environ.get("MCP_TRANSPORT", "streamable-http").strip().lower()

    # Build the MCP ASGI app (SDK provides these)
    if transport == "sse":
        mcp_app = poly_mcp.sse_app()
    else:
        # default: streamable-http
        mcp_app = poly_mcp.streamable_http_app()

    app = make_health_wrapped_app(mcp_app)

    uvicorn.run(app, host=host, port=port, log_level="info")
