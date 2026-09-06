# Recipe Parser App

This application extracts recipe information from Social Media videos using audio transcription and LLM-based parsing.

## Setup Instructions

1. Install Python dependencies

   ```bash
   pip install -r requirements.txt
   ```

2. Project architecture and models

   The model servers are provided as separate services. This repository contains the application plus an optional model stack:
   - `llm` (optional): builds and runs the llama.cpp HTTP server (see `./llama.cpp`)
   - `whisper` (optional): builds and runs the whisper.cpp HTTP server (see `./whisper.cpp`)
   - `url-to-mealie`: the recipe parser web app (this folder)

   Models should live in the top-level `models/` directory (shared volume).

   The model services mount `./models` into their containers at `/app/models` (read-only).

3. Environment variables

   Required (for the parser):
   - `MEALIE_BASE_URL`: Your Mealie instance URL (e.g., "http://localhost:9000")
   - `MEALIE_TOKEN`: Your Mealie API token

   The application connects to the Docker service names `http://llm` and `http://whisper` on the internal container network. Their host-facing ports are configured only in `docker-compose.models.yaml`.

4. Running the project with Docker (recommended)

   The model and application stacks share the external Docker network named `url-to-mealie`. Create it once before starting either stack:

   ```bash
   docker network create ${DOCKER_NETWORK_NAME:-url-to-mealie}
   ```

   If you use a different network name, set `DOCKER_NETWORK_NAME` for both Compose commands.

   Start the model services:

   ```bash
   docker compose -f docker-compose.models.yaml up --build
   ```

   Start the application in a second terminal:

   ```bash
   docker compose -f docker-compose.yaml up --build
   ```

   To change ports exposed on the host, set `LLAMA_HOST_PORT` or `WHISPER_HOST_PORT` when starting `docker-compose.models.yaml`. The application does not need to change because it uses the internal service names on port 80.

## Features

- Transcribes audio from Social Media videos using Whisper
- Extracts recipe information using an external LLM service (llama.cpp)
- Parses ingredients, instructions, and metadata
- Integrates with Mealie recipe manager including thumbnails
- Preserves original video URL and caption
- Includes spell checking and validation
- Fallback to basic parsing if LLM fails
- Health monitoring and memory usage tracking
- Docker support for easy deployment

## API Endpoints

- `GET /`: Web interface for submitting videos
- `POST /submit`: Process a video and add to Mealie
- `GET /health`: Health check endpoint with memory stats

## Environment Setup

The application can be run either directly with Python or using Docker:

### Docker Setup

1. Configure environment variables in `.env` file
2. Run `docker-compose up --build`
3. Access the web interface at http://localhost:8000

### Python Setup

1. Install dependencies with `pip install -r requirements.txt`
2. Download the Gemma model as described above
3. Configure environment variables
4. Run `python src/main.py`

## Configuration

Required Environment Variables:

- `MEALIE_BASE_URL`: Your Mealie instance URL
- `MEALIE_TOKEN`: Your Mealie API token

Optional Settings:

- `MODEL_DIR`: Custom path for model storage
- Docker settings can be adjusted in docker-compose.yaml

## Development

### Code Style

This project uses the Black code formatter for consistent Python code styling. To format the code:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run Black formatter
black .
```

The Black configuration is set to:

- Line length: 88 characters (default)
- Target version: Python 3.8+
- Excludes: `.venv`, `build`, `dist`
