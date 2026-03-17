# Praxis CO Platform — Production Container
# Optimized for Cloud Run free tier (256MB RAM, cold starts)

FROM python:3.12-slim AS base

# Prevent Python from buffering stdout/stderr (important for Cloud Run logs)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies for cryptography package
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files for install
COPY pyproject.toml README.md ./
COPY src/ src/

# Install as a regular package (not editable)
RUN pip install --no-cache-dir .

# Create data directories
RUN mkdir -p /data /data/keys

# Environment defaults for Cloud Run
ENV PRAXIS_DEV_MODE=false
ENV DATABASE_URL=sqlite:////data/praxis.db
ENV PRAXIS_KEY_DIR=/data/keys
ENV PRAXIS_KEY_ID=default
ENV PRAXIS_API_HOST=0.0.0.0
ENV PRAXIS_API_PORT=8080
ENV PRAXIS_CORS_ORIGINS=*
ENV LOG_LEVEL=INFO
ENV LOG_FORMAT=json

# Cloud Run sends SIGTERM for graceful shutdown
STOPSIGNAL SIGTERM

EXPOSE 8080

# Health check (Cloud Run uses HTTP health checks)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Start with uvicorn (AsyncLocalRuntime compatible)
CMD ["python", "-c", "\
from praxis.api.app import create_app; \
import uvicorn; \
app = create_app(); \
uvicorn.run(app._gateway.app, host='0.0.0.0', port=8080, log_level='info', workers=1) \
"]
