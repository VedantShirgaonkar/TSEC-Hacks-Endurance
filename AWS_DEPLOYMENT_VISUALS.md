# AWS Deployment - Visual Reference

## Your App Components

### What You Have (Local)
```
Your Laptop
├── Python FastAPI Server 1 (Port 8000)
│   ├── api/main.py
│   └── Endurance Metrics Engine
│
├── Python FastAPI Server 2 (Port 8001)
│   ├── chatbot/api.py
│   ├── LangChain RAG Pipeline
│   ├── Groq LLM calls
│   └── OpenAI embeddings
│
├── React Frontend (Port 5173)
│   └── dashboard/
│
└── Local ChromaDB
    ├── Vector store
    └── Document embeddings
```

### What AWS Handles (Deployed)
```
AWS Cloud
├── Lambda Functions (Serverless Compute)
│   ├── endurance-chatbot (1GB RAM, 60s timeout)
│   ├── endurance-api (512MB RAM, 30s timeout)
│   └── (No servers to manage!)
│
├── API Gateway (REST Endpoints)
│   ├── POST /chat
│   ├── POST /evaluate
│   └── GET /health
│
├── Storage (S3)
│   ├── RAG documents
│   ├── Frontend assets
│   └── Lambda code packages
│
├── Database (DynamoDB)
│   ├── Sessions table
│   ├── Feedback table
│   └── Audit logs table
│
├── CDN (CloudFront)
│   └── Fast frontend delivery
│
└── Monitoring (CloudWatch)
    └── Logs & metrics
```

---

## Request Flow Diagram

### User Asks Question

```
┌──────────────┐
│ User's Browser│
└────────┬─────┘
         │ 1. User asks question
         │ GET https://domain.com
         ▼
    ┌─────────────┐
    │ CloudFront  │ ← Serves frontend (HTML/JS)
    │ CDN         │   from S3, cached
    └────────┬────┘
             │ 2. Send API request
             │ POST /chat (JSON)
             ▼
         ┌────────────────┐
         │ API Gateway    │ ← Routes to Lambda
         │ REST API       │   Handles HTTPS, CORS
         └────────┬───────┘
                  │ 3. Invoke Lambda
                  ▼
          ┌────────────────────┐
          │ Lambda Function    │ ← Your chatbot API code
          │ (Chatbot API)      │   Runs when called
          └────────┬───────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
    ┌────────────┐      ┌──────────────┐
    │ Groq API   │      │ OpenAI API   │
    │ (LLM)      │      │ (Embeddings) │
    │ External   │      │ External     │
    └────────┬───┘      └────────┬─────┘
             │                   │
             └────────┬──────────┘
                      │ 4. Process query
                      │ Search documents
                      ▼
              ┌─────────────────┐
              │ S3 Bucket       │ ← Get RAG documents
              │ (Documents)     │   Already in S3
              └────────┬────────┘
                       │ 5. Search & match
                       ▼
            ┌──────────────────────┐
            │ Groq LLM Response    │ ← Get answer with sources
            │ (Streamed or direct) │
            └────────┬─────────────┘
                     │ 6. Save to DB
                     ▼
          ┌─────────────────────────┐
          │ DynamoDB               │ ← Store session
          │ (sessions table)        │
          └────────┬────────────────┘
                   │ 7. Maybe run evaluation
                   ▼
         ┌──────────────────────┐
         │ Lambda Function 2    │ ← Your metrics API code
         │ (Endurance API)      │   Evaluates response quality
         └────────┬─────────────┘
                  │ 8. Compute metrics
                  ▼
       ┌──────────────────────────┐
       │ DynamoDB               │ ← Store evaluation results
       │ (audit_logs table)      │
       └────────┬─────────────────┘
                │ 9. Return to browser
                ▼
         ┌──────────────────┐
         │ Browser          │ ← Display response + evaluation
         │ Shows answer     │
         │ & metrics        │
         └──────────────────┘
```

---

## Cost Flow Diagram

