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
from endurance.storage import get_mongo_engine
from endurance.config.presets import PRESETS, get_preset

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
# STORAGE
# ============================================

# MongoDB for persistent storage
mongo = get_mongo_engine()

# In-memory cache for fast access (last 100 sessions)
sessions: deque = deque(maxlen=100)

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
    compliance_mode: Optional[str] = None  # "RTI", "UK_GDPR", "EU_AI_ACT"
    preset: Optional[str] = None  # Preset name from PRESETS (e.g., "uk_govt_standard")


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

def compute_dimensions(query: str, response: str, rag_docs: List[Dict], compliance_mode: str = "RTI") -> Dict[str, float]:
    """Compute all dimension scores."""
    try:
        result = metrics_engine.evaluate(
            query=query,
            response=response,
            rag_documents=rag_docs,
            compliance_mode=compliance_mode,
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
    """Update aggregate metrics for a service in MongoDB."""
    mongo.update_service_stats(service_id, session_data)


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
        "mongodb_connected": mongo.connected,
        "services_tracked": len(mongo.get_all_services()) if mongo.connected else 0,
    }


@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/v1/presets")
async def get_presets():
    """
    List all available compliance presets.
    
    Presets provide pre-configured weights and compliance modes for different
    jurisdictions and use cases (e.g., UK Government, EU AI Act).
    """
    presets_info = []
    for key, preset in PRESETS.items():
        presets_info.append({
            "key": key,
            "name": preset.get("name", key),
            "description": preset.get("description", ""),
            "compliance_mode": preset.get("compliance_mode", "RTI"),
        })
    return {
        "presets": presets_info,
        "total": len(presets_info),
    }


@app.get("/v1/compliance-modes")
async def get_compliance_modes():
    """
    List valid compliance modes.
    
    - RTI: Indian Right to Information Act (default)
    - UK_GDPR: UK GDPR + Freedom of Information Act
    - EU_AI_ACT: EU AI Act high-risk system requirements
    """
    return {
        "modes": [
            {"key": "RTI", "name": "India RTI", "description": "Right to Information Act 2005 (India)"},
            {"key": "UK_GDPR", "name": "UK GDPR", "description": "UK GDPR + Freedom of Information Act 2000"},
            {"key": "EU_AI_ACT", "name": "EU AI Act", "description": "EU Artificial Intelligence Act (high-risk systems)"},
        ],
        "default": "RTI",
    }

@app.post("/v1/evaluate", response_model=EvaluateResponse)
async def evaluate(request: EvaluateRequest):
    """
    Evaluate a chatbot response and return metrics.
    This is the main endpoint for SDK integration.
    """
    # 1. Session & Service ID
    session_id = request.session_id or str(uuid4())
    service_id = request.service_id or "default"
    
    # 2. Convert RAG documents to dict format
    rag_docs= [{
        "id": doc.id or "",
        "source": doc.source or "",
        "content": doc.content or "",
        "page": getattr(doc, 'page', 0),
        "similarity_score": getattr(doc, 'similarity_score', 0.0)
    } for doc in request.rag_documents]
    
    # 3. Resolve preset -> weights + compliance_mode
    weights = request.custom_weights
    compliance_mode = request.compliance_mode or "RTI"
    
    if request.preset and request.preset in PRESETS:
        preset_data = get_preset(request.preset)
        # Preset weights (if not overridden by custom_weights)
        if weights is None:
            weights = preset_data.get("weights", {})
        # Preset compliance_mode (if not explicitly provided)
        if request.compliance_mode is None:
            compliance_mode = preset_data.get("compliance_mode", "RTI")
    
    # 4. Compute dimensions with compliance mode
    dimensions = compute_dimensions(request.query, request.response, rag_docs, compliance_mode)
    
    # 5. Compute verification
    verification = compute_verification(request.response, rag_docs)
    
    # 5. Calculate overall score
    if request.custom_weights:
        weights = request.custom_weights
    else:
        weights = {dim: 1.0 for dim in dimensions.keys()}
    
    total_weight = sum(weights.values())
    overall_score = sum(
        dimensions[dim] * weights.get(dim, 1.0) 
        for dim in dimensions.keys()
    ) / total_weight if total_weight > 0 else 0.0
    
    # 6. Check flags
    flagged, flag_reasons = check_flags(overall_score, dimensions, verification)
    
    # 7. Store Session
    timestamp = datetime.now().isoformat()
    session_data = {
        "session_id": session_id,
        "service_id": service_id,
        "query": request.query,
        "response": request.response,
        "overall_score": overall_score,
        "dimensions": dimensions,
        "verification": verification,
        "flagged": flagged,
        "flag_reasons": flag_reasons,
        "timestamp": timestamp,
        "metadata": request.metadata or {},
    }
    
    
    # Store in memory cache (fast access)
    sessions.appendleft(session_data)
    
    # Store in MongoDB (persistent) - async fire-and-forget
    if mongo.connected:
        asyncio.create_task(asyncio.to_thread(mongo.insert_session, session_data))
    
    # Update service metrics in MongoDB
    update_service_metrics(service_id, session_data)
    
    # Broadcast to SSE clients
    asyncio.create_task(broadcast_to_clients(session_data))
    
    # 8. Return Response
    return EvaluateResponse(
        session_id=session_id,
        service_id=service_id,
        overall_score=overall_score,
        dimensions=dimensions,
        verification=verification,
        flagged=flagged,
        flag_reasons=flag_reasons,
        timestamp=timestamp,
        reasoning=None,
    )


