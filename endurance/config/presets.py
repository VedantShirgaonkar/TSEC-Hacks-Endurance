"""
Department Presets for Endurance RAI Metrics Platform

These presets provide pre-configured weight profiles for different
government departments and use cases. Selected from the Dashboard dropdown.

Weight Distribution:
- All weights should sum to 1.0
- Dimensions: bias_fairness, data_grounding, explainability, ethical_alignment,
              human_control, legal_compliance, security, response_quality, environmental_cost
"""

from typing import Dict

# ============================================================================
# STANDARD PRESETS
# ============================================================================

STANDARD_RTI = {
    "name": "Standard RTI",
    "description": "Balanced weights for general RTI queries",
    "weights": {
        "bias_fairness": 0.10,
        "data_grounding": 0.15,
        "explainability": 0.10,
        "ethical_alignment": 0.10,
        "human_control": 0.10,
        "legal_compliance": 0.15,
        "security": 0.10,
        "response_quality": 0.15,
        "environmental_cost": 0.05,
    }
}

DEFENSE_MINISTRY = {
    "name": "Defence Ministry",
    "description": "High security and legal compliance focus for sensitive departments",
    "weights": {
        "bias_fairness": 0.05,
        "data_grounding": 0.10,
        "explainability": 0.05,
        "ethical_alignment": 0.10,
        "human_control": 0.10,
        "legal_compliance": 0.25,  # HIGH - Section 8 exemptions critical
        "security": 0.25,          # HIGH - Sensitive information handling
        "response_quality": 0.08,
        "environmental_cost": 0.02,
    }
}

PUBLIC_GRIEVANCE = {
    "name": "Public Grievance Cell",
    "description": "High emphasis on fairness and ethical handling of citizen complaints",
    "weights": {
        "bias_fairness": 0.20,      # HIGH - Equal treatment
        "data_grounding": 0.10,
        "explainability": 0.10,
        "ethical_alignment": 0.20,   # HIGH - Respectful handling
        "human_control": 0.15,       # Escalation paths important
        "legal_compliance": 0.10,
        "security": 0.05,
        "response_quality": 0.08,
        "environmental_cost": 0.02,
    }
}

FINANCE_MINISTRY = {
    "name": "Finance Ministry",
    "description": "High accuracy for budget and expenditure queries",
    "weights": {
        "bias_fairness": 0.05,
        "data_grounding": 0.25,      # HIGH - Accuracy critical for financials
        "explainability": 0.10,
        "ethical_alignment": 0.10,
        "human_control": 0.10,
        "legal_compliance": 0.15,
        "security": 0.10,
        "response_quality": 0.12,
        "environmental_cost": 0.03,
    }
}

HEALTH_MINISTRY = {
    "name": "Health Ministry",
    "description": "Balanced with emphasis on accuracy and ethical handling",
    "weights": {
        "bias_fairness": 0.10,
        "data_grounding": 0.20,      # Accuracy for health data
        "explainability": 0.15,      # Clear explanations for public health
        "ethical_alignment": 0.15,   # Sensitive health topics
        "human_control": 0.10,
        "legal_compliance": 0.10,
        "security": 0.10,
        "response_quality": 0.08,
        "environmental_cost": 0.02,
    }
}

# ============================================================================
# UK GOVERNMENT PRESETS
# ============================================================================

UK_GOVT_STANDARD = {
    "name": "UK Government Standard",
    "description": "Aligned with UK ICO ATRS and AI Principles (Transparency, Fairness, Accountability)",
    "compliance_mode": "UK_GDPR",
    "weights": {
        "bias_fairness": 0.15,       # HIGH - UK Equality Act compliance
        "data_grounding": 0.12,
        "explainability": 0.18,      # HIGH - Article 22 Right to Explanation
        "ethical_alignment": 0.12,
        "human_control": 0.12,       # Contestability and redress
        "legal_compliance": 0.15,    # HIGH - FOI Act, GDPR
        "security": 0.08,
        "response_quality": 0.06,
        "environmental_cost": 0.02,
    }
}

