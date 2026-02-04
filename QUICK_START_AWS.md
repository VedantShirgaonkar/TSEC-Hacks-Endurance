# AWS Free Tier Deployment - Quick Start (15 Min Overview)

## TL;DR - What You'll Deploy

```
Your RAG App on AWS:
├── API Layer (Lambda) - Chatbot & Metrics APIs
├── Storage (S3) - Documents & Frontend
├── Database (DynamoDB) - Sessions & Feedback
├── CDN (CloudFront) - Fast Frontend delivery
└── Monitoring (CloudWatch) - Logs & Metrics

Total Cost: $0/month (within free tier limits)
```

---

## Prerequisites (5 mins)

### 1. Get API Keys
```bash
# Groq (Free, up to 5K requests/month)
# Go to: https://console.groq.com → API Keys → Create
export GROQ_API_KEY=gsk_abc123...

# OpenAI (Free $5 credit)
# Go to: https://platform.openai.com → API Keys → Create
export OPENAI_API_KEY=sk-proj-abc123...
```

### 2. Configure AWS
```bash
# Install AWS CLI
brew install awscli

# Login to AWS
aws configure
# Enter: Access Key, Secret Key, Region (ap-south-1), Output (json)

# Verify
aws sts get-caller-identity
```

### 3. Verify Your App
```bash
# Test locally first
cd /path/to/TSEC-Hacks-Endurance
python3 -m chatbot.api  # Should work
python3 -m api.main     # Should work
```

---

## Deployment (10 mins)

### Step 1: Create Infrastructure (3 mins)

```bash
# Create S3 buckets for storage
SUFFIX=$(date +%s)
aws s3 mb s3://endurance-docs-$SUFFIX
aws s3 mb s3://endurance-dashboard-$SUFFIX
aws s3 mb s3://endurance-lambda-deploy-$SUFFIX

# Upload your documents
aws s3 sync ./chatbot/rag_docs s3://endurance-docs-$SUFFIX/

# Create DynamoDB tables
aws dynamodb create-table \
  --table-name endurance-sessions \
  --attribute-definitions AttributeName=session_id,AttributeType=S \
  --key-schema AttributeName=session_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# (See guide for other tables)
```

### Step 2: Package Lambda Code (4 mins)

```bash
# Chatbot Lambda
mkdir lambda-chatbot && cd lambda-chatbot
python3 -m venv venv && source venv/bin/activate
pip install fastapi mangum langchain langchain-openai langchain-groq chromadb
cp -r ../chatbot . && cp -r ../endurance .

cat > lambda_handler.py << 'EOF'
from mangum import Mangum
from chatbot.api import app
handler = Mangum(app)
EOF

pip install -r requirements.txt --target ./package
cp -r chatbot endurance lambda_handler.py ./package/
cd package && zip -r ../function.zip . && cd ..
aws s3 cp function.zip s3://endurance-lambda-deploy-$SUFFIX/
cd ..
```

### Step 3: Deploy to AWS (3 mins)

```bash
# Create IAM role
aws iam create-role \
  --role-name endurance-lambda-role \
  --assume-role-policy-document file://trust.json
# (See guide for trust.json content)

# Deploy Lambda
aws lambda create-function \
  --function-name endurance-chatbot \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT:role/endurance-lambda-role \
  --handler lambda_handler.handler \
  --timeout 60 \
  --memory-size 1024 \
  --s3-bucket endurance-lambda-deploy-$SUFFIX \
  --s3-key function.zip \
  --environment Variables="{GROQ_API_KEY=$GROQ_API_KEY,OPENAI_API_KEY=$OPENAI_API_KEY}"

# (See guide for API Gateway setup)
```

---

## After Deployment

### Your New Endpoints
```bash
# Chat API
curl -X POST https://YOUR_API_GATEWAY/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is the IT budget?"}'

# Metrics API
curl -X POST https://YOUR_API_GATEWAY/evaluate \
  -H "Content-Type: application/json" \
  -d '{"query":"...","response":"...","documents":[...]}'

# Health Check
curl https://YOUR_API_GATEWAY/health
```

