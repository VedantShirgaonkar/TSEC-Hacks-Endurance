# AWS Free Tier Deployment Guide ($100 Budget)
## Complete RAG Application Deployment

**Date**: February 2026  
**Budget**: $100 USD Free Tier  
**Duration**: ~2 hours

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Cost Breakdown](#cost-breakdown)
3. [Pre-Deployment Setup](#pre-deployment-setup)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Monitoring & Optimization](#monitoring--optimization)
6. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         AWS Free Tier                            │
│                                                                  │
│  ┌─────────────┐      ┌──────────────┐      ┌──────────────┐   │
│  │ CloudFront  │─────▶│ S3 Bucket    │      │ S3 Bucket    │   │
│  │ CDN         │      │ (Frontend)   │      │ (Docs)       │   │
│  └─────────────┘      └──────────────┘      └──────────────┘   │
│                                                      ▲            │
│                                                      │            │
│  ┌─────────────────────────────────────────────────┼────────┐   │
│  │           API Gateway (Free Tier)               │        │   │
│  │  /chat, /evaluate, /health endpoints           │        │   │
│  └─────────────────────────────────────────────────┼────────┘   │
│                                                      │            │
│        ┌─────────────────────┬────────────────────────┐          │
│        │                     │                        │          │
│   ┌────▼────────┐    ┌──────▼────────┐    ┌─────────▼───┐      │
│   │ Lambda@Edge │    │ Lambda        │    │ Lambda      │      │
│   │ (Chatbot)   │    │ (Endurance)   │    │ (Trigger)   │      │
│   │ 1GB RAM     │    │ 512MB RAM     │    │ 128MB RAM   │      │
│   └─────────────┘    └───────────────┘    └─────────────┘      │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │         DynamoDB (Free Tier 25GB)                        │  │
│   │  - Sessions table                                        │  │
│   │  - Feedback table                                        │  │
│   │  - Audit logs                                            │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  CloudWatch Logs (Free Tier: 5GB/month)                 │  │
│   │  Monitoring & debugging                                 │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

External Services (Free/Paid):
- Groq API (Free tier: 5,000 requests/month)
- OpenAI API (Embeddings: ~$0.02 per 1M tokens - 250k free trial)
```

---

## Cost Breakdown

### AWS Services (Free Tier Eligible)

| Service | Free Tier Limit | Your Usage | Cost |
|---------|-----------------|-----------|------|
| **Lambda** | 1M requests/month | ~30K/month | **FREE** |
| **Lambda** (compute) | 400,000 GB-seconds/month | ~10K GB-s/month | **FREE** |
| **API Gateway** | 1M requests/month | ~30K/month | **FREE** |
| **S3** | 5GB storage | 50MB (docs+assets) | **FREE** |
| **S3** Data transfer | 100GB OUT/month | ~10MB/month | **FREE** |
| **DynamoDB** | 25GB + 1B writes/month | <100MB | **FREE** |
| **CloudFront** | 1TB data transfer | ~100MB | **FREE** |
| **CloudWatch** | 5GB logs/month | ~50MB/month | **FREE** |

### External APIs (Not AWS)

| Service | Free Tier | Estimated Monthly Cost |
|---------|-----------|------------------------|
| **Groq LLM** | 5,000 requests/month | **FREE** ✅ |
| **OpenAI Embeddings** | $5 credit/month | **FREE** ✅ (5 months) |

### **Total Estimated Cost: $0 - $10/month**

⚠️ **Budget Alert**: Your $100 will cover ~10 months with this setup!

---

## Pre-Deployment Setup

### Prerequisites Checklist
- [ ] AWS Account with Free Tier activated
- [ ] AWS CLI installed locally (`brew install awscli`)
- [ ] Python 3.11+
- [ ] Git installed
- [ ] Groq API Key (free from https://console.groq.com)
- [ ] OpenAI API Key ($5 free credit from https://platform.openai.com)

### 1. Install AWS CLI & Configure Credentials

```bash
# Install AWS CLI
brew install awscli

# Configure with your AWS credentials
aws configure

# You'll be prompted for:
# AWS Access Key ID: [from IAM console]
# AWS Secret Access Key: [from IAM console]
# Default region: ap-south-1  # or your preferred region
# Default output format: json
```

### 2. Get Your API Keys

**Groq API**:
1. Go to https://console.groq.com
2. Create account and sign in
3. Click "Keys" → "Create API Key"
4. Save the key (looks like: `gsk_abc123...`)

**OpenAI API**:
1. Go to https://platform.openai.com/account/api-keys
2. Create new API key
3. Save the key (looks like: `sk-proj-abc123...`)
4. You'll get $5 free credit immediately

### 3. Create IAM User for Deployment

```bash
# Create IAM user with programmatic access
aws iam create-user --user-name endurance-deployer

# Attach policies for Lambda, API Gateway, S3, DynamoDB
aws iam attach-user-policy \
  --user-name endurance-deployer \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Create access keys
aws iam create-access-key --user-name endurance-deployer
```

---

## Step-by-Step Implementation

### PHASE 1: AWS Foundation (30 mins)

#### Step 1.1: Create S3 Buckets

```bash
# Bucket 1: Frontend/Dashboard
aws s3 mb s3://endurance-dashboard-$(date +%s) \
  --region ap-south-1

# Bucket 2: RAG Documents
aws s3 mb s3://endurance-docs-$(date +%s) \
  --region ap-south-1

# Bucket 3: Lambda Deployment Packages
aws s3 mb s3://endurance-lambda-deploy-$(date +%s) \
  --region ap-south-1

# Enable versioning on all buckets (optional, for safety)
aws s3api put-bucket-versioning \
  --bucket endurance-dashboard-XXXXX \
  --versioning-configuration Status=Enabled
```

**Save your bucket names** - you'll need them later!

```bash
# Set as environment variables for easy reference
export DASH_BUCKET="endurance-dashboard-XXXXX"
export DOCS_BUCKET="endurance-docs-XXXXX"
export DEPLOY_BUCKET="endurance-lambda-deploy-XXXXX"
```

#### Step 1.2: Upload RAG Documents to S3

```bash
# Upload all documentation
aws s3 sync \
  /path/to/chatbot/rag_docs/ \
  s3://$DOCS_BUCKET/ \
  --region ap-south-1

# Verify upload
aws s3 ls s3://$DOCS_BUCKET/ --region ap-south-1
```

#### Step 1.3: Create DynamoDB Tables

**Table 1: Sessions**
```bash
aws dynamodb create-table \
  --table-name endurance-sessions \
  --attribute-definitions \
    AttributeName=session_id,AttributeType=S \
    AttributeName=timestamp,AttributeType=N \
  --key-schema \
    AttributeName=session_id,KeyType=HASH \
    AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region ap-south-1
```

**Table 2: Feedback**
```bash
aws dynamodb create-table \
  --table-name endurance-feedback \
  --attribute-definitions \
    AttributeName=feedback_id,AttributeType=S \
  --key-schema \
    AttributeName=feedback_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-south-1
```

**Table 3: Audit Logs**
```bash
aws dynamodb create-table \
  --table-name endurance-audit-logs \
  --attribute-definitions \
    AttributeName=log_id,AttributeType=S \
    AttributeName=timestamp,AttributeType=N \
  --key-schema \
    AttributeName=log_id,KeyType=HASH \
    AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --time-to-live-specification AttributeName=ttl,Enabled=true \
  --region ap-south-1
```

✅ **PHASE 1 Complete** - Foundation is ready!

---

### PHASE 2: Package Lambda Functions (45 mins)

#### Step 2.1: Create Lambda Deployment Package - Chatbot API

```bash
# Create deployment directory
mkdir -p lambda-packages/chatbot
cd lambda-packages/chatbot

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install \
  fastapi \
  mangum \
  langchain \
  langchain-core \
  langchain-openai \
  langchain-groq \
  langchain-community \
  chromadb \
  pydantic \
  boto3

# Copy your application code
cp -r /path/to/chatbot ./
cp -r /path/to/endurance ./

# Create AWS-specific handler
cat > lambda_handler.py << 'EOF'
"""AWS Lambda handler for Chatbot API"""
from mangum import Mangum
from chatbot.api import app

# Handler for API Gateway
handler = Mangum(app, lifespan="off")
EOF

# Create deployment package
pip install -r requirements.txt --target ./package
cp -r chatbot ./package/
cp -r endurance ./package/
cp lambda_handler.py ./package/

# Zip it
cd package
zip -r ../chatbot-layer.zip .
cd ..

# Upload to S3
aws s3 cp chatbot-layer.zip \
  s3://$DEPLOY_BUCKET/chatbot-layer.zip \
  --region ap-south-1

cd ../..
```

#### Step 2.2: Create Lambda Deployment Package - Endurance API

```bash
# Create deployment directory
mkdir -p lambda-packages/endurance
cd lambda-packages/endurance

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install \
  fastapi \
  mangum \
  numpy \
  scikit-learn \
  pydantic \
  boto3 \
  httpx

# Copy application code
cp -r /path/to/api ./
cp -r /path/to/endurance ./

# Create AWS-specific handler
cat > lambda_handler.py << 'EOF'
"""AWS Lambda handler for Endurance API"""
from mangum import Mangum
from api.main import app

# Handler for API Gateway
handler = Mangum(app, lifespan="off")
EOF

# Create deployment package
pip install -r requirements.txt --target ./package 2>/dev/null || true
cp -r api ./package/
cp -r endurance ./package/
cp lambda_handler.py ./package/

# Zip it
cd package
zip -r ../endurance-layer.zip .
cd ..

# Upload to S3
aws s3 cp endurance-layer.zip \
  s3://$DEPLOY_BUCKET/endurance-layer.zip \
  --region ap-south-1

cd ../..
```

#### Step 2.3: Create IAM Execution Role for Lambda

```bash
# Create trust policy
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
  --role-name endurance-lambda-role \
  --assume-role-policy-document file://trust-policy.json

# Create inline policy for DynamoDB, S3, CloudWatch
cat > lambda-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/endurance-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::endurance-docs-*",
        "arn:aws:s3:::endurance-docs-*/*"
      ]
    }
  ]
}
EOF

