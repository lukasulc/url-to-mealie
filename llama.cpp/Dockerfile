# Use Ubuntu 22.04 base image with multi-stage build
FROM ubuntu:22.04 AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    ccache \
    cmake \
    git \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*


# Clone the llama.cpp repository directly
RUN git clone --depth 1 https://github.com/ggml-org/llama.cpp.git . --branch=b6428


# Build llama-server binary
RUN cmake -B build -DLLAMA_STATIC=ON
RUN cmake --build build --config Release -j$(nproc)

# Runtime stage
FROM ubuntu:22.04

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libcurl4 \
    libtbb12 \
    libgomp1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/build/bin/ /app/

COPY --from=builder /build/build/bin/libllama.so /app/libllama.so
COPY --from=builder /build/build/bin/libggml.so /app/libggml.so
COPY --from=builder /build/build/bin/libmtmd.so /app/libmtmd.so
COPY --from=builder /build/build/bin/libggml-cpu.so /app/libggml-cpu.so
COPY --from=builder /build/build/bin/libggml-base.so /app/libggml-base.so


# Create directory for models
RUN mkdir -p /app/models

# Expose port for llama-server HTTP server
EXPOSE 6998

# Default command runs llama-server with environment variables
CMD ["./llama-server"]
