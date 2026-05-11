# =========================
# Builder stage
# =========================
FROM ubuntu:24.04 AS builder

WORKDIR /build

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install build tools and Python3, pip
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    python3 \
    python3-pip \
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
FROM ubuntu:24.04

WORKDIR /app

# Install runtime dependencies, Python3, pip, and nginx
RUN apt-get update && apt-get install -y \
    nginx \
    python3 \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
# RUN echo "alias ll='ls -alF'" >> ~/.bashrc

# Copy virtual environment
# COPY --from=builder /build/.venv /.venv
# RUN ls -la /

# Use virtual environment binaries
# ENV PATH="/.venv/bin:$PATH"
# RUN which python

# Copy built application
COPY pyproject.toml uv.lock /app/main.py /app/
COPY --from=builder /build/dist/app /app
RUN rm /app/*.so
RUN ls -la /app

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]