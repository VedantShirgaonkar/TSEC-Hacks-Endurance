"""
Dimension 8: Response Quality

Metrics:
- Accuracy Score
- Completeness Score
- Relevance Score
- F1 Score (combined)
- Confidence Level (hedging density)

Research Alignment:
- Linguistic Uncertainty: Detects hedging language as proxy for confidence
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
    Compute Response Quality metrics.
    """
    MR = _get_metric_result()
    metrics = []
    
    # Metric 1: Accuracy (from verification if available)
    accuracy = calculate_accuracy(response, rag_documents, metadata)
    metrics.append(MR(
        name="accuracy",
        dimension="response_quality",
        raw_value=accuracy,
        normalized_score=normalize_score(accuracy, 0, 1),
        explanation=f"Response accuracy: {accuracy*100:.0f}%"
    ))
    
    # Metric 2: Completeness
    completeness = calculate_completeness(query, response, rag_documents)
    metrics.append(MR(
        name="completeness",
        dimension="response_quality",
        raw_value=completeness,
        normalized_score=normalize_score(completeness, 0, 1),
        explanation="Completeness of response relative to query"
    ))
    
    # Metric 3: Relevance
    relevance = calculate_relevance(query, response)
    metrics.append(MR(
        name="relevance",
        dimension="response_quality",
        raw_value=relevance,
        normalized_score=normalize_score(relevance, 0, 1),
        explanation="Relevance of response to the query"
    ))
    
    # Metric 4: F1 Score (balance of precision and recall)
    f1 = calculate_f1_score(accuracy, completeness)
    metrics.append(MR(
        name="f1_score",
        dimension="response_quality",
        raw_value=f1,
        normalized_score=normalize_score(f1, 0, 1),
        explanation="F1 score balancing precision and recall"
    ))
    
    # Metric 5: Confidence Level (inverse of hedging density)
    # Research: Linguistic uncertainty detection as proxy for model confidence
    hedging_density = calculate_hedging_density(response)
    confidence = 1.0 - hedging_density  # Low hedging = high confidence
    metrics.append(MR(
        name="confidence_level",
        dimension="response_quality",
        raw_value=confidence,
        normalized_score=normalize_score(confidence, 0, 1),
        explanation=f"Response confidence (hedging density: {hedging_density*100:.0f}%)"
    ))
    
    return metrics


def calculate_accuracy(response: str, rag_documents: list, metadata: Dict[str, Any]) -> float:
    """
    Calculate accuracy of the response.
    Uses verification results if available, otherwise estimates.
    """
    # Use verification results if available
    verified = metadata.get("verified_claims", None)
    total = metadata.get("total_claims", None)
    
    if verified is not None and total is not None and total > 0:
        return verified / total
    
    # Estimate accuracy based on content analysis
    if not rag_documents:
        return 0.5
    
    score = 0.0
    response_lower = response.lower()
    
    # Check for specific data points (numbers, dates)
    has_numbers = bool(re.search(r'[\d₹$€]', response))
    has_dates = bool(re.search(r'\d{4}[-–]\d{2,4}', response))
    has_sources = bool(re.search(r'(according to|based on|source)', response_lower))
    
    if has_numbers:
        score += 0.35
    if has_dates:
        score += 0.25
    if has_sources:
        score += 0.4
    
    return min(score, 1.0)


def calculate_completeness(query: str, response: str, rag_documents: list) -> float:
    """
    Calculate how completely the query was addressed.
    """
    score = 0.0
    query_lower = query.lower()
    response_lower = response.lower()
    
    # Extract what the query is asking for
    query_aspects = []
    
    # Check for question types
    if 'what' in query_lower:
        query_aspects.append('definition')
    if 'how much' in query_lower or 'expenditure' in query_lower or 'cost' in query_lower:
        query_aspects.append('amount')
    if 'when' in query_lower:
        query_aspects.append('time')
    if 'who' in query_lower or 'vendor' in query_lower or 'name' in query_lower:
        query_aspects.append('entities')
    if 'why' in query_lower:
        query_aspects.append('reason')
    if 'list' in query_lower or 'all' in query_lower:
        query_aspects.append('enumeration')
    
    if not query_aspects:
        query_aspects = ['information']  # Default
    
    # Check if response addresses each aspect
    addressed = 0
    
    if 'amount' in query_aspects and re.search(r'[\d₹$€]', response):
        addressed += 1
    if 'time' in query_aspects and re.search(r'(\d{4}|january|february|march|april|may|june|july|august|september|october|november|december)', response_lower):
        addressed += 1
    if 'entities' in query_aspects and re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+|[A-Z]{2,}', response):
        addressed += 1
    if 'enumeration' in query_aspects and (response.count(',') >= 2 or response.count('\n') >= 2):
        addressed += 1
    if 'definition' in query_aspects and len(response.split()) >= 20:
        addressed += 1
    if 'reason' in query_aspects and re.search(r'(because|therefore|due to|reason)', response_lower):
        addressed += 1
    if 'information' in query_aspects and len(response.split()) >= 15:
        addressed += 1
    
    completeness = addressed / len(query_aspects) if query_aspects else 0.5
    
    # Bonus for substantive response
    if len(response.split()) >= 50:
        completeness = min(completeness + 0.1, 1.0)
    
    return completeness


