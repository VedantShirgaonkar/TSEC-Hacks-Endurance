# Endurance Platform - Improved Implementation Plan

## Executive Summary

Endurance is an **AI Ethics Metrics Platform** that evaluates the credibility and ethical compliance of government conversational AI systems. This plan addresses the identified gaps and provides a complete architecture for **response verification without building an AI agent**.

---

## Key Design Principle: We Don't Build AI, We Verify It

> **Our platform receives AI outputs and verifies them against ground truth sources - we don't generate responses ourselves.**

```
┌─────────────────────────────────────────────────────────────────────┐
│                      ENDURANCE VERIFICATION FLOW                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Government AI System              Endurance Platform                │
│  ┌──────────────────┐              ┌──────────────────┐             │
│  │ User Query ────────────────────►│ Capture Query    │             │
│  │                  │              │                  │             │
│  │ RAG Retrieval ───────────────►│ Capture RAG Docs │             │
│  │ (from approved   │              │ & Similarity     │             │
│  │  docs)           │              │                  │             │
│  │                  │              │                  │             │
│  │ LLM Response ────────────────►│ Capture Response │             │
│  └──────────────────┘              └────────┬─────────┘             │
│                                             │                        │
│                                    ┌────────▼─────────┐             │
│                                    │ VERIFICATION     │             │
│                                    │ ENGINE           │             │
│                                    │                  │             │
│                                    │ • Compare response│             │
│                                    │   to RAG sources │             │
│                                    │ • Detect claims  │             │
│                                    │ • Verify facts   │             │
│                                    │ • Score metrics  │             │
│                                    └────────┬─────────┘             │
│                                             │                        │
│                                    ┌────────▼─────────┐             │
│                                    │ Dashboard +      │             │
│                                    │ Audit Trail      │             │
│                                    └──────────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Gap Resolutions

### Gap 1: Integration - Now with Complete Deployment Options

**Resolution: Multiple Integration Adapters**

| Integration Method | Code Changes Required | Best For |
|-------------------|----------------------|----------|
| **SDK Integration** | 3 lines of code | New AI systems |
| **Webhook Adapter** | Config only | Existing systems with webhook support |
| **Log Tailing** | None | Legacy systems with structured logs |
| **API Gateway Proxy** | Network config | AWS API Gateway users |

#### SDK Integration (3 Lines)
```python
# Add to your AI system
from endurance import EnduranceTracker

tracker = EnduranceTracker(api_key="your-key")
tracker.log(query=user_query, response=ai_response, rag_docs=retrieved_docs)
```

#### Webhook Adapter (Zero Code)
```yaml
# endurance-config.yaml
integration:
  type: webhook
  endpoint: https://your-ai-system/hooks
  events: [query_received, rag_retrieved, response_generated]
```

#### Log Tailing (Zero Code)
```yaml
# For systems that log to CloudWatch/files
integration:
  type: log_tailing
  source: cloudwatch
  log_group: /aws/lambda/your-ai-function
  patterns:
    query: "USER_QUERY: (.*)"
    rag_docs: "RAG_RETRIEVED: (.*)"
    response: "AI_RESPONSE: (.*)"
```

---

### Gap 2: RAG Data Access - Complete Strategy

**The Critical Question: How do we know what documents the AI used?**

#### Option A: Explicit RAG Logging (Recommended)

Most RAG systems (LangChain, LlamaIndex, AWS Kendra) can be configured to log:

```python
# LangChain example - add callback to log RAG
from langchain.callbacks import BaseCallbackHandler

class EnduranceRAGCallback(BaseCallbackHandler):
    def on_retriever_end(self, documents, **kwargs):
        # Send to Endurance
        endurance.log_rag(
            documents=[doc.page_content for doc in documents],
            sources=[doc.metadata.get("source") for doc in documents],
            scores=[doc.metadata.get("score") for doc in documents]
        )
```

#### Option B: API Gateway Interception

If AI system uses AWS Bedrock/SageMaker with RAG:

```
User ─► API Gateway ─► Lambda ─► Bedrock
              │
              ▼ (capture request/response)
         Endurance Collector
