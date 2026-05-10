# =========================
# Builder stage
# =========================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install dependencies
RUN uv sync

# Build dist artifacts
RUN uv run compile


# =========================
# Runtime stage
# =========================
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


# Copy virtual environment
COPY --from=builder /build/.venv /.venv
RUN ls -la /

# Use virtual environment binaries
ENV PATH="/.venv/bin:$PATH"
RUN which python

# Copy built application
COPY --from=builder /build/dist/app/. /app/
COPY --from=builder /build/app/main.py /app
RUN ls -la /app

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

# Start services
CMD ["sh", "-c", "nginx && python -m uvicorn app.main:app --host 0.0.0.0"]