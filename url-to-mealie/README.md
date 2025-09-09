# Recipe Parser App

This application extracts recipe information from Social Media videos using audio transcription and LLM-based parsing.

## Setup Instructions

1. Install Python dependencies

   ```bash
   pip install -r requirements.txt
   ```

2. Project architecture and models

   The LLM is now provided as a separate service (llama.cpp server). This repository contains two main services:

   - `llm` (optional): builds and runs the llama.cpp HTTP server (see `./llama.cpp`)
   - `url-to-mealie`: the recipe parser web app (this folder)

   Models should live in the top-level `models/` directory (shared volume).

   The `llm` service mounts `./models` into the container at `/app/models` (read-only). Update `docker-compose.yaml` if you want a different path or filename.

3. Environment variables

   Required (for the parser):

   - `MEALIE_BASE_URL`: Your Mealie instance URL (e.g., "http://localhost:9000")
   - `MEALIE_TOKEN`: Your Mealie API token

   Parser-specific optional:

   - `LLM_SERVER_URL`: URL of the llama.cpp HTTP server (default: `http://llm:6998` when using docker-compose)

   LLM service (if you run it via `docker-compose`):

   - `PORT` (default `6998`)
   - `MODEL_PATH` (set in `docker-compose.yaml` environment or point to the model file inside `/app/models`)

4. Running the project with Docker (recommended)

   The repository includes a `docker-compose.yaml` which defines two services: `llm` and `url-to-mealie`.

   - If you want the stack fully self-contained, leave `llm` enabled. It will build the server from `./llama.cpp` and serve the model from the shared `models/` volume.
   - If you already run a llama.cpp server elsewhere, you can comment out or remove the `llm` service and set `LLM_SERVER_URL` in the parser `.env` (or export it) to point to your existing server.

   Example: bring up both services locally

   ```bash
   docker-compose up --build
   ```

   Example: use your own LLM server and only run the parser

   ```bash
   # comment out llm service in docker-compose.yaml
   export LLM_SERVER_URL=http://your-llm-host:6998
   docker-compose up --build url-to-mealie
   ```

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
