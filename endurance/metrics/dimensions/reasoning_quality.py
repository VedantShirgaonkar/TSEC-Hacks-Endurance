"""
Dimension 10: Reasoning Quality

Evaluates the quality of chain-of-thought reasoning traces from reasoning models
(e.g., GPT-OSS-120B, DeepSeek R1).

Metrics:
- Step Count: Number of discrete reasoning steps
- Reasoning Depth: Effort relative to query complexity
- Groundedness: Citation of source documents in reasoning
- Coherence: Logical flow and absence of contradictions
- Uncertainty: Hedging language in reasoning trace
- Self-Verification: Presence of self-checking behavior

Research Basis:
- REVEAL Benchmark (Google, ACL 2024)
- Scheherazade (arXiv, Feb 2025)
- OpenAI CoT Monitorability (July 2025)
- LVU Framework (2024)
"""

from typing import List, Dict, Any, Optional
import re
from endurance.metrics.normalizer import normalize_score

MetricResult = None


def _get_metric_result():
    global MetricResult
    if MetricResult is None:
        from endurance.metrics import MetricResult as MR
        MetricResult = MR
    return MetricResult


# ============================================
# PATTERN DEFINITIONS
# ============================================

# Step detection patterns (Scheherazade, 2025)
STEP_PATTERNS = [
    r'^\s*\d+[\.\)]\s',           # "1. First..." or "1) First..."
    r'^\s*Step\s+\d+',            # "Step 1:"
    r'^\s*(?:First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth)[,:]',
    r'(?:Let me|I will|I\'ll)\s+(?:think|analyze|consider|examine)',
    r'(?:Next|Then|After that|Finally|Lastly)[,:]',
    r'(?:Now|Moving on)[,:]?\s+(?:I|let)',
]

# Logical connectors for coherence
LOGICAL_CONNECTORS = [
    r'\btherefore\b',
    r'\bbecause\b',
    r'\bthus\b',
    r'\bhence\b',
    r'\bconsequently\b',
    r'\bas a result\b',
    r'\bthis means\b',
    r'\bwhich implies\b',
    r'\bso\b',
    r'\bsince\b',
    r'\bgiven that\b',
    r'\bbased on\b',
    r'\bfrom this\b',
    r'\bit follows\b',
]

# Contradiction indicators
CONTRADICTION_PATTERNS = [
    r'\bhowever\b.*\bactually\b',
    r'\bwait\b.*\bthat\'s wrong\b',
    r'\bno\b.*\bthat\'s incorrect\b',
    r'\bI was wrong\b',
    r'\blet me correct\b',
    r'\bactually\b.*\bnot\b.*\bbut\b',
    r'\bcontradicts\b',
    r'\binconsistent\b',
]

# Uncertainty patterns (LVU Framework, 2024)
UNCERTAINTY_PATTERNS = [
    (r'\bnot sure\b', 1.0),
    (r'\bunclear\b', 1.0),
    (r'\buncertain\b', 1.0),
    (r'\bperhaps\b', 0.9),
    (r'\bpossibly\b', 0.9),
    (r'\bmight be\b', 0.8),
    (r'\bcould be\b', 0.8),
    (r'\bmay be\b', 0.8),
    (r'\bi think\b', 0.6),
    (r'\bi believe\b', 0.5),
    (r'\bassuming\b', 0.7),
    (r'\bif correct\b', 0.8),
    (r'\bif I understand\b', 0.7),
    (r'\bseems to\b', 0.7),
    (r'\bappears to\b', 0.7),
    (r'\bprobably\b', 0.6),
    (r'\blikely\b', 0.5),
]

# Self-verification patterns (OpenAI Monitorability, 2025)
VERIFICATION_PATTERNS = [
    r'let me (?:check|verify|confirm|validate)',
    r'double[- ]?check',
    r'to confirm',
    r'this matches',
    r'cross[- ]?referenc',
    r'both sources (?:agree|confirm|say)',
    r'verif(?:y|ied|ying)',
    r'I can confirm',
    r'checking (?:against|with)',
    r'as stated in',
    r'according to the (?:document|source|data)',
    r'the (?:document|source) (?:says|states|confirms)',
]

# Source reference patterns for groundedness
SOURCE_REFERENCE_PATTERNS = [
    r'(?:from|in|according to)\s+(?:the\s+)?(?:document|source|file|pdf|page)',
    r'\[(?:source|doc|page)\s*\d*\]',
    r'(?:document|source)\s+(?:mentions|states|says|indicates)',
    r'based on (?:the\s+)?(?:provided|retrieved|given)',
    r'the (?:text|passage|excerpt) (?:says|states)',
    r'as (?:mentioned|stated|noted) in',
    r'referring to',
    r'citation',
    r'quote[ds]?\s+from',
]


# ============================================
# METRIC FUNCTIONS
# ============================================

