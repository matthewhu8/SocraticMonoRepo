#!/bin/bash
set -e

# Region
AWS_REGION="us-east-1"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
if [ -z "$AWS_ACCOUNT_ID" ]; then
  echo "Failed to get AWS account ID. Make sure your AWS credentials are set up correctly."
  exit 1
fi

echo "AWS Account ID: $AWS_ACCOUNT_ID"

# Define service names and their corresponding Docker image names
# Skipping LLM service for now due to its large size
ECR_REPOS=(
  "socratic-vector-service"
  "socratic-frontend"
  "socratic-main-service"
  "socratic-database-service"
)

DOCKER_IMAGES=(
  "socratic/vector-service"
  "socratic/frontend"
  "socratic/main-service"
  "socratic/database-service"
)

# Login to ECR
echo "Logging in to Amazon ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Create repositories and push images
for ((i=0; i<${#ECR_REPOS[@]}; i++)); do
  repo="${ECR_REPOS[$i]}"
  image="${DOCKER_IMAGES[$i]}"
  
  # Create repository if it doesn't exist
  if ! aws ecr describe-repositories --repository-names $repo --region $AWS_REGION &> /dev/null; then
    echo "Creating repository $repo..."
    aws ecr create-repository --repository-name $repo --region $AWS_REGION
  else
    echo "Repository $repo already exists."
  fi
  
  # Tag the local image
  echo "Tagging $image as $repo..."
  docker tag $image:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$repo:latest
  
  # Push the image to ECR
  echo "Pushing $repo to ECR..."
  docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$repo:latest
done

echo "All images pushed to Amazon ECR successfully!" 