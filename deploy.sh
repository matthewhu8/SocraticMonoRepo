#!/bin/bash
set -e

# Configuration
AWS_REGION=$(aws configure get region)
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
CLUSTER_NAME="socratic-cluster"
ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/socratic"

# Create EFS for persistent storage
echo "Creating EFS file system for persistent storage..."
EFS_ID=$(aws efs create-file-system \
  --performance-mode generalPurpose \
  --throughput-mode bursting \
  --encrypted \
  --tags Key=Name,Value=SocraticEFS \
  --query "FileSystemId" \
  --output text)

echo "Created EFS with ID: ${EFS_ID}"

# Create VPC and subnets if they don't exist
echo "Checking for default VPC..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text)

if [ "$VPC_ID" == "None" ]; then
  echo "No default VPC found. Creating a new VPC..."
  VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 --query "Vpc.VpcId" --output text)
  aws ec2 create-tags --resources $VPC_ID --tags Key=Name,Value=SocraticVPC
  
  # Create internet gateway
  IGW_ID=$(aws ec2 create-internet-gateway --query "InternetGateway.InternetGatewayId" --output text)
  aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID
  
  # Create route table
  ROUTE_TABLE_ID=$(aws ec2 create-route-table --vpc-id $VPC_ID --query "RouteTable.RouteTableId" --output text)
  aws ec2 create-route --route-table-id $ROUTE_TABLE_ID --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID
fi

# Get or create subnets
echo "Setting up subnets..."
SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[*].SubnetId" --output text)
SUBNET_ARRAY=($SUBNET_IDS)

if [ ${#SUBNET_ARRAY[@]} -lt 2 ]; then
  echo "Need to create subnets..."
  # Get available AZs
  AZS=$(aws ec2 describe-availability-zones --query "AvailabilityZones[0:2].ZoneName" --output text)
  AZ_ARRAY=($AZS)
  
  # Create two subnets in different AZs
  SUBNET1_ID=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 --availability-zone ${AZ_ARRAY[0]} --query "Subnet.SubnetId" --output text)
  SUBNET2_ID=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.2.0/24 --availability-zone ${AZ_ARRAY[1]} --query "Subnet.SubnetId" --output text)
  
  aws ec2 modify-subnet-attribute --subnet-id $SUBNET1_ID --map-public-ip-on-launch
  aws ec2 modify-subnet-attribute --subnet-id $SUBNET2_ID --map-public-ip-on-launch
  
  # Associate subnets with route table
  ROUTE_TABLE_ID=$(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" --query "RouteTables[0].RouteTableId" --output text)
  aws ec2 associate-route-table --subnet-id $SUBNET1_ID --route-table-id $ROUTE_TABLE_ID
  aws ec2 associate-route-table --subnet-id $SUBNET2_ID --route-table-id $ROUTE_TABLE_ID
  
  SUBNET_ARRAY=($SUBNET1_ID $SUBNET2_ID)
fi

# Create EFS mount targets
echo "Creating EFS mount targets..."
for SUBNET_ID in "${SUBNET_ARRAY[@]:0:2}"; do
  aws efs create-mount-target \
    --file-system-id ${EFS_ID} \
    --subnet-id ${SUBNET_ID} \
    --security-groups $(aws ec2 describe-security-groups --filters Name=vpc-id,Values=$VPC_ID Name=group-name,Values=default --query "SecurityGroups[0].GroupId" --output text)
done

# Update task definition files with correct values
echo "Updating task definition files..."
sed -i.bak "s|\${AWS_ACCOUNT_ID}|${AWS_ACCOUNT_ID}|g; s|\${AWS_REGION}|${AWS_REGION}|g; s|\${ECR_REPO}|${ECR_REPO}|g; s|\${EFS_ID}|${EFS_ID}|g" llm-service-task-def.json
sed -i.bak "s|\${AWS_ACCOUNT_ID}|${AWS_ACCOUNT_ID}|g; s|\${AWS_REGION}|${AWS_REGION}|g; s|\${ECR_REPO}|${ECR_REPO}|g; s|\${EFS_ID}|${EFS_ID}|g" non-gpu-services-task-def.json

# Create execution role if it doesn't exist
echo "Setting up IAM execution role..."
if ! aws iam get-role --role-name ecsTaskExecutionRole 2>/dev/null; then
  echo "Creating ecsTaskExecutionRole..."
  aws iam create-role \
    --role-name ecsTaskExecutionRole \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
  
  aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
  
  aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess
fi

# Store Hugging Face token in Parameter Store if provided
if [ ! -z "$HUGGING_FACE_HUB_TOKEN" ]; then
  echo "Storing Hugging Face token in Parameter Store..."
  aws ssm put-parameter \
    --name "/socratic/HUGGING_FACE_HUB_TOKEN" \
    --value "$HUGGING_FACE_HUB_TOKEN" \
    --type "SecureString" \
    --overwrite
else
  echo "No HUGGING_FACE_HUB_TOKEN provided. Make sure it's already in Parameter Store."
fi

# Register task definitions
echo "Registering task definitions..."
aws ecs register-task-definition --cli-input-json file://llm-service-task-def.json
aws ecs register-task-definition --cli-input-json file://non-gpu-services-task-def.json

# Create log groups
echo "Creating CloudWatch log groups..."
aws logs create-log-group --log-group-name "/ecs/socratic-llm-service" || true
aws logs create-log-group --log-group-name "/ecs/socratic-postgres" || true
aws logs create-log-group --log-group-name "/ecs/socratic-redis" || true
aws logs create-log-group --log-group-name "/ecs/socratic-main-service" || true
aws logs create-log-group --log-group-name "/ecs/socratic-database-service" || true
aws logs create-log-group --log-group-name "/ecs/socratic-vector-service" || true
aws logs create-log-group --log-group-name "/ecs/socratic-frontend" || true

# Create non-GPU services first using Fargate
echo "Creating non-GPU services using Fargate..."
SUBNET_STRING="${SUBNET_ARRAY[0]},${SUBNET_ARRAY[1]}"
SECURITY_GROUP=$(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=default" --query "SecurityGroups[0].GroupId" --output text)

aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name socratic-services \
  --task-definition socratic-services \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_STRING],securityGroups=[$SECURITY_GROUP],assignPublicIp=ENABLED}"

