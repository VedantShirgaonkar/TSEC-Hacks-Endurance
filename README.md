# Endurance - RAI Metrics Platform

A Responsible AI (RAI) Metrics Platform for evaluating government conversational AI systems.

## Quick Start

```bash
# Install dependencies
uv pip install -r requirements.txt

# Run API server
cd api && uvicorn main:app --reload

# Run dashboard (in another terminal)
cd dashboard && npm install && npm run dev
```

## Project Structure

```
endurance/
├── endurance/           # Core metrics library
│   ├── metrics/         # 9 ethical dimensions
│   ├── verification/    # Claim extraction & hallucination detection
│   └── adapters/        # Integration adapters
├── api/                 # FastAPI backend
├── dashboard/           # React frontend
├── demo/                # Demo data & mock AI service
└── tests/               # Test suite
```

## Ethical Dimensions

1. Bias & Fairness
2. Data Grounding & Drift
3. Explainability & Transparency
4. Ethical Alignment
5. Human Control & Oversight
6. Legal & Regulatory Compliance
7. Security & Robustness
8. Response Quality
9. Environmental & Cost

## API Endpoints

- `POST /v1/evaluate` - Submit query for evaluation
- `GET /v1/metrics/{session_id}` - Get computed metrics
- `GET /v1/verify/{session_id}` - Get verification details
- `POST /v1/feedback` - Submit human evaluation
- `GET /v1/audit/{session_id}` - Get audit trail

## License

MIT
