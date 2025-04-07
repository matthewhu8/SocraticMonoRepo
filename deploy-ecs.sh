#!/bin/bash
set -e

# Region and account ID
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)

if [ -z "$AWS_ACCOUNT_ID" ]; then
  echo "Failed to get AWS account ID. Make sure your AWS credentials are set up correctly."
  exit 1
fi

echo "AWS Account ID: $AWS_ACCOUNT_ID"

# Step 1: Create ECS cluster (if not exists)
CLUSTER_NAME="socratic-cluster"

if ! aws ecs describe-clusters --clusters $CLUSTER_NAME --region $AWS_REGION | grep -q "clusterName"; then
  echo "Creating ECS cluster $CLUSTER_NAME..."
  aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $AWS_REGION
else
  echo "ECS cluster $CLUSTER_NAME already exists."
fi

# Step 2: Create log groups for each service
SERVICES=(
  "socratic-llm-service"
  "socratic-vector-service"
  "socratic-frontend"
  "socratic-main-service"
  "socratic-database-service"
  "socratic-postgres"
  "socratic-redis"
)

for service in "${SERVICES[@]}"; do
  LOG_GROUP="/ecs/$service"
  if ! aws logs describe-log-groups --log-group-name-prefix $LOG_GROUP --region $AWS_REGION | grep -q "$LOG_GROUP"; then
    echo "Creating log group $LOG_GROUP..."
    aws logs create-log-group --log-group-name $LOG_GROUP --region $AWS_REGION
  else
    echo "Log group $LOG_GROUP already exists."
  fi
done

# Step 3: Create VPC, subnets, etc. (check if they already exist)
VPC_INFO=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=SocraticVPC" --region $AWS_REGION)
if echo "$VPC_INFO" | grep -q "VpcId"; then
  VPC_ID=$(echo "$VPC_INFO" | jq -r '.Vpcs[0].VpcId')
  echo "Using existing VPC: $VPC_ID"
else
  echo "Creating VPC..."
  VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 --region $AWS_REGION | jq -r '.Vpc.VpcId')
  aws ec2 create-tags --resources $VPC_ID --tags Key=Name,Value=SocraticVPC --region $AWS_REGION
  aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support --region $AWS_REGION
  aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames --region $AWS_REGION
fi

# Create subnets
SUBNET_INFO=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=SocraticPublicSubnet1" --region $AWS_REGION)
if echo "$SUBNET_INFO" | grep -q "SubnetId"; then
  SUBNET1_ID=$(echo "$SUBNET_INFO" | jq -r '.Subnets[0].SubnetId')
  echo "Using existing subnet 1: $SUBNET1_ID"
else
  echo "Creating subnet 1..."
  AZ1=$(aws ec2 describe-availability-zones --region $AWS_REGION | jq -r '.AvailabilityZones[0].ZoneName')
  SUBNET1_ID=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 --availability-zone $AZ1 --region $AWS_REGION | jq -r '.Subnet.SubnetId')
  aws ec2 create-tags --resources $SUBNET1_ID --tags Key=Name,Value=SocraticPublicSubnet1 --region $AWS_REGION
  aws ec2 modify-subnet-attribute --subnet-id $SUBNET1_ID --map-public-ip-on-launch --region $AWS_REGION
fi

SUBNET_INFO=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=SocraticPublicSubnet2" --region $AWS_REGION)
if echo "$SUBNET_INFO" | grep -q "SubnetId"; then
  SUBNET2_ID=$(echo "$SUBNET_INFO" | jq -r '.Subnets[0].SubnetId')
  echo "Using existing subnet 2: $SUBNET2_ID"
else
  echo "Creating subnet 2..."
  AZ2=$(aws ec2 describe-availability-zones --region $AWS_REGION | jq -r '.AvailabilityZones[1].ZoneName')
  SUBNET2_ID=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.2.0/24 --availability-zone $AZ2 --region $AWS_REGION | jq -r '.Subnet.SubnetId')
  aws ec2 create-tags --resources $SUBNET2_ID --tags Key=Name,Value=SocraticPublicSubnet2 --region $AWS_REGION
  aws ec2 modify-subnet-attribute --subnet-id $SUBNET2_ID --map-public-ip-on-launch --region $AWS_REGION
