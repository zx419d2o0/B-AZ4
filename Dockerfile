# =========================
# Builder stage
# =========================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies (needed for poetry install / compile)
RUN apt-get update && apt-get install -y \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install --no-cache-dir poetry

# Copy project files (full source needed for compile)
COPY . .

# Install dependencies
RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi --no-root

# Run compile step (generate dist)
RUN poetry run compile && ls -la dist


# =========================
# Runtime stage
# =========================
FROM python:3.12-slim

WORKDIR /app

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y nginx \
    && rm -rf /var/lib/apt/lists/*

# Install poetry (only for runtime deps install)
RUN pip install --no-cache-dir poetry

# Copy dependency definition only
COPY pyproject.toml poetry.lock* ./

# Install ONLY runtime dependencies (no build tools)
RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi --only main

# Copy built artifacts from builder
COPY --from=builder /build/dist/app ./app

# Copy app needed for uvicorn runtime
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["sh", "-c", "nginx && uvicorn app.main:app --host 0.0.0.0 --port 43210"]