```
Your $100 Budget
│
├─ AWS Free Tier (Month 1-12)
│  │
│  ├─ 1M Lambda requests ($0)
│  ├─ 1M API Gateway requests ($0)
│  ├─ 400K GB-seconds compute ($0)
│  ├─ 5GB S3 storage ($0)
│  ├─ 25GB DynamoDB ($0)
│  ├─ 1TB CloudFront ($0)
│  ├─ 5GB CloudWatch logs ($0)
│  │
│  └─ Subtotal: $0/month × 12 = $0
│
├─ External APIs (Month 1-12)
│  │
│  ├─ Groq LLM (free tier)
│  │  ├─ 5,000 requests/month
│  │  ├─ Your usage: ~100-500/month
│  │  └─ Cost: $0/month
│  │
│  ├─ OpenAI Embeddings (free tier + paid)
│  │  ├─ First 5 months: $5 credit each = $25 total
│  │  ├─ Month 6+: $0.02 per 1M tokens (~$0.10/mo)
│  │  └─ Cost: ~$1-10 over 12 months
│  │
│  └─ Subtotal: $0-10 over 12 months
│
└─ TOTAL: $0-10/month = Uses only 10% of your $100 budget!
   
   Remaining after 12 months: $90 for other services
```

---

## Deployment Timeline

```
Hour 0
│
├─ 0:00 - 0:15 → Setup (AWS credentials, API keys)
│                └─ aws configure
│                └─ export GROQ_API_KEY=...
│
├─ 0:15 - 0:45 → Phase 1: AWS Foundation (30 mins)
│                ├─ Create S3 buckets (3)
│                ├─ Create DynamoDB tables (3)
│                ├─ Upload documents
│                └─ Create IAM role
│
├─ 0:45 - 1:30 → Phase 2: Package Lambda (45 mins)
│                ├─ Create virtual environments
│                ├─ Install dependencies
│                ├─ Create Lambda handlers
│                └─ Package and upload to S3
│
├─ 1:30 - 2:00 → Phase 3: Deploy Lambda (30 mins)
│                ├─ Create Lambda functions
│                ├─ Set environment variables
│                └─ Verify functions exist
│
├─ 2:00 - 2:25 → Phase 4: API Gateway (25 mins)
│                ├─ Create API Gateway
│                ├─ Add endpoints (/chat, /evaluate, /health)
│                ├─ Connect to Lambda functions
│                └─ Deploy to prod stage
│
├─ 2:25 - 2:45 → Phase 5: Frontend (20 mins)
│                ├─ Build React app (npm run build)
│                ├─ Upload to S3
│                └─ Create CloudFront distribution
│
├─ 2:45 - 3:00 → Phase 6: Testing (15 mins)
│                ├─ Test /health endpoint
│                ├─ Test /chat endpoint
│                ├─ Test /evaluate endpoint
│                └─ Verify CloudWatch logs
│
└─ 3:00 ✅ Done! Your app is live on AWS!
```

---

## Free Tier Limits vs Your Usage

```
Service                 | Free Limit              | Your Usage    | % Used
────────────────────────────────────────────────────────────────────────
Lambda requests/month   | 1,000,000               | ~30,000       | 3%
Lambda GB-seconds/month | 400,000                 | ~10,000       | 2.5%
API Gateway requests    | 1,000,000               | ~30,000       | 3%
S3 storage              | 5 GB                    | ~0.1 GB       | 2%
S3 outbound transfer    | 100 GB/month            | ~0.1 GB       | 0.1%
DynamoDB storage        | 25 GB                   | ~0.1 GB       | 0.4%
DynamoDB write units    | 1 billion/month         | ~100,000      | 0.01%
CloudFront transfer     | 1 TB/month              | ~0.1 GB       | 0.01%
CloudWatch logs         | 5 GB/month              | ~0.1 GB       | 2%

✅ All services stay within free tier!
```

---

## AWS Services You're Using

### Lambda (Compute)
```
Function 1: endurance-chatbot
├─ Handler: lambda_handler.handler
├─ Runtime: Python 3.11
├─ Memory: 1024 MB (increased for embeddings)
├─ Timeout: 60 seconds (for LLM calls)
├─ VPC: None (for faster startup)
└─ Trigger: API Gateway /chat

Function 2: endurance-api
├─ Handler: lambda_handler.handler
├─ Runtime: Python 3.11
├─ Memory: 512 MB (for metrics computation)
├─ Timeout: 30 seconds (fast calculations)
├─ VPC: None
└─ Trigger: API Gateway /evaluate
```

### API Gateway (REST API)
```
API: "Endurance RAI API"
├─ Type: REST API
├─ Stage: prod
├─ Endpoints:
│  ├─ POST /chat → Lambda: endurance-chatbot
│  ├─ POST /evaluate → Lambda: endurance-api
│  └─ GET /health → Mock response
├─ CORS: Enabled
├─ Throttling: 10,000 requests/second
└─ Domain: https://API_ID.execute-api.ap-south-1.amazonaws.com/prod
```

