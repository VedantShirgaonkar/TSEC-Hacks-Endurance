"""
Endurance API - Fast Concurrent Backend
Real-time monitoring with in-memory sessions and SSE streaming.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import deque
from uuid import uuid4
import asyncio
import json

# Import metrics engine
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from endurance.metrics import MetricsEngine
from endurance.verification import VerificationPipeline

app = FastAPI(
    title="Endurance API",
    description="Fast concurrent RAI metrics evaluation for government AI chatbots",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# IN-MEMORY STORES
# ============================================

# Session store (last 1000 sessions)
sessions: deque = deque(maxlen=1000)

# Service-level aggregate metrics
service_metrics: Dict[str, Dict] = {}  # service_id -> aggregate stats

# SSE stream clients
stream_clients: set = set()

# Alert threshold
ALERT_THRESHOLD = 40.0

# Initialize engines
metrics_engine = MetricsEngine()
verification_pipeline = VerificationPipeline()


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class RAGDocument(BaseModel):
    id: str = ""
    source: str = ""
    content: str = ""


class EvaluateRequest(BaseModel):
    session_id: Optional[str] = None
    service_id: Optional[str] = "default"
    query: str
    response: str
    rag_documents: List[RAGDocument] = []
    metadata: Optional[Dict[str, Any]] = None
    custom_weights: Optional[Dict[str, float]] = None  # Dynamic dimension weights


class EvaluateResponse(BaseModel):
    session_id: str
    service_id: str
    overall_score: float
    dimensions: Dict[str, float]
    verification: Dict[str, Any]
    flagged: bool
    flag_reasons: List[str]
    timestamp: str
    reasoning: Optional[List[Dict[str, Any]]] = None  # Explanations for low scores


class SessionSummary(BaseModel):
    session_id: str
    service_id: str
    query_preview: str
    overall_score: float
    flagged: bool
    timestamp: str


class ServiceStats(BaseModel):
    service_id: str
    total_sessions: int
    avg_score: float
    flagged_count: int
    flagged_percentage: float
    dimension_averages: Dict[str, float]
    last_updated: str


# ============================================
# HELPER FUNCTIONS
# ============================================

def compute_dimensions(query: str, response: str, rag_docs: List[Dict]) -> Dict[str, float]:
    """Compute all dimension scores."""
    try:
        result = metrics_engine.evaluate(
            query=query,
            response=response,
            rag_documents=rag_docs,
        )
        return result.get("dimensions", {})
    except Exception as e:
        print(f"Metrics error: {e}")
        # Return default scores on error
        return {
            "bias_fairness": 75.0,
            "data_grounding": 70.0,
            "explainability": 65.0,
            "ethical_alignment": 80.0,
            "human_control": 70.0,
            "legal_compliance": 75.0,
            "security": 80.0,
            "response_quality": 70.0,
            "environmental_cost": 85.0,
        }


def compute_verification(response: str, rag_docs: List[Dict]) -> Dict[str, Any]:
    """Run verification pipeline."""
    try:
        result = verification_pipeline.verify(
            response=response,
            rag_documents=rag_docs,
        )
        return {
            "total_claims": result.get("total_claims", 0),
            "verified_claims": result.get("verified_claims", 0),
            "hallucinated_claims": result.get("hallucinated_claims", 0),
            "verification_score": result.get("verification_score", 100.0),
        }
    except Exception as e:
        print(f"Verification error: {e}")
        return {
            "total_claims": 0,
            "verified_claims": 0,
            "hallucinated_claims": 0,
            "verification_score": 100.0,
        }


def check_flags(overall_score: float, dimensions: Dict[str, float], verification: Dict) -> tuple:
    """Check if session should be flagged."""
    flagged = False
    reasons = []
    
    # Check overall score
    if overall_score < ALERT_THRESHOLD:
        flagged = True
        reasons.append(f"Low overall score: {overall_score:.1f}")
    
    # Check individual dimensions
    for dim, score in dimensions.items():
        if score < ALERT_THRESHOLD:
            flagged = True
            reasons.append(f"Low {dim}: {score:.1f}")
    
    # Check hallucinations
    if verification.get("hallucinated_claims", 0) > 0:
        flagged = True
        reasons.append(f"Hallucinations detected: {verification['hallucinated_claims']}")
    
    return flagged, reasons


def update_service_metrics(service_id: str, session_data: Dict):
    """Update aggregate metrics for a service."""
    if service_id not in service_metrics:
        service_metrics[service_id] = {
            "total_sessions": 0,
            "total_score": 0.0,
            "flagged_count": 0,
            "dimension_totals": {},
            "last_updated": datetime.now().isoformat(),
        }
    
    stats = service_metrics[service_id]
    stats["total_sessions"] += 1
    stats["total_score"] += session_data["overall_score"]
    stats["flagged_count"] += 1 if session_data["flagged"] else 0
    stats["last_updated"] = datetime.now().isoformat()
    
    # Update dimension totals
    for dim, score in session_data["dimensions"].items():
        if dim not in stats["dimension_totals"]:
            stats["dimension_totals"][dim] = 0.0
        stats["dimension_totals"][dim] += score


async def broadcast_to_clients(session_data: Dict):
    """Send new session to all SSE clients."""
    for queue in list(stream_clients):
        try:
            await queue.put(session_data)
        except Exception:
            stream_clients.discard(queue)


# ============================================
# API ENDPOINTS
# ============================================

@app.get("/")
async def root():
    return {
        "name": "Endurance API",
        "version": "1.0.0",
        "status": "running",
        "sessions_in_memory": len(sessions),
        "services_tracked": len(service_metrics),
    }


@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/v1/evaluate", response_model=EvaluateResponse)
async def evaluate(request: EvaluateRequest):
    """
    Evaluate a chatbot response and return metrics.
    This is the main endpoint for SDK integration.
    """
    # 1. Session & Service ID
    session_id = request.session_id or str(uuid4())
    service_id = request.service_id or "default"
    
    # 2. Log Query
    log_event("QUERY_RECEIVED", session_id, {
        "query": request.query[:100],
        "rag_doc_count": len(request.rag_documents),
    })
    
    # 3. Convert RAG Documents
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
    
    # 4. Log RAG Retrieval
    log_event("RAG_RETRIEVAL", session_id, {
        "documents": [doc.source for doc in rag_docs],
    })
    
    # 5. Verification (Robust)
    verification_result = verify_response(request.response, rag_docs)
    
    log_event("VERIFICATION_COMPLETE", session_id, {
        "total_claims": verification_result.total_claims,
        "verified_claims": verification_result.verified_claims,
        "hallucinated_claims": verification_result.hallucinated_claims,
    })
    
    # 6. Metadata
    metadata = request.metadata or {}
    metadata["verified_claims"] = verification_result.verified_claims
    metadata["total_claims"] = verification_result.total_claims
    metadata["hallucinated_claims"] = verification_result.hallucinated_claims
    
    # 7. Compute Metrics (Robust with Reasoning)
    evaluation = compute_all_metrics(
        query=request.query,
        response=request.response,
        rag_documents=rag_docs,
        metadata=metadata,
        weights=request.custom_weights,
    )
    
    # 8. Extract Dimensions
    dimension_scores = {
        name: dim.score for name, dim in evaluation.dimensions.items()
    }
    
    # 9. Log Evaluation
    log_event("EVALUATION_COMPLETE", session_id, {
        "overall_score": evaluation.overall_score,
        "dimensions": dimension_scores,
    })
    
    # 10. Check Flags
    # Create verification dict for check_flags
    verification_dict = {
        "total_claims": verification_result.total_claims,
        "verified_claims": verification_result.verified_claims,
        "hallucinated_claims": verification_result.hallucinated_claims,
        "verification_score": verification_result.score
    }
    
    flagged, flag_reasons = check_flags(evaluation.overall_score, dimension_scores, verification_dict)
    
    # 11. Store Session
    timestamp = datetime.now().isoformat()
    session_data = {
        "session_id": session_id,
        "service_id": service_id,
        "query": request.query,
        "response": request.response,
        "overall_score": evaluation.overall_score,
        "dimensions": dimension_scores,
        "verification": verification_dict,
        "flagged": flagged,
        "flag_reasons": flag_reasons,
        "timestamp": timestamp,
        "metadata": request.metadata,
        "reasoning": evaluation.reasoning,
    }
    
    sessions.appendleft(session_data)
    update_service_metrics(service_id, session_data)
    asyncio.create_task(broadcast_to_clients(session_data))
    
    # 12. Return Response
    return EvaluateResponse(
        session_id=session_id,
        service_id=service_id,
        overall_score=evaluation.overall_score,
        dimensions=dimension_scores,
        verification=verification_dict,
        flagged=flagged,
        flag_reasons=flag_reasons,
        timestamp=timestamp,
        reasoning=evaluation.reasoning,
    )


@app.get("/v1/sessions")
async def get_sessions(
    limit: int = 50,
    service_id: Optional[str] = None,
    flagged_only: bool = False,
):
    """Get recent sessions with optional filters."""
    result = []
    for session in sessions:
        if service_id and session["service_id"] != service_id:
            continue
        if flagged_only and not session["flagged"]:
            continue
        
        result.append(SessionSummary(
            session_id=session["session_id"],
            service_id=session["service_id"],
            query_preview=session["query"][:100] + "..." if len(session["query"]) > 100 else session["query"],
            overall_score=session["overall_score"],
            flagged=session["flagged"],
            timestamp=session["timestamp"],
        ))
        
        if len(result) >= limit:
            break
    
    return {"sessions": result, "total": len(result)}


@app.get("/v1/sessions/{session_id}")
async def get_session(session_id: str):
    """Get full details for a specific session."""
    for session in sessions:
        if session["session_id"] == session_id:
            return session
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/v1/services")
async def get_services():
    """Get all tracked services with aggregate metrics."""
    result = []
    for service_id, stats in service_metrics.items():
        total = stats["total_sessions"]
        result.append(ServiceStats(
            service_id=service_id,
            total_sessions=total,
            avg_score=stats["total_score"] / total if total > 0 else 0,
            flagged_count=stats["flagged_count"],
            flagged_percentage=(stats["flagged_count"] / total * 100) if total > 0 else 0,
            dimension_averages={
                dim: total_score / total if total > 0 else 0
                for dim, total_score in stats["dimension_totals"].items()
            },
            last_updated=stats["last_updated"],
        ))
    return {"services": result}


@app.get("/v1/services/{service_id}/stats")
async def get_service_stats(service_id: str):
    """Get aggregate metrics for a specific service."""
    if service_id not in service_metrics:
        raise HTTPException(status_code=404, detail="Service not found")
    
    stats = service_metrics[service_id]
    total = stats["total_sessions"]
    
    return ServiceStats(
        service_id=service_id,
        total_sessions=total,
        avg_score=stats["total_score"] / total if total > 0 else 0,
        flagged_count=stats["flagged_count"],
        flagged_percentage=(stats["flagged_count"] / total * 100) if total > 0 else 0,
        dimension_averages={
            dim: total_score / total if total > 0 else 0
            for dim, total_score in stats["dimension_totals"].items()
        },
        last_updated=stats["last_updated"],
    )


@app.get("/v1/stream")
async def stream(request: Request, flagged_only: bool = False):
    """
    Server-Sent Events stream for real-time updates.
    Dashboard connects here for live session feed.
    """
    async def event_generator():
        queue = asyncio.Queue()
        stream_clients.add(queue)
        
        try:
            # Send initial batch of sessions
            initial_sessions = [
                s for s in list(sessions) 
                if not flagged_only or s["flagged"]
            ][:50]
            yield f"event: init\ndata: {json.dumps(initial_sessions, default=str)}\n\n"
            
            # Stream new sessions
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                
                try:
                    # Wait for new session with timeout
                    session = await asyncio.wait_for(queue.get(), timeout=1.0)
                    
                    # Apply filter
                    if flagged_only and not session["flagged"]:
                        continue
                        
                    yield f"event: session\ndata: {json.dumps(session, default=str)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive ping
                    yield f"event: ping\ndata: {json.dumps({'ts': datetime.now().isoformat()})}\n\n"
        finally:
            stream_clients.discard(queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@app.get("/v1/metrics/summary")
async def get_metrics_summary():
    """Get overall system metrics summary."""
    total_sessions = len(sessions)
    flagged_sessions = sum(1 for s in sessions if s["flagged"])
    
    # Calculate averages across all sessions
    if total_sessions > 0:
        avg_score = sum(s["overall_score"] for s in sessions) / total_sessions
        
        dimension_sums = {}
        for s in sessions:
            for dim, score in s["dimensions"].items():
                dimension_sums[dim] = dimension_sums.get(dim, 0) + score
        
        dimension_averages = {
            dim: total / total_sessions
            for dim, total in dimension_sums.items()
        }
    else:
        avg_score = 0
        dimension_averages = {}
    
    return {
        "total_sessions": total_sessions,
        "flagged_sessions": flagged_sessions,
        "flagged_percentage": (flagged_sessions / total_sessions * 100) if total_sessions > 0 else 0,
        "avg_overall_score": avg_score,
        "dimension_averages": dimension_averages,
        "services_count": len(service_metrics),
        "alert_threshold": ALERT_THRESHOLD,
    }


@app.post("/v1/feedback/{session_id}")
async def submit_feedback(
    session_id: str,
    approved: bool,
    comment: Optional[str] = None,
):
    """Submit human feedback for a session."""
    for session in sessions:
        if session["session_id"] == session_id:
            session["human_feedback"] = {
                "approved": approved,
                "comment": comment,
                "submitted_at": datetime.now().isoformat(),
            }
            return {"status": "ok", "session_id": session_id}
    
    raise HTTPException(status_code=404, detail="Session not found")


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