fi

# Create internet gateway
IGW_INFO=$(aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=$VPC_ID" --region $AWS_REGION)
if echo "$IGW_INFO" | grep -q "InternetGatewayId"; then
  IGW_ID=$(echo "$IGW_INFO" | jq -r '.InternetGateways[0].InternetGatewayId')
  echo "Using existing internet gateway: $IGW_ID"
else
  echo "Creating internet gateway..."
  IGW_ID=$(aws ec2 create-internet-gateway --region $AWS_REGION | jq -r '.InternetGateway.InternetGatewayId')
  aws ec2 create-tags --resources $IGW_ID --tags Key=Name,Value=SocraticIGW --region $AWS_REGION
  aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID --region $AWS_REGION
fi

# Create route table
RT_INFO=$(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=SocraticPublicRT" --region $AWS_REGION)
if echo "$RT_INFO" | grep -q "RouteTableId"; then
  RT_ID=$(echo "$RT_INFO" | jq -r '.RouteTables[0].RouteTableId')
  echo "Using existing route table: $RT_ID"
else
  echo "Creating route table..."
  RT_ID=$(aws ec2 create-route-table --vpc-id $VPC_ID --region $AWS_REGION | jq -r '.RouteTable.RouteTableId')
  aws ec2 create-tags --resources $RT_ID --tags Key=Name,Value=SocraticPublicRT --region $AWS_REGION
  aws ec2 create-route --route-table-id $RT_ID --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID --region $AWS_REGION
  aws ec2 associate-route-table --route-table-id $RT_ID --subnet-id $SUBNET1_ID --region $AWS_REGION
  aws ec2 associate-route-table --route-table-id $RT_ID --subnet-id $SUBNET2_ID --region $AWS_REGION
fi

# Create security group
SG_INFO=$(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=SocraticECSSecurityGroup" --region $AWS_REGION)
if echo "$SG_INFO" | grep -q "GroupId"; then
  SG_ID=$(echo "$SG_INFO" | jq -r '.SecurityGroups[0].GroupId')
  echo "Using existing security group: $SG_ID"
else
  echo "Creating security group..."
  SG_ID=$(aws ec2 create-security-group --group-name SocraticECSSecurityGroup --description "Security group for Socratic ECS cluster" --vpc-id $VPC_ID --region $AWS_REGION | jq -r '.GroupId')
  aws ec2 create-tags --resources $SG_ID --tags Key=Name,Value=SocraticECSSecurityGroup --region $AWS_REGION
  aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 0-65535 --cidr 0.0.0.0/0 --region $AWS_REGION
fi

# Step 4: Register task definitions for each service
echo "Registering task definitions..."

# Update EFS ID in task definition files (if EFS is used)
# EFS_ID="your-efs-id"  # If you use EFS, set this value
# sed -i "s/\${EFS_ID}/$EFS_ID/g" *.json

# Update ECR image URLs in the task definition files
for service in "${SERVICES[@]}"; do
  if [ -f "${service}-task-def.json" ]; then
    echo "Updating image in ${service}-task-def.json..."
    sed -i "s|\"image\": \".*${service}:latest\"|\"image\": \"${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${service}:latest\"|g" ${service}-task-def.json
    
    # Register the task definition
    echo "Registering task definition for $service..."
    aws ecs register-task-definition --cli-input-json file://${service}-task-def.json --region $AWS_REGION
  fi
done

# Step 5: Create ECS services
echo "Creating ECS services..."

# Create the postgres service first
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name socratic-postgres \
  --task-definition socratic-postgres:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET1_ID,$SUBNET2_ID],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
  --region $AWS_REGION

# Wait for postgres to be running
echo "Waiting for postgres service to stabilize..."
aws ecs wait services-stable --cluster $CLUSTER_NAME --services socratic-postgres --region $AWS_REGION

# Create the redis service
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name socratic-redis \
  --task-definition socratic-redis:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET1_ID,$SUBNET2_ID],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
  --region $AWS_REGION

# Wait for redis to be running
echo "Waiting for redis service to stabilize..."
aws ecs wait services-stable --cluster $CLUSTER_NAME --services socratic-redis --region $AWS_REGION

# Create the database service
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name socratic-database-service \
  --task-definition socratic-database-service:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET1_ID,$SUBNET2_ID],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
  --region $AWS_REGION