# Attach policy
aws iam put-role-policy \
  --role-name endurance-lambda-role \
  --policy-name endurance-lambda-policy \
  --policy-document file://lambda-policy.json
```

✅ **PHASE 2 Complete** - Lambda packages ready!

---

### PHASE 3: Deploy Lambda Functions (30 mins)

#### Step 3.1: Create Chatbot Lambda Function

```bash
# Get the role ARN
ROLE_ARN=$(aws iam get-role \
  --role-name endurance-lambda-role \
  --query 'Role.Arn' \
  --output text)

# Create Lambda function for Chatbot
aws lambda create-function \
  --function-name endurance-chatbot \
  --runtime python3.11 \
  --role $ROLE_ARN \
  --handler lambda_handler.handler \
  --timeout 60 \
  --memory-size 1024 \
  --s3-bucket $DEPLOY_BUCKET \
  --s3-key chatbot-layer.zip \
  --environment \
    Variables="{
      GROQ_API_KEY=$(echo $GROQ_API_KEY | sed 's/\$/\\$/g'),
      OPENAI_API_KEY=$(echo $OPENAI_API_KEY | sed 's/\$/\\$/g'),
      ENDURANCE_ENV=aws,
      S3_DOCS_PATH=s3://$DOCS_BUCKET/,
      AWS_REGION=ap-south-1
    }" \
  --region ap-south-1

