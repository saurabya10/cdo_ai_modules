"""Intent analysis-related exceptions"""

from .base import CDOAIError


class IntentAnalysisError(CDOAIError):
    """Base exception for intent analysis errors"""
    
    def __init__(self, message: str, user_input: str = None):
        super().__init__(
            message,
            error_code="INTENT_ANALYSIS_ERROR",
            details={"user_input": user_input} if user_input else {}
        )
        self.user_input = user_input


class InvalidIntentCategoryError(IntentAnalysisError):
    """Raised when an invalid intent category is encountered"""
    
    def __init__(self, category: str, valid_categories: list = None):
        message = f"Invalid intent category: {category}"
        if valid_categories:
            message += f". Valid categories: {', '.join(valid_categories)}"
            
        super().__init__(message)
        self.error_code = "INVALID_INTENT_CATEGORY"
        self.details.update({
            "invalid_category": category,
            "valid_categories": valid_categories or []
        })


class IntentParsingError(IntentAnalysisError):
    """Raised when intent analysis response cannot be parsed"""
    
    def __init__(self, message: str, raw_response: str = None):
        super().__init__(message)
        self.error_code = "INTENT_PARSING_ERROR"
        if raw_response:
            self.details["raw_response"] = raw_response[:500]  # Truncate for logging


class LowConfidenceIntentError(IntentAnalysisError):
    """Raised when intent confidence is below threshold"""
    
    def __init__(self, confidence: float, threshold: float, category: str = None):
        message = f"Intent confidence {confidence:.2f} below threshold {threshold:.2f}"
        if category:
            message += f" for category '{category}'"
            
        super().__init__(message)
        self.error_code = "LOW_CONFIDENCE_INTENT"
        self.details.update({
            "confidence": confidence,
            "threshold": threshold,
            "category": category
        })