### S3 (Object Storage)
```
Bucket 1: endurance-dashboard-XXXXX
├─ Purpose: Frontend assets (HTML, CSS, JS)
├─ Policy: Public read
├─ Size: ~50 MB typical
└─ CloudFront: Yes (distribution attached)

Bucket 2: endurance-docs-XXXXX
├─ Purpose: RAG documents
├─ Content: MD files (4 × 500KB each)
├─ Size: ~2 MB
└─ Lambda access: Yes (via IAM role)

Bucket 3: endurance-lambda-deploy-XXXXX
├─ Purpose: Lambda deployment packages
├─ Content: ZIP files (chatbot + metrics)
├─ Size: ~50 MB each
└─ Versioning: Enabled
```

### DynamoDB (NoSQL Database)
```
Table 1: endurance-sessions
├─ Partition Key: session_id (string)
├─ Sort Key: timestamp (number)
├─ TTL: None (keep forever)
├─ Capacity Mode: On-demand (auto-scales)
└─ Estimated Size: <1 GB for 1 year of data

Table 2: endurance-feedback
├─ Partition Key: feedback_id (string)
├─ Sort Key: None
├─ TTL: None
├─ Capacity Mode: On-demand
└─ Estimated Size: <10 MB

Table 3: endurance-audit-logs
├─ Partition Key: log_id (string)
├─ Sort Key: timestamp (number)
├─ TTL: Yes (90 days, then auto-delete)
├─ Capacity Mode: On-demand
└─ Estimated Size: <100 MB (old logs auto-deleted)
```

### CloudFront (CDN)
```
Distribution: Endurance Dashboard
├─ Origin: S3 bucket (endurance-dashboard-XXXXX)
├─ Edge Locations: Automatically chosen by AWS
├─ Cache TTL: 
│  ├─ index.html: 1 hour
│  └─ Static assets: 24 hours
├─ HTTPS: Automatic (CloudFront certificate)
├─ Domain: d123xyz.cloudfront.net
└─ Free transfer: Up to 1 TB/month
```

### CloudWatch (Monitoring)
```
Logs:
├─ /aws/lambda/endurance-chatbot
│  └─ Auto-created when Lambda runs
├─ /aws/lambda/endurance-api
│  └─ Auto-created when Lambda runs
└─ /aws/apigateway/endurance-api
   └─ Optional, can enable in API Gateway

Metrics:
├─ Lambda Duration (how long each call takes)
├─ Lambda Errors (failed invocations)
├─ Lambda Throttles (if too many concurrent calls)
├─ API Gateway Count (number of requests)
└─ DynamoDB Consumed Write/Read Units

Alarms (Optional):
├─ Alert if errors > 5/minute
├─ Alert if Lambda duration > 30s
└─ Alert if estimated bill > $10
```

---

## Networking & Security

```
Internet Traffic
│
└─► https://YOUR_API_GATEWAY_URL
    │
    ├─ Encrypted (TLS 1.2+)
    ├─ Public endpoint (no VPN needed)
    ├─ Rate limited (10K req/sec default)
    └─ CORS enabled (cross-origin requests allowed)
       │
       └─► API Gateway
           │
           ├─ Authentication: None (or add API keys)
           ├─ Authorization: None (or add cognito)
           ├─ Logging: CloudWatch (optional)
           └─ Throttling: Per-API-key (optional)
              │
              └─► Lambda Execution Role (IAM)
                  │
                  ├─ Can read S3 (documents only)
                  ├─ Can write DynamoDB (specific tables)
                  ├─ Can write CloudWatch logs
                  └─ CANNOT access other AWS resources
                     │
                     └─► Isolates your app (security)
```

---

## Data Flow

### Session Storage
```
User Chat Session
│
├─ Request: {"message": "What is the IT budget?", "session_id": "abc123"}
│
├─ Lambda Function
│  ├─ Call Groq LLM
│  ├─ Get sources from S3
│  ├─ Maybe call Endurance API for evaluation
│  └─ Create response
│
├─ Store in DynamoDB
│  └─ endurance-sessions table
│     ├─ session_id: "abc123"
│     ├─ timestamp: 1707891200
│     ├─ user_message: "What is the IT budget?"
│     ├─ bot_response: "According to IT_Budget_Statement_2022-23.md..."
│     ├─ sources: [...]
│     └─ evaluation: {...}
│
└─ Return to user
   └─ Response: {"session_id": "abc123", "response": "...", "sources": [...]}
      │
      └─ User sees answer in frontend
```

