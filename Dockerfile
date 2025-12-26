# Multi-stage Dockerfile for SentinelShare
# Stage 1: Build Frontend
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --include=dev

# Copy frontend source
COPY frontend/ ./

# Build frontend
RUN npm run build

# Stage 2: Setup Python Backend
FROM python:3.12-slim AS backend-builder

WORKDIR /app

# Install system dependencies required for Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 3: Final Production Image
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy backend code
COPY backend/ ./backend/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Copy frontend build from frontend-builder
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Copy entrypoint script
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Create data directory for application data (receipts, logs)
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
