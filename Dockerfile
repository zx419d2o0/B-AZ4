# =========================
# Builder stage
# =========================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (recommended official binary install)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:$PATH"

# Copy full project
COPY . .

# Install dependencies using uv
RUN uv sync

# Run compile step (generate dist)
RUN ls -la
# RUN uv run python -c "from scripts.commands import compile; compile()" \
#     && ls -la dist


# =========================
# Runtime stage
# =========================
# FROM python:3.12-slim

# WORKDIR /app

# # Install minimal runtime dependencies
# RUN apt-get update && apt-get install -y \
#     nginx \
#     curl \
#     && rm -rf /var/lib/apt/lists/*

# # Install uv (binary install)
# RUN curl -LsSf https://astral.sh/uv/install.sh | sh
# ENV PATH="/root/.local/bin:$PATH"

# # Copy dependency definition only
# COPY pyproject.toml uv.lock* ./

# # Install ONLY runtime dependencies
# RUN uv sync --frozen

# # Copy built artifacts from builder
# COPY --from=builder /build/dist ./dist

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["sh", "-c", "nginx && uvicorn app.main:app --host 0.0.0.0 --port 43210"]