UK_HIGH_SECURITY = {
    "name": "UK High Security",
    "description": "For sensitive departments (Home Office, Defence) with strict FOI exemptions",
    "compliance_mode": "UK_GDPR",
    "weights": {
        "bias_fairness": 0.05,
        "data_grounding": 0.10,
        "explainability": 0.08,
        "ethical_alignment": 0.10,
        "human_control": 0.12,
        "legal_compliance": 0.25,    # VERY HIGH - FOI exemptions critical
        "security": 0.22,            # HIGH - Classified information handling
        "response_quality": 0.06,
        "environmental_cost": 0.02,
    }
}

# ============================================================================
# EU AI ACT PRESETS
# ============================================================================

EU_STRICT_COMPLIANCE = {
    "name": "EU Strict Compliance",
    "description": "Maximum alignment with EU AI Act requirements for high-risk AI systems",
    "compliance_mode": "EU_AI_ACT",
    "weights": {
        "bias_fairness": 0.15,       # HIGH - Non-discrimination
        "data_grounding": 0.10,
        "explainability": 0.15,      # HIGH - Transparency obligation
        "ethical_alignment": 0.12,
        "human_control": 0.15,       # HIGH - Human oversight requirement
        "legal_compliance": 0.18,    # VERY HIGH - AI Act compliance
        "security": 0.08,
        "response_quality": 0.05,
        "environmental_cost": 0.02,
    }
}

EU_CRITICAL_INFRASTRUCTURE = {
    "name": "EU Critical Infrastructure",
    "description": "For energy, transport, and critical public services under AI Act Annex III",
    "compliance_mode": "EU_AI_ACT",
    "weights": {
        "bias_fairness": 0.08,
        "data_grounding": 0.12,
        "explainability": 0.10,
        "ethical_alignment": 0.10,
        "human_control": 0.18,       # CRITICAL - Human oversight mandatory
        "legal_compliance": 0.20,    # VERY HIGH - Annex III requirements
        "security": 0.15,            # HIGH - Infrastructure protection
        "response_quality": 0.05,
        "environmental_cost": 0.02,
    }
}

# ============================================================================
# PRESET REGISTRY
# ============================================================================

PRESETS: Dict[str, dict] = {
    # India RTI Presets
    "standard_rti": STANDARD_RTI,
    "defense_ministry": DEFENSE_MINISTRY,
    "public_grievance": PUBLIC_GRIEVANCE,
    "finance_ministry": FINANCE_MINISTRY,
    "health_ministry": HEALTH_MINISTRY,
    # UK Government Presets
    "uk_govt_standard": UK_GOVT_STANDARD,
    "uk_high_security": UK_HIGH_SECURITY,
    # EU AI Act Presets
    "eu_strict_compliance": EU_STRICT_COMPLIANCE,
    "eu_critical_infrastructure": EU_CRITICAL_INFRASTRUCTURE,
}


def get_preset(preset_name: str) -> dict:
    """
    Get a preset by name.
    
    Args:
        preset_name: Key from PRESETS dict (e.g., "defense_ministry")
    
    Returns:
        Preset config dict with 'name', 'description', 'weights'
    
    Raises:
        KeyError: If preset not found
    """
    if preset_name not in PRESETS:
        available = list(PRESETS.keys())
        raise KeyError(f"Preset '{preset_name}' not found. Available: {available}")
    return PRESETS[preset_name]


def get_preset_weights(preset_name: str) -> Dict[str, float]:
    """
    Get just the weights from a preset.
    
    Args:
        preset_name: Key from PRESETS dict
    
    Returns:
        Dict of dimension -> weight mappings
    """
    return get_preset(preset_name)["weights"]


def list_presets() -> list:
    """
    List all available presets with names and descriptions.
    
    Returns:
        List of dicts with 'key', 'name', 'description'
    """
    return [
        {
            "key": key,
            "name": preset["name"],
            "description": preset["description"],
        }
        for key, preset in PRESETS.items()
    ]


def validate_weights(weights: Dict[str, float]) -> bool:
    """
    Validate that weights sum to approximately 1.0.
    
    Args:
        weights: Dict of dimension -> weight mappings
    
    Returns:
        True if valid (sum is between 0.99 and 1.01)
    """
    total = sum(weights.values())
    return 0.99 <= total <= 1.01
