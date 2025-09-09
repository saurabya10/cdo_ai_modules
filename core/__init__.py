# -*- coding: utf-8 -*-
"""
Core Intent Analysis System with SQLite Conversation Persistence

This package provides production-grade components for:
- Intent analysis using Azure OpenAI
- Persistent SQLite conversation history
- Session-based conversation management
- Automatic conversation tracking
"""

from .chat_history_manager import ChatHistoryManager, SQLiteChatHistoryBackend
from .intent_analyzer import IntentAnalyzer, ConversationalIntentAnalyzer, IntentCategory, IntentAnalysisResult
from .conversation_manager import ConversationManager, create_conversation_manager

__version__ = "1.0.0"
__author__ = "Intent Analysis System"

__all__ = [
    # Chat History Components
    "ChatHistoryManager",
    "SQLiteChatHistoryBackend",
    
    # Intent Analysis Components
    "IntentAnalyzer",
    "ConversationalIntentAnalyzer",
    "IntentCategory",
    "IntentAnalysisResult",
    
    # Conversation Management
    "ConversationManager",
    "create_conversation_manager",
]

# Package metadata
PACKAGE_INFO = {
    "name": "core",
    "version": __version__,
    "description": "Intent Analysis System with SQLite Conversation Persistence",
    "features": [
        "Intent Classification",
        "SQLite Conversation History",
        "Session Management",
        "Automatic Context Tracking",
        "Production-ready Architecture"
    ],
    "dependencies": [
        "langchain",
        "langchain-openai",
        "sqlite3"
    ]
}
