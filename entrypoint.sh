#!/bin/bash
set -e

# Start Nginx server
echo "[entrypoint] Launching Nginx..."
nginx

# Start FastAPI application with Uvicorn as PID 1
echo "[entrypoint] Launching FastAPI via uvicorn..."
exec cd /app && python -m uvicorn main:app --host 0.0.0.0