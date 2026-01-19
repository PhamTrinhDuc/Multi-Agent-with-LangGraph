
################ 1. Base image - lightweight Python image ################
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \ 
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

################# 2. Builder stage - install dependencies #################
FROM base AS builder

# Dev tools để build C extensions nếu cần
# psycopg2-binary, numpy, cryptography cần các tools này
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libpq-dev \
        libffi-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Tạo non-root user
RUN useradd --create-home appuser && \
    mkdir -p /home/appuser/app && \
    chown -R appuser:appuser /home/appuser

USER appuser
WORKDIR /home/appuser/app

# Cài uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/appuser/.local/bin:$PATH"


# Copy dependency files trước (cache layer này khi code thay đổi)
COPY --chown=appuser pyproject.toml uv.lock ./

# Cài dependencies
RUN uv sync --frozen --no-dev --compile-bytecode

# Copy source code
COPY --chown=appuser . .

##################### 3. Runtime stage #####################
FROM base AS runtime

# Chỉ cài runtime libs nếu thực sự cần (ví dụ: psycopg2, pillow...)
# Nếu pure Python thì bỏ hẳn block này
# Cài ONLY runtime libraries (không cần build-essential)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        libgomp1 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Tạo non-root user
RUN useradd --create-home appuser && \
    mkdir -p /home/appuser/app && \
    chown -R appuser:appuser /home/appuser

USER appuser
WORKDIR /home/appuser/app

# Copy virtual environment và source code từ builder
COPY --from=builder --chown=appuser:appuser /home/appuser/app .
# COPY --chown=appuser:appuser ../data/dsm-5-cac-tieu-chuan-chan-doan.pdf /app/data/
# COPY --chown=appuser:appuser ../data/dsm5_chunks.json /app/data/ 2>/dev/null || true

# Kích hoạt venv
ENV PATH="/home/appuser/app/.venv/bin:$PATH" \
    PYTHONPATH="/home/appuser/app:$PYTHONPATH"

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/liveness')" || exit 1

LABEL maintainer="duc78240@email.com" \
    version="1.0" \
    description="Backend server for AI Chatbot Langchain"

# app port
EXPOSE 8000 

# Graceful shutdown với --timeout-graceful-shutdown
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-graceful-shutdown", "30"]

# cmd build image: docker build -f Dockerfile -t ai-agent:1.0 .