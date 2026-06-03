# ============================================
# Vartovii Trust Agent — Production Dockerfile
# ============================================
# Multi-stage build: Python 3.12 + Node.js 20 (for MongoDB MCP Server)
# Deploys to Google Cloud Run

FROM python:3.12-slim AS base

# Install Node.js 20 (required for mongodb-mcp-server via npx)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify installations
RUN python --version && node --version && npm --version

# Set working directory
WORKDIR /app

# Copy dependency files first (Docker layer caching)
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[api]" 2>/dev/null || \
    pip install --no-cache-dir \
    "google-adk==2.0.0" \
    "python-dotenv>=1.0.0" \
    "pymongo[srv]>=4.7.0" \
    "mcp>=1.0.0" \
    "fastapi>=0.115.0" \
    "uvicorn>=0.30.0"

# Pre-install MongoDB MCP Server globally (faster cold start)
RUN npx -y mongodb-mcp-server --version 2>/dev/null || true

# Copy application code
COPY agent/ ./agent/
COPY services/ ./services/
COPY api/ ./api/
COPY web/ ./web/
COPY scripts/ ./scripts/
COPY README.md LICENSE ./

# Environment defaults (overridden at runtime)
ENV PORT=8080
ENV GEMINI_MODEL_PROFILE=stable
ENV ADK_ENABLED=true
ENV MONGODB_ENABLED=true
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# Start the combined server
CMD ["python", "-m", "uvicorn", "api.dashboard_api:app", "--host", "0.0.0.0", "--port", "8080"]
