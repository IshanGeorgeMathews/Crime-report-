# Kerala Police Intelligence Platform — Backend API
# Build context must be the project root (Code/), not the backend/ subdirectory.
# The root docker-compose.yml sets context: . and dockerfile: backend/Dockerfile.

FROM python:3.11-slim

WORKDIR /app

# System dependencies for native extensions (numpy, torch, neo4j driver, docx)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (cached layer — copy requirements first)
COPY backend/requirements.txt ./requirements_backend.txt
COPY requirements.txt ./requirements_root.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements_backend.txt && \
    pip install --no-cache-dir -r requirements_root.txt

# Copy backend application code
COPY backend/app/ ./app/

# Copy scripts/
COPY scripts/ ./scripts/

# Create uploads directory
RUN mkdir -p /app/uploads /app/pp_templates

# Health check — verify the API is alive
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/openapi.json || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
