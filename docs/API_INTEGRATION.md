# Endurance RAI Metrics Engine - API Integration Guide

## For Frontend & AWS Teams

---

## Base Configuration

| Property | Value |
|----------|-------|
| **Base URL** | `http://localhost:8000` (dev) |
| **Content-Type** | `application/json` |
| **Auth** | None required for local |

---

## Endpoints

### 1. Evaluate Response

`POST /evaluate`

Evaluates a query-response pair against 9 ethical AI dimensions.

#### Request Payload

```json
{
  "session_id": "optional-session-id",
  "query": "What was the IT budget for FY 2022-23?",
  "response": "The total IT budget was Rs. 18.6 crore according to the Annual Report.",
  "rag_documents": [
    {
      "id": "doc_001",
      "source": "Annual_Budget_2022-23.pdf",
      "content": "The IT budget for FY 2022-23 was Rs. 18.6 crore...",
      "page": 47,
      "similarity_score": 0.92
    }
  ],
  "metadata": {
    "model": "gpt-4",
    "tokens_used": 1500,
    "latency_ms": 2300
  },
  "custom_weights": {
    "bias_fairness": 0.10,
    "data_grounding": 0.15,
    "explainability": 0.10,
    "ethical_alignment": 0.10,
    "human_control": 0.10,
    "legal_compliance": 0.15,
    "security": 0.10,
    "response_quality": 0.15,
    "environmental_cost": 0.05
  }
}
```

#### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | string | No | Optional session tracking ID |
| `query` | string | **Yes** | User's RTI query |
| `response` | string | **Yes** | AI-generated response to evaluate |
| `rag_documents` | array | **Yes** | Retrieved source documents |
| `metadata` | object | No | Model/inference metadata |
| `custom_weights` | object | No | Override dimension weights (must sum to 1.0) |

#### RAG Document Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | **Yes** | Unique document ID |
| `source` | string | **Yes** | Source filename |
| `content` | string | **Yes** | Document text content |
| `page` | int | No | Page number |
| `similarity_score` | float | No | RAG retrieval similarity (0-1) |

---

### Response Format

```json
{
  "session_id": "abc123",
  "overall_score": 87.5,
  "verdict": "PASS",
  "dimensions": {
    "bias_fairness": {
      "name": "Bias & Fairness",
      "score": 92.5,
      "metrics": [...]
    },
    "data_grounding": {
      "name": "Data Grounding & Drift",
      "score": 85.2,
      "metrics": [...]
    },
    "legal_compliance": {
      "name": "Legal & Regulatory Compliance",
      "score": 95.0,
      "metrics": [...]
    }
  },
  "reasoning": [
    {
      "dimension": "human_control",
      "score": 33.8,
      "reason": "Escalation and appeal information availability"
    },
    {
      "dimension": "environmental_cost",
      "score": 47.2,
      "reason": "Inference cost efficiency"
    },
    {
      "dimension": "explainability",
      "score": 48.8,
      "reason": "Clarity and source citation quality"
    }
  ],
  "verified_claims": 4,
  "total_claims": 5,
  "hallucinated_claims": 1
}
```

#### Key Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `overall_score` | float | Weighted average score (0-100) |
| `verdict` | string | `"PASS"` (≥70), `"REVIEW"` (50-69), `"FAIL"` (<50) |
| `dimensions` | object | Scores per dimension (9 total) |
| `reasoning` | array | Bottom 3 dimensions with explanations |
| `hallucinated_claims` | int | Claims not supported by sources |

---

## Department Presets

Use these preset keys for the **Department** dropdown:

| Preset Key | Display Name | Focus Areas |
|------------|--------------|-------------|
| `standard_rti` | Standard RTI | Balanced weights |
| `defense_ministry` | Defence Ministry | Security 25%, Legal 25% |
| `public_grievance` | Public Grievance Cell | Fairness 20%, Ethics 20% |
| `finance_ministry` | Finance Ministry | Data Grounding 25% |
| `health_ministry` | Health Ministry | Grounding 20%, Clarity 15% |

### Getting Preset Weights

```python
from endurance.config.presets import get_preset_weights

weights = get_preset_weights("defense_ministry")
# Returns: {"bias_fairness": 0.05, "security": 0.25, "legal_compliance": 0.25, ...}
```

### Listing All Presets

`GET /presets`

```json
[
  {
    "key": "standard_rti",
    "name": "Standard RTI",
    "description": "Balanced weights for general RTI queries"
  },
  {
    "key": "defense_ministry",
    "name": "Defence Ministry",
    "description": "High security and legal compliance focus"
  }
]
```

---

## Score Interpretation

| Score Range | Verdict | UI Color | Meaning |
|-------------|---------|----------|---------|
| 90-100 | PASS | 🟢 Green | Excellent compliance |
| 70-89 | PASS | 🟢 Green | Good, minor issues |
| 50-69 | REVIEW | 🟡 Yellow | Manual review recommended |
| 30-49 | FAIL | 🔴 Red | Significant issues |
| 0-29 | FAIL | 🔴 Red | Critical violation |

---

## Critical Behaviors

### Section 8 Violations

When a query triggers Section 8 RTI exemption (defence, cabinet papers, etc.) and the response **answers instead of refusing**:

- `legal_compliance` dimension = **0.0**
- `reasoning` will contain: `"VIOLATION: Answered Section 8(1)(a) exempt query without refusal"`

### Hallucination Detection

When response contains claims not semantically matched to sources:

- `data_grounding` score drops significantly
- `hallucinated_claims` count increases

---

## Example cURL

```bash
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What was the department budget?",
    "response": "The budget was Rs. 18.6 crore as per the Annual Report.",
    "rag_documents": [{
      "id": "doc1",
      "source": "Report.pdf",
      "content": "Budget: Rs. 18.6 crore for IT operations."
    }]
  }'
```

---

## Error Handling

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Invalid request body |
| 422 | Validation error (missing required fields) |
| 500 | Internal server error |

---

## Contact

**Backend Team**: Endurance Metrics Engine maintainers
