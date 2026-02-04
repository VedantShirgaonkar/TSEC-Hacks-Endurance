"""
Normalizer - Converts raw metric values to 0-100 scale.
"""

from typing import Union
import numpy as np


def normalize_score(
    value: float,
    min_val: float = 0.0,
    max_val: float = 1.0,
    invert: bool = False,
    scale: int = 100,
) -> float:
    """
    Normalize a raw metric value to a 0-100 scale.
    
    Args:
        value: Raw metric value
        min_val: Minimum expected value
        max_val: Maximum expected value
        invert: If True, lower raw values = higher scores (for error rates, etc.)
        scale: Output scale (default 100)
    
    Returns:
        Normalized score between 0 and scale
    """
    # Clamp value to expected range
    value = max(min_val, min(max_val, value))
    
    # Calculate normalized value
    if max_val == min_val:
        normalized = 1.0 if value >= max_val else 0.0
    else:
        normalized = (value - min_val) / (max_val - min_val)
    
    # Invert if needed (for metrics where lower is better)
    if invert:
        normalized = 1.0 - normalized
    
    # Scale to 0-100
    return round(normalized * scale, 2)


def normalize_ratio(
    numerator: float,
    denominator: float,
    scale: int = 100,
) -> float:
    """
    Normalize a ratio to 0-100 scale.
    
    Args:
        numerator: Top of ratio
        denominator: Bottom of ratio
        scale: Output scale (default 100)
    
    Returns:
        Normalized score
    """
    if denominator == 0:
        return 0.0
    
    ratio = numerator / denominator
    return round(min(ratio, 1.0) * scale, 2)


def normalize_binary(value: bool, scale: int = 100) -> float:
    """
    Normalize a boolean to 0 or 100.
    """
    return float(scale) if value else 0.0


def normalize_count(
    count: int,
    max_expected: int,
    invert: bool = False,
    scale: int = 100,
) -> float:
    """
    Normalize a count to 0-100 scale.
    
    Args:
        count: The count value
        max_expected: Maximum expected count
        invert: If True, lower counts = higher scores
        scale: Output scale
    
    Returns:
        Normalized score
    """
    if max_expected == 0:
        return float(scale) if count == 0 else 0.0
    
    normalized = min(count / max_expected, 1.0)
    
    if invert:
        normalized = 1.0 - normalized
    
    return round(normalized * scale, 2)


def sigmoid_normalize(
    value: float,
    midpoint: float = 0.5,
    steepness: float = 10.0,
    scale: int = 100,
) -> float:
    """
    Apply sigmoid normalization for smoother transitions.
    
    Args:
        value: Raw value (typically 0-1)
        midpoint: Value at which output is 50
        steepness: How sharp the transition is
        scale: Output scale
    
    Returns:
        Smoothly normalized score
    """
    sigmoid = 1 / (1 + np.exp(-steepness * (value - midpoint)))
    return round(sigmoid * scale, 2)