# Get function ARN
CHATBOT_ARN=$(aws lambda get-function \
  --function-name endurance-chatbot \
  --region ap-south-1 \
  --query 'Configuration.FunctionArn' \
  --output text)

echo "Chatbot Lambda ARN: $CHATBOT_ARN"
```

#### Step 3.2: Create Endurance API Lambda Function

```bash
# Create Lambda function for Endurance
aws lambda create-function \
  --function-name endurance-api \
  --runtime python3.11 \
  --role $ROLE_ARN \
  --handler lambda_handler.handler \
  --timeout 30 \
  --memory-size 512 \
  --s3-bucket $DEPLOY_BUCKET \
  --s3-key endurance-layer.zip \
  --environment \
    Variables="{
      ENDURANCE_ENV=aws,
      AWS_REGION=ap-south-1
    }" \
  --region ap-south-1

# Get function ARN
ENDURANCE_ARN=$(aws lambda get-function \
  --function-name endurance-api \
  --region ap-south-1 \
  --query 'Configuration.FunctionArn' \
  --output text)

echo "Endurance Lambda ARN: $ENDURANCE_ARN"
```

✅ **PHASE 3 Complete** - Lambda functions deployed!

---

### PHASE 4: Create API Gateway (25 mins)

#### Step 4.1: Create API Gateway

```bash
# Create API Gateway
API_ID=$(aws apigateway create-rest-api \
  --name "Endurance RAI API" \
  --description "Chatbot and Metrics Evaluation API" \
  --region ap-south-1 \
  --query 'id' \
  --output text)

echo "API Gateway ID: $API_ID"

# Get root resource
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --region ap-south-1 \
  --query 'items[0].id' \
  --output text)

