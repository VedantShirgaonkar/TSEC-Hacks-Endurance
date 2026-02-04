# Backend System Design
## Supporting SDK, Webhook, and Self-Hosted Integrations

---

## Overview

Endurance needs to support **3 integration modes** for monitoring AI chatbots:

| Mode | Description | Latency | Use Case |
|------|-------------|---------|----------|
| **SDK** | Direct API call after each response | Sync ~200ms | Real-time monitoring |
| **Webhook** | Fire-and-forget async POST | Async ~50ms | Non-blocking, high volume |
| **Self-Hosted** | Docker container with local metrics | Local | Air-gapped, enterprise |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ENDURANCE BACKEND                                 │
│                                                                             │
│    ┌─────────────────────────────────────────────────────────────────┐     │
│    │                      API GATEWAY                                 │     │
│    │                                                                  │     │
│    │   /v1/evaluate/sync    → SDK Integration (sync response)        │     │
│    │   /v1/evaluate/async   → Webhook Integration (202 Accepted)     │     │
│    │   /v1/stream           → WebSocket for dashboard                │     │
│    │                                                                  │     │
│    └───────────────────────────────┬─────────────────────────────────┘     │
│                                    │                                        │
│    ┌───────────────────────────────▼─────────────────────────────────┐     │
│    │                     EVALUATION ENGINE                            │     │
│    │                                                                  │     │
│    │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │     │
│    │   │   Metrics    │  │ Verification │  │  Scoring     │         │     │
│    │   │   Engine     │  │  Pipeline    │  │  Aggregator  │         │     │
│    │   │              │  │              │  │              │         │     │
│    │   │ 9 Dimensions │  │ Claim Extract│  │ Weighted Sum │         │     │
│    │   │ 36 Metrics   │  │ Source Match │  │ Penalties    │         │     │
│    │   └──────────────┘  └──────────────┘  └──────────────┘         │     │
│    │                                                                  │     │
│    └───────────────────────────────┬─────────────────────────────────┘     │
│                                    │                                        │
│    ┌───────────────────────────────▼─────────────────────────────────┐     │
│    │                     DATA LAYER                                   │     │
│    │                                                                  │     │
│    │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │     │
│    │   │   PostgreSQL │  │    Redis     │  │   S3/Blob    │         │     │
│    │   │   (Sessions) │  │   (Cache)    │  │   (Logs)     │         │     │
│    │   └──────────────┘  └──────────────┘  └──────────────┘         │     │
│    │                                                                  │     │
│    └─────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Integration Mode Details

### 1. SDK Integration (Synchronous)

**Endpoint**: `POST /v1/evaluate/sync`

**Flow**:
```
Chatbot → Endurance API → Evaluation → Response with scores
         ────────────────────────────────────────────────────►
                              ~200ms
```

**Request**:
```json
{
  "api_key": "ek_live_xxx",
  "session_id": "sess_123",
  "query": "What is the IT budget?",
  "response": "The total IT budget is ₹78 crore...",
  "rag_documents": [
    {"id": "doc_1", "source": "Budget.md", "content": "..."}
  ],
  "metadata": {
    "model": "gpt-4",
    "latency_ms": 1200
  }
}
```

**Response**:
```json
{
  "session_id": "sess_123",
  "overall_score": 87.5,
  "dimensions": {
    "bias_fairness": 85.2,
    "data_grounding": 92.1,
    "explainability": 78.3,
    ...
  },
  "verification": {
    "total_claims": 5,
    "verified": 4,
    "hallucinated": 1
  },
  "alerts": [
    {"type": "hallucination", "claim": "...", "severity": "medium"}
  ]
}
```

**SDK Code (Python)**:
```python
from endurance import EnduranceClient

client = EnduranceClient(api_key="ek_live_xxx")

# After chatbot response
evaluation = client.evaluate(
    session_id="sess_123",
    query=user_query,
    response=bot_response,
    rag_documents=sources,
)

if evaluation.overall_score < 60:
    # Flag for human review
    flag_for_review(session_id)
```

---

### 2. Webhook Integration (Asynchronous)

**Endpoint**: `POST /v1/evaluate/async`

**Flow**:
```
Chatbot → Endurance API → 202 Accepted
         ────────────────────────────►
                    ~50ms
         
         [Background: Evaluation runs]
         
         [Later: Webhook POST to client]
         ◄────────────────────────────
```

**Request**: Same as SDK

**Response**:
```json
{
  "evaluation_id": "eval_789",
  "status": "processing",
  "webhook_url": "https://myapp.com/endurance-webhook"
}
```

