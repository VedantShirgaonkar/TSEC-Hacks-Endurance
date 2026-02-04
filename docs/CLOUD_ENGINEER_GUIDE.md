# Cloud Engineer Deployment Guide
## Endurance Platform - AWS Deployment (Fast Backend)

---

## Current Status ✅

The API design is **complete and verified**. We have a fast, asynchronous FastAPI backend ready for deployment.

| Component | Status | Port | Technology |
|-----------|--------|------|------------|
| Endurance API | ✅ READY | 8002 | FastAPI + Async (Metrics Engine) |
| Chatbot API | ✅ READY | 8001 | FastAPI + LangChain (Client) |

---

## Deployment Strategy: "Fast & Free" Architecture

We are targeting **AWS Free Tier** with a high-concurrency serverless architecture.

### 1. Endurance API (The Core Service)

**Description**: The metrics engine that evaluates chatbot conversations in real-time.

**Implementation Details**:
- **Framework**: FastAPI (Async)
- **State**: In-memory `deque` (no database required initially)
- **Concurrency**: Fully non-blocking for high throughput

**Deployment Steps (AWS Lambda)**:
1.  **Package**: Zip `api/` folder + `endurance/` folder + `requirements.txt`.
    *   *Note*: Ensure `numpy` and `scikit-learn` are compatible with Lambda (use AWS Layers or `manylinux` wheels).
2.  **Create Function**: `endurance-api-prod`
    *   Runtime: Python 3.11
    *   Memory: 512 MB (Important for ML interference)
    *   Timeout: 29 seconds (API Gateway limit)
3.  **Function URL**: **Enable Function URL** (Auth type: NONE for public access, or IAM for secured).
4.  **Environment Variables**:
    *   `PYTHONPATH`: `/var/task`

### 2. Chatbot API (The Test Client)

**Description**: A sample government chatbot (RTI Assistant) to demonstrate integration.

**Deployment Steps (AWS Lambda)**:
1.  **Package**: Zip `chatbot/` + `endurance/` (for shared types) + `requirements.txt`.
2.  **Create Function**: `rti-chatbot-prod`
    *   Runtime: Python 3.11
    *   Memory: 1024 MB (Crucial for Embeddings/RAG)
    *   Timeout: 60 seconds
3.  **Function URL**: Enable.
4.  **Environment Variables**:
    *   `GROQ_API_KEY`: `gsk_...` (Get from secure notes)
    *   `OPENAI_API_KEY`: `sk-proj-...`
    *   `ENDURANCE_URL`: `<The URL from Step 1>`
    *   `ENDURANCE_ENV`: `aws`

### 3. Dashboard (The Visuals)

**Deployment Steps (S3 + CloudFront)**:
1.  **Build**: Run `npm run build` in `dashboard/` directory.
2.  **S3 Bucket**: Create `endurance-dashboard-prod` (Block Public Access: OFF or use Policy).
3.  **Upload**: Upload contents of `dist/` to the bucket.
4.  **Web Hosting**: Enable Static Web Hosting in S3 properties.
5.  *(Optional)* **CloudFront**: Set up distribution pointing to S3 for HTTPS and caching.

---

## RAG Context Handling

For the system to evaluate "Data Grounding" and "Hallucinations", it **MUST** receive the retrieved documents (context) used by the LLM.

**Our Protocol**:
The Chatbot (or SDK/Webhook) sends the context in the `evaluate` request body.

```json
POST /v1/evaluate
{
  "query": "What is the budget?",
  "response": "The budget is 100M.",
  "rag_documents": [
    {
      "source": "budget_2024.pdf",
      "content": "The allocated budget for FY24 is 100 Million USD...",
      "score": 0.92
    }
  ]
}
```

**Note to Engineer**:
Ensure the ingress (API Gateway/Lambda) allows payload sizes up to **1MB** to accommodate large context chunks.

---

## Testing the Deployment

Once deployed, verify the pipeline:

1.  **Health Check**:
    ```bash
    curl https://<endurance-url>/health
    # Expect: {"status": "ok", ...}
    ```

2.  **End-to-End**:
    ```bash
    curl -X POST https://<chatbot-url>/chat \
      -H "Content-Type: application/json" \
      -d '{"message": "Test query"}'
    ```

3.  **Verify Monitoring**:
    Check the Dashboard URL. You should see the test session appear in real-time.

---

**Contact**: Message backend team if you face issues with Python dependencies on Lambda (specifically `numpy`/`scikit-learn` layers).

