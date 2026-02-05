"""
Pydantic models for Endurance RAI SDK
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class RAGDocument(BaseModel):
    """
    Represents a retrieved document from RAG system
    
    Example:
        >>> doc = RAGDocument(
        ...     source="FOI_Act_2000.pdf",
        ...     content="The Freedom of Information Act...",
        ...     page=1,
        ...     similarity_score=0.92
        ... )
    """
    source: str = Field(..., description="Source of the document (filename, URL, etc.)")
    content: str = Field(..., description="Text content of the document")
    page: int = Field(default=0, description="Page number (0 if not applicable)")
    similarity_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Similarity score from retrieval")


class DimensionScores(BaseModel):
    """RAI dimension scores (0-100 scale)"""
    bias_fairness: float = Field(..., ge=0.0, le=100.0)
    data_grounding: float = Field(..., ge=0.0, le=100.0)
    explainability: float = Field(..., ge=0.0, le=100.0)
    ethical_alignment: float = Field(..., ge=0.0, le=100.0)
    human_control: float = Field(..., ge=0.0, le=100.0)
    legal_compliance: float = Field(..., ge=0.0, le=100.0)
    security: float = Field(..., ge=0.0, le=100.0)
    response_quality: float = Field(..., ge=0.0, le=100.0)
    environmental_cost: float = Field(..., ge=0.0, le=100.0)


class EvaluationResult(BaseModel):
    """
    Result from Endurance RAI evaluation
    
    Example:
        >>> result = await client.evaluate(...)
        >>> print(f"Score: {result.overall_score}")
        >>> if result.flagged:
        ...     print("FLAGGED FOR REVIEW")
    """
    session_id: str = Field(..., description="Unique session identifier")
    service_id: str = Field(..., description="Service that made the request")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Aggregate RAI score")
    flagged: bool = Field(..., description="True if session requires review")
    dimensions: DimensionScores = Field(..., description="Individual dimension scores")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")
    timestamp: str = Field(..., description="Evaluation timestamp (ISO 8601)")
    
    def __str__(self):
        status = "🚨 FLAGGED" if self.flagged else "✅ OK"
        return f"Endurance Evaluation: {self.overall_score:.1f}/100 {status}"
