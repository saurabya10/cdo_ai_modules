"""Base exceptions for CDO AI Modules"""

from typing import Optional, Dict, Any


class CDOAIError(Exception):
    """Base exception for all CDO AI errors"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format"""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "type": self.__class__.__name__
        }