**Webhook Callback**:
```json
POST https://myapp.com/endurance-webhook
{
  "event": "evaluation.complete",
  "evaluation_id": "eval_789",
  "session_id": "sess_123",
  "overall_score": 87.5,
  "dimensions": {...},
  "alerts": [...]
}
```

**Configuration**:
```json
POST /v1/services
{
  "name": "RTI Chatbot",
  "webhook_url": "https://myapp.com/endurance-webhook",
  "webhook_secret": "whsec_xxx",
  "integration_mode": "webhook"
}
```

---

### 3. Self-Hosted (Docker)

**Deployment**:
```bash
docker run -d \
  -p 8000:8000 \
  -e LICENSE_KEY=xxx \
  -v /data/endurance:/data \
  endurance/metrics-engine:latest
```

**Features**:
- All data stays on-premises
- No network calls to Endurance cloud
- License file for enterprise customers
- Sync telemetry (anonymized) optional

**API**: Same as cloud, but at `http://localhost:8000`

---

## API Specification

### Authentication

All requests require an API key:
```
Authorization: Bearer ek_live_xxx
```

Or as header:
```
X-Endurance-Key: ek_live_xxx
```

### Rate Limits

| Plan | Rate Limit | Burst |
|------|------------|-------|
| Free | 100/hour | 10 |
| Pro | 10,000/hour | 100 |
| Enterprise | Unlimited | 500 |

### Error Responses

```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Retry after 60s.",
    "retry_after": 60
  }
}
```

---

## Database Schema

### Sessions Table
```sql
CREATE TABLE sessions (
  id UUID PRIMARY KEY,
  service_id UUID REFERENCES services(id),
  query TEXT NOT NULL,
  response TEXT NOT NULL,
  overall_score FLOAT,
  dimensions JSONB,
  verification JSONB,
  alerts JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Services Table
```sql
CREATE TABLE services (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  api_key VARCHAR(64) UNIQUE,
  integration_mode VARCHAR(20), -- 'sdk', 'webhook', 'docker'
  webhook_url TEXT,
  webhook_secret VARCHAR(64),
  config JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Alerts Table
```sql
CREATE TABLE alerts (
  id UUID PRIMARY KEY,
  session_id UUID REFERENCES sessions(id),
  alert_type VARCHAR(50), -- 'hallucination', 'bias', 'low_score'
  severity VARCHAR(20),   -- 'low', 'medium', 'high', 'critical'
  details JSONB,
  acknowledged BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Implementation Plan

### Phase 1: Unified Evaluation Endpoint

```python
# api/routes/evaluate.py

@router.post("/v1/evaluate/sync")
async def evaluate_sync(request: EvaluateRequest):
    """Synchronous evaluation - waits for result."""
    result = await evaluation_engine.evaluate(request)
    await db.save_session(result)
    await ws_manager.broadcast(result)  # Real-time to dashboard
    return result

@router.post("/v1/evaluate/async")
async def evaluate_async(request: EvaluateRequest):
    """Async evaluation - returns immediately, webhooks later."""
    eval_id = await queue.enqueue(request)
    return {"evaluation_id": eval_id, "status": "processing"}
```

### Phase 2: Background Worker

```python
# workers/evaluator.py

async def process_evaluation(eval_id: str):
    """Background worker for async evaluations."""
    request = await queue.get(eval_id)
    result = await evaluation_engine.evaluate(request)
    await db.save_session(result)
    
    # Send webhook
    service = await db.get_service(request.service_id)
    if service.webhook_url:
        await send_webhook(service.webhook_url, service.webhook_secret, result)
```

### Phase 3: Real-Time Updates

```python
# api/routes/stream.py

@router.websocket("/v1/stream")
async def websocket_endpoint(websocket: WebSocket, service_id: str = None):
    """Real-time session stream for dashboard."""
    await manager.connect(websocket, service_id)
    try:
        while True:
            # Keep connection alive, push updates via manager.broadcast()
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

---

## Next Steps

1. **Implement unified `/v1/evaluate/sync` endpoint**
2. **Add Redis queue for async evaluations**
3. **Create webhook delivery service**
4. **Build WebSocket stream for dashboard**
5. **Add PostgreSQL session storage**
6. **Create Docker image for self-hosted**

---

## Questions

1. **Queue Technology**: Redis, RabbitMQ, or AWS SQS?
2. **Database**: PostgreSQL or MongoDB for sessions?
3. **Docker Registry**: DockerHub or private ECR?

---

**Owner**: Backend Team  
**Status**: Planning  
**Target**: MVP in 1 week
