"""Custom exceptions for CDO AI Modules"""

from .base import CDOAIError
from .config import ConfigurationError, MissingConfigurationError, InvalidConfigurationError
from .llm import LLMError, LLMConnectionError, LLMAuthenticationError, LLMTimeoutError, LLMRateLimitError
from .storage import StorageError, DatabaseError, SessionNotFoundError, DatabaseConnectionError
from .intent import IntentAnalysisError, IntentParsingError

__all__ = [
    "CDOAIError",
    "ConfigurationError",
    "MissingConfigurationError", 
    "InvalidConfigurationError",
    "LLMError",
    "LLMConnectionError",
    "LLMAuthenticationError",
    "LLMTimeoutError",
    "LLMRateLimitError",
    "StorageError",
    "DatabaseError",
    "SessionNotFoundError",
    "DatabaseConnectionError",
    "IntentAnalysisError",
    "IntentParsingError"
]
