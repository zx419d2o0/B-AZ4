FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (nginx)
RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

# Install poetry

RUN pip install --no-cache-dir poetry

# Copy poetry files

COPY pyproject.toml poetry.lock* ./

# Install dependencies

RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY app /app/app

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Expose ports (nginx entrypoint)
EXPOSE 80

# Start nginx + uvicorn
CMD sh -c "nginx && uvicorn app.main:app --host 0.0.0.0 --port 43210"