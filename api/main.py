"""
FastAPI Backend for Endurance RAI Metrics Platform.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

# Import our metrics engine
from endurance.metrics import (
    compute_all_metrics,
    RAGDocument,
    EvaluationResult,
)
from endurance.verification import verify_response

app = FastAPI(
    title="Endurance RAI Metrics API",
    description="API for evaluating ethical quality of government AI responses",
    version="0.1.0",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo
sessions_db: Dict[str, Dict] = {}
feedback_db: Dict[str, List[Dict]] = {}
audit_log: List[Dict] = []


# Request/Response Models
class RAGDocumentRequest(BaseModel):
    id: str
    source: str
    content: str
    page: Optional[int] = None
    similarity_score: Optional[float] = None


class EvaluateRequest(BaseModel):
    session_id: Optional[str] = None
    query: str
    response: str
    rag_documents: List[RAGDocumentRequest]
    metadata: Optional[Dict[str, Any]] = None


class EvaluateResponse(BaseModel):
    session_id: str
    overall_score: float
    dimensions: Dict[str, float]
    verification_score: float
    verified_claims: int
    total_claims: int
    hallucinated_claims: int
    timestamp: str


class FeedbackRequest(BaseModel):
    session_id: str
    accuracy_rating: int = Field(ge=1, le=5)
    completeness_rating: int = Field(ge=1, le=5)
    clarity_rating: int = Field(ge=1, le=5)
    issues: List[str] = []
    comments: Optional[str] = None
    evaluator_id: Optional[str] = None


class FeedbackResponse(BaseModel):
    feedback_id: str
    session_id: str
    average_rating: float
    timestamp: str


# API Endpoints
@app.get("/")
async def root():
    return {
        "name": "Endurance RAI Metrics API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/v1/evaluate", response_model=EvaluateResponse)
async def evaluate_response(request: EvaluateRequest):
    """
    Evaluate an AI response against ethical dimensions.
    """
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    # Log to audit trail
    log_event("QUERY_RECEIVED", session_id, {
        "query": request.query[:100],
        "rag_doc_count": len(request.rag_documents),
    })
    
    # Convert RAG documents
    rag_docs = [
        RAGDocument(
            id=doc.id,
            source=doc.source,
            content=doc.content,
            page=doc.page,
            similarity_score=doc.similarity_score,
        )
        for doc in request.rag_documents
    ]
    
    # Log RAG retrieval
    log_event("RAG_RETRIEVAL", session_id, {
        "documents": [doc.source for doc in rag_docs],
    })
    
    # Run verification first
    verification_result = verify_response(request.response, rag_docs)
    
    log_event("VERIFICATION_COMPLETE", session_id, {
        "total_claims": verification_result.total_claims,
        "verified_claims": verification_result.verified_claims,
        "hallucinated_claims": verification_result.hallucinated_claims,
    })
    
    # Prepare metadata for metrics
    metadata = request.metadata or {}
    metadata["verified_claims"] = verification_result.verified_claims
    metadata["total_claims"] = verification_result.total_claims
    metadata["hallucinated_claims"] = verification_result.hallucinated_claims
    
    # Compute all metrics
    evaluation = compute_all_metrics(
        query=request.query,
        response=request.response,
        rag_documents=rag_docs,
        metadata=metadata,
    )
    
    # Extract dimension scores
    dimension_scores = {
        name: dim.score for name, dim in evaluation.dimensions.items()
    }
    
    log_event("EVALUATION_COMPLETE", session_id, {
        "overall_score": evaluation.overall_score,
        "dimensions": dimension_scores,
    })
    
    # Store session
    timestamp = datetime.now().isoformat()
    sessions_db[session_id] = {
        "session_id": session_id,
        "query": request.query,
        "response": request.response,
        "rag_documents": [doc.dict() for doc in request.rag_documents],
        "evaluation": {
            "overall_score": evaluation.overall_score,
            "dimensions": dimension_scores,
            "metrics": {k: {"name": v.name, "score": v.normalized_score} 
                       for k, v in evaluation.metrics.items()},
        },
        "verification": {
            "score": verification_result.verification_score,
            "claims": verification_result.claims,
            "hallucinations": verification_result.hallucinations,
        },
        "timestamp": timestamp,
    }
    
    return EvaluateResponse(
        session_id=session_id,
        overall_score=evaluation.overall_score,
        dimensions=dimension_scores,
        verification_score=verification_result.verification_score,
        verified_claims=verification_result.verified_claims,
        total_claims=verification_result.total_claims,
        hallucinated_claims=verification_result.hallucinated_claims,
        timestamp=timestamp,
    )


@app.get("/v1/metrics/{session_id}")
async def get_metrics(session_id: str):
    """
    Get computed metrics for a session.
    """
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions_db[session_id]
    return {
        "session_id": session_id,
        "evaluation": session["evaluation"],
        "timestamp": session["timestamp"],
    }


@app.get("/v1/verify/{session_id}")
async def get_verification(session_id: str):
    """
    Get verification details for a session.
    """
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions_db[session_id]
    return {
        "session_id": session_id,
        "verification": session["verification"],
        "timestamp": session["timestamp"],
    }


@app.get("/v1/claims/{session_id}")
async def get_claims(session_id: str):
    """
    Get extracted claims for a session.
    """
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions_db[session_id]
    return {
        "session_id": session_id,
        "claims": session["verification"]["claims"],
    }


@app.post("/v1/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    Submit human feedback for a session.
    """
    if request.session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    
    feedback_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    avg_rating = (
        request.accuracy_rating +
        request.completeness_rating +
        request.clarity_rating
    ) / 3
    
    feedback = {
        "feedback_id": feedback_id,
        "session_id": request.session_id,
        "accuracy_rating": request.accuracy_rating,
        "completeness_rating": request.completeness_rating,
        "clarity_rating": request.clarity_rating,
        "average_rating": avg_rating,
        "issues": request.issues,
        "comments": request.comments,
        "evaluator_id": request.evaluator_id,
        "timestamp": timestamp,
    }
    
    if request.session_id not in feedback_db:
        feedback_db[request.session_id] = []
    feedback_db[request.session_id].append(feedback)
    
    log_event("HUMAN_FEEDBACK", request.session_id, {
        "average_rating": avg_rating,
        "issues_count": len(request.issues),
    })
    
    return FeedbackResponse(
        feedback_id=feedback_id,
        session_id=request.session_id,
        average_rating=avg_rating,
        timestamp=timestamp,
    )


