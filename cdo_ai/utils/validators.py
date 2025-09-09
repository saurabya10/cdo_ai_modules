"""Input validation utilities"""

import re
from typing import Optional


def validate_user_input(user_input: str) -> tuple[bool, Optional[str]]:
    """
    Validate user input for processing
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not user_input:
        return False, "Input cannot be empty"
    
    if not user_input.strip():
        return False, "Input cannot be only whitespace"
    
    if len(user_input) > 10000:  # 10KB limit
        return False, "Input exceeds maximum length of 10,000 characters"
    
    # Check for potentially harmful content (basic check)
    if any(char in user_input for char in ['\x00', '\x01', '\x02']):
        return False, "Input contains invalid control characters"
    
    return True, None


def validate_session_id(session_id: str) -> tuple[bool, Optional[str]]:
    """
    Validate session ID format
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not session_id:
        return False, "Session ID cannot be empty"
    
    if len(session_id) > 100:
        return False, "Session ID exceeds maximum length of 100 characters"
    
    # UUID format or alphanumeric with hyphens/underscores
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    alphanumeric_pattern = r'^[a-zA-Z0-9_-]+$'
    
    if (re.match(uuid_pattern, session_id, re.IGNORECASE) or 
        re.match(alphanumeric_pattern, session_id)):
        return True, None
    
    return False, "Session ID must be UUID format or alphanumeric with hyphens/underscores"


def validate_email(email: str) -> tuple[bool, Optional[str]]:
    """
    Validate email format
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not email:
        return False, "Email cannot be empty"
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(email_pattern, email):
        return True, None
    
    return False, "Invalid email format"


def validate_confidence_score(confidence: float) -> tuple[bool, Optional[str]]:
    """
    Validate confidence score range
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(confidence, (int, float)):
        return False, "Confidence must be a number"
    
    if not 0.0 <= confidence <= 1.0:
        return False, "Confidence must be between 0.0 and 1.0"
    
    return True, None