```

#### Option C: Require RAG in System Design

For new government AI deployments, mandate structured logging:

```json
{
  "session_id": "sess_123",
  "timestamp": "2024-02-04T12:00:00Z",
  "query": "What was IT expenditure in FY 2022-23?",
  "rag_retrieval": {
    "documents": [
      {"id": "doc_456", "source": "FinancialStatement_2023.pdf", "section": "4.1"},
      {"id": "doc_789", "source": "ProcurementRegister.xlsx", "row": "PR-IT-22-09"}
    ],
    "similarity_scores": [0.95, 0.88]
  },
  "response": "The total expenditure was ₹18.6 crore...",
  "model": "gpt-4-turbo",
  "tokens": {"prompt": 1200, "completion": 350}
}
```

---

### Gap 3: Non-AWS Deployment

**Resolution: Platform-Agnostic Docker Deployment**

```yaml
# docker-compose.yml (for any infrastructure)
version: '3.8'
services:
  endurance-api:
    image: endurance/api:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:5432/endurance
      - STORAGE_BACKEND=minio  # or s3, azure_blob, gcs
    
  endurance-metrics:
    image: endurance/metrics-engine:latest
    depends_on:
      - endurance-api
      
  endurance-dashboard:
    image: endurance/dashboard:latest
    ports:
      - "3000:3000"
      
  postgres:
    image: postgres:15
    
  minio:
    image: minio/minio  # S3-compatible storage
```

**Cloud Mapping:**

| Component | AWS | Azure | GCP | Self-Hosted |
|-----------|-----|-------|-----|-------------|
| API | Lambda | Functions | Cloud Functions | FastAPI/Docker |
| Database | DynamoDB | CosmosDB | Firestore | PostgreSQL |
| Storage | S3 | Blob Storage | GCS | MinIO |
| Monitoring | CloudWatch | Monitor | Cloud Monitoring | Prometheus/Grafana |
| Queue | SQS | Service Bus | Pub/Sub | RabbitMQ/Redis |

---

### Gap 4: Automated Metrics Calculation Pipeline

**Resolution: Complete Pipeline Architecture**

```
                         METRICS CALCULATION PIPELINE
┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌─────────────┐    │
│  │ Ingest  │───►│ Extract  │───►│ Compute  │───►│ Aggregate   │    │
│  │ Data    │    │ Features │    │ Metrics  │    │ & Normalize │    │
│  └─────────┘    └──────────┘    └──────────┘    └─────────────┘    │
│       │              │               │                │             │
│       ▼              ▼               ▼                ▼             │
│  ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌─────────────┐    │
│  │ Query   │    │ Claims   │    │ Per-Claim│    │ Dimension   │    │
│  │ Response│    │ Sources  │    │ Scores   │    │ Scores      │    │
│  │ RAG     │    │ Entities │    │          │    │             │    │
│  │ Tokens  │    │          │    │          │    │ Overall: 86 │    │
│  └─────────┘    └──────────┘    └──────────┘    └─────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Gap 5: Domain Adaptation - Plugin Architecture

**Resolution: Configurable Compliance Profiles**

```python
# compliance_profiles/healthcare.yaml
profile:
  name: "Healthcare Department"
  base_regulations: [rti_act, dpdp_act]
  additional_regulations: [hipaa, clinical_guidelines]
  
dimension_weights:
  bias_fairness: 0.10
  data_grounding: 0.15
  explainability: 0.10
  ethical_alignment: 0.10
  human_control: 0.10
  legal_compliance: 0.25  # Higher for healthcare
  security: 0.15          # Higher for healthcare
  response_quality: 0.05

custom_metrics:
  - name: phi_detection
    description: "Detect Protected Health Information in response"
    type: binary
    weight: 0.3
    
  - name: clinical_accuracy
    description: "Verify against clinical guidelines"
    type: score_0_100
    weight: 0.4

thresholds:
  accuracy: {min: 0.98, alert: 0.95}  # Stricter for healthcare
  harm_risk: {max: 0.02, alert: 0.05}
  response_latency: {max: 3000ms}
```

---

## Part 2: User Integration Journeys

### Journey 1: Central Government Ministry (RTI Portal)

**Scenario**: Ministry of Finance deploys AI for RTI queries about budget allocations.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MINISTRY OF FINANCE - RTI AI                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  EXISTING INFRASTRUCTURE:                                            │
│  • AWS Government Cloud                                              │
│  • AI: Azure OpenAI via API Gateway                                  │
│  • RAG: AWS Kendra on ministry documents                             │
│  • Storage: S3 buckets (encrypted)                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

