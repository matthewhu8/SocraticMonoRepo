# Socratic App Deployment to AWS EKS

This guide outlines the steps to deploy the Socratic application to AWS Elastic Kubernetes Service (EKS).

## Prerequisites

1. AWS CLI installed and configured
2. eksctl installed
3. kubectl installed
4. Docker installed
5. Access to AWS ECR (Elastic Container Registry)

## Step 1: Create ECR repositories

Create an ECR repository for each service:

```bash
aws ecr create-repository --repository-name socratic-frontend
aws ecr create-repository --repository-name socratic-main-service
aws ecr create-repository --repository-name socratic-database-service
aws ecr create-repository --repository-name socratic-vector-service
aws ecr create-repository --repository-name socratic-llm-service
```

## Step 2: Build and push Docker images

For each service, build and push to ECR:

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin {your-aws-account-id}.dkr.ecr.us-east-1.amazonaws.com

# Build and push each service (repeat for each service)
# Example for main service:
cd Backend/main_service
docker build -t {your-aws-account-id}.dkr.ecr.us-east-1.amazonaws.com/socratic-main-service:latest .
docker push {your-aws-account-id}.dkr.ecr.us-east-1.amazonaws.com/socratic-main-service:latest
```

## Step 3: Create EKS cluster

```bash
eksctl create cluster \
  --name socratic-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 4 \
  --with-oidc \
  --managed
```

## Step 4: Create Kubernetes resources

### Create namespace

```bash
kubectl create namespace socratic
```

### Create secrets

```bash
kubectl create secret generic db-credentials \
  --from-literal=POSTGRES_PASSWORD=postgres \
  --from-literal=POSTGRES_USER=postgres \
  --namespace socratic

kubectl create secret generic huggingface-token \
  --from-literal=HUGGING_FACE_HUB_TOKEN=your-token-here \
  --namespace socratic
```

### Deploy Kubernetes manifests

Create the following resource files in the `kubernetes` directory and apply them:

1. `postgres.yaml` - For PostgreSQL database
2. `redis.yaml` - For Redis cache
3. `database-service.yaml` - For database service
4. `vector-service.yaml` - For vector service
5. `llm-service.yaml` - For LLM service
6. `main-service.yaml` - For main API service
7. `frontend.yaml` - For frontend application
8. `ingress.yaml` - For routing external traffic

Apply the files:

```bash
kubectl apply -f kubernetes/
```

## Step 5: Set up Ingress controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/aws/deploy.yaml
```

## Step 6: Create DNS records

Create DNS records in Route 53 to point to the LoadBalancer created by the Ingress controller.

## Step 7: Set up monitoring

Set up monitoring using CloudWatch:

```bash
eksctl create iamserviceaccount \
  --name cloudwatch-agent \
  --namespace amazon-cloudwatch \
  --cluster socratic-cluster \
  --attach-policy-arn arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy \
  --approve \
  --override-existing-serviceaccounts

kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/cloudwatch-namespace.yaml

kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/cwagent/cwagent-serviceaccount.yaml

kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/cwagent/cwagent-configmap.yaml

kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/cwagent/cwagent-daemonset.yaml
```

## Alternative Deployment: Using AWS ECS (Elastic Container Service)

If you prefer a simpler deployment using ECS instead of EKS:

1. Create an ECS cluster
2. Create Task Definitions for each service
3. Create Services for each Task Definition
4. Use Application Load Balancer to route traffic

ECS may be simpler for smaller applications, but EKS offers better scalability, flexibility, and control.

## Considerations for Production

1. **Persistent Storage:** Use EFS for shared file storage or S3 for object storage.
2. **Database:** Consider using RDS for PostgreSQL instead of a containerized database.
3. **Caching:** Consider ElastiCache for Redis.
4. **Secrets Management:** Use AWS Secrets Manager for sensitive information.
5. **CDN:** Use CloudFront as a CDN for the frontend.
6. **CI/CD:** Set up CI/CD using AWS CodePipeline or GitHub Actions.
7. **Logging:** Centralize logs using CloudWatch Logs.
8. **Monitoring:** Use CloudWatch for metrics and alarms.
9. **Costs:** Consider using Spot Instances for non-critical workloads to reduce costs. 