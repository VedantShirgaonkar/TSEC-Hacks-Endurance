# Endurance Platform - Implementation Roadmap

## Team Roles

| Role | Responsibilities | Key Skills |
|------|------------------|------------|
| **ML Engineer** | Metrics engine, verification pipeline, claim extraction, NLP | Python, ML/NLP, Embeddings, Scoring |
| **Cloud Engineer** | Backend API, infrastructure, integrations, deployment | FastAPI, Docker, AWS, Databases |

---

## Phase Overview (24-Hour Hackathon)

```
HOUR  0         4         8         12        16        20        24
      │─────────│─────────│─────────│─────────│─────────│─────────│
      ├─ Phase 1 ─┤
      │  SETUP   │
      │          ├─ Phase 2 ─────────┤
      │          │  CORE ENGINE      │
      │          │                   ├─ Phase 3 ─────────┤
      │          │                   │  VERIFICATION     │
      │          │                   │                   ├─ Phase 4 ───────┤
      │          │                   │                   │  DASHBOARD      │
      │          │                   │                   │                 ├ Phase 5 ┤
      │          │                   │                   │                 │ DEMO    │
      │          │                   │                   │                 │        ├┤ P6
      │          │                   │                   │                 │        ││SHIP
```

---

## Phase 1: Setup & Foundation (Hours 0-3)

### Goal
Get development environment running with basic structure.

### ML Engineer Tasks

#### Checklist
- [ ] Clone/create repository
- [ ] Set up Python virtual environment (`uv venv`)
- [ ] Install core dependencies (sentence-transformers, spacy, sklearn)
- [ ] Create project structure:
  ```
  endurance/
  ├── metrics/
  │   ├── __init__.py
  │   └── dimensions/
  ├── verification/
  │   ├── __init__.py
  │   ├── claim_extractor.py
  │   └── source_matcher.py
  └── tests/
  ```
- [ ] Download NLP models (spaCy en_core_web_sm)
- [ ] Create sample test data (queries, responses, RAG docs)

#### Deliverable
- Project structure ready
- Can run: `python -c "from endurance.metrics import *"`

---

### Cloud Engineer Tasks

#### Checklist
- [ ] Set up FastAPI project structure:
  ```
  api/
  ├── main.py
  ├── routes/
  │   ├── __init__.py
  │   ├── metrics.py
  │   └── health.py
  ├── models/
  │   └── schemas.py
  └── config.py
  ```
- [ ] Create Docker setup:
  ```
  docker-compose.yml
  Dockerfile
  ```
- [ ] Set up PostgreSQL/SQLite database
- [ ] Create basic React dashboard scaffold:
  ```
  npx create-react-app dashboard --template typescript
  ```
- [ ] Configure CORS, basic auth

#### Deliverable
- API running at `localhost:8000`
- Dashboard running at `localhost:3000`
- Health check endpoint: `GET /health` returns `{"status": "ok"}`

---

### Phase 1 Test
```bash
# Test API
curl http://localhost:8000/health
# Expected: {"status": "ok"}

# Test Python imports
python -c "from endurance.verification.claim_extractor import extract_claims; print('OK')"

# Test Dashboard
# Open http://localhost:3000 - should see React app
```

---

## Phase 2: Core Metrics Engine (Hours 3-8)

### Goal
Implement all 30+ metrics across 8 dimensions.

### ML Engineer Tasks

#### Checklist
- [ ] **Dimension 1: Bias & Fairness**
  - [ ] Statistical Parity calculation
  - [ ] Equal Opportunity calculation
  - [ ] Disparate Impact ratio
  - [ ] Average Odds Difference

- [ ] **Dimension 2: Data Grounding & Drift**
  - [ ] Population Stability Index (PSI)
  - [ ] KL Divergence
  - [ ] Feature Drift detection
  - [ ] Prediction Drift detection

- [ ] **Dimension 3: Explainability**
  - [ ] Feature Importance Coverage
  - [ ] Source Citation Score
  - [ ] Confidence Score extraction

- [ ] **Dimension 4: Ethical Alignment**
  - [ ] Harm Risk Score
  - [ ] Norm Violation Counter

- [ ] **Dimension 5: Human Control**
  - [ ] Override Frequency tracking
  - [ ] Escalation Path logging