# Wait for database service to be running
echo "Waiting for database service to stabilize..."
aws ecs wait services-stable --cluster $CLUSTER_NAME --services socratic-database-service --region $AWS_REGION

# Create the vector service
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name socratic-vector-service \
  --task-definition socratic-vector-service:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET1_ID,$SUBNET2_ID],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
  --region $AWS_REGION

# Create the main service
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name socratic-main-service \
  --task-definition socratic-main-service:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET1_ID,$SUBNET2_ID],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
  --region $AWS_REGION

# Wait for main service to be running
echo "Waiting for main service to stabilize..."
aws ecs wait services-stable --cluster $CLUSTER_NAME --services socratic-main-service --region $AWS_REGION

# Create the frontend service
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name socratic-frontend \
  --task-definition socratic-frontend:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET1_ID,$SUBNET2_ID],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
  --region $AWS_REGION

# Step 6: Get service URLs
echo "Retrieving service endpoints..."

POSTGRES_TASK=$(aws ecs list-tasks --cluster $CLUSTER_NAME --service-name socratic-postgres --region $AWS_REGION | jq -r '.taskArns[0]')
POSTGRES_ENI=$(aws ecs describe-tasks --cluster $CLUSTER_NAME --tasks $POSTGRES_TASK --region $AWS_REGION | jq -r '.tasks[0].attachments[0].details[] | select(.name=="networkInterfaceId") | .value')
POSTGRES_IP=$(aws ec2 describe-network-interfaces --network-interface-ids $POSTGRES_ENI --region $AWS_REGION | jq -r '.NetworkInterfaces[0].Association.PublicIp')

MAIN_SERVICE_TASK=$(aws ecs list-tasks --cluster $CLUSTER_NAME --service-name socratic-main-service --region $AWS_REGION | jq -r '.taskArns[0]')
MAIN_SERVICE_ENI=$(aws ecs describe-tasks --cluster $CLUSTER_NAME --tasks $MAIN_SERVICE_TASK --region $AWS_REGION | jq -r '.tasks[0].attachments[0].details[] | select(.name=="networkInterfaceId") | .value')
MAIN_SERVICE_IP=$(aws ec2 describe-network-interfaces --network-interface-ids $MAIN_SERVICE_ENI --region $AWS_REGION | jq -r '.NetworkInterfaces[0].Association.PublicIp')

FRONTEND_TASK=$(aws ecs list-tasks --cluster $CLUSTER_NAME --service-name socratic-frontend --region $AWS_REGION | jq -r '.taskArns[0]')
FRONTEND_ENI=$(aws ecs describe-tasks --cluster $CLUSTER_NAME --tasks $FRONTEND_TASK --region $AWS_REGION | jq -r '.tasks[0].attachments[0].details[] | select(.name=="networkInterfaceId") | .value')
FRONTEND_IP=$(aws ec2 describe-network-interfaces --network-interface-ids $FRONTEND_ENI --region $AWS_REGION | jq -r '.NetworkInterfaces[0].Association.PublicIp')

echo "Deployment complete!"
echo "=================="
echo "Postgres: $POSTGRES_IP:5432"
echo "Main Service: http://$MAIN_SERVICE_IP:8000"
echo "Frontend: http://$FRONTEND_IP:80"
echo "==================="
echo "Note: The LLM service requires a GPU instance and needs to be set up manually." 