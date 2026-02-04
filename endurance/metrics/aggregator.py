"""
Aggregator - Combines dimension scores into overall score.
"""

from typing import Dict, Any
import numpy as np


def aggregate_dimensions(
    dimension_results: Dict[str, Any],
    weights: Dict[str, float],
) -> float:
    """
    Aggregate dimension scores into a single overall score.
    
    Args:
        dimension_results: Dict of dimension name -> DimensionResult
        weights: Dict of dimension name -> weight (should sum to 1.0)
    
    Returns:
        Weighted average overall score (0-100)
    """
    total_weight = sum(weights.values())
    weighted_sum = 0.0
    
    for dim_name, dim_result in dimension_results.items():
        weight = weights.get(dim_name, 0.0)
        weighted_sum += dim_result.score * weight
    
    # Normalize by total weight (in case weights don't sum to 1.0)
    if total_weight > 0:
        overall = weighted_sum / total_weight
    else:
        overall = 0.0
    
    return round(overall, 2)


def aggregate_with_penalties(
    dimension_results: Dict[str, Any],
    weights: Dict[str, float],
    penalties: Dict[str, float] = None,
) -> float:
    """
    Aggregate with penalty multipliers for critical issues.
    
    Args:
        dimension_results: Dict of dimension scores
        weights: Dimension weights
        penalties: Dict of penalty name -> multiplier (0-1)
            e.g., {"hallucination": 0.8} means 20% penalty
    
    Returns:
        Overall score with penalties applied
    """
    base_score = aggregate_dimensions(dimension_results, weights)
    
    if penalties:
        total_penalty = 1.0
        for penalty_name, multiplier in penalties.items():
            total_penalty *= multiplier
        base_score *= total_penalty
    
    return round(base_score, 2)


def calculate_dimension_score(metrics: list) -> float:
    """
    Calculate a dimension score from its component metrics.
    
    Args:
        metrics: List of MetricResult objects
    
    Returns:
        Average score for the dimension
    """
    if not metrics:
        return 0.0
    
    scores = [m.normalized_score for m in metrics]
    return round(np.mean(scores), 2)
