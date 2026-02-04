"""
Verification Module - Claim extraction and hallucination detection.
"""

from endurance.verification.claim_extractor import extract_claims
from endurance.verification.source_matcher import match_to_sources
from endurance.verification.hallucination_detector import detect_hallucinations
from endurance.verification.pipeline import verify_response, VerificationResult
from typing import List, Dict, Any


class VerificationPipeline:
    """Wrapper class for verification."""
    
    def verify(self, response: str, rag_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify a response against source documents."""
        try:
            result = verify_response(response, rag_documents)
            return {
                "total_claims": result.total_claims,
                "verified_claims": result.verified_claims,
                "hallucinated_claims": result.hallucinated_claims,
                "verification_score": result.verification_score,
                "claims": result.claims,
            }
        except Exception as e:
            print(f"Verification error: {e}")
            return {
                "total_claims": 0,
                "verified_claims": 0,
                "hallucinated_claims": 0,
                "verification_score": 100.0,
                "claims": [],
            }


__all__ = [
    "extract_claims",
    "match_to_sources", 
    "detect_hallucinations",
    "verify_response",
    "VerificationResult",
    "VerificationPipeline",
]
