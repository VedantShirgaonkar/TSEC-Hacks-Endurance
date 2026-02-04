"""
Chatbot API - FastAPI endpoints for the RTI Assistant chatbot.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx

from chatbot.chain import get_rag_chain
from chatbot.config import ENDURANCE_URL

app = FastAPI(
    title="RTI Assistant Chatbot",
    description="LangChain RAG chatbot for RTI queries with Endurance monitoring",
    version="0.1.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    include_evaluation: bool = True  # Whether to run Endurance evaluation


class ChatResponse(BaseModel):
    session_id: str
    message: str
    response: str
    sources: List[Dict[str, Any]]
    evaluation: Optional[Dict[str, Any]] = None
    timestamp: str


class SourceDocument(BaseModel):
    source: str
    content: str


@app.get("/")
async def root():
    return {
        "name": "RTI Assistant Chatbot",
        "version": "0.1.0",
        "status": "running",
        "model": "Groq llama-3.3-70b-versatile",
    }


@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the chatbot and get a response.
    Optionally includes Endurance evaluation.
    """
    import uuid
    
    session_id = request.session_id or str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    try:
        # Get RAG chain and query
        rag_chain = get_rag_chain()
        result = rag_chain.query(request.message)
        
        response_text = result["answer"]
        rag_documents = result["rag_documents"]
        
        # Format sources for response
        sources = [
            {
                "source": doc["source"],
                "content": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
            }
            for doc in rag_documents
        ]
        
        # Run Endurance evaluation if requested
        evaluation = None
        if request.include_evaluation:
            evaluation = await evaluate_response(
                session_id=session_id,
                query=request.message,
                response=response_text,
                rag_documents=rag_documents,
            )
        
        return ChatResponse(
            session_id=session_id,
            message=request.message,
            response=response_text,
            sources=sources,
            evaluation=evaluation,
            timestamp=timestamp,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def evaluate_response(
    session_id: str,
    query: str,
    response: str,
    rag_documents: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Call Endurance API to evaluate the response.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            eval_response = await client.post(
                f"{ENDURANCE_URL}/v1/evaluate",
                json={
                    "session_id": session_id,
                    "query": query,
                    "response": response,
                    "rag_documents": rag_documents,
                },
            )
            
            if eval_response.status_code == 200:
                return eval_response.json()
            else:
                print(f"Endurance evaluation failed: {eval_response.status_code}")
                return None
                
    except Exception as e:
        print(f"Endurance evaluation error: {e}")
        return None


@app.get("/sources")
async def get_sources(query: str):
    """
    Get relevant source documents for a query without generating a response.
    """
    rag_chain = get_rag_chain()
    docs = rag_chain.get_relevant_documents(query)
    return {"query": query, "documents": docs}


@app.post("/reload")
async def reload_documents():
    """
    Reload documents and rebuild the vector store.
    """
    rag_chain = get_rag_chain()
    rag_chain.initialize(force_reload=True)
    return {"status": "Documents reloaded successfully"}


# Run with: uvicorn chatbot.api:app --port 8001 --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
