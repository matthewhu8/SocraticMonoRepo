FROM python:3.10-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8002 \
    CHROMA_PERSIST_DIRECTORY=/app/data/chroma_db \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies - keep this layer small
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Split requirements into multiple layers to improve cacheability
# Copy and install base requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY ./app /app/app
RUN mkdir -p ${CHROMA_PERSIST_DIRECTORY}
EXPOSE ${PORT}

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"] 