# Local Testing Guide: Testing Docker Containers Before AWS Deployment

Before deploying your Socratic application to AWS, it's a good practice to test each Docker container locally. This ensures that your services work as expected in production-like environments and helps identify issues before the actual deployment.

## Prerequisites

- Docker installed on your local machine
- Docker Compose installed on your local machine

## Option 1: Test with Docker Compose (Recommended)

The easiest and most reliable way to test your entire application is using Docker Compose, which handles the networking between containers automatically:

```bash
# Navigate to the root directory of your project
cd ~/Desktop/SocraticMonoRepo

# Run all services using docker-compose
docker-compose up

# You can also run in detached mode
# docker-compose up -d

# View logs if running in detached mode
# docker-compose logs -f
```

This automatically sets up all containers with proper networking and environment variables as defined in your docker-compose.yml file.

## Option 2: Test Individual Containers

If you need to test individual containers, you should create a Docker network first to ensure containers can communicate:

```bash
# Create a custom Docker network
docker network create socratic-network
```

### Step 1: Start Dependent Services First

```bash
# Start PostgreSQL
docker run --name postgres-test --network socratic-network \
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres -e POSTGRES_DB=socratic \
  -p 5432:5432 -d postgres:15-alpine

# Start Redis
docker run --name redis-test --network socratic-network \
  -p 6379:6379 -d redis:alpine
```

### Step 2: Build and Run Service Containers

#### Database Service

```bash
# Navigate to the database service directory
cd ~/Desktop/SocraticMonoRepo/Backend/database_service

# Build the container
docker build -t socratic-database-service:test .

# Run the database service container
docker run --name database-service --network socratic-network \
  -p 8001:8001 \
  -e DATABASE_URL=postgresql://postgres:postgres@postgres-test:5432/socratic \
  socratic-database-service:test

# In a separate terminal, test the service
curl http://localhost:8001/health
```

#### Vector Service

```bash
# Navigate to the vector service directory
cd ~/Desktop/SocraticMonoRepo/Backend/vector_service

# Build the container
docker build -t socratic-vector-service:test .

# Create a volume for persistent data
docker volume create vector-data

# Run the container
docker run --name vector-service --network socratic-network \
  -p 8002:8002 \
  -v vector-data:/app/data/chroma_db \
  socratic-vector-service:test

# In a separate terminal, test the service
curl http://localhost:8002/health
```

#### LLM Service

```bash
# Navigate to the LLM service directory
cd ~/Desktop/SocraticMonoRepo/Backend/llm_service

# Build the container
docker build -t socratic-llm-service:test .

# Create a volume for model cache
docker volume create llm-cache

# Run the container
docker run --name llm-service --network socratic-network \
  -p 8003:8001 \
  -v llm-cache:/app/model_cache \
  -e HUGGING_FACE_HUB_TOKEN=your-token-here \
  -e PORT=8001 \
  -e MODEL_CACHE_DIR=/app/model_cache \
  socratic-llm-service:test

# In a separate terminal, test the service
curl http://localhost:8003/health
```

#### Main Service

```bash
# Navigate to the main service directory
cd ~/Desktop/SocraticMonoRepo/Backend/main_service

# Build the container
docker build -t socratic-main-service:test .

# Run the container with correct service URLs
docker run --name main-service --network socratic-network \
  -p 8000:8000 \
  -e DATABASE_SERVICE_URL=http://database-service:8001 \
  -e VECTOR_SERVICE_URL=http://vector-service:8002 \
  -e LLM_SERVICE_URL=http://llm-service:8001 \
  -e REDIS_URL=redis://redis-test:6379 \
  socratic-main-service:test

# In a separate terminal, test the API
curl http://localhost:8000/health
```

#### Frontend Service

```bash
# Navigate to the frontend directory
cd ~/Desktop/SocraticMonoRepo/socratic-frontend

# Build the container
docker build -t socratic-frontend:test .

# Run the container
docker run --name frontend --network socratic-network \
  -p 80:80 \
  -e REACT_APP_API_URL=http://main-service:8000 \
  socratic-frontend:test

# Access the frontend in your browser
# http://localhost:80
```