echo "Root Resource ID: $ROOT_ID"
```

#### Step 4.2: Create /chat Endpoint (Chatbot)

```bash
# Create /chat resource
CHAT_RESOURCE=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part chat \
  --region ap-south-1 \
  --query 'id' \
  --output text)

# Create POST method for /chat
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $CHAT_RESOURCE \
  --http-method POST \
  --authorization-type NONE \
  --region ap-south-1

# Create Lambda integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $CHAT_RESOURCE \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/${CHATBOT_ARN}/invocations" \
  --region ap-south-1

# Grant API Gateway permission to invoke Lambda
aws lambda add-permission \
  --function-name endurance-chatbot \
  --statement-id AllowAPIGatewayInvoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:ap-south-1:*:${API_ID}/*/*" \
  --region ap-south-1
```

#### Step 4.3: Create /evaluate Endpoint (Endurance API)

```bash
# Create /evaluate resource
EVAL_RESOURCE=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part evaluate \
  --region ap-south-1 \
  --query 'id' \
  --output text)

# Create POST method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $EVAL_RESOURCE \
  --http-method POST \
  --authorization-type NONE \
  --region ap-south-1

# Create Lambda integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $EVAL_RESOURCE \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/${ENDURANCE_ARN}/invocations" \
  --region ap-south-1

# Grant permission
aws lambda add-permission \
  --function-name endurance-api \
  --statement-id AllowAPIGatewayInvoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:ap-south-1:*:${API_ID}/*/*" \
  --region ap-south-1
```

#### Step 4.4: Create Health Check Endpoint

```bash
# Create /health resource
HEALTH_RESOURCE=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part health \
  --region ap-south-1 \
  --query 'id' \
  --output text)

# Create GET method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $HEALTH_RESOURCE \
  --http-method GET \
  --authorization-type NONE \
  --region ap-south-1

# Create mock integration (simple response)
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $HEALTH_RESOURCE \
  --http-method GET \
  --type MOCK \
  --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
  --region ap-south-1

# Create method response
aws apigateway put-method-response \
  --rest-api-id $API_ID \
  --resource-id $HEALTH_RESOURCE \
  --http-method GET \
  --status-code 200 \
  --region ap-south-1

# Create integration response
aws apigateway put-integration-response \
  --rest-api-id $API_ID \
  --resource-id $HEALTH_RESOURCE \
  --http-method GET \
  --status-code 200 \
  --response-templates '{"application/json": "{\"status\": \"healthy\", \"timestamp\": \"$(context.requestTime)\"}"}' \
  --region ap-south-1
```

#### Step 4.5: Deploy API

```bash
# Create deployment stage
DEPLOYMENT=$(aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --region ap-south-1 \
  --query 'id' \
  --output text)

echo "Deployment ID: $DEPLOYMENT"

# Get the API endpoint URL
API_ENDPOINT="https://${API_ID}.execute-api.ap-south-1.amazonaws.com/prod"
echo "API Endpoint: $API_ENDPOINT"

# Save this for later use!
echo $API_ENDPOINT > api-endpoint.txt
```

✅ **PHASE 4 Complete** - API Gateway deployed!

---

### PHASE 5: Deploy Frontend (CloudFront + S3) (20 mins)

⚠️ **Note**: If you don't have a frontend yet, skip to Step 5.3

#### Step 5.1: Build Frontend (if exists)

```bash
# If you have a React/Vite dashboard
cd dashboard
npm install
npm run build

# Get the dist folder ready
ls -la dist/
```

#### Step 5.2: Upload Frontend to S3

```bash
# Upload static files
aws s3 sync dist/ s3://$DASH_BUCKET/ \
  --delete \
  --cache-control "max-age=3600" \
  --region ap-south-1

# Set bucket policy for public read
cat > bucket-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicRead",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::BUCKET_NAME/*"
    }
  ]
}
EOF

# Replace BUCKET_NAME with your actual bucket name
sed -i "s/BUCKET_NAME/$DASH_BUCKET/g" bucket-policy.json

# Apply policy
aws s3api put-bucket-policy \
  --bucket $DASH_BUCKET \
  --policy file://bucket-policy.json
