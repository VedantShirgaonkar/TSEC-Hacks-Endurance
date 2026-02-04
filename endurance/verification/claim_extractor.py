"""
Claim Extractor - Extract factual claims from AI responses.

Claims are categorized as:
- NUMERIC: Numbers, amounts, percentages
- ENTITY: Names, organizations, places
- TEMPORAL: Dates, time periods
- CITATION: Source references
- ASSERTION: General factual statements
"""

from typing import List, Dict, Any
from dataclasses import dataclass
import re


@dataclass
class Claim:
    """A factual claim extracted from a response."""
    text: str
    claim_type: str  # NUMERIC, ENTITY, TEMPORAL, CITATION, ASSERTION
    start_pos: int
    end_pos: int
    entities: List[str]  # Extracted entities within the claim
    confidence: float  # How confident we are this is a claim (0-1)


def extract_claims(response: str) -> List[Claim]:
    """
    Extract all factual claims from a response.
    
    Args:
        response: The AI-generated response text
    
    Returns:
        List of Claim objects
    """
    claims = []
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', response)
    
    current_pos = 0
    for sentence in sentences:
        if len(sentence.strip()) < 10:
            current_pos += len(sentence) + 1
            continue
        
        # Find start position in original text
        start_pos = response.find(sentence, current_pos)
        end_pos = start_pos + len(sentence) if start_pos >= 0 else current_pos + len(sentence)
        
        # Extract claims from this sentence
        sentence_claims = extract_claims_from_sentence(sentence, start_pos, end_pos)
        claims.extend(sentence_claims)
        
        current_pos = end_pos + 1
    
    return claims


def extract_claims_from_sentence(
    sentence: str,
    start_pos: int,
    end_pos: int,
) -> List[Claim]:
    """
    Extract claims from a single sentence.
    """
    claims = []
    
    # 1. Extract NUMERIC claims
    numeric_patterns = [
        r'₹[\d,]+(?:\.\d+)?\s*(?:crore|lakh|thousand|million|billion)?',
        r'\$[\d,]+(?:\.\d+)?\s*(?:thousand|million|billion)?',
        r'[\d,]+(?:\.\d+)?\s*(?:crore|lakh|thousand|million|billion|percent|%)',
        r'(?:total|sum|amount|expenditure|cost|budget).*?[\d,]+',
    ]
    
    for pattern in numeric_patterns:
        matches = re.finditer(pattern, sentence, re.IGNORECASE)
        for match in matches:
            claims.append(Claim(
                text=match.group(0),
                claim_type="NUMERIC",
                start_pos=start_pos + match.start(),
                end_pos=start_pos + match.end(),
                entities=[match.group(0)],
                confidence=0.9
            ))
    
    # 2. Extract ENTITY claims (proper nouns, organization names)
    entity_patterns = [
        r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+',  # Multi-word proper nouns
        r'[A-Z]{2,}(?:\s+[A-Z]{2,})*',  # Acronyms
        r'(?:Mr\.|Mrs\.|Dr\.|Prof\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*',  # Names with titles
    ]
    
    for pattern in entity_patterns:
        matches = re.finditer(pattern, sentence)
        for match in matches:
            # Skip common words that happen to be capitalized
            if match.group(0).lower() in ['the', 'based', 'according', 'financial', 'annual']:
                continue
            claims.append(Claim(
                text=match.group(0),
                claim_type="ENTITY",
                start_pos=start_pos + match.start(),
                end_pos=start_pos + match.end(),
                entities=[match.group(0)],
                confidence=0.8
            ))
    
    # 3. Extract TEMPORAL claims
    temporal_patterns = [
        r'\d{4}[-–]\d{2,4}',  # Year ranges like 2022-23
        r'FY\s*\d{4}[-–]?\d{0,4}',  # Fiscal years
        r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
        r'(?:Q[1-4]|quarter\s+[1-4])\s*\d{4}',
    ]
    
    for pattern in temporal_patterns:
        matches = re.finditer(pattern, sentence, re.IGNORECASE)
        for match in matches:
            claims.append(Claim(
                text=match.group(0),
                claim_type="TEMPORAL",
                start_pos=start_pos + match.start(),
                end_pos=start_pos + match.end(),
                entities=[match.group(0)],
                confidence=0.95
            ))
    
    # 4. Extract CITATION claims
    citation_patterns = [
        r'(?:according to|based on|as per|source:)\s+[^,.]+',
        r'(?:section|page|paragraph|clause)\s+[\d.]+',
    ]
    
    for pattern in citation_patterns:
        matches = re.finditer(pattern, sentence, re.IGNORECASE)
        for match in matches:
            claims.append(Claim(
                text=match.group(0),
                claim_type="CITATION",
                start_pos=start_pos + match.start(),
                end_pos=start_pos + match.end(),
                entities=[match.group(0)],
                confidence=0.85
            ))
    
    # 5. If sentence contains factual indicators but no specific claims extracted,
    # treat the whole sentence as an ASSERTION
    factual_indicators = ['is', 'was', 'are', 'were', 'total', 'spent', 'incurred', 'amounted']
    if not claims and any(ind in sentence.lower() for ind in factual_indicators):
        claims.append(Claim(
            text=sentence.strip(),
            claim_type="ASSERTION",
            start_pos=start_pos,
            end_pos=end_pos,
            entities=extract_key_terms(sentence),
            confidence=0.6
        ))
    
    return claims


def extract_key_terms(text: str) -> List[str]:
    """
    Extract key terms from text for matching.
    """
    # Remove common words
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'must', 'shall',
        'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'from',
        'and', 'or', 'but', 'not', 'this', 'that', 'these', 'those',
    }
    
    words = re.findall(r'\b\w+\b', text.lower())
    key_terms = [w for w in words if w not in stop_words and len(w) > 3]
    
    return key_terms


def get_claim_summary(claims: List[Claim]) -> Dict[str, Any]:
    """
    Get a summary of extracted claims.
    """
    return {
        "total_claims": len(claims),
        "by_type": {
            "numeric": sum(1 for c in claims if c.claim_type == "NUMERIC"),
            "entity": sum(1 for c in claims if c.claim_type == "ENTITY"),
            "temporal": sum(1 for c in claims if c.claim_type == "TEMPORAL"),
            "citation": sum(1 for c in claims if c.claim_type == "CITATION"),
            "assertion": sum(1 for c in claims if c.claim_type == "ASSERTION"),
        },
        "claims": [
            {
                "text": c.text[:100],
                "type": c.claim_type,
                "confidence": c.confidence,
            }
            for c in claims
        ]
    }
