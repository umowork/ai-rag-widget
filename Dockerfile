# ──────────────────────────────────────────────────────
# Dockerfile — AI RAG Widget
#
# Multi-stage build with optional heavy dependencies.
# ──────────────────────────────────────────────────────

FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --user \
    sentence-transformers \
    openai \
    python-docx \
    -r requirements.txt

# ─── Runtime ─────────────────────────────────────────

FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p chroma_db uploads

# Set PYTHONPATH so backend modules resolve
ENV PYTHONPATH=/app/backend

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python3 -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5)" || exit 1

RUN useradd --create-home appuser
USER appuser

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
