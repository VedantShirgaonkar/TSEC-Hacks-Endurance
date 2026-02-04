# Endurance Architecture Walkthrough

## 1. The "Life of a Request" Analysis

Tracing a user query: **"What is the budget?"**

### Phase 1: The Chatbot (Simulation)
1.  **Entry Point:**
    - The user hits `POST /chat` in **`chatbot/api.py`**.
    - Payload: `{"message": "What is the budget?"}`.

2.  **RAG Generation:**
    - `chatbot/api.py` calls `rag_chain.query("What is the budget?")`.
    - Inside **`chatbot/chain.py`**:
        - **Retrieval:** Searches `Chroma` vector store for relevant PDFs.
        - **Generation:** Sends retrieved context + query to **Groq (Llama-3)**.
        - **Result:** "The budget is 50 Crores."

3.  **The Critical Handoff:**
    - Back in **`chatbot/api.py`**, the `chat` function prepares to audit the response.
    - It calls `evaluate_response(...)`.
    - **specific Line:** `eval_response = await client.post(f"{ENDURANCE_URL}/v1/evaluate", ...)`
    - *This is where the Chatbot (AWS Simulation) stops, and Endurance (The Auditor) begins.*

### Phase 2: The Endurance Engine (The Auditor)
4.  **Metric Computation:**
    - The request hits `POST /v1/evaluate` in **`api/main.py`**.
    - It calls `compute_all_metrics()` in **`endurance/metrics/__init__.py`**.
    - **Action:** Runs all 9 dimensions (Bias, Security, Legal, Tone, etc.) against the query/response pair.

5.  **The Return:**
    - `api/main.py` returns a JSON object with scores, reasoning, and flags.
    - `chatbot/api.py` receives this JSON and embeds it into the final `ChatResponse`.

---

## 2. Directory Map (The Big Picture)

| Directory | Role | Description |
|-----------|------|-------------|
| **`chatbot/`** | **The Simulation** | Represents the Government's existing AI system. Contains the RAG pipeline (`chain.py`) and its own API (`api.py`). It consumes our Metric Engine. |
| **`api/`** | **The Auditor** | The Endurance Metrics Engine API. This is the **Backend** that provides the scoring service. It hosts the `/v1/evaluate` endpoint. |
| **`endurance/`** | **The Core** | The shared library containing the actual metric logic (`metrics/`), verification rules (`verification/`), and scoring math. Both `api` and `chatbot` can import from here if needed, but usually `api` wraps it. |
| **`tests/`** | **Verification** | Usage scripts and tests. `red_team_attack.py` (Adversarial testing) and `test_chatbot_flow.py` (Integration testing) live here. |
| **`docs/`** | **Manuals** | Documentation for Cloud Engineers (`CLOUD_ENGINEER_GUIDE.md`), Judges, and Developers. |

---

## 3. System Architecture Diagram

```mermaid
graph TD
    User[User / Frontier UI] -->|POST /chat| ChatbotAPI[Chatbot API<br/>(chatbot/api.py)]
    
    subgraph "AWS Simulation (The Client)"
        ChatbotAPI -->|Query| RAGChain[RAG Chain<br/>(chatbot/chain.py)]
        RAGChain -->|Retrieve| VectorDB[(Chroma DB)]
        RAGChain -->|Generate| GroqLLM[Groq Llama-3]
        GroqLLM -->|Answer| ChatbotAPI
    end subgraph
    
    ChatbotAPI -->|POST /v1/evaluate<br/>(The Handoff)| EnduranceAPI[Endurance API<br/>(api/main.py)]
    
    subgraph "Endurance Platform (The Auditor)"
        EnduranceAPI -->|Compute| MetricsEngine[Metrics Engine<br/>(endurance/metrics/)]
        MetricsEngine -->|Check| Legal[Legal Compliance<br/>(Section 8 Check)]
        MetricsEngine -->|Check| Tone[Tone & Professionalism]
        MetricsEngine -->|Check| Security[Security & Injection]
        MetricsEngine -->|Score| Scorer[Weighted Scorer]
    end subgraph
    
    Scorer -->|JSON Score + Reasoning| EnduranceAPI
    EnduranceAPI -->|Response| ChatbotAPI
    ChatbotAPI -->|Final JSON| User
```

### ASCII Flowchart

```text
USER QUERY
    │
    ▼
[Chatbot API (Port 8001)] ────────────────────────┐
    │                                             │
    │ 1. Generate Answer (RAG)                    │
    │    (Groq LLM + Vector Store)                │
    │                                             │
    │ 2. HANDOFF: Send to Auditor                 │
    │    (POST http://localhost:8000/evaluate)    │
    │                                             │
    ▼                                             │
[Endurance API (Port 8000)] ◄─────────────────────┘
    │
    │ 3. Compute Metrics (The Engine)
    │    ├── Check Section 8 (Legal)
    │    ├── Check Tone (Chattiness)
    │    └── Check Hallucination (Grounding)
    │
    ▼
[RETURN SCORE & REASONING]
    │
    ▼
[Chatbot API] combines Answer + Score
    │
    ▼
USER RECEIVES:
   - Answer: "The budget is 50 Crores."
   - Score: 92/100 (Green)
   - Reasoning: "Slight tone issue, but legally valid."
```