## Option 3: Create a Production-Like Test Environment

This approach simulates your production environment more closely by creating a dedicated Docker Compose file:

```bash
# Navigate to the root directory of your project
cd ~/Desktop/SocraticMonoRepo

# Create a testing-docker-compose.yml file
cat > testing-docker-compose.yml << EOF
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_DB=socratic
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  frontend:
    build:
      context: ./socratic-frontend
    ports:
      - "80:80"
    depends_on:
      - main_service
    environment:
      - REACT_APP_API_URL=http://main_service:8000

  main_service:
    build:
      context: ./Backend/main_service
    ports:
      - "8000:8000"
    depends_on:
      - database_service
      - vector_service
      - llm_service
    environment:
      - DATABASE_SERVICE_URL=http://database_service:8001
      - VECTOR_SERVICE_URL=http://vector_service:8002
      - LLM_SERVICE_URL=http://llm_service:8003
      - REDIS_URL=redis://redis:6379

  database_service:
    build:
      context: ./Backend/database_service
    ports:
      - "8001:8001"
    depends_on:
      - postgres
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/socratic

  vector_service:
    build:
      context: ./Backend/vector_service
    ports:
      - "8002:8002"
    volumes:
      - vector_data:/app/data/chroma_db

  llm_service:
    build:
      context: ./Backend/llm_service
    ports:
      - "8003:8001"
    volumes:
      - llm_cache:/app/model_cache
    environment:
      - PORT=8001
      - MODEL_CACHE_DIR=/app/model_cache
      - HUGGING_FACE_HUB_TOKEN=your-token-here

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  vector_data:
  llm_cache:
  redis_data:
EOF

# Run with this production-like configuration
docker-compose -f testing-docker-compose.yml up
```

## Additional Testing Options

### Load Testing (Optional)

Before deploying to production, you might want to perform load testing to ensure your application can handle the expected traffic:

```bash
# Install k6 for load testing
brew install k6

# Create a simple load test script
cat > load-test.js << EOF
import http from 'k6/http';
import { sleep } from 'k6';

export default function () {
  http.get('http://localhost:8000/health');
  sleep(1);
}

export const options = {
  vus: 10,
  duration: '30s',
};
EOF

# Run the load test
k6 run load-test.js
```

### Security Testing (Optional)

Run basic security checks on your containers:

```bash
# Install Trivy
brew install aquasecurity/trivy/trivy

# Scan your images for vulnerabilities
trivy image socratic-frontend:test
trivy image socratic-main-service:test
trivy image socratic-database-service:test
trivy image socratic-vector-service:test
trivy image socratic-llm-service:test
```

## Clean Up

After testing, clean up your local environment:

```bash
# If using docker-compose
docker-compose down
# Or for the testing-specific compose file
docker-compose -f testing-docker-compose.yml down

# If testing individual containers
docker stop postgres-test redis-test database-service vector-service llm-service main-service frontend
docker rm postgres-test redis-test database-service vector-service llm-service main-service frontend

# Remove network
docker network rm socratic-network

# Remove volumes created for testing
docker volume rm vector-data llm-cache

# Remove test images
docker rmi socratic-frontend:test
docker rmi socratic-main-service:test
docker rmi socratic-database-service:test
docker rmi socratic-vector-service:test
docker rmi socratic-llm-service:test
```

## Troubleshooting

- **Container won't start**: Check logs with `docker logs <container_id>`
- **Service unavailable**: Ensure all dependent services are running and accessible
- **Communication issues**: Make sure containers are on the same network and using the correct service names for DNS resolution
- **Database connection issues**: Verify PostgreSQL is running and credentials are correct
- **Network problems**: Use `docker network inspect socratic-network` to check container networking
- **Volume permission issues**: Check if proper permissions are set for mounted volumes 