def calculate_step_count(reasoning_trace: str) -> int:
    """
    Count discrete reasoning steps in the trace.
    
    Research: Scheherazade (2025) - Accuracy declines with chain length.
    """
    if not reasoning_trace:
        return 0
    
    step_count = 0
    lines = reasoning_trace.split('\n')
    
    for line in lines:
        for pattern in STEP_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE | re.MULTILINE):
                step_count += 1
                break
    
    # Also count paragraph breaks as implicit steps
    paragraph_breaks = reasoning_trace.count('\n\n')
    
    # Use max of explicit steps or paragraph-based estimate
    return max(step_count, paragraph_breaks + 1)


def calculate_reasoning_depth(
    reasoning_trace: str,
    query: str,
) -> float:
    """
    Calculate reasoning depth relative to query complexity.
    
    Returns: 0.0-1.0 where:
        - < 0.3: Shallow (may be insufficient)
        - 0.3-0.7: Appropriate
        - > 0.7: Deep (thorough or verbose)
    
    Uses relative thresholds based on query:response ratio.
    """
    if not reasoning_trace:
        return 0.0
    
    query_words = len(query.split())
    reasoning_words = len(reasoning_trace.split())
    
    if query_words == 0:
        return 0.5
    
    # Expected reasoning length multiplier
    # Simple queries (< 10 words): expect 5-10x
    # Medium queries (10-30 words): expect 3-5x
    # Complex queries (> 30 words): expect 2-3x
    
    if query_words < 10:
        expected_multiplier = 7.5
    elif query_words < 30:
        expected_multiplier = 4.0
    else:
        expected_multiplier = 2.5
    
    expected_reasoning_length = query_words * expected_multiplier
    depth_ratio = reasoning_words / expected_reasoning_length
    
    # Normalize: 0.5x expected = 0.0, 1.0x = 0.5, 2.0x = 1.0
    normalized_depth = min(max((depth_ratio - 0.5) / 1.5, 0.0), 1.0)
    
    return normalized_depth


def calculate_groundedness(
    reasoning_trace: str,
    rag_documents: list,
) -> float:
    """
    Check if reasoning references source documents.
    
    Research: REVEAL (Google, ACL 2024) - Attribution to evidence passages.
    """
    if not reasoning_trace:
        return 0.0
    
    reasoning_lower = reasoning_trace.lower()
    
    # Count source reference patterns
    reference_count = 0
    for pattern in SOURCE_REFERENCE_PATTERNS:
        matches = re.findall(pattern, reasoning_lower, re.IGNORECASE)
        reference_count += len(matches)
    
    # Check for direct quotes or content overlap with RAG docs
    content_overlap = 0
    for doc in rag_documents:
        doc_content = ""
        if isinstance(doc, dict):
            doc_content = doc.get("content", "")
        elif hasattr(doc, "content"):
            doc_content = doc.content
        
        if doc_content:
            # Extract key phrases (3+ word sequences)
            doc_words = doc_content.lower().split()
            for i in range(len(doc_words) - 2):
                phrase = " ".join(doc_words[i:i+3])
                if len(phrase) > 10 and phrase in reasoning_lower:
                    content_overlap += 1
    
    # Combine metrics
    # Reference patterns: 0-0.5 score based on count
    ref_score = min(reference_count / 5, 0.5)
    
    # Content overlap: 0-0.5 score based on matches
    overlap_score = min(content_overlap / 10, 0.5)
    
    return ref_score + overlap_score


def calculate_coherence(reasoning_trace: str) -> float:
    """
    Evaluate logical flow and absence of contradictions.
    
    Research: ACL Multi-hop Reasoning (2024) - Coherent reasoning has
    logical connectors and no internal contradictions.
    """
    if not reasoning_trace:
        return 0.0
    
    reasoning_lower = reasoning_trace.lower()
    word_count = len(reasoning_trace.split())
    
    if word_count == 0:
        return 0.0
    
    # Count logical connectors
    connector_count = 0
    for pattern in LOGICAL_CONNECTORS:
        matches = re.findall(pattern, reasoning_lower)
        connector_count += len(matches)
    
    # Connector density (per 100 words)
    connector_density = (connector_count / word_count) * 100
    
    # Ideal: 2-5 connectors per 100 words
    if connector_density < 1:
        connector_score = connector_density / 1  # 0-1
    elif connector_density <= 5:
        connector_score = 1.0  # optimal
    else:
        connector_score = max(0.5, 1.0 - (connector_density - 5) / 10)  # penalize excessive
    
    # Check for contradictions
    contradiction_count = 0
    for pattern in CONTRADICTION_PATTERNS:
        if re.search(pattern, reasoning_lower, re.IGNORECASE):
            contradiction_count += 1
    
    # Penalty for contradictions (each contradiction reduces score by 0.2)
    contradiction_penalty = min(contradiction_count * 0.2, 0.5)
    
    # Final coherence score
    coherence = (connector_score * 0.7) - contradiction_penalty + 0.3
    
    return max(0.0, min(1.0, coherence))