# Create GPU service (requires GPU-enabled EC2 instance)
echo "Creating GPU service for LLM..."

# Check if we have an existing p3 or g4 instance
GPU_INSTANCE=$(aws ec2 describe-instances \
  --filters "Name=instance-type,Values=g4dn*,p3*,p4d*" "Name=instance-state-name,Values=running" \
  --query "Reservations[0].Instances[0].InstanceId" --output text)

if [ "$GPU_INSTANCE" == "None" ]; then
  echo "No running GPU instance found. You need to create a GPU instance and register it with the ECS cluster."
  echo "Here's how to do it manually:"
  echo "1. Launch a g4dn.xlarge or similar GPU instance using the ECS-optimized AMI"
  echo "2. Make sure it has the following user data:"
  echo "   #!/bin/bash"
  echo "   echo ECS_CLUSTER=${CLUSTER_NAME} >> /etc/ecs/ecs.config"
  echo "   echo ECS_ENABLE_GPU_SUPPORT=true >> /etc/ecs/ecs.config"
  echo "3. Wait for the instance to register with the cluster"
else
  echo "Found GPU instance: $GPU_INSTANCE"
fi

# Create the LLM service with EC2 launch type
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name socratic-llm-service \
  --task-definition socratic-llm-service \
  --desired-count 1 \
  --launch-type EC2 \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_STRING],securityGroups=[$SECURITY_GROUP],assignPublicIp=ENABLED}"

echo "Deployment completed!"
echo "Notes:"
echo "1. The non-GPU services are running on Fargate"
echo "2. The LLM service requires a GPU instance in the ECS cluster"
echo "   - If a GPU instance was not found, you need to create one manually and register it with the cluster"
echo "3. You can check the status of your services with:"
echo "   aws ecs list-services --cluster $CLUSTER_NAME"
echo "   aws ecs describe-services --cluster $CLUSTER_NAME --services socratic-services socratic-llm-service" 