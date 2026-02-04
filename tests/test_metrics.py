"""
Test script to verify the metrics engine works correctly.
"""

import sys
sys.path.insert(0, '.')

from endurance.metrics import compute_all_metrics, RAGDocument
from endurance.verification import verify_response


def test_good_response():
    """Test with a good RTI response."""
    print("\n" + "="*60)
    print("TEST: Good Response (Expected Score: ~86)")
    print("="*60)
    
    query = "Please provide the total expenditure on external IT consultants during FY 2022-23, along with the names of vendors engaged."
    
    response = """
Based on the Department's Annual Financial Statement for FY 2022-23 and the Procurement Register, the total expenditure on external IT consultants during this period was ₹18.6 crore.

The vendors engaged were:
1. ABC Technologies Pvt Ltd - ₹8.2 crore (Software Development)
2. National Informatics Services - ₹6.1 crore (System Integration)
3. DataCore Solutions India - ₹4.3 crore (Data Analytics)

Source: Annual Financial Statement 2022-23, Section 4.1 (Page 47) and Procurement Register 2022-23.
    """
    
    rag_documents = [
        RAGDocument(
            id="doc_001",
            source="Annual_Financial_Statement_2022-23.pdf",
            content="""
Section 4.1: IT Consultancy Expenditure
Total expenditure on external IT consultants during FY 2022-23: ₹18.6 crore
Breakdown by vendor:
- ABC Technologies Pvt Ltd: ₹8.2 crore
- National Informatics Services: ₹6.1 crore
- DataCore Solutions India: ₹4.3 crore
            """,
            page=47,
            similarity_score=0.95,
        ),
        RAGDocument(
            id="doc_002",
            source="Procurement_Register_2022-23.xlsx",
            content="""
IT Consultancy Procurement Records FY 2022-23
Vendor: ABC Technologies Pvt Ltd | Amount: ₹8.2 crore
Vendor: National Informatics Services | Amount: ₹6.1 crore
Vendor: DataCore Solutions India | Amount: ₹4.3 crore
Total IT Consultancy: ₹18.6 crore
            """,
            similarity_score=0.88,
        ),
    ]
    
    # Run verification
    print("\n--- Verification ---")
    verification = verify_response(response, rag_documents)
    print(f"Verification Score: {verification.verification_score}")
    print(f"Total Claims: {verification.total_claims}")
    print(f"Verified Claims: {verification.verified_claims}")
    print(f"Hallucinations: {verification.hallucinated_claims}")
    print(f"Summary: {verification.summary}")
    
    # Run metrics
    print("\n--- Metrics ---")
    metadata = {
        "verified_claims": verification.verified_claims,
        "total_claims": verification.total_claims,
        "hallucinated_claims": verification.hallucinated_claims,
    }
    
    result = compute_all_metrics(query, response, rag_documents, metadata)
    
    print(f"\nOverall Score: {result.overall_score}")
    print("\nDimension Scores:")
    for dim_name, dim_result in result.dimensions.items():
        print(f"  {dim_result.name}: {dim_result.score}")
    
    return result


def test_bad_response():
    """Test with a bad RTI response (contains hallucination)."""
    print("\n" + "="*60)
    print("TEST: Bad Response (Expected Score: ~34)")
    print("="*60)
    
    query = "Please provide the total expenditure on external IT consultants during FY 2022-23, along with the names of vendors engaged."
    
    response = """
The department spent approximately ₹20-25 crore on IT consultants last year. Various vendors were engaged for different projects. The exact breakdown is not readily available but the major expenditure was on software and system development. Director Sharma oversaw most of these projects and ensured quality delivery.
    """
    
    rag_documents = [
        RAGDocument(
            id="doc_001",
            source="Annual_Financial_Statement_2022-23.pdf",
            content="""
Section 4.1: IT Consultancy Expenditure
Total expenditure on external IT consultants during FY 2022-23: ₹18.6 crore
Breakdown by vendor:
- ABC Technologies Pvt Ltd: ₹8.2 crore
- National Informatics Services: ₹6.1 crore
- DataCore Solutions India: ₹4.3 crore
            """,
            page=47,
            similarity_score=0.95,
        ),
    ]
    
    # Run verification
    print("\n--- Verification ---")
    verification = verify_response(response, rag_documents)
    print(f"Verification Score: {verification.verification_score}")
    print(f"Total Claims: {verification.total_claims}")
    print(f"Verified Claims: {verification.verified_claims}")
    print(f"Hallucinations: {verification.hallucinated_claims}")
    print(f"Summary: {verification.summary}")
    
    if verification.hallucinations:
        print("\nHallucinations Detected:")
        for h in verification.hallucinations:
            print(f"  - {h['claim'][:50]}... ({h['severity']})")
    
    # Run metrics
    print("\n--- Metrics ---")
    metadata = {
        "verified_claims": verification.verified_claims,
        "total_claims": verification.total_claims,
        "hallucinated_claims": verification.hallucinated_claims,
    }
    
    result = compute_all_metrics(query, response, rag_documents, metadata)
    
    print(f"\nOverall Score: {result.overall_score}")
    print("\nDimension Scores:")
    for dim_name, dim_result in result.dimensions.items():
        print(f"  {dim_result.name}: {dim_result.score}")
    
    return result


if __name__ == "__main__":
    print("Endurance Metrics Engine - Test Suite")
    print("="*60)
    
    try:
        good_result = test_good_response()
        bad_result = test_bad_response()
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Good Response Score: {good_result.overall_score}")
        print(f"Bad Response Score:  {bad_result.overall_score}")
        print(f"Difference:          {good_result.overall_score - bad_result.overall_score}")
        
        if good_result.overall_score > bad_result.overall_score:
            print("\n✅ TEST PASSED: Good response scored higher than bad response")
        else:
            print("\n❌ TEST FAILED: Bad response scored higher than good response")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