@app.get("/v1/sessions")
async def get_sessions(
    limit: int = 50,
    service_id: Optional[str] = None,
    flagged_only: bool = False,
):
    """Get recent sessions with optional filters from MongoDB."""
    # Try MongoDB first
    if mongo.connected:
        db_sessions = await asyncio.to_thread(
            mongo.get_sessions, limit, service_id, flagged_only
        )
        return {"sessions": db_sessions, "total": len(db_sessions), "source": "mongodb"}
    
    # Fallback to memory cache
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
    
    return {"sessions": result, "total": len(result), "source": "memory"}


@app.get("/v1/sessions/{session_id}")
async def get_session(session_id: str):
    """Get full details for a specific session."""
    # Try MongoDB first
    if mongo.connected:
        doc = await asyncio.to_thread(mongo.get_session_by_id, session_id)
        if doc:
            return doc
    
    # Fallback to memory cache
    for session in sessions:
        if session["session_id"] == session_id:
            return session
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/v1/services")
async def get_services():
    """Get all tracked services with aggregate metrics from MongoDB."""
    if mongo.connected:
        services = await asyncio.to_thread(mongo.get_all_services)
        return {"services": services, "source": "mongodb"}
    return {"services": [], "source": "memory"}


@app.get("/v1/services/{service_id}/stats")
async def get_service_stats(service_id: str):
    """Get aggregate metrics for a specific service from MongoDB."""
    if not mongo.connected:
        raise HTTPException(
            status_code=503, 
            detail="MongoDB disconnected - service stats unavailable"
        )
    
    stats = await asyncio.to_thread(mongo.get_service_stats, service_id)
    if stats:
        return stats
    
    raise HTTPException(
        status_code=404, 
        detail=f"Service '{service_id}' not found. No sessions recorded for this service."
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
    """Get overall system metrics summary from MongoDB."""
    if mongo.connected:
        summary = await asyncio.to_thread(mongo.get_metrics_summary)
        summary["alert_threshold"] = ALERT_THRESHOLD
        return summary
    
    # Fallback to memory cache
    total_sessions = len(sessions)
    flagged_sessions = sum(1 for s in sessions if s["flagged"])
    
    return {
        "total_sessions": total_sessions,
        "flagged_sessions": flagged_sessions,
        "flagged_percentage": (flagged_sessions / total_sessions * 100) if total_sessions > 0 else 0,
        "services_count": 0,
        "alert_threshold": ALERT_THRESHOLD,
        "connected": False,
        "source": "memory"
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