INTEGRATION STEPS:

Week 1: Discovery & Setup
├── Day 1-2: Audit existing AI architecture
│   └── Identify: API endpoints, log locations, RAG configuration
├── Day 3-4: Deploy Endurance collector
│   └── Method: API Gateway integration (zero code change)
└── Day 5: Configure compliance profile
    └── Select: RTI Act, DPDP Act, Ministry-specific rules

Week 2: Integration & Testing
├── Day 1-2: Connect log streams
│   └── CloudWatch → Endurance Collector via Kinesis
├── Day 3-4: Configure RAG capture
│   └── Add Kendra callback to log retrieved documents
└── Day 5: Validate with test queries

Week 3: Go-Live
├── Enable real-time monitoring
├── Train ministry staff on dashboard
└── Set up alert notifications

INTEGRATION ARCHITECTURE:

  Citizen ──► NIC Portal ──► API Gateway ──► Lambda ──► Azure OpenAI
                                  │                         │
                                  │                         ▼
                                  │                    AWS Kendra
                                  │                    (RAG)
                                  │                         │
                                  ▼                         ▼
                            ┌─────────────────────────────────┐
                            │      ENDURANCE COLLECTOR        │
                            │  (API Gateway Extension)        │
                            └───────────────┬─────────────────┘
                                            │
                                            ▼
                            ┌─────────────────────────────────┐
                            │      ENDURANCE DASHBOARD        │
                            │  • RTI Compliance Score         │
                            │  • Response Accuracy            │
                            │  • Hallucination Detection      │
                            └─────────────────────────────────┘
```

---

### Journey 2: State Government (Citizen Services)

**Scenario**: State of Maharashtra deploys AI chatbot for scheme eligibility queries.

```
EXISTING INFRASTRUCTURE:
• On-premise data center (not cloud)
• AI: Self-hosted LLaMA model
• Documents: Local PostgreSQL with PDFs
• No existing observability

INTEGRATION APPROACH: Sidecar Pattern

  Citizen ──► State Portal ──► Nginx ──► LLaMA API ──► PostgreSQL
                                │              │           (RAG)
                                │              │
                                ▼              ▼
                         ┌──────────────────────────┐
                         │   ENDURANCE SIDECAR      │
                         │   (Docker container)     │
                         │                          │
                         │   • Intercepts HTTP      │
                         │   • Tails application    │
                         │     logs                 │
                         │   • Pushes to local      │
                         │     Endurance instance   │
                         └──────────────────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │   ENDURANCE (Self-Host)  │
                         │   • Docker Compose       │
                         │   • PostgreSQL backend   │
                         │   • Local dashboard      │
                         └──────────────────────────┘

CONFIGURATION:

# sidecar-config.yaml
mode: http_proxy
upstream: http://llama-api:8080
capture:
  request_body: true
  response_body: true
  
