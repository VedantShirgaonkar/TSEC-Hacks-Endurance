"""
Verification Pipeline - End-to-end response verification.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from endurance.verification.claim_extractor import extract_claims, Claim
from endurance.verification.source_matcher import match_to_sources, SourceMatch
from endurance.verification.hallucination_detector import (
    detect_hallucinations,
    HallucinationResult,
    calculate_hallucination_penalty,
)


@dataclass
class VerificationResult:
    """Complete verification result for a response."""
    response: str
    total_claims: int
    verified_claims: int
    hallucinated_claims: int
    verification_score: float  # 0-100
    hallucination_penalty: float  # 0-1 multiplier
    claims: List[Dict[str, Any]] = field(default_factory=list)
    hallucinations: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""


def verify_response(
    response: str,
    rag_documents: List[Any],
    strict_mode: bool = False,
) -> VerificationResult:
    """
    Verify an AI response against RAG source documents.
    
    This is the main entry point for the verification pipeline.
    
    Args:
        response: The AI-generated response to verify
        rag_documents: List of RAG documents used for the response
        strict_mode: If True, any hallucination fails verification
    
    Returns:
        VerificationResult with full verification details
    """
    # Step 1: Extract claims from response
    claims = extract_claims(response)
    
    if not claims:
        return VerificationResult(
            response=response,
            total_claims=0,
            verified_claims=0,
            hallucinated_claims=0,
            verification_score=50.0,  # Can't verify with no claims
            hallucination_penalty=1.0,
            claims=[],
            hallucinations=[],
            summary="No verifiable claims found in response",
        )
    
    # Step 2: Match claims to sources
    source_matches = match_to_sources(claims, rag_documents)
    
    # Step 3: Detect hallucinations
    hallucination_results = detect_hallucinations(claims, source_matches)
    
    # Step 4: Calculate scores
    verified = sum(1 for m in source_matches if m.matched and m.confidence >= 0.5)
    hallucinated = len(hallucination_results)
    total = len(claims)
    
    # Verification score
    if total > 0:
        base_score = (verified / total) * 100
    else:
        base_score = 50.0
    
    # Apply hallucination penalty
    penalty = calculate_hallucination_penalty(hallucination_results)
    final_score = base_score * penalty
    
    if strict_mode and hallucinated > 0:
        final_score = min(final_score, 30.0)
    
    # Build claims detail
    claims_detail = []
    for i, claim in enumerate(claims):
        match = source_matches[i] if i < len(source_matches) else None
        claims_detail.append({
            "text": claim.text[:100],
            "type": claim.claim_type,
            "status": "VERIFIED" if match and match.matched else "UNVERIFIED",
            "source": match.source_name if match and match.matched else None,
            "confidence": match.confidence if match else 0.0,
        })
    
    # Build hallucinations detail
    hallucinations_detail = [
        {
            "claim": h.claim_text[:100],
            "severity": h.severity,
            "reason": h.reason,
        }
        for h in hallucination_results
    ]
    
    # Generate summary
    summary = generate_summary(total, verified, hallucinated, final_score)
    
    return VerificationResult(
        response=response,
        total_claims=total,
        verified_claims=verified,
        hallucinated_claims=hallucinated,
        verification_score=round(final_score, 2),
        hallucination_penalty=penalty,
        claims=claims_detail,
        hallucinations=hallucinations_detail,
        summary=summary,
    )


def generate_summary(
    total: int,
    verified: int,
    hallucinated: int,
    score: float,
) -> str:
    """
    Generate a human-readable summary of verification.
    """
    if total == 0:
        return "No verifiable claims found in the response."
    
    parts = []
    
    # Overall assessment
    if score >= 80:
        parts.append("Response is well-grounded and highly reliable.")
    elif score >= 60:
        parts.append("Response is mostly reliable with some minor concerns.")
    elif score >= 40:
        parts.append("Response has significant verification issues.")
    else:
        parts.append("Response has major credibility concerns.")
    
    # Claim stats
    parts.append(f"{verified}/{total} claims verified against source documents.")
    
    # Hallucination warning
    if hallucinated > 0:
        if hallucinated == 1:
            parts.append("1 potential hallucination detected.")
        else:
            parts.append(f"{hallucinated} potential hallucinations detected.")
    
    return " ".join(parts)