### Frontend
```bash
# Upload to S3
npm run build
aws s3 sync dist/ s3://endurance-dashboard-$SUFFIX/

# Access via CloudFront
# (Created in detailed guide)
```

---

## Cost Reality Check

### What You Get (Free)
- 1M Lambda requests/month
- 400K GB-seconds compute/month
- 1M API Gateway requests/month
- 5GB S3 storage
- 25GB DynamoDB + 1B writes/month
- 1TB CloudFront transfer
- 5GB CloudWatch logs

### Monthly Bill
```
AWS Services:    $0 (all free tier)
Groq API:        $0 (5K free requests)
OpenAI (first 5 months): $0 (with $5 credit)
─────────────
TOTAL:           $0 - $10/month
```

---

## Common Issues & Fixes

| Problem | Solution |
|---------|----------|
| "ModuleNotFoundError" in Lambda | Ensure all dependencies in ZIP file |
| Lambda timeout | Increase timeout from 30s → 60s |
| API Gateway CORS error | Already enabled in FastAPI code |
| S3 access denied | Check IAM role permissions |
| Can't find documents | Verify S3 upload path matches code |

See full guide for detailed troubleshooting.

---

## Next: Choose Your Path

### Path A: Automated (Recommended)
```bash
# Run deployment script (handles most steps)
bash aws-deploy.sh
bash aws-deploy-lambdas.sh
bash aws-deploy-apigateway.sh
```

### Path B: Manual (For Learning)
```bash
# Follow step-by-step guide
cat docs/AWS_DEPLOYMENT_FREETIER_GUIDE.md
```

### Path C: Web Console (Slowest)
```bash
# Use AWS console at https://console.aws.amazon.com
# No command line needed, but takes longer
```

---

## Monitor Your Deployment

```bash
# View Lambda logs
aws logs tail /aws/lambda/endurance-chatbot --follow

# Check function status
aws lambda get-function --function-name endurance-chatbot

# View DynamoDB usage
aws dynamodb scan --table-name endurance-sessions --select COUNT

# Check current spend
aws ce get-cost-and-usage \
  --time-period Start=2024-02-01,End=2024-02-28 \
  --granularity MONTHLY \
  --metrics BlendedCost
```

---

## Success Criteria ✓

After deployment, you should have:

- [ ] 2 S3 buckets created and populated
- [ ] 3 DynamoDB tables accessible
- [ ] 2 Lambda functions running
- [ ] API Gateway with /chat and /evaluate endpoints
- [ ] CloudFront serving your frontend
- [ ] All tests passing
- [ ] CloudWatch logs available
- [ ] $0 AWS charges

---

## Still Have Questions?

| What | Where |
|------|-------|
| Detailed step-by-step guide | `docs/AWS_DEPLOYMENT_FREETIER_GUIDE.md` |
| Complete checklist | `AWS_DEPLOYMENT_CHECKLIST.md` |
| Deployment script | `aws-deploy.sh` |
| Architecture diagrams | Same guides (see ASCII art) |
| Cost calculator | AWS Free Tier page |
| AWS CLI reference | `aws help` |

---

## Estimated Timeline

```
Setup AWS:              10 mins
Create infrastructure:  15 mins
Package code:           20 mins
Deploy Lambda:          10 mins
Setup API Gateway:      15 mins
Deploy frontend:        10 mins
Test & verify:          10 mins
─────────────────────────────
TOTAL:                 ~90 mins
```

---

## Save These For Later

```bash
# Save your API endpoint
API_URL=$(aws apigateway get-rest-apis --query 'items[0].id' --output text)
REGION=ap-south-1
STAGE=prod
echo "https://${API_URL}.execute-api.${REGION}.amazonaws.com/${STAGE}"

# Save bucket names
aws s3 ls | grep endurance

# Save Lambda ARNs
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `endurance`)].FunctionArn'
```

---

**Ready to deploy?** Start with the full guide or use the automation script!

Generated: February 2026