- [ ] **Dimension 6: Legal Compliance**
  - [ ] RTI Act rule checker
  - [ ] DPDP Act rule checker
  - [ ] GDPR alignment scorer

- [ ] **Dimension 7: Security**
  - [ ] Adversarial input detection (basic)
  - [ ] PII detection in response

- [ ] **Dimension 8: Response Quality**
  - [ ] Accuracy scoring
  - [ ] Completeness scoring
  - [ ] F1 Score calculation

- [ ] Create normalization functions (raw → 0-100)
- [ ] Create aggregation function (dimensions → overall score)
- [ ] Unit tests for each metric

#### Deliverable
```python
from endurance.metrics import compute_all_metrics

result = compute_all_metrics(
    query="What was IT expenditure?",
    response="The expenditure was ₹18.6 crore...",
    rag_documents=[...]
)
# Returns: {"overall": 86, "dimensions": {...}, "metrics": {...}}
```

---

### Cloud Engineer Tasks

#### Checklist
- [ ] Create data models:
  ```python
  class QueryRequest(BaseModel):
      session_id: str
      query: str
      response: str
      rag_documents: List[RAGDocument]
      metadata: Optional[dict]
  
  class MetricResult(BaseModel):
      overall_score: float
      dimensions: Dict[str, float]
      metrics: Dict[str, MetricValue]
      verification: VerificationResult
  ```

- [ ] Create API endpoints:
  - [ ] `POST /v1/evaluate` - Submit query for evaluation
  - [ ] `GET /v1/metrics/{session_id}` - Get computed metrics
  - [ ] `GET /v1/dimensions` - List all dimensions

- [ ] Set up database tables:
  - [ ] `sessions` - Query sessions
  - [ ] `metrics` - Computed metrics
  - [ ] `audit_logs` - Audit trail

- [ ] Create mock AI service for demo:
  ```python
  # mock_ai_service.py
  @app.post("/generate")
  def generate_response(query: str, mode: str = "good"):
      if mode == "good":
          return GOOD_RESPONSE
      else:
          return BAD_RESPONSE
  ```

#### Deliverable
```bash
curl -X POST http://localhost:8000/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{"query": "...", "response": "...", "rag_documents": [...]}'
# Returns: {"overall_score": 86, ...}
```

---

### Phase 2 Test
```bash
# Test metrics calculation
python -m pytest tests/test_metrics.py -v

# Test API endpoint
curl -X POST http://localhost:8000/v1/evaluate \
  -d @test_data/sample_query.json

# Verify all 8 dimensions have scores
python -c "
from endurance.metrics import compute_all_metrics
result = compute_all_metrics(...)
assert len(result['dimensions']) == 8
print('All dimensions computed!')
"
```

---

## Phase 3: Verification Pipeline (Hours 8-14)

### Goal
Build claim extraction and hallucination detection.

### ML Engineer Tasks

#### Checklist
- [ ] **Claim Extractor**
  - [ ] NER for entities (numbers, organizations, dates)
  - [ ] Pattern matching for factual statements
  - [ ] Sentence segmentation
  - [ ] Claim classification (numeric, entity, citation)

- [ ] **Source Matcher**
  - [ ] Exact string matching
  - [ ] Semantic similarity (sentence-transformers)
  - [ ] NLI entailment check (optional, if time)
  - [ ] Confidence scoring

- [ ] **Hallucination Detector**
  - [ ] Match claims to RAG documents
  - [ ] Flag unmatched claims
  - [ ] Calculate hallucination rate
  - [ ] Generate explanation

- [ ] Create verification pipeline:
  ```python
  def verify_response(response: str, rag_docs: List[Document]) -> VerificationResult:
      claims = extract_claims(response)
      matches = match_to_sources(claims, rag_docs)
      hallucinations = detect_hallucinations(claims, matches)
      return VerificationResult(...)
  ```

- [ ] Create sample embedding index for demo documents

#### Deliverable
```python
from endurance.verification import verify_response

result = verify_response(
    response="The expenditure was ₹18.6 crore. Director Sharma oversaw it.",
    rag_docs=[financial_statement, procurement_register]
)
# Returns: {
#   "verified_claims": 4,
#   "hallucinated_claims": 1,
#   "details": [
#     {"claim": "₹18.6 crore", "status": "VERIFIED", "source": "..."},
#     {"claim": "Director Sharma", "status": "HALLUCINATION", "reason": "..."}
#   ]
# }
```

