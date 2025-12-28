import os
import json
import uvicorn

from mcp_massive.server import poly_mcp, massive_query  # <-- import massive_query too


def json_response(status_code: int, payload: dict):
    body = json.dumps(payload).encode("utf-8")
    headers = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode("utf-8")),
    ]
    return status_code, headers, body


async def read_body(receive) -> bytes:
    chunks = []
    while True:
        message = await receive()
        if message["type"] != "http.request":
            continue
        chunks.append(message.get("body", b""))
        if not message.get("more_body", False):
            break
    return b"".join(chunks)


def make_wrapped_app(mcp_asgi_app):
    async def app(scope, receive, send):
        if scope["type"] != "http":
            # Hand off non-HTTP to MCP app
            await mcp_asgi_app(scope, receive, send)
            return

        path = scope.get("path", "")
        method = (scope.get("method") or "GET").upper()

        # ---- Health endpoints (always 200) ----
        if path in ("/", "/healthz", "/health"):
            status, headers, body = json_response(200, {"status": "ok"})
            await send({"type": "http.response.start", "status": status, "headers": headers})
            await send({"type": "http.response.body", "body": body})
            return

        # ---- myGPT Actions endpoint (REST JSON) ----
        if path == "/api/market_query":
            if method != "POST":
                status, headers, body = json_response(
                    405, {"ok": False, "error": "Method not allowed. Use POST."}
                )
                await send({"type": "http.response.start", "status": status, "headers": headers})
                await send({"type": "http.response.body", "body": body})
                return

            raw = await read_body(receive)
            try:
                payload = json.loads(raw.decode("utf-8") if raw else "{}")
            except Exception:
                status, headers, body = json_response(
                    400, {"ok": False, "error": "Invalid JSON body"}
                )
                await send({"type": "http.response.start", "status": status, "headers": headers})
                await send({"type": "http.response.body", "body": body})
                return

            provider = (payload.get("provider") or "").strip()
            operation = (payload.get("operation") or "").strip()
            params = payload.get("params") or {}

            if not provider or not operation:
                status, headers, body = json_response(
                    400,
                    {
                        "ok": False,
                        "error": "Missing required fields: provider, operation",
                    },
                )
                await send({"type": "http.response.start", "status": status, "headers": headers})
                await send({"type": "http.response.body", "body": body})
                return

            try:
                data = massive_query(provider=provider, operation=operation, params=params)

                # Treat router “Error: …” strings as 400 for clarity
                if isinstance(data, str) and data.lower().startswith("error"):
                    status, headers, body = json_response(
                        400,
                        {
                            "ok": False,
                            "provider": provider,
                            "operation": operation,
                            "error": data,
                        },
                    )
                else:
                    status, headers, body = json_response(
                        200,
                        {
                            "ok": True,
                            "provider": provider,
                            "operation": operation,
                            "data": str(data),
                        },
                    )

                await send({"type": "http.response.start", "status": status, "headers": headers})
                await send({"type": "http.response.body", "body": body})
                return

            except Exception as e:
                status, headers, body = json_response(
                    500, {"ok": False, "error": f"Server error: {e}"}
                )
                await send({"type": "http.response.start", "status": status, "headers": headers})
                await send({"type": "http.response.body", "body": body})
                return

        # ---- Everything else goes to MCP ASGI app (e.g., /mcp) ----
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
        mcp_app = poly_mcp.streamable_http_app()

    app = make_wrapped_app(mcp_app)

    uvicorn.run(app, host=host, port=port, log_level="info")
