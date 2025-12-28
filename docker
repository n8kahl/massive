FROM python:3.12-slim

# Node for mcp-proxy
RUN apt-get update && apt-get install -y curl ca-certificates && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python tooling
RUN pip install --no-cache-dir uv

# Copy your repo
COPY . /app

# Install Massive MCP package (repo uses pyproject; installs server entrypoints)
RUN uv pip install --system -e .

# Install the SSE/HTTP gateway
RUN npm i -g mcp-proxy

COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
