"""LLM-related exceptions"""

from .base import CDOAIError


class LLMError(CDOAIError):
    """Base exception for LLM-related errors"""
    
    def __init__(self, message: str, provider: str = None):
        super().__init__(
            message,
            error_code="LLM_ERROR",
            details={"provider": provider} if provider else {}
        )
        self.provider = provider


class LLMConnectionError(LLMError):
    """Raised when LLM service connection fails"""
    
    def __init__(self, message: str, provider: str = None, endpoint: str = None):
        super().__init__(message, provider)
        self.error_code = "LLM_CONNECTION_ERROR"
        if endpoint:
            self.details["endpoint"] = endpoint


class LLMAuthenticationError(LLMError):
    """Raised when LLM service authentication fails"""
    
    def __init__(self, message: str, provider: str = None):
        super().__init__(message, provider)
        self.error_code = "LLM_AUTH_ERROR"


class LLMTimeoutError(LLMError):
    """Raised when LLM service request times out"""
    
    def __init__(self, message: str, provider: str = None, timeout_seconds: int = None):
        super().__init__(message, provider)
        self.error_code = "LLM_TIMEOUT_ERROR"
        if timeout_seconds:
            self.details["timeout_seconds"] = timeout_seconds


class LLMRateLimitError(LLMError):
    """Raised when LLM service rate limit is exceeded"""
    
    def __init__(self, message: str, provider: str = None, retry_after: int = None):
        super().__init__(message, provider)
        self.error_code = "LLM_RATE_LIMIT_ERROR"
        if retry_after:
            self.details["retry_after_seconds"] = retry_after
