# AWS RAG Integration: Enabling Reasoning Trace

**For:** AWS Team (Lamaq)  
**Purpose:** Enable GPT-OSS-120B reasoning output to be sent to Endurance Metrics Engine

---

## Overview

To leverage chain-of-thought analysis in Endurance, we need the reasoning trace from GPT-OSS-120B. This doc explains how to enable and send it.

---

## Step 1: Switch to GPT-OSS-120B on Groq

```python
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])
```

**Model ID:** `openai/gpt-oss-120b`

---

## Step 2: Enable Reasoning in API Call

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ],
    # ↓↓↓ ADD THESE PARAMETERS ↓↓↓
    reasoning_format="parsed",   # Returns structured reasoning
    reasoning_effort="medium",   # Options: "low", "medium", "high"
)
```

**Parameters:**
| Parameter | Value | Description |
|-----------|-------|-------------|
| `reasoning_format` | `"parsed"` | Separates reasoning from final answer |
| `reasoning_effort` | `"medium"` | How much thinking (low/medium/high) |

---

## Step 3: Extract Reasoning Trace

```python
# The response now has TWO parts:
final_answer = response.choices[0].message.content
reasoning_trace = response.choices[0].message.reasoning  # ← NEW

# If reasoning is nested differently:
# reasoning_trace = response.choices[0].message.get("reasoning", "")
```

---

## Step 4: Send to Endurance API

Update the payload sent to `/v1/evaluate`:

```python
payload = {
    "query": user_query,
    "response": final_answer,
    "reasoning_trace": reasoning_trace,  # ← ADD THIS
    "rag_documents": [
        {"content": doc.page_content, "source": doc.metadata.get("source", "")}
        for doc in retrieved_docs
    ],
    "metadata": {
        "model": "gpt-oss-120b",
        "reasoning_effort": "medium",
        "tokens_used": response.usage.total_tokens,
        "latency_ms": latency,
    }
}

await client.post(f"{ENDURANCE_URL}/v1/evaluate", json=payload)
```

---

## Expected Reasoning Trace Example

```
Let me analyze this query step by step.

1. The user is asking about the education budget for FY 2024-25.
2. From the retrieved document [Budget_Speech_2024.pdf], I found a reference 
   to education allocation on page 12.
3. The exact figure mentioned is ₹1,48,000 crore (₹1.48 lakh crore).
4. Cross-referencing with [MoE_Annual_Report.pdf], this figure is confirmed.
5. I am confident in this answer as multiple sources align.
```

---

## Quick Checklist

- [ ] Switched model to `openai/gpt-oss-120b`
- [ ] Added `reasoning_format="parsed"` to API call
- [ ] Added `reasoning_effort="medium"` to API call
- [ ] Extracting `response.choices[0].message.reasoning`
- [ ] Sending `reasoning_trace` field to Endurance

---

## Questions?

Once this is deployed, Endurance will be able to:
- Analyze coherence of reasoning steps
- Check if reasoning cites RAG sources
- Detect uncertainty in the thinking process
- Count reasoning depth (number of steps)

Ping when ready to test! 🚀