@app.get("/v1/feedback/{session_id}")
async def get_feedback(session_id: str):
    """
    Get human feedback for a session.
    """
    if session_id not in feedback_db:
        return {"session_id": session_id, "feedback": []}
    
    return {
        "session_id": session_id,
        "feedback": feedback_db[session_id],
    }


@app.get("/v1/audit/{session_id}")
async def get_audit_log(session_id: str):
    """
    Get audit log for a session.
    """
    session_events = [e for e in audit_log if e.get("session_id") == session_id]
    return {
        "session_id": session_id,
        "events": session_events,
    }


@app.get("/v1/audit")
async def get_full_audit_log(limit: int = 100):
    """
    Get full audit log (limited).
    """
    return {
        "total_events": len(audit_log),
        "events": audit_log[-limit:],
    }


@app.get("/v1/dimensions")
async def list_dimensions():
    """
    List all ethical dimensions.
    """
    return {
        "dimensions": [
            {"id": "bias_fairness", "name": "Bias & Fairness", "weight": 0.12},
            {"id": "data_grounding", "name": "Data Grounding & Drift", "weight": 0.15},
            {"id": "explainability", "name": "Explainability & Transparency", "weight": 0.10},
            {"id": "ethical_alignment", "name": "Ethical Alignment", "weight": 0.10},
            {"id": "human_control", "name": "Human Control & Oversight", "weight": 0.08},
            {"id": "legal_compliance", "name": "Legal & Regulatory Compliance", "weight": 0.15},
            {"id": "security", "name": "Security & Robustness", "weight": 0.10},
            {"id": "response_quality", "name": "Response Quality", "weight": 0.12},
            {"id": "environmental_cost", "name": "Environmental & Cost", "weight": 0.08},
        ]
    }


# Utility functions
def log_event(event_type: str, session_id: str, data: Dict[str, Any]):
    """Add event to audit log."""
    audit_log.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "session_id": session_id,
        "data": data,
    })


# Run with: uvicorn api.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
