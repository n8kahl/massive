import os

# Import your existing server entry.
# One of these imports will match depending on how the repo is structured.
try:
    # common pattern
    from mcp_massive.__main__ import main
except Exception:
    try:
        from mcp_massive import main
    except Exception:
        # fallback: if upstream uses an entrypoint.py already
        from entrypoint import main  # type: ignore


if __name__ == "__main__":
    # Force network transport for hosted use
    os.environ.setdefault("MCP_TRANSPORT", "streamable-http")

    # Railway requires binding to the injected port
    os.environ.setdefault("HOST", "0.0.0.0")
    os.environ.setdefault("PORT", os.environ.get("PORT", "8000"))

    main()