log_tailing:
  enabled: true
  path: /var/log/llama-api/*.log
  patterns:
    query: "Query: (.*)"
    rag_docs: "Retrieved: (.*)"
    response: "Response: (.*)"
```

---

### Journey 3: Public Sector Bank (Financial Services)

**Scenario**: SBI deploys AI for customer query resolution about schemes and loans.

```
REQUIREMENTS:
• RBI FREE-AI Framework compliance
• DPDP Act compliance
• No customer data leaves India
• High accuracy required (financial advice)

INTEGRATION: SDK Integration (Full Control)

# In bank's AI application code:
from endurance import EnduranceClient, ComplianceProfile

# Initialize with banking profile
endurance = EnduranceClient(
    api_key=os.environ["ENDURANCE_KEY"],
    profile=ComplianceProfile.BANKING_INDIA,
    data_residency="IN"  # Data stays in India
)

# Wrap AI calls
async def handle_customer_query(query: str):
    # 1. RAG retrieval
    docs = await retrieve_relevant_docs(query)
    
    # Log RAG to Endurance
    endurance.log_rag(
        session_id=session.id,
        documents=docs,
        sources=[d.source for d in docs]
    )
    
    # 2. Generate response
    response = await llm.generate(query, context=docs)
    
    # 3. Log and verify response
    verification = await endurance.verify(
        query=query,
        response=response,
        rag_documents=docs,
        verify_claims=True,  # Extract and verify factual claims
        check_compliance=["rbi_free_ai", "dpdp_act"]
    )
    
    # 4. If verification fails, flag for human review
    if verification.risk_score > 0.3:
        await flag_for_review(session.id, verification.issues)
    
    return response, verification.score
```

---

### Journey 4: Defense/High-Security (Air-Gapped)

**Scenario**: Defense ministry needs AI monitoring with no internet connectivity.

```
REQUIREMENTS:
• Completely air-gapped deployment
• OFFICIAL-SENSITIVE classification
• No external dependencies
• Audit trail with cryptographic verification

DEPLOYMENT: Fully Self-Contained

┌─────────────────────────────────────────────────────────────────────┐
│                    AIR-GAPPED DEFENSE NETWORK                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────┐     ┌───────────────┐     ┌────────────────┐    │
│  │ Defense AI    │────►│ Endurance     │────►│ Secure Audit   │    │
│  │ System        │     │ (Air-Gapped)  │     │ Database       │    │
│  └───────────────┘     └───────────────┘     └────────────────┘    │
│         │                     │                      │              │
│         │                     │                      │              │
│         ▼                     ▼                      ▼              │
│  ┌───────────────┐     ┌───────────────┐     ┌────────────────┐    │
│  │ Local LLM     │     │ Local Metrics │     │ Blockchain     │    │
│  │ (No internet) │     │ Engine        │     │ Audit Chain    │    │
│  └───────────────┘     └───────────────┘     └────────────────┘    │
│                                                                      │
│  All components run on isolated network with NO external access      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

FEATURES:
• All ML models (for verification) pre-loaded locally
• SQLite/PostgreSQL for storage (no cloud DB)
• Cryptographic hashing of all audit entries
• USB export for compliance reporting
```

---

## Part 3: Response Verification & Hallucination Detection

### The Core Challenge

> **How do we know if an AI response is correct without being an AI ourselves?**

### Answer: We Don't Generate - We Verify Against Ground Truth

```
┌─────────────────────────────────────────────────────────────────────┐
│                    VERIFICATION vs GENERATION                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ❌ WRONG APPROACH (What we DON'T do):                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ User Query ──► Our AI ──► Generate "correct" answer          │   │
│  │                          Compare with their answer            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  Problem: We'd need our own AI, which could also hallucinate!       │
│                                                                      │
│  ✅ CORRECT APPROACH (What we DO):                                  │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 1. Receive: Query + Response + RAG Documents                  │   │
│  │ 2. Extract: Factual claims from response                      │   │
│  │ 3. Verify: Each claim against RAG documents                   │   │
│  │ 4. Score: Based on claim verification results                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  Key: We verify against SOURCE DOCUMENTS, not our own knowledge     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Verification Pipeline: Step by Step

#### Step 1: Claim Extraction

Extract factual claims from the AI response:

```python
# Input
response = """
Based on the Department's Annual Financial Statement for FY 2022–23, 
the total expenditure on external IT consultants was ₹18.6 crore. 
The vendors engaged were ABC Technologies, National Informatics Services, 
and DataCore Solutions.
"""

# Output: Extracted Claims
claims = [
    {"text": "total expenditure was ₹18.6 crore", "type": "numeric", "entity": "18.6 crore"},
    {"text": "vendors: ABC Technologies", "type": "entity", "entity": "ABC Technologies"},
    {"text": "vendors: National Informatics Services", "type": "entity"},
    {"text": "vendors: DataCore Solutions", "type": "entity"},
    {"text": "source: Annual Financial Statement FY 2022-23", "type": "source_citation"}
]
```

**How we extract claims:**
- NER (Named Entity Recognition) for numbers, organizations, dates
- Rule-based patterns for "X is Y", "total was X", "according to X"
- Sentence segmentation + classification

---

#### Step 2: Source Document Matching

Match each claim to the RAG documents:

```python
# RAG Documents received from AI system
rag_documents = [
    {
        "id": "doc_001",
        "source": "Financial_Statement_2023.pdf",
        "content": "Section 4.1: IT Consultancy Expenditure\n"
                   "Total: ₹18.6 crore\n"
                   "Vendors: ABC Technologies Pvt Ltd (₹8.2 crore), "
                   "National Informatics Services (₹6.1 crore), "
                   "DataCore Solutions (₹4.3 crore)",
        "page": 47
    }
]

# Claim Verification Results
verification_results = [
    {
        "claim": "total expenditure was ₹18.6 crore",
        "status": "VERIFIED",
        "source_match": "doc_001, page 47, exact match",
        "confidence": 1.0
    },
    {
        "claim": "vendors: ABC Technologies",
        "status": "VERIFIED", 
        "source_match": "doc_001, page 47",
        "confidence": 0.95
    },
    ...
]
```

**Verification Methods:**

| Method | Description | Best For |
|--------|-------------|----------|
| **Exact Match** | Substring search in documents | Numbers, proper nouns |
| **Semantic Similarity** | Embedding cosine similarity | Paraphrased facts |
| **NLI (Natural Language Inference)** | Does document entail claim? | Complex claims |
| **Regex Patterns** | Pattern matching for structured data | Dates, amounts, IDs |

---

#### Step 3: Hallucination Detection

A claim is a **hallucination** if:
1. It's not found in ANY RAG document, AND
2. It's not a reasonable inference from the documents

```python
def detect_hallucination(claim, rag_documents):
    """
    Returns: (is_hallucination: bool, confidence: float, reason: str)
    """
    
    # 1. Check exact match
    for doc in rag_documents:
        if claim.text.lower() in doc.content.lower():
            return False, 1.0, "Exact match found"
    
    # 2. Check semantic similarity
    claim_embedding = embed(claim.text)
    for doc in rag_documents:
        doc_embedding = embed(doc.content)
        similarity = cosine_similarity(claim_embedding, doc_embedding)
        if similarity > 0.85:
            return False, similarity, "High semantic similarity"
    
    # 3. Check NLI entailment
    for doc in rag_documents:
        entailment = nli_model.predict(premise=doc.content, hypothesis=claim.text)
        if entailment.label == "ENTAILMENT" and entailment.score > 0.8:
            return False, entailment.score, "Entailed by source"
    
    # 4. If none match, it's likely a hallucination
    return True, 0.9, "Claim not supported by source documents"
```

---

#### Step 4: Scoring

```python
def calculate_verification_score(claims, verification_results):
    """
    Calculate overall response credibility score
    """
    total_claims = len(claims)
    verified_claims = sum(1 for r in verification_results if r.status == "VERIFIED")
    hallucinated_claims = sum(1 for r in verification_results if r.status == "HALLUCINATED")
    
    # Base accuracy score
    accuracy = verified_claims / total_claims if total_claims > 0 else 0
    
    # Hallucination penalty (severe)
    hallucination_penalty = hallucinated_claims * 0.15
    
    # Final score
    score = max(0, accuracy * 100 - hallucination_penalty * 100)
    
    return {
        "overall_score": score,
        "verified_claims": verified_claims,
        "total_claims": total_claims,
        "hallucinations": hallucinated_claims,
        "breakdown": verification_results
    }
```

---

### Complete Verification Example

```
INPUT:
─────────────────────────────────────────────────────────────────────
Query: "What was the IT expenditure in FY 2022-23?"

Response: "The Department spent ₹18.6 crore on IT consultants. Major 
vendors were ABC Technologies (₹8.2 crore), National Informatics (₹6.1 
crore), and DataCore (₹4.3 crore). The project was overseen by 
Director Sharma."

RAG Documents:
- Financial_Statement_2023.pdf (contains IT expenditure details)
- Procurement_Register.xlsx (contains vendor list)

VERIFICATION PROCESS:
─────────────────────────────────────────────────────────────────────
Claim 1: "₹18.6 crore on IT consultants"
  → Search Financial_Statement_2023.pdf
  → FOUND: "Section 4.1: Total IT Consultancy: ₹18.6 crore"
  → Status: ✅ VERIFIED (exact match)

Claim 2: "ABC Technologies ₹8.2 crore"
  → Search Procurement_Register.xlsx
  → FOUND: "ABC Technologies Pvt Ltd - ₹8.2 crore"
  → Status: ✅ VERIFIED (exact match)

Claim 3: "National Informatics ₹6.1 crore"
  → Search all documents
  → FOUND in Procurement_Register
  → Status: ✅ VERIFIED

Claim 4: "DataCore ₹4.3 crore"
  → FOUND in Procurement_Register
  → Status: ✅ VERIFIED

Claim 5: "Project overseen by Director Sharma"
  → Search all documents
  → NOT FOUND in any RAG document
  → NLI check: No entailment
  → Status: ❌ HALLUCINATION

OUTPUT:
─────────────────────────────────────────────────────────────────────
{
  "overall_score": 80,
  "verified_claims": 4,
  "total_claims": 5,
  "hallucinations": 1,
  "hallucination_details": [
    {
      "claim": "Project overseen by Director Sharma",
      "reason": "Not found in source documents",
      "severity": "MEDIUM",
      "recommendation": "Remove unsupported personnel references"
    }
  ]
}
```

---

### Metrics from Verification

| Metric | Formula | From Above Example |
|--------|---------|-------------------|
| **Groundedness Score** | `verified_claims / total_claims` | 4/5 = 0.80 |
| **Hallucination Rate** | `hallucinated_claims / total_claims` | 1/5 = 0.20 |
| **Source Coverage** | `claims_with_citations / total_claims` | 4/5 = 0.80 |
| **Factual Accuracy** | `correct_facts / total_facts` | 4/5 = 0.80 |
| **Response Completeness** | `addressed_aspects / query_aspects` | 1.0 |

---

## Part 4: Technical Implementation

### Core Modules

```
endurance/
├── adapters/                    # Integration adapters
│   ├── sdk/                     # Python/JS SDKs
│   ├── webhook/                 # Webhook receiver
│   ├── log_tailing/             # Log parser
│   └── api_gateway/             # AWS API Gateway integration
│
├── verification/                # Core verification engine
│   ├── claim_extractor.py       # Extract claims from response
│   ├── source_matcher.py        # Match claims to documents
│   ├── hallucination_detector.py# Detect unsupported claims
│   └── scorer.py                # Calculate scores
│
├── metrics/                     # Metrics calculation
│   ├── dimensions/              # 8 ethical dimensions
│   │   ├── bias_fairness.py
│   │   ├── data_grounding.py
│   │   ├── explainability.py
│   │   ├── ethical_alignment.py
│   │   ├── human_control.py
│   │   ├── legal_compliance.py
│   │   ├── security.py
│   │   └── response_quality.py
│   ├── aggregator.py            # Combine dimension scores
│   └── normalizer.py            # 0-100 normalization
│
├── compliance/                  # Compliance checking
│   ├── profiles/                # Domain-specific profiles
│   │   ├── rti_act.yaml
│   │   ├── gdpr.yaml
│   │   ├── dpdp_act.yaml
│   │   └── healthcare.yaml
│   └── rule_engine.py           # Compliance rule execution
│
├── api/                         # FastAPI backend
│   ├── routes/
│   ├── models/
│   └── app.py
│
├── dashboard/                   # React frontend
│   └── ...
│
└── deployment/                  # Deployment configs
    ├── docker-compose.yml       # Self-hosted
    ├── aws/                     # AWS CDK/Terraform
    ├── azure/                   # Azure ARM templates
    └── kubernetes/              # K8s manifests
```

---

## Verification Plan

### Automated Tests

1. **Unit Tests**: Run via `pytest tests/`
   - Claim extraction accuracy
   - Source matching precision
   - Hallucination detection recall
   - Metrics calculation correctness

2. **Integration Tests**: Run via `pytest tests/integration/`
   - End-to-end verification pipeline
   - API endpoint responses
   - Database operations

### Manual Verification

1. **Demo Scenario Test**:
   - Use RTI example from RAIT document
   - Verify 86/100 score is reproduced
   - Check all 8 dimension scores

2. **Hallucination Detection Test**:
   - Input response with known hallucination
   - Verify system detects and flags it

---

## User Review Required

> [!IMPORTANT]
> Please review and confirm:
> 1. Is the verification approach (claims vs source documents) acceptable?
> 2. Should we support all 4 deployment scenarios or focus on 1-2 for MVP?
> 3. Any specific government agency requirements to prioritize?

