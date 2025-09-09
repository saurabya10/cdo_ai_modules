"""Formatting utilities"""

from datetime import datetime, timedelta
from typing import Optional


def format_timestamp(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string"""
    return timestamp.strftime(format_str)


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"


def format_relative_time(timestamp: datetime) -> str:
    """Format timestamp relative to now (e.g., '2 hours ago')"""
    now = datetime.now()
    diff = now - timestamp
    
    if diff.total_seconds() < 60:
        return "just now"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human-readable string"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def format_percentage(value: float, decimal_places: int = 1) -> str:
    """Format decimal as percentage"""
    return f"{value * 100:.{decimal_places}f}%"


def format_confidence_score(confidence: float) -> str:
    """Format confidence score with appropriate color/indicator"""
    if confidence >= 0.8:
        indicator = "●"  # High confidence
    elif confidence >= 0.6:
        indicator = "◐"  # Medium confidence  
    else:
        indicator = "○"  # Low confidence
    
    return f"{indicator} {confidence:.2f}"


def format_intent_category(category: str) -> str:
    """Format intent category for display"""
    return category.replace("_", " ").title()
