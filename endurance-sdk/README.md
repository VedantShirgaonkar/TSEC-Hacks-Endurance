# Endurance RAI SDK

Official Python SDK for **Endurance RAI Engine** - Responsible AI monitoring for government chatbots.

## Installation

```bash
pip install endurance-rai
```

Or install from source:

```bash
git clone https://github.com/yourcompany/endurance-sdk.git
cd endurance-sdk
pip install -e .
```

## Quick Start

```python
import asyncio
from endurance import EnduranceClient, RAGDocument

async def main():
    # Initialize client
    client = EnduranceClient(
        base_url="https://lamaq-endurance-backend-4-hods.hf.space"
    )
    
    # Prepare RAG documents
    docs = [
        RAGDocument(
            source="FOI_Act_2000.pdf",
            content="Public authorities must respond within 20 working days...",
            page=1,
            similarity_score=0.95
        )
    ]
    
    # Evaluate chatbot response
    result = await client.evaluate(
        query="How long for FOI response?",
        response="Public authorities must respond within 20 working days.",
        service_id="uk_gov_chatbot",
        rag_documents=docs
    )
    
    # Check results
    print(f"Overall Score: {result.overall_score}/100")
    print(f"Flagged: {result.flagged}")
    print(f"Grounding: {result.dimensions.data_grounding}")

asyncio.run(main())
```

## Features

- ✅ **Async/await support** for non-blocking evaluations
- ✅ **Automatic retry logic** with exponential backoff
- ✅ **Type hints** for IDE autocomplete
- ✅ **Comprehensive error handling**
- ✅ **9 RAI dimensions** evaluated

## API Reference

### EnduranceClient

Main client for interacting with Endurance RAI Engine.

**Parameters:**
- `base_url` (str): Endurance backend URL
- `api_key` (str, optional): API key for authentication
- `timeout` (float, default=10.0): Request timeout in seconds
- `max_retries` (int, default=3): Maximum retry attempts

**Methods:**
- `evaluate()`: Evaluate chatbot response
- `health_check()`: Check service availability
- `get_service_stats()`: Get aggregate statistics

### RAGDocument

Represents a retrieved document from RAG system.

**Fields:**
- `source` (str): Document source
- `content` (str): Document text
- `page` (int): Page number
- `similarity_score` (float): Retrieval score (0-1)

### EvaluationResult

Result from RAI evaluation.

**Fields:**
- `overall_score` (float): Aggregate score (0-100)
- `flagged` (bool): Whether response requires review
- `dimensions` (DimensionScores): Individual dimension scores
- `session_id` (str): Unique session ID
- `timestamp` (str): Evaluation timestamp

## Error Handling

```python
from endurance import EnduranceClient, EnduranceError, RateLimitError

client = EnduranceClient()

try:
    result = await client.evaluate(...)
except RateLimitError:
    print("Rate limit exceeded")
except EnduranceError as e:
    print(f"Error: {e}")
```

## License

MIT License

## Support

- Documentation: https://endurance-rai.readthedocs.io
- Issues: https://github.com/yourcompany/endurance-sdk/issues
- Email: contact@endurance-rai.com
