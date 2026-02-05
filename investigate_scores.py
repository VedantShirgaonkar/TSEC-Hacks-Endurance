"""
Detailed investigation of Endurance scoring
"""

import httpx
import asyncio

BASE_URL = "https://lamaq-endurance-backend-4-hods.hf.space"

async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        
        # Test 1: Good response with proper RAG docs
        print("=" * 70)
        print("TEST 1: GOOD RESPONSE WITH RAG DOCUMENTS")
        print("=" * 70)
        
        payload = {
            "query": "How long does a government department have to respond to an FOI request?",
            "response": "According to the Freedom of Information Act 2000, public authorities must respond to your request within 20 working days from receipt. If you haven't received a response, you can contact the ICO for guidance.",
            "service_id": "demo_test",
            "rag_documents": [
                {
                    "id": "foi_1",
                    "source": "ICO_FOI_Guidance.pdf",
                    "content": "The Freedom of Information Act 2000 gives you the right to request information from public authorities. They must respond within 20 working days. Public authorities include government departments, local councils, NHS trusts, schools and police forces."
                }
            ]
        }
        
        resp = await client.post(f"{BASE_URL}/v1/evaluate", json=payload)
        result = resp.json()
        
        print(f"\nOverall Score: {result.get('overall_score', 0):.1f}")
        print(f"Flagged: {result.get('flagged', False)}")
        
        print("\nAll Dimensions:")
        dims = result.get("dimensions", {})
        for dim, score in sorted(dims.items(), key=lambda x: x[1]):
            if score < 40:
                print(f"  🔴 {dim}: {score:.1f} ** CAUSING FLAG **")
            elif score < 60:
                print(f"  🟡 {dim}: {score:.1f}")
            else:
                print(f"  🟢 {dim}: {score:.1f}")
        
        print(f"\nFlag Reasons: {result.get('flag_reasons', [])}")
        
        # Test 2: Empty RAG
        print("\n" + "=" * 70)
        print("TEST 2: WITHOUT RAG DOCUMENTS (Expected to be low)")
        print("=" * 70)
        
        payload_no_rag = {
            "query": "What is the budget?",
            "response": "The budget is 50 million dollars.",
            "service_id": "demo_test",
            "rag_documents": []
        }
        
        resp = await client.post(f"{BASE_URL}/v1/evaluate", json=payload_no_rag)
        result = resp.json()
        
        print(f"\nOverall Score: {result.get('overall_score', 0):.1f}")
        print(f"Flagged: {result.get('flagged', False)}")
        print("\nDimensions below 40 (causing flag):")
        dims = result.get("dimensions", {})
        low_dims = {k: v for k, v in dims.items() if v < 40}
        for dim, score in low_dims.items():
            print(f"  🔴 {dim}: {score:.1f}")
        
        # Test 3: Check verification
        print("\n" + "=" * 70)
        print("TEST 3: VERIFICATION DATA")
        print("=" * 70)
        
        print(f"Verification: {result.get('verification', {})}")

asyncio.run(main())
