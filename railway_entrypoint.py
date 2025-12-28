import os

# Force FastMCP to bind publicly (Railway needs this)
os.environ["FASTMCP_HOST"] = "0.0.0.0"
os.environ["FASTMCP_PORT"] = os.environ.get("PORT", "8000")

# Ensure you're running the right transport/path
os.environ.setdefault("MCP_TRANSPORT", "streamable-http")
os.environ.setdefault("FASTMCP_STREAMABLE_HTTP_PATH", "/mcp")

# Now import and run the existing entrypoint
import entrypoint  # noqa: F401