def calculate_uncertainty(reasoning_trace: str) -> float:
    """
    Measure hedging/uncertainty language in reasoning.
    
    Research: LVU Framework (2024) - Linguistic uncertainty correlates
    with actual model uncertainty.
    
    Returns: 0.0-1.0 where:
        - 0.0: High uncertainty (lots of hedging)
        - 1.0: Low uncertainty (confident reasoning)
    """
    if not reasoning_trace:
        return 0.5  # Neutral when no trace
    
    reasoning_lower = reasoning_trace.lower()
    word_count = len(reasoning_trace.split())
    
    if word_count == 0:
        return 0.5
    
    # Count weighted uncertainty markers
    uncertainty_score = 0.0
    uncertainty_count = 0
    
    for pattern, weight in UNCERTAINTY_PATTERNS:
        matches = re.findall(pattern, reasoning_lower)
        if matches:
            uncertainty_count += len(matches)
            uncertainty_score += len(matches) * weight
    
    # Normalize by length (per 100 words)
    uncertainty_per_100 = (uncertainty_count / word_count) * 100
    
    # High uncertainty = low confidence score
    # 0 markers = 1.0 confidence
    # 5+ markers per 100 words = 0.0 confidence
    confidence = max(0.0, 1.0 - (uncertainty_per_100 / 5))
    
    return confidence


def calculate_self_verification(reasoning_trace: str) -> float:
    """
    Detect self-checking and verification behavior.
    
    Research: OpenAI CoT Monitorability (2025) - Self-verification
    patterns indicate higher reliability.
    """
    if not reasoning_trace:
        return 0.0
    
    reasoning_lower = reasoning_trace.lower()
    
    # Count verification patterns
    verification_count = 0
    for pattern in VERIFICATION_PATTERNS:
        matches = re.findall(pattern, reasoning_lower, re.IGNORECASE)
        verification_count += len(matches)
    
    # Normalize
    # 0 verifications = 0.0
    # 1-2 verifications = 0.3-0.6
    # 3+ verifications = 0.8-1.0
    
    if verification_count == 0:
        return 0.0
    elif verification_count == 1:
        return 0.4
    elif verification_count == 2:
        return 0.6
    elif verification_count == 3:
        return 0.8
    else:
        return 1.0


# ============================================
# MAIN COMPUTE FUNCTION
# ============================================

def compute(
    query: str,
    response: str,
    rag_documents: list,
    metadata: Dict[str, Any],
    reasoning_trace: Optional[str] = None,
) -> list:
    """
    Compute Reasoning Quality metrics.
    
    This dimension is OPTIONAL - only computed when reasoning_trace is provided.
    If no reasoning trace is available, returns empty list.
    """
    MR = _get_metric_result()
    metrics = []
    
    # Skip if no reasoning trace provided
    if not reasoning_trace:
        return metrics
    
    # Metric 1: Step Count
    step_count = calculate_step_count(reasoning_trace)
    # Normalize: 3-10 steps is ideal
    step_score = 0.0
    if step_count < 2:
        step_score = step_count * 0.3
    elif step_count <= 10:
        step_score = 0.6 + (min(step_count - 2, 8) / 8) * 0.4
    else:
        step_score = max(0.5, 1.0 - (step_count - 10) * 0.05)
    
    metrics.append(MR(
        name="reasoning_step_count",
        dimension="reasoning_quality",
        raw_value=float(step_count),
        normalized_score=normalize_score(step_score, 0, 1),
        explanation=f"Detected {step_count} reasoning steps"
    ))
    
    # Metric 2: Reasoning Depth
    depth = calculate_reasoning_depth(reasoning_trace, query)
    metrics.append(MR(
        name="reasoning_depth",
        dimension="reasoning_quality",
        raw_value=depth,
        normalized_score=normalize_score(depth, 0, 1),
        explanation=f"Reasoning depth: {depth*100:.0f}% of expected"
    ))
    
    # Metric 3: Groundedness
    groundedness = calculate_groundedness(reasoning_trace, rag_documents)
    metrics.append(MR(
        name="reasoning_groundedness",
        dimension="reasoning_quality",
        raw_value=groundedness,
        normalized_score=normalize_score(groundedness, 0, 1),
        explanation=f"Reasoning references sources: {groundedness*100:.0f}%"
    ))
    
    # Metric 4: Coherence
    coherence = calculate_coherence(reasoning_trace)
    metrics.append(MR(
        name="reasoning_coherence",
        dimension="reasoning_quality",
        raw_value=coherence,
        normalized_score=normalize_score(coherence, 0, 1),
        explanation=f"Logical coherence: {coherence*100:.0f}%"
    ))
    
    # Metric 5: Uncertainty (inverted - high score = low uncertainty)
    confidence = calculate_uncertainty(reasoning_trace)
    metrics.append(MR(
        name="reasoning_confidence",
        dimension="reasoning_quality",
        raw_value=confidence,
        normalized_score=normalize_score(confidence, 0, 1),
        explanation=f"Reasoning confidence: {confidence*100:.0f}%"
    ))
    
    # Metric 6: Self-Verification
    verification = calculate_self_verification(reasoning_trace)
    metrics.append(MR(
        name="reasoning_self_verification",
        dimension="reasoning_quality",
        raw_value=verification,
        normalized_score=normalize_score(verification, 0, 1),
        explanation=f"Self-verification present: {verification*100:.0f}%"
    ))
    
    return metrics