---

### Cloud Engineer Tasks

#### Checklist
- [ ] **API Endpoints for Verification**
  - [ ] `GET /v1/verify/{session_id}` - Get verification details
  - [ ] `GET /v1/claims/{session_id}` - Get extracted claims

- [ ] **Audit Logging**
  - [ ] Log all events with timestamps
  - [ ] Create hash chain for immutability
  - [ ] Endpoint: `GET /v1/audit/{session_id}`

- [ ] **Human Feedback API**
  - [ ] `POST /v1/feedback` - Submit human evaluation
  - [ ] `GET /v1/feedback/{session_id}` - Get feedback
  - [ ] Store in database

- [ ] **Demo Data Preparation**
  - [ ] Create 5 RTI query scenarios
  - [ ] Create good/bad response pairs
  - [ ] Create mock RAG documents (PDF content as text)

#### Deliverable
```bash
# Get verification details
curl http://localhost:8000/v1/verify/sess_123
# Returns claim-by-claim breakdown

# Submit human feedback
curl -X POST http://localhost:8000/v1/feedback \
  -d '{"session_id": "sess_123", "accuracy": 4, "completeness": 5}'
```

---

### Phase 3 Test
```bash
# Test claim extraction
python -m pytest tests/test_claim_extractor.py

# Test hallucination detection
python -c "
from endurance.verification import verify_response
result = verify_response(
    'Director Sharma managed the project.',
    [{'content': 'IT expenditure was ₹18.6 crore'}]
)
assert result.hallucinated_claims > 0
print('Hallucination detected!')
"

# Test audit logging
curl http://localhost:8000/v1/audit/sess_123
# Should return timeline of events
```

---

## Phase 4: Dashboard Implementation (Hours 14-20)

### Goal
Build interactive dashboard with all features.

### ML Engineer Tasks

#### Checklist
- [ ] Create API response formatters for dashboard
- [ ] Add explanation text generation for metrics
- [ ] Create trend calculation (for historical view)
- [ ] Support demo mode with pre-computed results
- [ ] Create summary text generator

---

### Cloud Engineer Tasks

#### Checklist
- [ ] **React Components**
  - [ ] `ScoreGauge` - Overall score visualization
  - [ ] `DimensionCards` - 8 dimension scores
  - [ ] `ClaimVerificationTable` - Claim-by-claim breakdown
  - [ ] `AuditTimeline` - Timeline of events
  - [ ] `HumanFeedbackForm` - Rating form
  - [ ] `ComplianceStatus` - Compliance indicators
  - [ ] `LiveQueryFeed` - Real-time queries

- [ ] **Pages**
  - [ ] `/` - Main dashboard
  - [ ] `/query/{id}` - Query detail view
  - [ ] `/audit` - Audit log view
  - [ ] `/demo` - Interactive demo page

- [ ] **API Integration**
  - [ ] Connect all components to backend APIs
  - [ ] Add loading states
  - [ ] Add error handling
  - [ ] WebSocket for real-time updates (optional)

- [ ] **Styling**
  - [ ] Dark mode theme
  - [ ] Responsive layout
  - [ ] Animations for score changes
  - [ ] Color coding (green/yellow/red)

#### Deliverable
- Full dashboard at `http://localhost:3000`
- Demo page with toggle for good/bad responses
- Working human feedback submission

---

### Phase 4 Test
```
1. Open http://localhost:3000/demo
2. Enter RTI query
3. Click "Analyze"
4. Verify:
   - Overall score appears
   - 8 dimension cards show
   - Claim verification table populates
   - Audit timeline updates
5. Submit human feedback
6. Verify score updates
```

---

## Phase 5: Integration & Demo Prep (Hours 20-23)

### Goal
End-to-end testing and demo preparation.

### Both Engineers

#### Checklist
- [ ] **End-to-End Testing**
  - [ ] Run through full demo script 3 times
  - [ ] Fix any integration bugs
  - [ ] Test all API endpoints
  - [ ] Test dashboard on different browsers

- [ ] **Demo Data**
  - [ ] Finalize 5 RTI query scenarios
  - [ ] Pre-compute all sample results
  - [ ] Create backup JSON files

