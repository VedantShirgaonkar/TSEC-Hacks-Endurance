"""
Dimension 2: Data Grounding & Drift

Metrics:
- Population Stability Index (PSI)
- KL Divergence
- Feature Drift
- Prediction Drift
- Groundedness Score
- Hallucination Rate
"""

from typing import List, Dict, Any
import re
import numpy as np
from endurance.metrics.normalizer import normalize_score

MetricResult = None

def _get_metric_result():
    global MetricResult
    if MetricResult is None:
        from endurance.metrics import MetricResult as MR
        MetricResult = MR
    return MetricResult


def compute(
    query: str,
    response: str,
    rag_documents: list,
    metadata: Dict[str, Any],
) -> list:
    """
    Compute Data Grounding & Drift metrics.
    
    Key metrics for RTI scenario:
    - Groundedness: Is the response grounded in source documents?
    - Hallucination Rate: What fraction of claims are unsupported?
    """
    MR = _get_metric_result()
    metrics = []
    
    # Metric 1: Groundedness Score
    # How much of the response is supported by RAG documents?
    groundedness, details = calculate_groundedness(response, rag_documents)
    metadata["groundedness_details"] = details
    metrics.append(MR(
        name="groundedness_score",
        dimension="data_grounding",
        raw_value=groundedness,
        normalized_score=normalize_score(groundedness, 0, 1),
        explanation=f"Response is {groundedness*100:.0f}% grounded in source documents"
    ))
    
    # Metric 2: Source Coverage
    # Does the response cite/reference sources?
    source_coverage = calculate_source_coverage(response, rag_documents)
    metrics.append(MR(
        name="source_coverage",
        dimension="data_grounding",
        raw_value=source_coverage,
        normalized_score=normalize_score(source_coverage, 0, 1),
        explanation="Coverage of source document references in response"
    ))
    
    # Metric 3: Hallucination Rate (inverted for scoring)
    # What fraction of content appears unsupported?
    halluc_rate = calculate_hallucination_rate(response, rag_documents, details)
    metadata["hallucinated_claims"] = details.get("unsupported_claims", 0)
    metadata["total_claims"] = details.get("total_claims", 0)
    metadata["verified_claims"] = details.get("supported_claims", 0)
    metrics.append(MR(
        name="hallucination_rate",
        dimension="data_grounding",
        raw_value=halluc_rate,
        normalized_score=normalize_score(halluc_rate, 0, 1, invert=True),  # Lower is better
        explanation=f"Hallucination rate: {halluc_rate*100:.0f}% of claims unsupported"
    ))
    
    # Metric 4: Population Stability Index (for comparing distributions)
    # In conversational AI, we compare response patterns over time
    psi = calculate_psi(response, metadata.get("baseline_response", ""))
    metrics.append(MR(
        name="psi",
        dimension="data_grounding",
        raw_value=psi,
        normalized_score=normalize_score(psi, 0, 0.25, invert=True),  # Lower PSI is better
        explanation=f"PSI = {psi:.4f} (stable if < 0.1)"
    ))
    
    return metrics


def calculate_groundedness(response: str, rag_documents: list) -> tuple:
    """
    Calculate how grounded the response is in source documents.
    
    Returns: (groundedness_score, details_dict)
    """
    if not rag_documents:
        return 0.0, {"error": "No RAG documents provided"}
    
    # Combine source content
    source_content = ""
    for doc in rag_documents:
        if hasattr(doc, 'content'):
            source_content += " " + doc.content.lower()
        else:
            source_content += " " + str(doc).lower()
    
    # Extract claims from response (simple approach: split by sentences)
    sentences = re.split(r'[.!?]', response)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    if not sentences:
        return 0.0, {"total_claims": 0, "supported_claims": 0, "unsupported_claims": 0}
    
    supported = 0
    unsupported = 0
    details = {"claims": []}
    
    for sentence in sentences:
        # Check if key terms from sentence appear in sources
        words = sentence.lower().split()
        key_words = [w for w in words if len(w) > 4]  # Focus on meaningful words
        
        if not key_words:
            continue
        
        matches = sum(1 for w in key_words if w in source_content)
        match_ratio = matches / len(key_words) if key_words else 0
        
        is_supported = match_ratio > 0.3
        
        if is_supported:
            supported += 1
            details["claims"].append({"text": sentence[:50], "status": "supported"})
        else:
            unsupported += 1
            details["claims"].append({"text": sentence[:50], "status": "unsupported"})
    
    total = supported + unsupported
    details["total_claims"] = total
    details["supported_claims"] = supported
    details["unsupported_claims"] = unsupported
    
    groundedness = supported / total if total > 0 else 0.0
    return groundedness, details


def calculate_source_coverage(response: str, rag_documents: list) -> float:
    """
    Calculate how well the response references source documents.
    """
    # Look for source citation patterns
    citation_patterns = [
        r'according to',
        r'based on',
        r'as per',
        r'source:',
        r'reference:',
        r'from the',
        r'document',
        r'statement',
        r'report',
        r'section',
        r'page',
    ]
    
    response_lower = response.lower()
    citation_count = 0
    
    for pattern in citation_patterns:
        if pattern in response_lower:
            citation_count += 1
    
    # Also check if specific source names are mentioned
    for doc in rag_documents:
        source_name = getattr(doc, 'source', '')
        if source_name and source_name.lower() in response_lower:
            citation_count += 2  # Bonus for explicit source mention
    
    # Normalize: expect at least 3 citation indicators
    coverage = min(citation_count / 3, 1.0)
    return coverage


def calculate_hallucination_rate(
    response: str,
    rag_documents: list,
    groundedness_details: dict,
) -> float:
    """
    Calculate the hallucination rate.
    """
    total = groundedness_details.get("total_claims", 0)
    unsupported = groundedness_details.get("unsupported_claims", 0)
    
    if total == 0:
        return 0.0
    
    return unsupported / total


def calculate_psi(current: str, baseline: str) -> float:
    """
    Calculate Population Stability Index between current and baseline responses.
    
    PSI measures distribution shift:
    - PSI < 0.1: No significant change
    - 0.1 <= PSI < 0.25: Moderate change
    - PSI >= 0.25: Significant change
    """
    if not baseline:
        return 0.0  # No baseline to compare
    
    # Create word frequency distributions
    def word_freq(text):
        words = text.lower().split()
        total = len(words)
        if total == 0:
            return {}
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        return {k: v/total for k, v in freq.items()}
    
    current_dist = word_freq(current)
    baseline_dist = word_freq(baseline)
    
    # Get all words
    all_words = set(current_dist.keys()) | set(baseline_dist.keys())
    
    if not all_words:
        return 0.0
    
    # Calculate PSI
    psi = 0.0
    epsilon = 0.0001  # Avoid log(0)
    
    for word in all_words:
        p_current = current_dist.get(word, epsilon)
        p_baseline = baseline_dist.get(word, epsilon)
        psi += (p_current - p_baseline) * np.log(p_current / p_baseline)
    
    return abs(psi)
