# Use a CUDA-enabled PyTorch image (adjust the version as needed)
FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

# Set working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY app/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt

# Copy the application code into the container
COPY app /app

# Expose the port that the microservice uses
EXPOSE 8001

# Command to run the FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
