"""
Main client for interacting with Endurance RAI Engine
"""

import httpx
from typing import List, Optional
from .models import RAGDocument, EvaluationResult
from .exceptions import (
    EnduranceError,
    RateLimitError,
    AuthenticationError,
    TimeoutError,
    ValidationError
)


class EnduranceClient:
    """
    Official Python client for Endurance RAI Engine
    
    Features:
    - Async/await support for non-blocking evaluations
    - Automatic retry logic with exponential backoff
    - Type hints for IDE autocomplete
    - Comprehensive error handling
    
    Example:
        >>> from endurance import EnduranceClient, RAGDocument
        >>> 
        >>> # Initialize client
        >>> client = EnduranceClient(
        ...     base_url="https://lamaq-endurance-backend-4-hods.hf.space",
        ...     api_key="optional-api-key"  # Optional: if backend requires auth
        ... )
        >>> 
        >>> # Prepare documents
        >>> docs = [
        ...     RAGDocument(
        ...         source="FOI_Act_2000.pdf",
        ...         content="Public authorities must respond within 20 working days...",
        ...         page=1,
        ...         similarity_score=0.95
        ...     )
        ... ]
        >>> 
        >>> # Evaluate response
        >>> result = await client.evaluate(
        ...     query="How long for FOI response?",
        ...     response="Public authorities must respond within 20 working days.",
        ...     service_id="uk_gov_chatbot",
        ...     rag_documents=docs
        ... )
        >>> 
        >>> print(f"Overall Score: {result.overall_score}/100")
        >>> print(f"Flagged: {result.flagged}")
        >>> print(f"Grounding: {result.dimensions.data_grounding}")
    """
    
    def __init__(
        self,
        base_url: str = "https://lamaq-endurance-backend-4-hods.hf.space",
        api_key: Optional[str] = None,
        timeout: float = 10.0,
        max_retries: int = 3
    ):
        """
        Initialize Endurance client
        
        Args:
            base_url: Endurance backend URL (default: HuggingFace Space)
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds (default: 10.0)
            max_retries: Maximum retry attempts for failed requests (default: 3)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
    
    async def evaluate(
        self,
        query: str,
        response: str,
        service_id: str,
        rag_documents: List[RAGDocument],
        metadata: Optional[dict] = None
    ) -> EvaluationResult:
        """
        Evaluate chatbot response for RAI compliance
        
        Args:
            query: User's question
            response: Chatbot's answer
            service_id: Identifier for your service (e.g., "uk_gov_chatbot")
            rag_documents: List of retrieved documents used as context
            metadata: Optional additional context (e.g., user_id, session_type)
        
        Returns:
            EvaluationResult with scores across 9 RAI dimensions
        
        Raises:
            ValidationError: If required fields are missing
            RateLimitError: If rate limit exceeded
            AuthenticationError: If API key invalid
            TimeoutError: If request times out
            EnduranceError: For other errors
        
        Example:
            >>> result = await client.evaluate(
            ...     query="What is the FOI response time?",
            ...     response="20 working days",
            ...     service_id="demo_chatbot",
            ...     rag_documents=[doc1, doc2]
            ... )
        """
        
        # Validation
        if not query or not response:
            raise ValidationError("Both 'query' and 'response' are required")
        
        if not service_id:
            raise ValidationError("'service_id' is required")
        
        # Prepare payload
        payload = {
            "query": query,
            "response": response,
            "service_id": service_id,
            "rag_documents": [doc.dict() for doc in rag_documents],
            "metadata": metadata or {}
        }
        
        # Prepare headers
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Make request with retry logic
        last_error = None
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as http_client:
                    http_response = await http_client.post(
                        f"{self.base_url}/v1/evaluate",
                        json=payload,
                        headers=headers
                    )
                    
                    # Handle specific status codes
                    if http_response.status_code == 429:
                        raise RateLimitError("Rate limit exceeded. Please try again later.")
                    
                    if http_response.status_code == 401:
                        raise AuthenticationError("Invalid API key or unauthorized access")
                    
                    if http_response.status_code == 400:
                        error_detail = http_response.json().get("detail", "Bad request")
                        raise ValidationError(f"Validation error: {error_detail}")
                    
                    http_response.raise_for_status()
                    
                    # Parse response
                    data = http_response.json()
                    return EvaluationResult(**data)
            
            except httpx.TimeoutException:
                last_error = TimeoutError(self.timeout)
                if attempt == self.max_retries - 1:
                    raise last_error
                # Exponential backoff: wait before retry
                await self._wait_exponential(attempt)
            
            except httpx.HTTPStatusError as e:
                if e.response.status_code in [429, 401, 400]:
                    # Don't retry these errors
                    raise
                last_error = EnduranceError(f"HTTP error: {e.response.status_code}")
                if attempt == self.max_retries - 1:
                    raise last_error
                await self._wait_exponential(attempt)
            
            except (RateLimitError, AuthenticationError, ValidationError):
                # Don't retry these errors
                raise
            
            except Exception as e:
                last_error = EnduranceError(f"Unexpected error: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise last_error
                await self._wait_exponential(attempt)
        
        # Should not reach here, but just in case
        raise last_error or EnduranceError("Request failed after retries")
    
    async def health_check(self) -> dict:
        """
        Check if Endurance service is available
        
        Returns:
            Health status dictionary with keys: status, version, uptime
        
        Example:
            >>> health = await client.health_check()
            >>> print(health["status"])  # "healthy" or "degraded"
        """
        try:
            async with httpx.AsyncClient(timeout=3.0) as http_client:
                response = await http_client.get(f"{self.base_url}/health")
                return response.json()
        except Exception as e:
            return {
                "status": "unavailable",
                "error": str(e)
            }
    
    async def get_service_stats(self, service_id: str) -> dict:
        """
        Get aggregate statistics for a service
        
        Args:
            service_id: Service identifier
        
        Returns:
            Statistics dictionary with session counts, average scores, etc.
        
        Example:
            >>> stats = await client.get_service_stats("uk_gov_chatbot")
            >>> print(f"Total sessions: {stats['total_sessions']}")
            >>> print(f"Average score: {stats['avg_score']}")
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as http_client:
                response = await http_client.get(
                    f"{self.base_url}/v1/services/{service_id}/stats"
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise EnduranceError(f"Service '{service_id}' not found")
            raise EnduranceError(f"Failed to fetch stats: {e.response.status_code}")
        except Exception as e:
            raise EnduranceError(f"Error fetching service stats: {str(e)}")
    
    @staticmethod
    async def _wait_exponential(attempt: int):
        """
        Exponential backoff wait between retries
        
        Args:
            attempt: Current attempt number (0-indexed)
        """
        import asyncio
        wait_time = min(2 ** attempt, 10)  # Max 10 seconds
        await asyncio.sleep(wait_time)
    
    def __repr__(self):
        return f"EnduranceClient(base_url='{self.base_url}')"
