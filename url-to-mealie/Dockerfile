FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
ENV PYTHONPATH="/app/src:${PYTHONPATH}"

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
        ffmpeg \
        wget \
        curl \
        build-essential \
        cmake \
        gcc \
        g++ \
        python3-dev \
        enchant-2 \
        libenchant-2-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies with optimizations
# ENV CMAKE_ARGS="-DGGML_CUDA=on -DLLAMA_CUBLAS=on -DCMAKE_CUDA_ARCHITECTURES=all-major"
# ENV FORCE_CMAKE=1
ENV CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS -DLLAMA_CUBLAS=OFF"
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/models /var/log && \
    touch /var/log/url-to-mealie.log && \
    chmod 666 /var/log/url-to-mealie.log

# Download parsing model
RUN wget -q https://huggingface.co/unsloth/gemma-3-1b-it-GGUF/resolve/main/gemma-3-1b-it-BF16.gguf \
    -O /app/models/parsing_model.gguf

# Copy application code
COPY . .

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:6999/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "6999"]
