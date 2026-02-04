"""
Hallucination Detector - Identify claims not supported by sources.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class HallucinationResult:
    """Result of hallucination detection for a claim."""
    claim_text: str
    is_hallucination: bool
    severity: str  # HIGH, MEDIUM, LOW
    reason: str
    confidence: float


def detect_hallucinations(
    claims: List[Any],
    source_matches: List[Any],
) -> List[HallucinationResult]:
    """
    Detect which claims are hallucinations (unsupported by sources).
    
    Args:
        claims: List of extracted claims
        source_matches: List of SourceMatch results
    
    Returns:
        List of HallucinationResult for unsupported claims
    """
    hallucinations = []
    
    for i, match in enumerate(source_matches):
        claim = claims[i] if i < len(claims) else None
        claim_text = match.claim_text
        claim_type = claim.claim_type if claim and hasattr(claim, 'claim_type') else "UNKNOWN"
        
        if not match.matched or match.confidence < 0.5:
            # Determine severity based on claim type
            severity = determine_severity(claim_type, match.confidence)
            reason = determine_reason(match, claim_type)
            
            hallucinations.append(HallucinationResult(
                claim_text=claim_text,
                is_hallucination=True,
                severity=severity,
                reason=reason,
                confidence=1.0 - match.confidence,
            ))
    
    return hallucinations


def determine_severity(claim_type: str, match_confidence: float) -> str:
    """
    Determine severity of hallucination based on claim type.
    
    NUMERIC claims that are wrong are HIGH severity (factual errors).
    ENTITY claims can be HIGH (inventing people/orgs).
    TEMPORAL claims are MEDIUM.
    ASSERTION claims are usually LOW.
    """
    if claim_type == "NUMERIC":
        return "HIGH" if match_confidence < 0.3 else "MEDIUM"
    elif claim_type == "ENTITY":
        return "HIGH" if match_confidence < 0.2 else "MEDIUM"
    elif claim_type == "TEMPORAL":
        return "MEDIUM"
    elif claim_type == "CITATION":
        return "HIGH"  # Fake citations are serious
    else:
        return "LOW" if match_confidence > 0.3 else "MEDIUM"


def determine_reason(match: Any, claim_type: str) -> str:
    """
    Generate human-readable reason for hallucination flag.
    """
    if match.match_type == "NONE":
        if claim_type == "NUMERIC":
            return "Numeric value not found in any source document"
        elif claim_type == "ENTITY":
            return "Named entity not found in source documents"
        elif claim_type == "CITATION":
            return "Cited source could not be verified"
        else:
            return "Claim not supported by any source document"
    
    elif match.match_type == "PARTIAL":
        return f"Only partial match found ({match.confidence*100:.0f}% confidence)"
    
    else:
        return f"Low confidence match ({match.confidence*100:.0f}%)"


def get_hallucination_summary(
    hallucinations: List[HallucinationResult],
    total_claims: int,
) -> Dict[str, Any]:
    """
    Get summary of hallucination detection results.
    """
    if total_claims == 0:
        return {
            "hallucination_count": 0,
            "hallucination_rate": 0.0,
            "by_severity": {},
            "details": [],
        }
    
    by_severity = {}
    for h in hallucinations:
        by_severity[h.severity] = by_severity.get(h.severity, 0) + 1
    
    return {
        "hallucination_count": len(hallucinations),
        "hallucination_rate": len(hallucinations) / total_claims,
        "by_severity": by_severity,
        "details": [
            {
                "claim": h.claim_text[:100],
                "severity": h.severity,
                "reason": h.reason,
            }
            for h in hallucinations
        ],
    }


def calculate_hallucination_penalty(
    hallucinations: List[HallucinationResult],
) -> float:
    """
    Calculate a penalty multiplier based on hallucinations.
    
    Returns a value between 0 and 1 to multiply the final score.
    """
    if not hallucinations:
        return 1.0  # No penalty
    
    penalty = 0.0
    
    for h in hallucinations:
        if h.severity == "HIGH":
            penalty += 0.15
        elif h.severity == "MEDIUM":
            penalty += 0.08
        else:  # LOW
            penalty += 0.03
    
    # Cap penalty at 50%
    penalty = min(penalty, 0.5)
    
    return 1.0 - penalty
