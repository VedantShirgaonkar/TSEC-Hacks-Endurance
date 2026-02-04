"""
Metrics Engine - Computes all ethical dimension scores.

9 Dimensions:
1. Bias & Fairness
2. Data Grounding & Drift  
3. Explainability & Transparency
4. Ethical Alignment
5. Human Control & Oversight
6. Legal & Regulatory Compliance
7. Security & Robustness
8. Response Quality
9. Environmental & Cost
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import numpy as np

from endurance.metrics.dimensions import (
    bias_fairness,
    data_grounding,
    explainability,
    ethical_alignment,
    human_control,
    legal_compliance,
    security,
    response_quality,
    environmental_cost,
)
from endurance.metrics.normalizer import normalize_score
from endurance.metrics.aggregator import aggregate_dimensions


@dataclass
class RAGDocument:
    """A document retrieved by RAG."""
    id: str
    source: str
    content: str
    page: Optional[int] = None
    similarity_score: Optional[float] = None


@dataclass
class MetricResult:
    """Result of a single metric calculation."""
    name: str
    dimension: str
    raw_value: float
    normalized_score: float  # 0-100
    explanation: str


@dataclass
class DimensionResult:
    """Result of a dimension (aggregated from metrics)."""
    name: str
    score: float  # 0-100
    metrics: List[MetricResult]


@dataclass
class EvaluationResult:
    """Complete evaluation result."""
    overall_score: float  # 0-100
    dimensions: Dict[str, DimensionResult]
    metrics: Dict[str, MetricResult]
    verified_claims: int
    total_claims: int
    hallucinated_claims: int


# Default dimension weights (sum to 1.0)
DEFAULT_WEIGHTS = {
    "bias_fairness": 0.12,
    "data_grounding": 0.15,
    "explainability": 0.10,
    "ethical_alignment": 0.10,
    "human_control": 0.08,
    "legal_compliance": 0.15,
    "security": 0.10,
    "response_quality": 0.12,
    "environmental_cost": 0.08,
}


def compute_all_metrics(
    query: str,
    response: str,
    rag_documents: List[RAGDocument],
    metadata: Optional[Dict[str, Any]] = None,
    weights: Optional[Dict[str, float]] = None,
) -> EvaluationResult:
    """
    Compute all metrics across 9 ethical dimensions.
    
    Args:
        query: The user's query/question
        response: The AI's response
        rag_documents: Documents retrieved by RAG
        metadata: Optional metadata (tokens, latency, model, etc.)
        weights: Optional custom dimension weights
    
    Returns:
        EvaluationResult with overall score and dimension breakdowns
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS
    
    if metadata is None:
        metadata = {}
    
    all_metrics = {}
    dimension_results = {}
    
    # Dimension 1: Bias & Fairness
    bf_metrics = bias_fairness.compute(query, response, rag_documents, metadata)
    bf_result = DimensionResult(
        name="Bias & Fairness",
        score=np.mean([m.normalized_score for m in bf_metrics]),
        metrics=bf_metrics
    )
    dimension_results["bias_fairness"] = bf_result
    for m in bf_metrics:
        all_metrics[m.name] = m
    
    # Dimension 2: Data Grounding & Drift
    dg_metrics = data_grounding.compute(query, response, rag_documents, metadata)
    dg_result = DimensionResult(
        name="Data Grounding & Drift",
        score=np.mean([m.normalized_score for m in dg_metrics]),
        metrics=dg_metrics
    )
    dimension_results["data_grounding"] = dg_result
    for m in dg_metrics:
        all_metrics[m.name] = m
    
    # Dimension 3: Explainability & Transparency
    ex_metrics = explainability.compute(query, response, rag_documents, metadata)
    ex_result = DimensionResult(
        name="Explainability & Transparency",
        score=np.mean([m.normalized_score for m in ex_metrics]),
        metrics=ex_metrics
    )
    dimension_results["explainability"] = ex_result
    for m in ex_metrics:
        all_metrics[m.name] = m
    
    # Dimension 4: Ethical Alignment
    ea_metrics = ethical_alignment.compute(query, response, rag_documents, metadata)
    ea_result = DimensionResult(
        name="Ethical Alignment",
        score=np.mean([m.normalized_score for m in ea_metrics]),
        metrics=ea_metrics
    )
    dimension_results["ethical_alignment"] = ea_result
    for m in ea_metrics:
        all_metrics[m.name] = m
    
    # Dimension 5: Human Control & Oversight
    hc_metrics = human_control.compute(query, response, rag_documents, metadata)
    hc_result = DimensionResult(
        name="Human Control & Oversight",
        score=np.mean([m.normalized_score for m in hc_metrics]),
        metrics=hc_metrics
    )
    dimension_results["human_control"] = hc_result
    for m in hc_metrics:
        all_metrics[m.name] = m
    
    # Dimension 6: Legal & Regulatory Compliance
    lc_metrics = legal_compliance.compute(query, response, rag_documents, metadata)
    lc_result = DimensionResult(
        name="Legal & Regulatory Compliance",
        score=np.mean([m.normalized_score for m in lc_metrics]),
        metrics=lc_metrics
    )
    dimension_results["legal_compliance"] = lc_result
    for m in lc_metrics:
        all_metrics[m.name] = m
    
    # Dimension 7: Security & Robustness
    sec_metrics = security.compute(query, response, rag_documents, metadata)
    sec_result = DimensionResult(
        name="Security & Robustness",
        score=np.mean([m.normalized_score for m in sec_metrics]),
        metrics=sec_metrics
    )
    dimension_results["security"] = sec_result
    for m in sec_metrics:
        all_metrics[m.name] = m
    
    # Dimension 8: Response Quality
    rq_metrics = response_quality.compute(query, response, rag_documents, metadata)
    rq_result = DimensionResult(
        name="Response Quality",
        score=np.mean([m.normalized_score for m in rq_metrics]),
        metrics=rq_metrics
    )
    dimension_results["response_quality"] = rq_result
    for m in rq_metrics:
        all_metrics[m.name] = m
    
    # Dimension 9: Environmental & Cost
    ec_metrics = environmental_cost.compute(query, response, rag_documents, metadata)
    ec_result = DimensionResult(
        name="Environmental & Cost",
        score=np.mean([m.normalized_score for m in ec_metrics]),
        metrics=ec_metrics
    )
    dimension_results["environmental_cost"] = ec_result
    for m in ec_metrics:
        all_metrics[m.name] = m
    
    # Aggregate overall score
    overall_score = aggregate_dimensions(dimension_results, weights)
    
    # Get verification stats from data grounding
    verified = metadata.get("verified_claims", 0)
    total = metadata.get("total_claims", 0)
    hallucinated = metadata.get("hallucinated_claims", 0)
    
    return EvaluationResult(
        overall_score=overall_score,
        dimensions=dimension_results,
        metrics=all_metrics,
        verified_claims=verified,
        total_claims=total,
        hallucinated_claims=hallucinated,
    )


__all__ = [
    "compute_all_metrics",
    "RAGDocument",
    "MetricResult",
    "DimensionResult",
    "EvaluationResult",
    "DEFAULT_WEIGHTS",
]
