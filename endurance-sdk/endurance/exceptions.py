"""
Custom exceptions for Endurance RAI SDK
"""


class EnduranceError(Exception):
    """Base exception for all Endurance SDK errors"""
    pass


class RateLimitError(EnduranceError):
    """Raised when API rate limit is exceeded"""
    def __init__(self, message="Rate limit exceeded. Please try again later."):
        super().__init__(message)


class AuthenticationError(EnduranceError):
    """Raised when authentication fails (invalid API key, etc.)"""
    def __init__(self, message="Authentication failed. Please check your API key."):
        super().__init__(message)


class TimeoutError(EnduranceError):
    """Raised when request times out"""
    def __init__(self, timeout_seconds):
        super().__init__(f"Request timed out after {timeout_seconds} seconds")
        self.timeout_seconds = timeout_seconds


class ValidationError(EnduranceError):
    """Raised when request validation fails"""
    pass
