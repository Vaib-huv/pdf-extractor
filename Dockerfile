# syntax=docker/dockerfile:1
FROM --platform=linux/amd64 python:3.11-slim

# Install tiny build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements & install
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Create runtime dirs
RUN mkdir -p /app/input /app/output
WORKDIR /app
COPY run.py .

ENTRYPOINT ["python", "run.py"]
