"""
Dimension 3: Explainability & Transparency

Metrics:
- Feature Importance Coverage (Source Citation)
- Counterfactual Availability
- Global Surrogate Clarity
- Confidence Score
"""

from typing import List, Dict, Any
import re
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
    Compute Explainability & Transparency metrics.
    """
    MR = _get_metric_result()
    metrics = []
    
    # Metric 1: Source Citation Score
    # Does the response cite its sources clearly?
    citation_score = calculate_citation_score(response, rag_documents)
    metrics.append(MR(
        name="source_citation_score",
        dimension="explainability",
        raw_value=citation_score,
        normalized_score=normalize_score(citation_score, 0, 1),
        explanation="How clearly the response cites its sources"
    ))
    
    # Metric 2: Response Clarity
    # Is the response clear and understandable?
    clarity = calculate_clarity_score(response)
    metrics.append(MR(
        name="response_clarity",
        dimension="explainability",
        raw_value=clarity,
        normalized_score=normalize_score(clarity, 0, 1),
        explanation="Clarity and readability of the response"
    ))
    
    # Metric 3: Reasoning Transparency
    # Does the response explain HOW it arrived at the answer?
    reasoning = calculate_reasoning_transparency(response)
    metrics.append(MR(
        name="reasoning_transparency",
        dimension="explainability",
        raw_value=reasoning,
        normalized_score=normalize_score(reasoning, 0, 1),
        explanation="Presence of reasoning/explanation in response"
    ))
    
    # Metric 4: Confidence Indicator
    # Does the response indicate confidence level?
    confidence = calculate_confidence_indication(response, metadata)
    metrics.append(MR(
        name="confidence_indicator",
        dimension="explainability",
        raw_value=confidence,
        normalized_score=normalize_score(confidence, 0, 1),
        explanation="Presence of confidence/certainty indicators"
    ))
    
    return metrics


def calculate_citation_score(response: str, rag_documents: list) -> float:
    """
    Calculate how well sources are cited in the response.
    """
    score = 0.0
    response_lower = response.lower()
    
    # Check for citation patterns
    citation_patterns = [
        (r'(according to|as per|based on)\s+[\w\s]+', 0.3),
        (r'(source|reference):\s*[\w\s]+', 0.3),
        (r'(section|page|paragraph)\s*\d+', 0.2),
        (r'\d{4}[-–]\d{2,4}', 0.1),  # Year references like 2022-23
    ]
    
    for pattern, weight in citation_patterns:
        if re.search(pattern, response_lower):
            score += weight
    
    # Bonus for mentioning specific document names
    for doc in rag_documents:
        source = getattr(doc, 'source', '')
        if source:
            source_name = source.lower().replace('.pdf', '').replace('.xlsx', '')
            if source_name in response_lower:
                score += 0.2
    
    return min(score, 1.0)


def calculate_clarity_score(response: str) -> float:
    """
    Calculate response clarity based on structure and readability.
    """
    score = 0.0
    
    # Check word count (not too short, not too long per sentence)
    sentences = re.split(r'[.!?]', response)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) >= 2:
        score += 0.2  # Multiple sentences
    
    avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
    if 10 <= avg_sentence_length <= 25:
        score += 0.3  # Good sentence length
    elif 5 <= avg_sentence_length <= 35:
        score += 0.15  # Acceptable
    
    # Check for structure (numbers, bullet points, etc.)
    if re.search(r'[\d₹$€]', response):
        score += 0.2  # Contains specific figures
    
    if re.search(r'[•\-\*]\s', response):
        score += 0.15  # Uses bullet points
    
    # Penalize overly complex words (basic readability)
    words = response.split()
    complex_words = [w for w in words if len(w) > 12]
    if len(complex_words) / max(len(words), 1) < 0.1:
        score += 0.15  # Not too many complex words
    
    return min(score, 1.0)


def calculate_reasoning_transparency(response: str) -> float:
    """
    Check if the response explains its reasoning.
    """
    score = 0.0
    response_lower = response.lower()
    
    # Reasoning indicators
    reasoning_patterns = [
        r'because',
        r'therefore',
        r'this is because',
        r'the reason',
        r'this shows',
        r'which means',
        r'as a result',
        r'consequently',
        r'based on this',
    ]
    
    for pattern in reasoning_patterns:
        if pattern in response_lower:
            score += 0.15
    
    # Check for step-by-step explanation
    if re.search(r'(first|second|third|finally|step)', response_lower):
        score += 0.2
    
    return min(score, 1.0)


def calculate_confidence_indication(response: str, metadata: Dict[str, Any]) -> float:
    """
    Check if response indicates confidence level.
    """
    score = 0.0
    response_lower = response.lower()
    
    # High confidence indicators
    high_conf_patterns = [
        r'(according to|as stated in|confirmed in)',
        r'(specifically|precisely|exactly)',
        r'(official|verified|documented)',
    ]
    
    # Low confidence indicators (uncertainty)
    low_conf_patterns = [
        r'(approximately|about|around|roughly)',
        r'(may|might|could|possibly)',
        r'(unclear|uncertain|not confirmed)',
        r'(estimate|approximately)',
    ]
    
    high_conf_count = sum(1 for p in high_conf_patterns if re.search(p, response_lower))
    low_conf_count = sum(1 for p in low_conf_patterns if re.search(p, response_lower))
    
    # Having confidence indicators (either high or low) is good for transparency
    if high_conf_count > 0:
        score += 0.5
    if low_conf_count > 0:
        score += 0.3  # Acknowledging uncertainty is also good
    
    # Check metadata for confidence score
    if 'confidence' in metadata or 'confidence_score' in metadata:
        score += 0.2
    
    return min(score, 1.0)
