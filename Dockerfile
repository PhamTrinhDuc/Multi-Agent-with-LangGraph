
################ 1. Base image ################
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

################# 2. Builder stage - install dependencies #################
FROM base AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
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

# Copy dependency files trước để tận dụng Docker layer cache
COPY --chown=appuser pyproject.toml ./

# Cài dependencies vào venv tại .venv
RUN uv venv .venv && \
    uv pip install --python .venv/bin/python -r pyproject.toml

# Copy source code
COPY --chown=appuser . .

##################### 3. Runtime stage #####################
FROM base AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
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

# Kích hoạt venv
ENV PATH="/home/appuser/app/.venv/bin:$PATH" \
    PYTHONPATH="/home/appuser/app:$PYTHONPATH"

# Health check — endpoint /health định nghĩa trong app.py
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

LABEL maintainer="duc78240@email.com" \
    version="1.0" \
    description="E-commerce Chatbot API with LangGraph"

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

# Build: docker build -f Dockerfile -t ecommerce-chatbot:1.0 .