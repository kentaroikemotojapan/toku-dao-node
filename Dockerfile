FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir pybind11 web3 requests fastapi uvicorn pytest

COPY . .

RUN python setup.py build_ext --inplace

CMD ["python", "container_node.py"]