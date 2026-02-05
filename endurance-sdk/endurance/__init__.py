"""
Endurance RAI SDK - Official Python SDK for Endurance RAI Engine
"""

from .client import EnduranceClient
from .models import RAGDocument, EvaluationResult, DimensionScores
from .exceptions import (
    EnduranceError,
    RateLimitError,
    AuthenticationError,
    TimeoutError
)

__version__ = "1.0.0"
__all__ = [
    "EnduranceClient",
    "RAGDocument",
    "EvaluationResult",
    "DimensionScores",
    "EnduranceError",
    "RateLimitError",
    "AuthenticationError",
    "TimeoutError",
]
