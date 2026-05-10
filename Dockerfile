# =========================
# Builder stage
# =========================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project files
COPY . .

# Install dependencies
RUN uv sync

# Build dist artifacts
RUN uv run compile && ls -la dist


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

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install runtime Python dependencies
RUN uv sync --frozen

# Copy built application
COPY --from=builder /build/dist ./app
COPY --from=builder /build/app/main.py ./app

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

# Start services
CMD ["sh", "-c", "nginx && uvicorn app.main:app --host 0.0.0.0 --port 43210"]