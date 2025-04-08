FROM python:3.10-slim

WORKDIR /app
ENV MODEL_NAME="deepseek-ai/DeepSeek-V3"
ENV DEVICE="-1"
ENV HUGGING_FACE_HUB_TOKEN=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

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY app/requirements.txt .
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app .

EXPOSE 8003

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]