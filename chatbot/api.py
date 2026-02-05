"""
Chatbot API - FastAPI endpoints for the RTI Assistant chatbot.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
import base64

import os

# S3 Configuration (same as chain_s3.py)
S3_BUCKET = os.getenv("S3_DOCS_BUCKET", "endurance-docs-1770201946")
S3_DOCS_PREFIX = os.getenv("S3_DOCS_PREFIX", "documents/")

# Use S3-based chain in AWS environment, local ChromaDB otherwise
if os.getenv("ENDURANCE_ENV", "local") == "aws":
    from chatbot.chain_s3 import get_rag_chain
else:
    from chatbot.chain import get_rag_chain

# Endurance telemetry URL (HuggingFace Space)
ENDURANCE_URL = os.getenv("ENDURANCE_URL", "https://lamaq-endurance-backend-4-hods.hf.space")

# Configure API paths based on environment
# In AWS Lambda with API Gateway, paths need the stage prefix
if os.getenv("ENDURANCE_ENV", "local") == "aws":
    # API Gateway stage prefix
    ROOT_PATH = "/prod"
    app = FastAPI(
        title="RTI Assistant Chatbot",
        description="LangChain RAG chatbot for RTI queries with Endurance monitoring",
        version="0.1.0",
        root_path=ROOT_PATH,
        openapi_url="/openapi.json",
        docs_url="/docs",
    )
else:
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
    enable_reasoning: bool = Field(default=False, description="Enable reasoning trace with reasoning model")
    reasoning_effort: str = Field(default="medium", description="Reasoning effort: low, medium, high")


class ChatResponse(BaseModel):
    session_id: str
    message: str
    response: str
    sources: List[Dict[str, Any]]
    evaluation: Optional[Dict[str, Any]] = None
    timestamp: str
    reasoning_trace: Optional[str] = None
    model_used: Optional[str] = None


class SourceDocument(BaseModel):
    source: str
    content: str


class IngestRequest(BaseModel):
    """Request model for document ingestion."""
    filename: str = Field(..., description="Name of the file to store (e.g., 'new_policy.md')")
    content: str = Field(..., description="Document content (plain text or base64 encoded)")
    is_base64: bool = Field(default=False, description="Set to True if content is base64 encoded")
    refresh_embeddings: bool = Field(default=True, description="Whether to refresh the RAG chain after ingestion")


class IngestResponse(BaseModel):
    """Response model for document ingestion."""
    success: bool
    message: str
    s3_key: str
    documents_loaded: Optional[int] = None
    chunks_created: Optional[int] = None
    timestamp: str


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


@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(request: IngestRequest):
    """
    Ingest a new document into the RAG system.
    
    In AWS: Uploads the document to S3 and refreshes the RAG chain embeddings.
    In Local: Saves the document to the local rag_docs folder.
    Supports both plain text and base64 encoded content.
    """
    timestamp = datetime.now().isoformat()
    is_aws = os.getenv("ENDURANCE_ENV", "local") == "aws"
    
    try:
        # Decode content if base64 encoded
        if request.is_base64:
            try:
                content_bytes = base64.b64decode(request.content)
                content = content_bytes.decode('utf-8')
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid base64 content: {str(e)}"
                )
        else:
            content = request.content
        
        # Ensure filename has .md extension (RAG chain only processes .md files)
        filename = request.filename
        if not filename.endswith('.md'):
            filename = f"{filename}.md"
        
        # Storage path/key
        s3_key = f"{S3_DOCS_PREFIX}{filename}"
        
        if is_aws:
            # Upload to S3 in AWS environment
            import boto3
            s3 = boto3.client('s3')
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=content.encode('utf-8'),
                ContentType='text/markdown'
            )
            print(f"[Ingest] Uploaded document to s3://{S3_BUCKET}/{s3_key}")
        else:
            # Save to local rag_docs folder in local environment
            local_docs_path = os.path.join(os.path.dirname(__file__), "rag_docs")
            os.makedirs(local_docs_path, exist_ok=True)
            local_file_path = os.path.join(local_docs_path, filename)
            with open(local_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[Ingest] Saved document to {local_file_path}")
        
        # Refresh RAG chain if requested
        documents_loaded = None
        chunks_created = None
        
        if request.refresh_embeddings:
            if is_aws:
                rag_chain = get_rag_chain()
                rag_chain.initialize(force_reload=True)
                documents_loaded = len([d for d in rag_chain.documents if d.metadata.get('source', '').endswith('.md')])
                chunks_created = len(rag_chain.documents)
                print(f"[Ingest] RAG chain refreshed: {documents_loaded} docs, {chunks_created} chunks")
            else:
                print("[Ingest] Document saved. Restart the server to reload documents in local mode.")
        
        return IngestResponse(
            success=True,
            message=f"Document '{filename}' uploaded successfully to S3",
            s3_key=s3_key,
            documents_loaded=documents_loaded,
            chunks_created=chunks_created,
            timestamp=timestamp,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest document: {str(e)}"
        )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the chatbot and get a response.
    Optionally enables reasoning trace for chain-of-thought analysis.
    Optionally sends telemetry to Endurance (fire-and-forget).
    """
    import uuid
    import asyncio
    
    session_id = request.session_id or str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    try:
        # Get RAG chain
        rag_chain = get_rag_chain()
        
        # Query with or without reasoning based on toggle
        if request.enable_reasoning:
            result = rag_chain.query_with_reasoning(
                request.message, 
                reasoning_effort=request.reasoning_effort
            )
        else:
            result = rag_chain.query(request.message)
        
        response_text = result["answer"]
        rag_documents = result["rag_documents"]
        reasoning_trace = result.get("reasoning_trace")
        model_used = result.get("model_used")
        metadata = result.get("metadata", {})
        
        # Format sources for response
        sources = [
            {
                "source": doc["source"],
                "content": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
            }
            for doc in rag_documents
        ]
        
        # Send to Endurance (await to ensure it completes before Lambda exits)
        evaluation_result = None
        if request.include_evaluation:
            evaluation_result = await send_to_endurance(
                session_id=session_id,
                query=request.message,
                response=response_text,
                rag_documents=rag_documents,
                reasoning_trace=reasoning_trace,
                metadata=metadata,
            )
        
        return ChatResponse(
            session_id=session_id,
            message=request.message,
            response=response_text,
            sources=sources,
            evaluation=evaluation_result,
            timestamp=timestamp,
            reasoning_trace=reasoning_trace,
            model_used=model_used,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def send_to_endurance(
    session_id: str,
    query: str,
    response: str,
    rag_documents: List[Dict[str, Any]],
    reasoning_trace: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Send telemetry to Endurance API and return evaluation result.
    Errors are logged but don't crash the chatbot.
    """
    try:
        # Build payload
        payload = {
            "session_id": session_id,
            "query": query,
            "response": response,
            "service_id": "rti_chatbot",
            "rag_documents": [
                {
                    "source": doc.get("source", "unknown"),
                    "content": doc.get("content", ""),
                    "id": doc.get("id", ""),
                    "similarity_score": doc.get("similarity_score", 0.0)
                }
                for doc in rag_documents
            ],
        }
        
        # Add optional reasoning trace
        if reasoning_trace:
            payload["reasoning_trace"] = reasoning_trace
        
        # Add optional metadata
        if metadata:
            payload["metadata"] = metadata
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            eval_response = await client.post(
                f"{ENDURANCE_URL}/v1/evaluate",
                json=payload,
            )
            if eval_response.status_code == 200:
                return eval_response.json()
            else:
                print(f"Endurance API error: {eval_response.status_code}")
                return {"status": "error", "code": eval_response.status_code}
    except Exception as e:
        # Don't let Endurance errors crash chatbot
        print(f"Endurance telemetry error (non-critical): {e}")
        return {"status": "error", "message": str(e)}


# Run with: uvicorn chatbot.api:app --port 8001 --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
