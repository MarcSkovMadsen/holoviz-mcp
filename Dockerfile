# Multi-stage build for HoloViz MCP Server
# Updated: 2025-12-01
FROM python:3.11-slim AS builder

# Build argument for version (can be set during build)
ARG VERSION=0.0.0+docker
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_HOLOVIZ_MCP=${VERSION}

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Pixi
RUN curl -fsSL https://pixi.sh/install.sh | bash
ENV PATH="/root/.pixi/bin:${PATH}"

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy project files
COPY pixi.toml pixi.lock pyproject.toml README.md LICENSE.txt MANIFEST.in ./
COPY src/ ./src/
COPY .git/ ./.git/

# Install dependencies using Pixi
RUN pixi install --locked

# Install the package using pip (editable mode, will use git for version)
RUN pixi run -e default postinstall

# Clean up .git to reduce image size after installation
RUN rm -rf .git

# Final stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy Pixi installation from builder
COPY --from=builder /root/.pixi /root/.pixi
ENV PATH="/root/.pixi/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy only necessary application files from builder (exclude .git)
COPY --from=builder /app/src /app/src
COPY --from=builder /app/pyproject.toml /app/README.md /app/LICENSE.txt /app/
COPY --from=builder /app/pixi.toml /app/pixi.lock /app/
COPY --from=builder /app/.pixi /app/.pixi
# Add any other necessary runtime files here

# Expose default MCP port (if using HTTP transport)
EXPOSE 8000

# Set environment variables for MCP server
ENV HOLOVIZ_MCP_TRANSPORT=stdio \
    HOLOVIZ_MCP_HOST=0.0.0.0 \
    HOLOVIZ_MCP_PORT=8000 \
    HOLOVIZ_MCP_LOG_LEVEL=INFO \
    PYTHONUNBUFFERED=1

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Update documentation index if requested\n\
if [ "$UPDATE_DOCS" = "true" ]; then\n\
    echo "Updating documentation index..."\n\
    pixi run -e default holoviz-mcp update index\n\
fi\n\
\n\
# Start the MCP server\n\
exec pixi run -e default holoviz-mcp "$@"\n\
' > /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
