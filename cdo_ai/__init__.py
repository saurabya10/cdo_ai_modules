"""
CDO AI Modules - Production-Ready Intent Analysis System

A modular, scalable conversational AI system with intent analysis,
persistent conversation history, and enterprise LLM integration.
"""

__version__ = "1.0.0"
__author__ = "CDO Team"
__email__ = "cdo-team@company.com"

from .services.intent_service import IntentAnalysisService
from .models.intent import IntentCategory, IntentAnalysisResult
from .models.conversation import ConversationSession, Message, MessageType

__all__ = [
    "IntentAnalysisService",
    "IntentCategory", 
    "IntentAnalysisResult",
    "ConversationSession",
    "Message",
    "MessageType"
]
