# =========================
# Single stage build + runtime
# =========================
FROM ubuntu:24.04

WORKDIR /tmp

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential gcc g++ \
    python3 python3-pip \
    nginx \
    libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project
COPY . .

# Install dependencies and build
RUN uv sync && uv run compile
RUN cd app && uv run init


WORKDIR /app

RUN cp -r /tmp/dist/. /app/
RUN mv /tmp/entrypoint.sh /entrypoint.sh
RUN mv /tmp/nginx.conf /etc/nginx/nginx.conf
RUN rm -rf /tmp/* /app/*.so
RUN ls -la /app
RUN ls -la /tmp

# Ensure entrypoint executable
RUN chmod +x /entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]