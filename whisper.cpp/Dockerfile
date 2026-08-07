ARG WHISPER_CUDA=off
ARG UBUNTU_VERSION=22.04
ARG CUDA_VERSION=13.3.1
ARG CUDA_DOCKER_ARCH=all

FROM docker.io/nvidia/cuda:${CUDA_VERSION}-devel-ubuntu${UBUNTU_VERSION} AS builder

ARG WHISPER_CUDA
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    ccache \
    cmake \
    git \
    ca-certificates \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

ENV CUDA_MAIN_VERSION=13.0
ENV LD_LIBRARY_PATH=/usr/local/cuda-${CUDA_MAIN_VERSION}/compat:$LD_LIBRARY_PATH

# Copy source code
COPY ./whisper.cpp .

# Build whisper-server target
RUN if [ "${WHISPER_CUDA}" = "on" ]; then \
      cmake -B build \
        -DWHISPER_BUILD_SERVER=ON \
        -DGGML_CUDA=1 \
        -DCMAKE_CUDA_ARCHITECTURES="75;80;86;90" \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_RPATH="\$ORIGIN" \
        -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON . ; \
    else \
      cmake -B build \
        -DWHISPER_BUILD_SERVER=ON \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_RPATH="\$ORIGIN" \
        -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON . ; \
    fi && \
    cmake --build build --config Release --target whisper-server -j$(nproc)

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

# Copy binary and all compiled shared libraries from builder stage
COPY --from=builder /build/build/bin/whisper-server /app/whisper-server
COPY --from=builder /build/build/bin/*.so* /app/

# Create directory for models
RUN mkdir -p /app/models

# Expose port for whisper-server
EXPOSE ${WHISPER_PORT}

# Default entry point
CMD ["./whisper-server"]