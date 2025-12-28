FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy project
COPY . .

# Install deps (works for pyproject/uv.lock or requirements.txt)
# Prefer uv sync if uv.lock exists; otherwise fall back.
RUN if [ -f "uv.lock" ] || [ -f "pyproject.toml" ]; then uv sync --frozen || uv sync; \
    elif [ -f "requirements.txt" ]; then pip install --no-cache-dir -r requirements.txt; \
    else echo "No dependency file found" && exit 1; fi

ENV PYTHONUNBUFFERED=1

# Railway provides PORT; default for local
ENV PORT=8000
ENV HOST=0.0.0.0
ENV MCP_TRANSPORT=streamable-http

CMD ["uv", "run", "entrypoint_railway.py"]
