"""Helper utility functions"""

import re
import uuid
from datetime import datetime
from typing import Optional, Dict, Any


def generate_session_name(prefix: str = "Session") -> str:
    """Generate a user-friendly session name"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"{prefix} {timestamp}"


def generate_unique_id() -> str:
    """Generate a unique identifier"""
    return str(uuid.uuid4())


def sanitize_input(text: str) -> str:
    """Sanitize user input by removing potentially harmful characters"""
    if not text:
        return ""
    
    # Remove control characters except newlines and tabs
    sanitized = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    # Normalize whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    return sanitized


def extract_keywords(text: str, min_length: int = 3) -> list[str]:
    """Extract keywords from text"""
    # Simple keyword extraction
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Remove common stop words
    stop_words = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
        'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
        'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy',
        'did', 'she', 'use', 'her', 'way', 'who', 'oil', 'sit', 'set', 'run'
    }
    
    keywords = [word for word in words if len(word) >= min_length and word not in stop_words]
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(keywords))


def merge_dictionaries(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries, with later ones taking precedence"""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dictionary with dot notation support"""
    try:
        keys = key.split('.')
        value = data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    except (AttributeError, TypeError, KeyError):
        return default


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    """Split text into chunks with optional overlap"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at word boundary
        if end < len(text):
            # Find the last space within the chunk
            space_pos = text.rfind(' ', start, end)
            if space_pos > start:
                end = space_pos
        
        chunks.append(text[start:end])
        start = max(start + 1, end - overlap)  # Ensure progress even with large overlap
    
    return chunks


def is_question(text: str) -> bool:
    """Check if text appears to be a question"""
    text = text.strip()
    
    # Check for question mark
    if text.endswith('?'):
        return True
    
    # Check for question words at the beginning
    question_words = ['what', 'who', 'where', 'when', 'why', 'how', 'which', 'whose', 'whom']
    first_word = text.split()[0].lower() if text.split() else ''
    
    return first_word in question_words


def estimate_reading_time(text: str, words_per_minute: int = 200) -> float:
    """Estimate reading time in minutes"""
    word_count = len(text.split())
    return word_count / words_per_minute


def format_json_pretty(data: Dict[str, Any], indent: int = 2) -> str:
    """Format dictionary as pretty JSON string"""
    import json
    return json.dumps(data, indent=indent, default=str, ensure_ascii=False)
