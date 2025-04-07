#!/bin/bash
set -e

# Configuration
AWS_REGION=$(aws configure get region)
CLUSTER_NAME="socratic-cluster"

# Find the latest ECS-optimized AMI with GPU support
echo "Finding latest ECS-optimized AMI with GPU support..."
AMI_ID=$(aws ssm get-parameters --names /aws/service/ecs/optimized-ami/amazon-linux-2/gpu/recommended --query "Parameters[0].Value" --output text | jq -r ".image_id")

echo "Using AMI: $AMI_ID"

# Create security group for the GPU instance if it doesn't exist
SG_NAME="socratic-gpu-ecs-sg"
SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$SG_NAME" --query "SecurityGroups[0].GroupId" --output text)

if [ "$SG_ID" == "None" ]; then
  echo "Creating security group for GPU instance..."
  VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text)
  SG_ID=$(aws ec2 create-security-group --group-name $SG_NAME --description "Security group for Socratic GPU ECS instances" --vpc-id $VPC_ID --query "GroupId" --output text)
  
  # Allow all outbound
  aws ec2 authorize-security-group-egress --group-id $SG_ID --protocol all --port -1 --cidr 0.0.0.0/0
  
  # Allow SSH inbound
  aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0
  
  # Allow all internal traffic
  aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol all --port -1 --source-group $SG_ID
fi

# Create IAM role for the EC2 instance if it doesn't exist
ROLE_NAME="ecsGPUInstanceRole"
if ! aws iam get-role --role-name $ROLE_NAME 2>/dev/null; then
  echo "Creating IAM role for GPU instance..."
  aws iam create-role \
    --role-name $ROLE_NAME \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
  
  aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role
  
  aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
  
  # Create instance profile
  aws iam create-instance-profile --instance-profile-name $ROLE_NAME
  aws iam add-role-to-instance-profile --instance-profile-name $ROLE_NAME --role-name $ROLE_NAME
  
  # Wait for instance profile to propagate
  sleep 10
fi

# User data to register with ECS cluster
USER_DATA=$(cat <<EOF
#!/bin/bash
echo ECS_CLUSTER=${CLUSTER_NAME} >> /etc/ecs/ecs.config
echo ECS_ENABLE_GPU_SUPPORT=true >> /etc/ecs/ecs.config

# Install NVIDIA drivers and Docker GPU runtime
amazon-linux-extras install -y nvidia-driver
yum install -y amazon-ecr-credential-helper

# Restart the Docker daemon to ensure it recognizes the GPU
systemctl restart docker
systemctl restart ecs
EOF
)

# Encode user data
USER_DATA_B64=$(echo "$USER_DATA" | base64 -w 0)

# Launch EC2 instance
echo "Launching g4dn.xlarge GPU instance..."
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type g4dn.xlarge \
  --security-group-ids $SG_ID \
  --iam-instance-profile Name=$ROLE_NAME \
  --user-data "$USER_DATA_B64" \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=SocraticGPUInstance}]" \
  --query "Instances[0].InstanceId" \
  --output text)

echo "Launched GPU instance: $INSTANCE_ID"
echo "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP address
PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query "Reservations[0].Instances[0].PublicIpAddress" --output text)
echo "GPU instance is running with public IP: $PUBLIC_IP"

echo "It will take a few minutes for the instance to register with the ECS cluster."
echo "You can check its status with:"
echo "aws ecs list-container-instances --cluster $CLUSTER_NAME"
echo ""
echo "After it's registered, you can run the deploy.sh script to deploy your services."
echo ""
echo "To SSH into this instance (if needed):"
echo "ssh -i your-key.pem ec2-user@$PUBLIC_IP"
echo ""
echo "Note: This instance is running as g4dn.xlarge, which costs approximately $0.50-$0.70 per hour."
echo "Remember to terminate it when not in use with:"
echo "aws ec2 terminate-instances --instance-ids $INSTANCE_ID" 