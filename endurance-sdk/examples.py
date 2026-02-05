"""
Example usage of Endurance RAI SDK
"""

import asyncio
from endurance import EnduranceClient, RAGDocument


async def basic_example():
    """
    Basic usage example: Evaluate a single response
    """
    print("=" * 60)
    print("EXAMPLE 1: Basic Evaluation")
    print("=" * 60)
    
    # Initialize client
    client = EnduranceClient(
        base_url="https://lamaq-endurance-backend-4-hods.hf.space"
    )
    
    # Check health
    health = await client.health_check()
    print(f"\nService Status: {health.get('status', 'unknown')}")
    
    # Prepare RAG documents
    docs = [
        RAGDocument(
            source="FOI_Act_2000.pdf",
            content="The Freedom of Information Act 2000 provides public access to information held by public authorities. Public authorities must respond to requests within 20 working days.",
            page=1,
            similarity_score=0.95
        ),
        RAGDocument(
            source="ICO_Guidance.pdf",
            content="The response deadline is 20 working days from receipt of the request. Extensions are possible for public interest test considerations.",
            page=3,
            similarity_score=0.88
        )
    ]
    
    # Evaluate response
    print("\n📩 Query: How long does a government department have to respond to an FOI request?")
    print("🤖 Response: Public authorities must respond within 20 working days.\n")
    
    result = await client.evaluate(
        query="How long does a government department have to respond to an FOI request?",
        response="Public authorities must respond within 20 working days.",
        service_id="demo_chatbot",
        rag_documents=docs
    )
    
    # Display results
    print(f"✅ Overall Score: {result.overall_score:.1f}/100")
    print(f"🚨 Flagged: {result.flagged}")
    print(f"\n📊 Dimension Scores:")
    print(f"  - Data Grounding: {result.dimensions.data_grounding:.1f}")
    print(f"  - Legal Compliance: {result.dimensions.legal_compliance:.1f}")
    print(f"  - Response Quality: {result.dimensions.response_quality:.1f}")
    print(f"  - Bias/Fairness: {result.dimensions.bias_fairness:.1f}")
    print(f"\n🆔 Session ID: {result.session_id}")


async def bad_example():
    """
    Example with a bad response (should be flagged)
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Bad Response (Hallucination)")
    print("=" * 60)
    
    client = EnduranceClient()
    
    # Same documents
    docs = [
        RAGDocument(
            source="FOI_Act_2000.pdf",
            content="Public authorities must respond within 20 working days.",
            page=1,
            similarity_score=0.95
        )
    ]
    
    # BAD response with hallucinations
    print("\n📩 Query: How long for FOI response?")
    print("🤖 Response: Government departments typically respond within 30 days, and may charge a £25 processing fee.\n")
    
    result = await client.evaluate(
        query="How long for FOI response?",
        response="Government departments typically respond within 30 days, and may charge a £25 processing fee.",
        service_id="demo_chatbot",
        rag_documents=docs
    )
    
    # Display results
    print(f"❌ Overall Score: {result.overall_score:.1f}/100")
    print(f"🚨 FLAGGED: {result.flagged}")
    print(f"\n📊 Dimension Scores:")
    print(f"  - Data Grounding: {result.dimensions.data_grounding:.1f} (LOW - hallucination detected)")
    print(f"  - Legal Compliance: {result.dimensions.legal_compliance:.1f}")
    
    if result.flagged:
        print("\n⚠️  This response was flagged for review due to low RAI scores.")


async def service_stats_example():
    """
    Example: Get service statistics
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Service Statistics")
    print("=" * 60)
    
    client = EnduranceClient()
    
    try:
        stats = await client.get_service_stats("demo_chatbot")
        print(f"\n📈 Service: demo_chatbot")
        print(f"  - Total Sessions: {stats.get('total_sessions', 'N/A')}")
        print(f"  - Average Score: {stats.get('avg_score', 'N/A'):.1f}")
        print(f"  - Flagged Sessions: {stats.get('flagged_count', 'N/A')}")
    except Exception as e:
        print(f"\n⚠️  Could not fetch stats: {e}")


async def main():
    """
    Run all examples
    """
    print("\n🛡️  ENDURANCE RAI SDK - EXAMPLES\n")
    
    try:
        await basic_example()
        await bad_example()
        await service_stats_example()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")


if __name__ == "__main__":
    asyncio.run(main())
