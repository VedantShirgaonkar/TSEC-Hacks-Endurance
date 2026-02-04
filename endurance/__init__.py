"""
Endurance - RAI Metrics Platform

A metrics library for evaluating the ethical quality of 
government conversational AI systems.
"""

__version__ = "0.1.0"

from endurance.metrics import compute_all_metrics
from endurance.verification import verify_response

__all__ = ["compute_all_metrics", "verify_response"]
