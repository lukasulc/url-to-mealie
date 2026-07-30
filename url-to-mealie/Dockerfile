FROM python:3.14-slim

WORKDIR /app
COPY requirements.txt .
ENV PYTHONPATH="/app/src:${PYTHONPATH}"

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
        ffmpeg \
        curl \
        enchant-2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /var/log && \
    touch /var/log/url-to-mealie.log && \
    chmod 666 /var/log/url-to-mealie.log

# Models will be mounted from host

# Copy application code
COPY . .

# Startup command is defined in docker-compose.yaml so service configuration stays in one place.
