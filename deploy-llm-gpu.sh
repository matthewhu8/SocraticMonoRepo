#!/bin/bash
set -e

# This script deploys the LLM service to a GPU-enabled EC2 instance
# Prerequisites: 
# 1. An EC2 instance with GPU (g4dn.xlarge) already running
# 2. ECS agent installed and configured on the EC2 instance
# 3. Instance registered with your ECS cluster (socratic-cluster)

# Region and account ID
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
CLUSTER_NAME="socratic-cluster"

if [ -z "$AWS_ACCOUNT_ID" ]; then
  echo "Failed to get AWS account ID. Make sure your AWS credentials are set up correctly."
  exit 1
fi

echo "AWS Account ID: $AWS_ACCOUNT_ID"

# Find GPU-enabled instances in your account
echo "Looking for GPU-enabled EC2 instances..."
GPU_INSTANCES=$(aws ec2 describe-instances --filters "Name=instance-type,Values=g4dn.xlarge,g4dn.2xlarge,p3.2xlarge,p3.8xlarge" --query "Reservations[*].Instances[*].[InstanceId,PublicIpAddress,State.Name]" --output text --region $AWS_REGION)

if [ -z "$GPU_INSTANCES" ]; then
  echo "No GPU instances found. Please launch a GPU instance first."
  echo "Example command:"
  echo "aws ec2 run-instances --image-id ami-0ccb473bada910e74 --instance-type g4dn.xlarge --key-name YOUR_KEY_PAIR --security-group-ids YOUR_SECURITY_GROUP"
  exit 1
fi

echo "Found GPU instances:"
echo "$GPU_INSTANCES"

# Get security group ID from the existing cluster
echo "Getting VPC and security group information..."
SUBNET_INFO=$(aws ec2 describe-subnets --filters "Name=tag:Name,Values=SocraticPublicSubnet*" --region $AWS_REGION)
SUBNET1_ID=$(echo "$SUBNET_INFO" | jq -r '.Subnets[0].SubnetId')
SUBNET2_ID=$(echo "$SUBNET_INFO" | jq -r '.Subnets[1].SubnetId')
VPC_ID=$(echo "$SUBNET_INFO" | jq -r '.Subnets[0].VpcId')

SG_INFO=$(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=SocraticECSSecurityGroup" --region $AWS_REGION)
SG_ID=$(echo "$SG_INFO" | jq -r '.SecurityGroups[0].GroupId')

echo "VPC: $VPC_ID"
echo "Subnet1: $SUBNET1_ID"
echo "Subnet2: $SUBNET2_ID"
echo "Security Group: $SG_ID"

# Update the LLM service task definition
echo "Updating LLM service task definition..."
sed -i "s|\"image\": \".*socratic-llm-service:latest\"|\"image\": \"${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/socratic-llm-service:latest\"|g" socratic-llm-service-task-def.json

# Create parameter store entry for Hugging Face token
if [ -z "$HUGGING_FACE_HUB_TOKEN" ]; then
  echo "Please enter your Hugging Face token:"
  read -s HUGGING_FACE_HUB_TOKEN
fi

echo "Creating Parameter Store entry for Hugging Face token..."
aws ssm put-parameter \
  --name "/socratic/HUGGING_FACE_HUB_TOKEN" \
  --value "$HUGGING_FACE_HUB_TOKEN" \
  --type "SecureString" \
  --overwrite \
  --region $AWS_REGION

# Register the task definition
echo "Registering LLM service task definition..."
aws ecs register-task-definition --cli-input-json file://socratic-llm-service-task-def.json --region $AWS_REGION

# Create the LLM service
echo "Creating LLM service..."
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name socratic-llm-service \
  --task-definition socratic-llm-service:1 \
  --desired-count 1 \
  --launch-type EC2 \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET1_ID,$SUBNET2_ID],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
  --region $AWS_REGION

echo "LLM service deployment initiated."
echo "Note: Make sure your EC2 instance has GPU drivers installed and is properly configured with the ECS agent."
echo "You can check the status with: aws ecs describe-services --cluster $CLUSTER_NAME --services socratic-llm-service --region $AWS_REGION"

# Instructions for checking the service
echo "======================="
echo "To check GPU utilization on your EC2 instance:"
echo "1. SSH into your instance: ssh -i your-key.pem ec2-user@your-gpu-instance-ip"
echo "2. Run: nvidia-smi"
echo "=======================" 