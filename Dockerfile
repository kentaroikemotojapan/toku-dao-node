FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# 1. 必要な開発パッケージと Python 環境を一括導入
RUN apt-get update && apt-get install -y \
    build-essential \
    clang \
    llvm \
    libbpf-dev \
    linux-headers-generic \
    cmake \
    git \
    curl \
    iproute2 \
    net-tools \
    python3 \
    python3-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# 2. pybind11 と requirements.txt の依存ライブラリを一括インストール
RUN pip3 install --no-cache-dir pybind11 -r requirements.txt

# 3. and_geometry_cpp.so (Python用 C++ 19.87μs Core) をコンテナ内でビルド
RUN g++ -O3 -shared -std=c++17 -fPIC \
    $(python3 -m pybind11 --includes) \
    and_geometry_core.cpp \
    -o and_geometry_cpp$(python3-config --extension-suffix)

CMD ["python3", "yokohama_sovereign_twin_demo.py"]