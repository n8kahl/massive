#!/usr/bin/env sh
set -e

# IMPORTANT: Do NOT set MCP_TRANSPORT here.
# Massive defaults to STDIO transport.  [oai_citation:2‡GitHub](https://github.com/massive-com/mcp_massive?utm_source=chatgpt.com)
# mcp-proxy will expose SSE over HTTP for Chat-data.  [oai_citation:3‡GitHub](https://github.com/punkpeye/mcp-proxy?utm_source=chatgpt.com)

# Railway injects PORT automatically
PORT="${PORT:-8080}"

# Expose SSE at /mcp (so your Chat-data URL can be .../mcp)
# --apiKey protects the endpoint (Chat-data will send X-API-Key).  [oai_citation:4‡GitHub](https://github.com/punkpeye/mcp-proxy?utm_source=chatgpt.com)
npx -y mcp-proxy \
  --server sse \
  --endpoint /mcp \
  --port "$PORT" \
  --apiKey "$MCP_PROXY_API_KEY" \
  --shell \
  "MASSIVE_API_KEY=$MASSIVE_API_KEY uv run mcp_massive"
