# Cloud Engineer Deployment Guide
## Endurance Platform - AWS Deployment

---

## Current Status ✅

The following components are **complete and tested locally**:

| Component | Status | Port | Technology |
|-----------|--------|------|------------|
| Endurance API | ✅ Ready | 8000 | FastAPI |
| Chatbot API | ✅ Ready | 8001 | FastAPI + LangChain |
| Dashboard | ✅ Ready | 5173 | React + Vite |
| Vector Store | ✅ Ready | - | ChromaDB |

---

## What Needs AWS Deployment

### 1. Endurance API (Metrics Engine)

**Location**: `api/main.py`

```
Deploy as: Lambda + API Gateway
Memory: 512MB minimum
Timeout: 30 seconds
Python: 3.11+
```

**Dependencies** (from pyproject.toml):
- fastapi, uvicorn, pydantic
- numpy, scikit-learn
- httpx, python-multipart

**Endpoints to expose**:
```
POST /v1/evaluate      - Main evaluation endpoint
GET  /v1/metrics       - Get dimension definitions
GET  /v1/sessions/{id} - Get session history
POST /v1/feedback      - Submit human feedback
GET  /health           - Health check
```

### 2. Chatbot API (RAG Service)

**Location**: `chatbot/api.py`

```
Deploy as: Lambda + API Gateway (or ECS for persistent vector store)
Memory: 1024MB minimum (embeddings are memory-intensive)
Timeout: 60 seconds
Python: 3.11+
```

**Environment Variables Required**:
```bash
GROQ_API_KEY=gsk_...          # Groq LLM API key
OPENAI_API_KEY=sk-proj-...    # OpenAI embeddings key
ENDURANCE_ENV=aws             # Switches to AWS mode
ENDURANCE_LAMBDA_URL=https://xxx.execute-api.region.amazonaws.com/prod
S3_DOCS_PATH=s3://endurance-docs/
```

**Dependencies**:
- langchain, langchain-openai, langchain-groq
- chromadb (local) → FAISS with S3 (AWS)

**Endpoints**:
```
POST /chat      - Main chat endpoint
GET  /sources   - Get relevant documents
POST /reload    - Reload vector store
GET  /health    - Health check
```

### 3. RAG Documents → S3

**Current Location**: `chatbot/rag_docs/`

Upload these files to S3:
```
s3://endurance-docs/
├── IT_Budget_Statement_2022-23.md
├── Employee_Statistics_2023.md
├── WFH_Policy_2023.md
└── Procurement_Register_2022-23.md
```

### 4. Dashboard → S3 + CloudFront

**Location**: `dashboard/`

```bash
cd dashboard
npm run build
# Upload dist/ to S3 static hosting
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          AWS Cloud                                  │
│                                                                     │
│   ┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐  │
│   │ CloudFront  │────▶│  S3 (Dashboard) │     │  S3 (RAG Docs)  │  │
│   └─────────────┘     └─────────────────┘     └────────┬────────┘  │
│                                                         │           │
│   ┌─────────────┐     ┌─────────────────┐              │           │
│   │ API Gateway │────▶│ Lambda          │◀─────────────┘           │
│   │ /chat       │     │ (Chatbot API)   │                          │
│   └─────────────┘     └────────┬────────┘                          │
│                                │                                    │
│                                ▼                                    │
│   ┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐  │
│   │ API Gateway │────▶│ Lambda          │────▶│ DynamoDB        │  │
│   │ /evaluate   │     │ (Endurance API) │     │ (Session Store) │  │
│   └─────────────┘     └─────────────────┘     └─────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Deployment Steps

### Step 1: Create S3 Buckets

```bash
aws s3 mb s3://endurance-dashboard --region ap-south-1
aws s3 mb s3://endurance-docs --region ap-south-1
```

### Step 2: Upload RAG Documents

```bash
aws s3 sync chatbot/rag_docs/ s3://endurance-docs/
```

### Step 3: Package Lambda Functions

Use AWS SAM or Serverless Framework:

```yaml
# serverless.yml
service: endurance

provider:
  name: aws
  runtime: python3.11
  region: ap-south-1

functions:
  endurance-api:
    handler: api.main.handler
    events:
      - http: ANY /v1/{proxy+}
    environment:
      PYTHONPATH: /var/task

  chatbot-api:
    handler: chatbot.api.handler
    events:
      - http: ANY /chat
    environment:
      GROQ_API_KEY: ${env:GROQ_API_KEY}
      OPENAI_API_KEY: ${env:OPENAI_API_KEY}
      ENDURANCE_LAMBDA_URL: !GetAtt EnduranceApiLambda.Arn
```

### Step 4: Deploy Dashboard

```bash
cd dashboard
npm run build
aws s3 sync dist/ s3://endurance-dashboard/ --delete
```

---

## Testing AWS Deployment

Once deployed, test with:

```bash
# Health check
curl https://your-api-gateway-url/health

# Chat test
curl -X POST https://your-api-gateway-url/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the IT budget?", "include_evaluation": true}'
```

---

## Questions for Cloud Engineer

1. **VPC Requirements**: Do we need private subnets for Lambda?
2. **WAF**: Enable AWS WAF for API Gateway?
3. **Monitoring**: CloudWatch dashboards for Lambda metrics?
4. **Cost Optimization**: Reserved concurrency for Lambda?

---

**Contact**: Message on Slack if blocked on any step.
