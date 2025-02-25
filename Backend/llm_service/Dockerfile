# Use a PyTorch image with CUDA support if you need GPU acceleration.
# For CPU-only usage, you can use a simpler image like python:3.9-slim.
FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY app/requirements.txt /app/requirements.txt

# Upgrade pip and install the dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy your application code into the container
COPY app /app

# Expose the port that FastAPI will run on (e.g., 8000)
EXPOSE 8000

# Command to run the FastAPI application using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

