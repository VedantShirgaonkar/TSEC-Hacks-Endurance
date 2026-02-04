"""
Dimension 9: Environmental & Cost

Metrics:
- Inference Cost (token-based)
- Compute Intensity
- Energy Efficiency Score
- Resource Utilization
"""

from typing import List, Dict, Any
from endurance.metrics.normalizer import normalize_score

MetricResult = None

def _get_metric_result():
    global MetricResult
    if MetricResult is None:
        from endurance.metrics import MetricResult as MR
        MetricResult = MR
    return MetricResult


# Token pricing estimates (per 1M tokens)
TOKEN_PRICING = {
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-4o": {"input": 5.0, "output": 15.0},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    "claude-3-opus": {"input": 15.0, "output": 75.0},
    "claude-3-sonnet": {"input": 3.0, "output": 15.0},
    "azure-openai": {"input": 10.0, "output": 30.0},
    "bedrock": {"input": 8.0, "output": 24.0},
    "default": {"input": 5.0, "output": 15.0},
}

# Estimated FLOP per token (rough estimates based on model size)
FLOP_PER_TOKEN = {
    "gpt-4-turbo": 1e12,  # ~1 TFLOP per token for GPT-4 class
    "gpt-4o": 8e11,
    "gpt-3.5-turbo": 1e11,
    "claude-3-opus": 1.5e12,
    "claude-3-sonnet": 5e11,
    "default": 5e11,
}

# Energy per TFLOP (kWh) - rough estimate
ENERGY_PER_TFLOP = 0.00004  # kWh per TFLOP


def compute(
    query: str,
    response: str,
    rag_documents: list,
    metadata: Dict[str, Any],
) -> list:
    """
    Compute Environmental & Cost metrics.
    """
    MR = _get_metric_result()
    metrics = []
    
    # Extract token counts from metadata
    prompt_tokens = metadata.get("prompt_tokens", estimate_tokens(query))
    completion_tokens = metadata.get("completion_tokens", estimate_tokens(response))
    model = metadata.get("model", "default")
    
    # Metric 1: Inference Cost
    cost = calculate_inference_cost(prompt_tokens, completion_tokens, model)
    # Normalize: $0.01 per query is expensive, $0.001 is cheap
    cost_score = 1.0 - min(cost / 0.01, 1.0)
    metrics.append(MR(
        name="inference_cost",
        dimension="environmental_cost",
        raw_value=cost,
        normalized_score=normalize_score(cost_score, 0, 1),
        explanation=f"Inference cost: ${cost:.4f}"
    ))
    
    # Metric 2: Compute Intensity (FLOP)
    flops = calculate_compute_flops(prompt_tokens + completion_tokens, model)
    # Normalize: 1e12 FLOP is high, 1e10 is low
    flop_ratio = min(flops / 1e12, 1.0)
    metrics.append(MR(
        name="compute_intensity",
        dimension="environmental_cost",
        raw_value=flops,
        normalized_score=normalize_score(flop_ratio, 0, 1, invert=True),  # Lower is better
        explanation=f"Compute intensity: {flops:.2e} FLOP"
    ))
    
    # Metric 3: Energy Consumption (estimated)
    energy_kwh = calculate_energy_consumption(flops)
    # Normalize: 0.001 kWh is high for a query, 0.0001 is low
    energy_ratio = min(energy_kwh / 0.001, 1.0)
    metrics.append(MR(
        name="energy_consumption",
        dimension="environmental_cost",
        raw_value=energy_kwh,
        normalized_score=normalize_score(energy_ratio, 0, 1, invert=True),
        explanation=f"Energy consumption: {energy_kwh*1000:.4f} Wh"
    ))
    
    # Metric 4: Efficiency Score (output value per cost)
    efficiency = calculate_efficiency(response, cost)
    metrics.append(MR(
        name="cost_efficiency",
        dimension="environmental_cost",
        raw_value=efficiency,
        normalized_score=normalize_score(efficiency, 0, 1),
        explanation=f"Cost efficiency score: {efficiency*100:.0f}%"
    ))
    
    return metrics


def estimate_tokens(text: str) -> int:
    """
    Estimate token count from text.
    Rough estimate: 1 token ≈ 4 characters for English text.
    """
    return max(1, len(text) // 4)


def calculate_inference_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model: str,
) -> float:
    """
    Calculate inference cost in USD.
    """
    pricing = TOKEN_PRICING.get(model, TOKEN_PRICING["default"])
    
    input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
    output_cost = (completion_tokens / 1_000_000) * pricing["output"]
    
    return input_cost + output_cost


def calculate_compute_flops(total_tokens: int, model: str) -> float:
    """
    Calculate estimated FLOP for the inference.
    """
    flop_per_token = FLOP_PER_TOKEN.get(model, FLOP_PER_TOKEN["default"])
    return total_tokens * flop_per_token


def calculate_energy_consumption(flops: float) -> float:
    """
    Calculate estimated energy consumption in kWh.
    """
    tflops = flops / 1e12
    return tflops * ENERGY_PER_TFLOP


def calculate_efficiency(response: str, cost: float) -> float:
    """
    Calculate efficiency: value per cost.
    Value is approximated by response quality indicators.
    """
    if cost <= 0:
        return 1.0
    
    # Estimate response value (0-1)
    value = 0.0
    
    # Length contributes to value
    word_count = len(response.split())
    if word_count >= 30:
        value += 0.3
    elif word_count >= 15:
        value += 0.15
    
    # Specificity (numbers, proper nouns) adds value
    import re
    if re.search(r'\d+', response):
        value += 0.3
    if re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+', response):
        value += 0.2
    
    # Sources add value
    if 'according to' in response.lower() or 'based on' in response.lower():
        value += 0.2
    
    # Efficiency = value / normalized_cost
    # Higher value at lower cost = better efficiency
    normalized_cost = min(cost / 0.01, 1.0)  # 1 cent = 1.0
    if normalized_cost > 0:
        efficiency = value / normalized_cost
        return min(efficiency, 1.0)
    
    return value