```

#### Step 5.3: Create CloudFront Distribution

```bash
# Create CloudFront distribution config
cat > cloudfront-config.json << 'EOF'
{
  "CallerReference": "endurance-$(date +%s)",
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3Origin",
        "DomainName": "BUCKET_NAME.s3.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3Origin",
    "ViewerProtocolPolicy": "redirect-to-https",
    "TrustedSigners": {
      "Enabled": false,
      "Quantity": 0
    },
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {
        "Forward": "none"
      }
    },
    "MinTTL": 0,
    "DefaultTTL": 3600,
    "MaxTTL": 86400
  },
  "CacheBehaviors": {
    "Quantity": 0
  },
  "CustomErrorResponses": {
    "Quantity": 1,
    "Items": [
      {
        "ErrorCode": 404,
        "ResponsePagePath": "/index.html",
        "ResponseCode": "200",
        "ErrorCachingMinTTL": 300
      }
    ]
  },
  "Enabled": true,
  "Comment": "Endurance RAI Dashboard"
}
EOF

# Replace bucket name
sed -i "s/BUCKET_NAME/$DASH_BUCKET/g" cloudfront-config.json

# Create distribution
DISTRIBUTION=$(aws cloudfront create-distribution \
  --distribution-config file://cloudfront-config.json \
  --region ap-south-1 \
  --query 'Distribution.Id' \
  --output text)

echo "CloudFront Distribution ID: $DISTRIBUTION"

# Get domain name
CDN_DOMAIN=$(aws cloudfront get-distribution \
  --id $DISTRIBUTION \
  --region ap-south-1 \
  --query 'Distribution.DomainName' \
  --output text)

echo "CDN URL: https://$CDN_DOMAIN"
```

✅ **PHASE 5 Complete** - Frontend deployed!

---

### PHASE 6: Configure Environment Variables (10 mins)

#### Step 6.1: Update Lambda Environment Variables with API Gateway URL

```bash
# Update Chatbot Lambda
aws lambda update-function-configuration \
  --function-name endurance-chatbot \
  --environment \
    Variables="{
      GROQ_API_KEY=$GROQ_API_KEY,
      OPENAI_API_KEY=$OPENAI_API_KEY,
      ENDURANCE_ENV=aws,
      S3_DOCS_PATH=s3://$DOCS_BUCKET/,
      ENDURANCE_LAMBDA_URL=$API_ENDPOINT/evaluate,
      AWS_REGION=ap-south-1
    }" \
  --region ap-south-1
```

#### Step 6.2: Update Frontend Configuration

Create a `.env.production` file in your frontend:

```env
VITE_API_BASE_URL=https://{API_ID}.execute-api.ap-south-1.amazonaws.com/prod
VITE_CHAT_ENDPOINT=/chat
VITE_EVALUATE_ENDPOINT=/evaluate
VITE_HEALTH_ENDPOINT=/health
```

Then rebuild and redeploy:

```bash
npm run build
aws s3 sync dist/ s3://$DASH_BUCKET/ --delete
```

✅ **PHASE 6 Complete** - Environment configured!

---

## Testing & Validation

### Test 1: Health Check

```bash
API_ENDPOINT=$(cat api-endpoint.txt)

curl -X GET \
  ${API_ENDPOINT}/health \
  -H "Content-Type: application/json"

# Expected response:
# {"status":"healthy","timestamp":"..."}
```

### Test 2: Chat Endpoint

```bash
curl -X POST \
  ${API_ENDPOINT}/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the IT budget for 2023?",
    "session_id": "test-session-1",
    "include_evaluation": true
  }'

# This should return:
# {
#   "session_id": "...",
#   "message": "...",
#   "response": "...",
#   "sources": [...],
#   "evaluation": {...}
# }
```

### Test 3: Evaluation Endpoint

```bash
curl -X POST \
  ${API_ENDPOINT}/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the WFH policy?",
    "response": "The WFH policy allows employees...",
    "documents": [
      {
        "id": "doc1",
        "source": "WFH_Policy_2023.md",
        "content": "..."
      }
    ]
  }'
```

### Test 4: Check CloudWatch Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/endurance-chatbot \
  --follow \
  --region ap-south-1

# View API Gateway logs
aws logs tail /aws/apigateway/endurance-api \
  --follow \
  --region ap-south-1
```

---

## Monitoring & Optimization

### CloudWatch Dashboard

```bash
# Create custom dashboard
aws cloudwatch put-dashboard \
  --dashboard-name "Endurance-RAI-Dashboard" \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            [ "AWS/Lambda", "Duration", { "stat": "Average" } ],
            [ ".", "Errors", { "stat": "Sum" } ],
            [ ".", "Throttles", { "stat": "Sum" } ],
            [ "AWS/ApiGateway", "Count", { "stat": "Sum" } ],
            [ "AWS/DynamoDB", "ConsumedWriteCapacityUnits" ]
          ],
          "period": 300,
          "stat": "Average",
          "region": "ap-south-1",
          "title": "Endurance Platform Metrics"
        }
      }
    ]
  }'
```