- [ ] **Documentation**
  - [ ] Write README with setup instructions
  - [ ] Document API endpoints
  - [ ] Create metric formulas document

- [ ] **Backup Preparation**
  - [ ] Record demo video (5 min)
  - [ ] Export static HTML dashboard
  - [ ] Create presentation slides (if needed)

- [ ] **Performance**
  - [ ] Ensure page loads < 3 seconds
  - [ ] Ensure API response < 2 seconds

---

### Phase 5 Test
```
[ ] Full demo runs without errors
[ ] All 5 scenarios work
[ ] Dashboard is responsive
[ ] Audit log is complete
[ ] Human feedback saves
[ ] Metrics calculations are correct
[ ] Video backup is ready
```

---

## Phase 6: Final Polish & Ship (Hours 23-24)

### Checklist
- [ ] Clean up console errors
- [ ] Remove debug code
- [ ] Final README update
- [ ] Push all code to repository
- [ ] Prepare talking points
- [ ] Test one more time
- [ ] **REST!**

---

## Parallel Work Schedule

### Hour-by-Hour

| Hour | ML Engineer | Cloud Engineer |
|------|-------------|----------------|
| 0-1 | Setup Python env, install deps | Setup FastAPI, Docker |
| 1-2 | Create project structure | Create React scaffold |
| 2-3 | Load NLP models, test data | Database setup, basic API |
| 3-4 | Bias/Fairness metrics | API endpoints design |
| 4-5 | Data Grounding metrics | Implement /evaluate endpoint |
| 5-6 | Explainability metrics | Database models |
| 6-7 | Remaining dimension metrics | Mock AI service |
| 7-8 | Aggregation & normalization | Integration with metrics |
| 8-9 | Claim Extractor | Audit logging |
| 9-10 | Source Matcher | Human feedback API |
| 10-11 | Hallucination Detector | Demo data prep |
| 11-12 | Verification pipeline | REST endpoints |
| 12-13 | **BREAK / Sync** | **BREAK / Sync** |
| 13-14 | Testing verification | Testing API |
| 14-15 | Dashboard API formatters | ScoreGauge component |
| 15-16 | Explanation generators | DimensionCards component |
| 16-17 | Trend calculations | ClaimVerification table |
| 17-18 | Demo mode support | AuditTimeline component |
| 18-19 | Review & help frontend | HumanFeedback form |
| 19-20 | Integration testing | Full page assembly |
| 20-21 | End-to-end testing | End-to-end testing |
| 21-22 | Documentation | Documentation |
| 22-23 | Demo rehearsal | Demo rehearsal |
| 23-24 | Final polish | Final polish |

---

## Dependency Map

```
Phase 1 (Setup)
    │
    ├── ML: Project structure ────────────────┐
    │                                         │
    └── Cloud: API + DB ──────────────────────┤
                                              │
                                              ▼
Phase 2 (Core Engine)                    INTEGRATION
    │                                    POINT #1
    ├── ML: Metrics Engine ───────────────────┤
    │                                         │
    └── Cloud: API endpoints ─────────────────┤
                                              │
                                              ▼
Phase 3 (Verification)                   INTEGRATION
    │                                    POINT #2
    ├── ML: Verification Pipeline ────────────┤
    │                                         │
    └── Cloud: Audit + Feedback ──────────────┤
                                              │
                                              ▼
Phase 4 (Dashboard)                      INTEGRATION
    │                                    POINT #3
    ├── ML: API formatters ───────────────────┤
    │                                         │
    └── Cloud: React components ──────────────┤
                                              │
                                              ▼
Phase 5 (Demo Prep)                      FINAL
    │                                    TESTING
    └── Both: Testing + Docs ─────────────────┤
                                              │
                                              ▼
Phase 6 (Ship)                           DEMO
                                         READY
```

---

## Quick Reference: What Each Role Owns

### ML Engineer Owns:
- All Python code in `endurance/metrics/`
- All Python code in `endurance/verification/`
- Metric formulas and calculations
- NLP models and embeddings
- Claim extraction and matching logic

### Cloud Engineer Owns:
- All code in `api/`
- All code in `dashboard/`
- Docker configuration
- Database schema
- API design and implementation
- Frontend components
- DevOps and deployment
