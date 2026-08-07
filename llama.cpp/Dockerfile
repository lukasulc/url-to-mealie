ARG LLAMA_CUDA=off
ARG UBUNTU_VERSION=22.04
ARG CUDA_VERSION=13.3.1

FROM docker.io/nvidia/cuda:${CUDA_VERSION}-devel-ubuntu${UBUNTU_VERSION} AS builder

ARG LLAMA_CUDA
WORKDIR /build

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      cmake \
      git \
      python3 \
      ca-certificates \
      libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ./llama.cpp .

RUN if [ "${LLAMA_CUDA}" = "on" ]; then \
      cmake -B build \
        -DLLAMA_BUILD_SERVER=ON \
        -DLLAMA_BUILD_UI=OFF \
        -DLLAMA_BUILD_TESTS=OFF \
        -DLLAMA_BUILD_EXAMPLES=OFF \
        -DLLAMA_BUILD_TOOLS=OFF \
        -DLLAMA_BUILD_APP=OFF \
        -DLLAMA_OPENSSL=OFF \
        -DLLAMA_BUILD_COMMON=ON \
        -DGGML_NATIVE=ON \
        -DGGML_CUDA=ON \
        -DCMAKE_BUILD_TYPE=Release . ; \
    else \
      cmake -B build \
        -DLLAMA_BUILD_SERVER=ON \
        -DLLAMA_BUILD_UI=OFF \
        -DLLAMA_BUILD_TESTS=OFF \
        -DLLAMA_BUILD_EXAMPLES=OFF \
        -DLLAMA_BUILD_TOOLS=OFF \
        -DLLAMA_BUILD_APP=OFF \
        -DLLAMA_OPENSSL=OFF \
        -DLLAMA_BUILD_COMMON=ON \
        -DGGML_NATIVE=ON \
        -DCMAKE_BUILD_TYPE=Release . ; \
    fi

RUN cmake --build build --config Release -j2

FROM docker.io/nvidia/cuda:${CUDA_VERSION}-runtime-ubuntu${UBUNTU_VERSION} AS runtime

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/build/bin/llama-server /app/llama-server
COPY --from=builder /build/build/bin/lib* /app/

RUN mkdir -p /app/models

EXPOSE ${LLAMA_ARG_PORT}

CMD ["./llama-server"]