### Cost Monitoring

```bash
# Set up billing alerts
aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget file://budget.json
```

**budget.json**:
```json
{
  "BudgetName": "Endurance-Free-Tier",
  "BudgetLimit": {
    "Amount": "100",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
```

---

## Cost Optimization Tips

### 1. Lambda Cold Starts
- **Problem**: First invocation takes 2-5 seconds
- **Solution**: 
  ```bash
  # Add provisioned concurrency (but this costs money!)
  # For free tier, just accept cold starts
  ```

### 2. DynamoDB On-Demand Pricing
- **Free Tier**: 25GB storage + 1B read/write units per month
- **Cost after**: $1.25 per GB + $0.25 per million write units
- **Optimization**: Archive old sessions monthly to S3

### 3. OpenAI Embeddings Cost
- **Free Trial**: $5 credit (lasts ~5 months)
- **Alternative**: Use Groq's free embeddings (slower but free)
- **Switch code**:
  ```python
  # In chatbot/chain.py
  from langchain_ollama import OllamaEmbeddings
  embeddings = OllamaEmbeddings(model="all-minilm")  # Free
  ```

### 4. API Gateway Caching
```bash
# Enable caching to reduce Lambda invocations
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name prod \
  --patch-operations \
    op=replace,path=/cacheClusterEnabled,value=true \
    op=replace,path=/cacheClusterSize,value=0.5 \
  --region ap-south-1
```

---

## Troubleshooting

### Issue: Lambda Timeout
**Solution**:
```bash
# Increase timeout from 30s to 60s
aws lambda update-function-configuration \
  --function-name endurance-chatbot \
  --timeout 60 \
  --region ap-south-1
```

### Issue: "Module not found" in Lambda
**Solution**:
```bash
# Ensure all dependencies are in the ZIP file
cd lambda-packages/chatbot/package
pip install -r requirements.txt --target .
zip -r ../chatbot-layer.zip .
```

### Issue: CORS Errors
**Solution**: Already enabled in FastAPI code, but if needed:
```bash
# Create CORS responses at API Gateway level
# (Already handled in chatbot/api.py and api/main.py)
```

### Issue: "Credentials not found" in Lambda
**Solution**: Ensure IAM role has proper permissions (see Step 2.3)

### Issue: S3 Documents Not Found
**Solution**:
```bash
# Verify documents uploaded
aws s3 ls s3://$DOCS_BUCKET/ --recursive

# Check Lambda environment variable
aws lambda get-function-configuration \
  --function-name endurance-chatbot \
  --query 'Environment' \
  --region ap-south-1
```

---

## Next Steps

### Phase 7: Custom Domain (Optional, +$0.50/month)
```bash
# Register domain on Route53
# Create certificate in ACM
# Update CloudFront distribution with custom domain
```

### Phase 8: Auto-Scaling (Optional, Free)
```bash
# Lambda auto-scales automatically (no configuration needed)
# DynamoDB on-demand scales automatically
```

### Phase 9: CI/CD Pipeline (Optional, Free)
```bash
# Use GitHub Actions to auto-deploy on push
# Setup CodePipeline for automated deployments
```

---

## Summary

✅ **What You've Deployed**:
- [x] Chatbot API (RAG with LangChain)
- [x] Endurance Metrics API (Evaluation engine)
- [x] DynamoDB database (sessions, feedback, logs)
- [x] S3 storage (documents, frontend)
- [x] API Gateway (REST endpoints)
- [x] CloudFront CDN (frontend delivery)
- [x] CloudWatch monitoring (logs, metrics)

✅ **Total Cost**: **$0-10/month** (well within $100 budget)

✅ **Performance**: 
- API latency: 200-500ms (depending on cold starts)
- Concurrent users: 1,000+ (API Gateway limit)
- Storage: Unlimited (within free tier)

---

## Additional Resources

- [AWS Free Tier](https://aws.amazon.com/free)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [LangChain AWS Integration](https://python.langchain.com/docs/integrations/platforms/aws)
- [Groq API Documentation](https://console.groq.com/docs)

---

**Last Updated**: February 2026  
**Status**: Ready for Production ✅
