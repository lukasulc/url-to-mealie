# Recipe Parser App

This application extracts recipe information from Social Media videos using audio transcription and LLM-based parsing.

## Setup Instructions

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Download the LLM model:

   - Visit [TheBloke/Gemma-3b-it-GGUF](https://huggingface.co/TheBloke/Gemma-3b-it-GGUF)
   - Download the `gemma-3b-it-q4_k_m.gguf` file
   - Place the downloaded file in the `models` directory inside the `url-to-mealie` folder
   - The final path should be: `url-to-mealie/models/parsing_model.gguf`

3. Set up environment variables:

   Required:

   - `MEALIE_BASE_URL`: Your Mealie instance URL (e.g., "http://localhost:9000")
   - `MEALIE_TOKEN`: Your Mealie API token

   Optional:

   - `MODEL_DIR`: Override the default models directory path

4. Run the application:

   Using Python directly:

   ```bash
   cd src
   python main.py
   ```

   Or using Docker:

   ```bash
   docker-compose up --build
   ```

## Model Options

The application uses Gemma 3B for recipe parsing. You can use different GGUF model variants based on your needs:

- `gemma-3b-it-q4_k_m.gguf`: Good balance of size and quality (default)
- `gemma-3b-it-q3_k_m.gguf`: Smaller size, slightly lower quality
- `gemma-3b-it-q5_k_m.gguf`: Larger size, slightly better quality

The model should be renamed to `parsing_model.gguf` when placed in the models directory.

GPU Acceleration (Work in Progress):

- GPU acceleration with CUDA is being implemented
- The application attempts to use GPU layers if available
- Current GPU support is experimental
- You can monitor GPU usage attempts in the application logs

## Features

- Transcribes audio from Social Media videos using Whisper
- Extracts recipe information using Gemma 2B
- Parses ingredients, instructions, and metadata
- Integrates with Mealie recipe manager including thumbnails
- Preserves original video URL and caption
- Includes spell checking and validation
- Supports GPU acceleration for faster processing
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