### Log Storage (CloudWatch)
```
Lambda Execution
│
├─ Start: print("[INFO] Starting chat processing")
├─ Progress: print("[INFO] Retrieved 4 documents from S3")
├─ LLM Call: print("[INFO] Calling Groq LLM...")
├─ Response: print("[INFO] LLM returned: ...")
├─ Saving: print("[INFO] Saving to DynamoDB...")
├─ End: print("[INFO] Request completed in 0.53s")
│
└─► CloudWatch Logs
    │
    ├─ Log Group: /aws/lambda/endurance-chatbot
    ├─ Log Stream: 2024/02/15/[$LATEST]abc123def456
    └─ Log Events: Searchable by time, error level, etc.
       │
       └─ Accessible via:
          ├─ AWS Console → CloudWatch → Logs
          ├─ AWS CLI: aws logs tail /aws/lambda/...
          └─ Log Insights: Query logs with SQL-like syntax
```

---

## Troubleshooting Flowchart

```
Something's broken!
│
├─ Is it AWS infrastructure?
│  │
│  ├─ Check AWS Console → CloudWatch → Logs
│  │  └─ Lambda not running? → Wrong handler name?
│  │
│  ├─ Check AWS Console → Lambda → Function
│  │  ├─ Is function created?
│  │  ├─ Does it have an IAM role?
│  │  └─ Are env vars set?
│  │
│  └─ Check AWS Console → DynamoDB → Tables
│     └─ Are tables accessible? → Correct region?
│
├─ Is it API Gateway?
│  │
│  ├─ Check https://URL/health
│  │  └─ 404 or timeout? → Endpoint not created?
│  │
│  └─ Check CORS headers
│     └─ Request blocked? → CORS not enabled?
│
├─ Is it your application code?
│  │
│  ├─ Check Lambda logs in CloudWatch
│  │  └─ "ModuleNotFoundError"? → Missing dependency in ZIP?
│  │
│  ├─ Check environment variables
│  │  └─ "GROQ_API_KEY not found"? → Env var not set?
│  │
│  └─ Test locally first
│     └─ python3 api/main.py
│        python3 chatbot/api.py
│
└─ All else fails:
   │
   ├─ Delete and redeploy (takes 30 mins)
   └─ AWS Support (if on paid tier)
```

---

## Performance Expectations

### First Request (Cold Start)
```
Request arrives at API Gateway
│
├─ Delay: 2-5 seconds (cold start)
│
├─ Lambda initializes
│  ├─ Load Python runtime: ~1s
│  ├─ Load dependencies: ~1s
│  ├─ Load embeddings model: ~2s
│  └─ First request ready: +Actual processing time
│
└─ Cold start over, subsequent requests fast (~0.5s)
```

### Typical Request Timeline
```
Total time: ~1-3 seconds
│
├─ API Gateway ingestion: 50ms
├─ Lambda startup/cold start: 2-5s first time, 0ms later
├─ Your code processing: 200-500ms
│  ├─ Parse input: 10ms
│  ├─ Call Groq LLM: 100-300ms (external)
│  ├─ Call OpenAI embeddings: 50-100ms (external)
│  ├─ Save to DynamoDB: 20-50ms
│  └─ Other processing: 20-50ms
└─ API Gateway response: 50ms
```

### Concurrent Users
```
Lambda Auto-scaling
│
├─ User 1: Starts Lambda instance #1
├─ User 2: Starts Lambda instance #2
├─ User 3: Starts Lambda instance #3 (if #1, #2 busy)
├─ ...
└─ Up to 1,000 concurrent instances (free tier)

If you exceed 1,000 concurrent requests:
├─ AWS throttles request
├─ Returns 429 (Too Many Requests)
└─ User experiences "service busy" error
   (Very unlikely for a government AI app!)
```

---

## Scaling Readiness

```
Current Setup (Free Tier):

Users/Day: 100 ✅
Requests/Day: 500 ✅
Peak Concurrent: 10 ✅
Cost: $0 ✅

When You Need to Scale:

Users/Day: 10,000
├─ Lambda scaling: Automatic ✅
├─ DynamoDB scaling: Automatic ✅
├─ API Gateway: Automatic ✅
├─ Cost: ~$50-100/month ❌ (free tier exceeded)
└─ Solution: Enable reserved capacity, optimize

Users/Day: 1,000,000
├─ Lambda scaling: Maxed out
├─ DynamoDB: Maxed out
├─ API Gateway: Throttled
├─ Cost: $5,000+/month
└─ Solution: Enterprise tier, multiple regions
```

---

This visual reference covers your entire deployment at a glance! 🚀