def calculate_relevance(query: str, response: str) -> float:
    """
    Calculate relevance of response to query.
    """
    # Extract meaningful words from query
    query_words = set(query.lower().split())
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'how', 'when', 
                  'where', 'why', 'which', 'who', 'of', 'in', 'on', 'for', 'to', 'with',
                  'and', 'or', 'but', 'not', 'be', 'have', 'has', 'had', 'do', 'does', 'did'}
    
    query_keywords = query_words - stop_words
    
    if not query_keywords:
        return 0.7  # Default if no keywords
    
    response_words = set(response.lower().split())
    
    # Calculate keyword overlap
    overlap = len(query_keywords & response_words)
    relevance = overlap / len(query_keywords)
    
    # Boost for exact phrase matches
    for keyword in query_keywords:
        if len(keyword) > 4 and keyword in response.lower():
            relevance += 0.05
    
    return min(relevance, 1.0)


def calculate_f1_score(precision: float, recall: float) -> float:
    """
    Calculate F1 score as harmonic mean of precision and recall.
    Here we use accuracy as precision and completeness as recall.
    """
    if precision + recall == 0:
        return 0.0
    
    f1 = 2 * (precision * recall) / (precision + recall)
    return f1


def calculate_hedging_density(response: str) -> float:
    """
    Calculate hedging density - a proxy for linguistic uncertainty.
    
    Research Alignment (XAI_RESEARCH_ANALYSIS_V1.md):
    - Hedging language indicates model uncertainty without probabilities
    - Phrases like "might", "possibly", "unclear" suggest low confidence
    
    Returns:
        float: 0.0 (no hedging) to 1.0 (heavily hedged response)
    
    Note:
        - "approximate" is only flagged if NOT followed by a number
        - Higher density = lower confidence = potential concern
    """
    if not response:
        return 0.0
    
    response_lower = response.lower()
    word_count = len(response.split())
    
    if word_count == 0:
        return 0.0
    
    # Hedging patterns with their weights (higher = stronger uncertainty signal)
    HEDGING_PATTERNS = [
        # Modal uncertainty
        (r'\bmaybe\b', 1.0),
        (r'\bperhaps\b', 1.0),
        (r'\bpossibly\b', 1.0),
        (r'\bmight\b', 0.8),
        (r'\bcould be\b', 0.8),
        (r'\bmay be\b', 0.8),
        
        # Evidential hedges
        (r'\bseems to\b', 0.9),
        (r'\bappears to\b', 0.9),
        (r'\bi guess\b', 1.0),
        (r'\bi think\b', 0.7),  # Lower weight as could be stylistic
        (r'\bi believe\b', 0.6),
        
        # Epistemic uncertainty
        (r'\bunclear\b', 1.0),
        (r'\bnot sure\b', 1.0),
        (r'\buncertain\b', 1.0),
        (r'\bprobably\b', 0.7),
        (r'\blikely\b', 0.5),  # Lower weight as can be factual
        
        # Approximation hedges (only if NOT followed by a number)
        (r'\bapproximate(?:ly)?\b(?!\s*\d)', 0.8),
        (r'\babout\b(?!\s*\d)', 0.4),  # Lower weight, common non-hedge usage
        (r'\baround\b(?!\s*\d)', 0.4),
        (r'\broughly\b(?!\s*\d)', 0.6),
        
        # Vagueness markers
        (r'\bsomewhat\b', 0.7),
        (r'\bsort of\b', 0.8),
        (r'\bkind of\b', 0.8),
        (r'\bmore or less\b', 0.9),
        
        # Attribution hedges (shifting responsibility)
        (r'\bsome say\b', 0.8),
        (r'\bit is said\b', 0.7),
        (r'\breportedly\b', 0.6),
        (r'\ballegedly\b', 0.9),
    ]
    
    total_hedge_score = 0.0
    hedge_count = 0
    
    for pattern, weight in HEDGING_PATTERNS:
        matches = re.findall(pattern, response_lower)
        if matches:
            hedge_count += len(matches)
            total_hedge_score += len(matches) * weight
    
    # Normalize by response length (per 100 words)
    # A response with 1 hedge per 20 words is heavily hedged
    hedges_per_100_words = (hedge_count / word_count) * 100
    
    # Map to 0-1 scale
    # 0 hedges = 0.0 density
    # 5+ hedges per 100 words = 1.0 density (very uncertain)
    MAX_HEDGES_PER_100 = 5.0
    density = min(hedges_per_100_words / MAX_HEDGES_PER_100, 1.0)
    
    return density
