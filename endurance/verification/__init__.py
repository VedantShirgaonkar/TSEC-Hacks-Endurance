"""
Verification Module - Claim extraction and hallucination detection.
"""

from endurance.verification.claim_extractor import extract_claims
from endurance.verification.source_matcher import match_to_sources
from endurance.verification.hallucination_detector import detect_hallucinations
from endurance.verification.pipeline import verify_response, VerificationResult

__all__ = [
    "extract_claims",
    "match_to_sources", 
    "detect_hallucinations",
    "verify_response",
    "VerificationResult",
]
