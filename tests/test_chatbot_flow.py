"""
Test script to verify the 'passthrough' of custom_weights 
from the Chatbot API to the Endurance Metrics Engine.
"""

import sys
import os
import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# MOCK ENVIRONMENT VARIABLES BEFORE IMPORTS to avoid Config errors
os.environ["GROQ_API_KEY"] = "dummy_key_for_testing"

# Import the app (we need to mock dependencies before importing/using)
from chatbot.api import app

client = TestClient(app)

# Decorators removed - managing mocks manually in __main__
def test_chatbot_custom_weights_passthrough(mock_post, mock_get_chain):
    """
    Test that custom_weights sent to /chat are passed to the Endurance API evaluation.
    """
    print("\n🚀 Starting Chatbot Passthrough Test...")

    # 1. Mock RAG Chain response (so we don't need LLM)
    mock_chain = MagicMock()
    mock_chain.query.return_value = {
        "answer": "This is a mock response about verification.",
        "rag_documents": [
            {"source": "test_doc.pdf", "content": "Verification content source."}
        ]
    }
    mock_get_chain.return_value = mock_chain

    # 2. Mock Endurance API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "session_id": "test-session",
        "overall_score": 85.0,
        "dimensions": {"security": 90.0, "tone": 80.0}
    }
    mock_post.return_value = mock_response

    # 3. Define custom weights to test
    test_weights = {"security": 0.8, "tone": 0.2}

    # 4. Make request to Chatbot API
    payload = {
        "message": "Test query",
        "include_evaluation": True,
        "custom_weights": test_weights
    }
    
    print(f"📡 Sending request to /chat with weights: {test_weights}")
    response = client.post("/chat", json=payload)

    # 5. Assertions
    assert response.status_code == 200, f"Request failed: {response.text}"
    data = response.json()
    
    print("✅ Chatbot response received.")

    # Verify RAG chain was called
    mock_chain.query.assert_called_once()
    
    # Verify Endurance API was called with correct payload
    assert mock_post.called, "Endurance API was not called"
    
    # Inspect the call arguments to httpx.post
    call_args = mock_post.call_args
    # call_args[0] is positional args (url)
    # call_args[1] is keyword args (json=...)
    
    request_json = call_args[1].get("json", {})
    
    print("\n🔍 Inspecting payload sent to Endurance Engine:")
    print(json.dumps(request_json, indent=2))

    assert "custom_weights" in request_json, "custom_weights missing from Endurance API payload!"
    assert request_json["custom_weights"] == test_weights, "Weights passed to Endurance do not match input!"

    print("\n🎉 SUCCESS: Custom weights were correctly passed through to the Metrics Engine!")

if __name__ == "__main__":
    # Manually run the test function if executed as script
    try:
        # Create mocks manually for script execution
        with patch("chatbot.api.get_rag_chain") as mock_chain_func, \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post_func:
            
            test_chatbot_custom_weights_passthrough(mock_post_func, mock_chain_func)
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
