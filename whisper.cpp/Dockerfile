FROM ubuntu:22.04 AS builder

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

# Copy source code
COPY ./whisper.cpp .

# Build whisper-server target
RUN cmake -B build \
    -DWHISPER_BUILD_SERVER=ON \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_RPATH="\$ORIGIN" \
    -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON
RUN cmake --build build --config Release --target whisper-server -j$(nproc)

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