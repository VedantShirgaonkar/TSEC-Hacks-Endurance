"""
Source Matcher - Match claims against RAG documents.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class SourceMatch:
    """A match between a claim and a source document."""
    claim_text: str
    matched: bool
    source_id: Optional[str]
    source_name: Optional[str]
    matched_text: Optional[str]
    match_type: str  # EXACT, SEMANTIC, PARTIAL, NONE
    confidence: float  # 0-1


def match_to_sources(
    claims: List[Any],  # List of Claim objects
    rag_documents: List[Any],
) -> List[SourceMatch]:
    """
    Match each claim to source documents.
    
    Args:
        claims: List of extracted claims
        rag_documents: List of RAG documents
    
    Returns:
        List of SourceMatch objects
    """
    matches = []
    
    # Combine all source content for searching
    source_contents = {}
    for doc in rag_documents:
        doc_id = getattr(doc, 'id', str(id(doc)))
        doc_source = getattr(doc, 'source', 'unknown')
        doc_content = getattr(doc, 'content', str(doc))
        source_contents[doc_id] = {
            'source': doc_source,
            'content': doc_content.lower(),
            'original': doc_content,
        }
    
    for claim in claims:
        match = match_single_claim(claim, source_contents)
        matches.append(match)
    
    return matches


def match_single_claim(
    claim: Any,
    source_contents: Dict[str, Dict],
) -> SourceMatch:
    """
    Match a single claim against all sources.
    """
    claim_text = claim.text if hasattr(claim, 'text') else str(claim)
    claim_lower = claim_text.lower()
    
    best_match = SourceMatch(
        claim_text=claim_text,
        matched=False,
        source_id=None,
        source_name=None,
        matched_text=None,
        match_type="NONE",
        confidence=0.0,
    )
    
    for doc_id, doc_info in source_contents.items():
        content = doc_info['content']
        
        # 1. Try exact match
        if claim_lower in content:
            return SourceMatch(
                claim_text=claim_text,
                matched=True,
                source_id=doc_id,
                source_name=doc_info['source'],
                matched_text=extract_context(doc_info['original'], claim_text),
                match_type="EXACT",
                confidence=1.0,
            )
        
        # 2. Try matching key entities
        entities = claim.entities if hasattr(claim, 'entities') else [claim_text]
        entity_matches = 0
        for entity in entities:
            if entity.lower() in content:
                entity_matches += 1
        
        if entities and entity_matches == len(entities):
            confidence = 0.9
            if confidence > best_match.confidence:
                best_match = SourceMatch(
                    claim_text=claim_text,
                    matched=True,
                    source_id=doc_id,
                    source_name=doc_info['source'],
                    matched_text=f"All entities found in {doc_info['source']}",
                    match_type="SEMANTIC",
                    confidence=confidence,
                )
        elif entities and entity_matches > 0:
            confidence = 0.5 * (entity_matches / len(entities))
            if confidence > best_match.confidence:
                best_match = SourceMatch(
                    claim_text=claim_text,
                    matched=True,
                    source_id=doc_id,
                    source_name=doc_info['source'],
                    matched_text=f"{entity_matches}/{len(entities)} entities found",
                    match_type="PARTIAL",
                    confidence=confidence,
                )
        
        # 3. Try fuzzy word matching
        claim_words = set(claim_lower.split())
        content_words = set(content.split())
        
        # Remove stop words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'of', 'in', 'on', 'to', 'for', 'and', 'or'}
        claim_words = claim_words - stop_words
        
        if claim_words:
            overlap = len(claim_words & content_words) / len(claim_words)
            if overlap > 0.7 and overlap > best_match.confidence:
                best_match = SourceMatch(
                    claim_text=claim_text,
                    matched=True,
                    source_id=doc_id,
                    source_name=doc_info['source'],
                    matched_text=f"{overlap*100:.0f}% word overlap",
                    match_type="PARTIAL",
                    confidence=overlap * 0.8,
                )
    
    return best_match


def extract_context(text: str, claim: str, context_length: int = 100) -> str:
    """
    Extract context around a matched claim.
    """
    claim_lower = claim.lower()
    text_lower = text.lower()
    
    pos = text_lower.find(claim_lower)
    if pos < 0:
        return text[:context_length] + "..."
    
    start = max(0, pos - context_length // 2)
    end = min(len(text), pos + len(claim) + context_length // 2)
    
    context = text[start:end]
    if start > 0:
        context = "..." + context
    if end < len(text):
        context = context + "..."
    
    return context


def get_match_statistics(matches: List[SourceMatch]) -> Dict[str, Any]:
    """
    Get statistics about source matches.
    """
    total = len(matches)
    if total == 0:
        return {
            "total_claims": 0,
            "matched": 0,
            "unmatched": 0,
            "match_rate": 0.0,
            "by_type": {},
        }
    
    matched = sum(1 for m in matches if m.matched)
    
    by_type = {}
    for m in matches:
        t = m.match_type
        by_type[t] = by_type.get(t, 0) + 1
    
    return {
        "total_claims": total,
        "matched": matched,
        "unmatched": total - matched,
        "match_rate": matched / total,
        "by_type": by_type,
    }
