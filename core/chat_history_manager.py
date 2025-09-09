# -*- coding: utf-8 -*-
"""
Generic Chat History Manager with SQLite backend
Provides automatic conversation tracking and context management
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from functools import wraps
import logging

from langchain.schema import HumanMessage, AIMessage, BaseMessage
from langchain.memory import ConversationBufferMemory

# Import compatibility handling
try:
    from langchain.memory.chat_message_histories.base import BaseChatMessageHistory
except ImportError:
    try:
        from langchain_core.chat_history import BaseChatMessageHistory
    except ImportError:
        # Fallback for older versions or missing LangChain
        class BaseChatMessageHistory:
            def add_message(self, message): pass
            def clear(self): pass
            @property
            def messages(self): return []

logger = logging.getLogger(__name__)


class SQLiteChatHistoryBackend(BaseChatMessageHistory):
    """
    Production-grade SQLite-based chat message history with automatic management.
    
    Features:
    - ACID compliant SQLite storage
    - Configurable message limits with automatic cleanup
    - Session-based conversation isolation
    - Automatic database initialization and migration
    - Thread-safe operations
    """
    
    def __init__(self, session_id: str = "default", db_path: str = "conversations.db", max_messages: int = 100):
        """
        Initialize SQLite chat history backend.
        
        Args:
            session_id: Unique identifier for conversation session
            db_path: Path to SQLite database file
            max_messages: Maximum messages per session (0 = unlimited)
        """
        self.session_id = session_id
        self.db_path = Path(db_path)
        self.max_messages = max_messages
        
        # Ensure database is properly initialized
        self._init_database()
        logger.info(f"Initialized SQLite chat history for session '{session_id}' at {db_path}")
    
    def _init_database(self):
        """Initialize SQLite database with required schema"""
        # Create directory if needed
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(str(self.db_path)) as conn:
            # Enable WAL mode for better concurrent access
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            
            # Create messages table with proper indexing
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    additional_kwargs TEXT DEFAULT '{}',
                    timestamp TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create optimized indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_created 
                ON chat_messages(session_id, created_at)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_type 
                ON chat_messages(session_id, message_type)
            """)
            
            conn.commit()
    
    def _message_to_dict(self, message: BaseMessage) -> Dict[str, Any]:
        """Convert LangChain message to storage format"""
        return {
            "type": message.__class__.__name__,
            "content": message.content,
            "additional_kwargs": json.dumps(getattr(message, 'additional_kwargs', {})),
            "timestamp": datetime.now().isoformat()
        }
    
    def _dict_to_message(self, msg_dict: Dict[str, Any]) -> BaseMessage:
        """Convert storage format back to LangChain message"""
        msg_type = msg_dict["message_type"]
        content = msg_dict["content"]
        additional_kwargs = json.loads(msg_dict.get("additional_kwargs", "{}"))
        
        if msg_type == "HumanMessage":
            return HumanMessage(content=content, additional_kwargs=additional_kwargs)
        elif msg_type == "AIMessage":
            return AIMessage(content=content, additional_kwargs=additional_kwargs)
        else:
            # Fallback to AIMessage for unknown types
            return AIMessage(content=content, additional_kwargs=additional_kwargs)
    
    def add_message(self, message: BaseMessage):
        """Add message to database with automatic cleanup"""
        msg_dict = self._message_to_dict(message)
        
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                INSERT INTO chat_messages 
                (session_id, message_type, content, additional_kwargs, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                self.session_id,
                msg_dict["type"],
                msg_dict["content"],
                msg_dict["additional_kwargs"],
                msg_dict["timestamp"]
            ))
            
            # Enforce message limit if configured
            if self.max_messages > 0:
                conn.execute("""
                    DELETE FROM chat_messages 
                    WHERE session_id = ? 
                    AND id NOT IN (
                        SELECT id FROM chat_messages 
                        WHERE session_id = ?
                        ORDER BY created_at DESC 
                        LIMIT ?
                    )
                """, (self.session_id, self.session_id, self.max_messages))
            
            conn.commit()
    
    @property
    def messages(self) -> List[BaseMessage]:
        """Retrieve all messages for current session"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT message_type, content, additional_kwargs
                FROM chat_messages 
                WHERE session_id = ?
                ORDER BY created_at ASC
            """, (self.session_id,))
            
            return [self._dict_to_message(dict(row)) for row in cursor.fetchall()]
    
    def clear(self):
        """Clear all messages for current session"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (self.session_id,))
            conn.commit()
        logger.info(f"Cleared conversation history for session '{self.session_id}'")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics for current session"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_messages,
                    MIN(created_at) as first_message,
                    MAX(created_at) as last_message,
                    COUNT(CASE WHEN message_type = 'HumanMessage' THEN 1 END) as user_messages,
                    COUNT(CASE WHEN message_type = 'AIMessage' THEN 1 END) as ai_messages
                FROM chat_messages 
                WHERE session_id = ?
            """, (self.session_id,))
            
            row = cursor.fetchone()
            return {
                "session_id": self.session_id,
                "total_messages": row[0] if row else 0,
                "first_message": row[1] if row and row[1] else None,
                "last_message": row[2] if row and row[2] else None,
                "user_messages": row[3] if row else 0,
                "ai_messages": row[4] if row else 0,
                "db_path": str(self.db_path),
                "max_messages": self.max_messages
            }
    
    @classmethod
    def list_sessions(cls, db_path: str = "conversations.db") -> List[str]:
        """List all available session IDs in database"""
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("SELECT DISTINCT session_id FROM chat_messages ORDER BY session_id")
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error:
            return []
    
    @classmethod
    def delete_session(cls, session_id: str, db_path: str = "conversations.db"):
        """Delete all messages for a specific session"""
        with sqlite3.connect(db_path) as conn:
            conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
            conn.commit()
        logger.info(f"Deleted session '{session_id}' from {db_path}")


class ChatHistoryManager:
    """
    Production-grade conversation manager with automatic tracking.
    
    Features:
    - Automatic conversation context injection
    - Multiple session management
    - Configuration-driven setup
    - Context decorators for seamless integration
    """
    
    def __init__(self, config_path: str = "chat_config.json"):
        """Initialize chat history manager with configuration"""
        self.config = self._load_config(config_path)
        self.active_sessions: Dict[str, SQLiteChatHistoryBackend] = {}
        self.current_session_id = self.config.get("default_session", "main_session")
        
        # Initialize default session
        self._get_or_create_session(self.current_session_id)
        logger.info(f"ChatHistoryManager initialized with session '{self.current_session_id}'")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration with fallback defaults"""
        default_config = {
            "db_path": "conversations.db",
            "max_messages": 100,
            "default_session": "main_session",
            "auto_backup": True,
            "session_timeout_hours": 24
        }
        
        try:
            if Path(config_path).exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return {**default_config, **config}
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return default_config
    
    def _get_or_create_session(self, session_id: str) -> SQLiteChatHistoryBackend:
        """Get existing session or create new one"""
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = SQLiteChatHistoryBackend(
                session_id=session_id,
                db_path=self.config["db_path"],
                max_messages=self.config["max_messages"]
            )
        return self.active_sessions[session_id]
    
    def get_current_session(self) -> SQLiteChatHistoryBackend:
        """Get current active session"""
        return self._get_or_create_session(self.current_session_id)
    
    def switch_session(self, session_id: str):
        """Switch to different session"""
        old_session = self.current_session_id
        self.current_session_id = session_id
        self._get_or_create_session(session_id)
        logger.info(f"Switched from session '{old_session}' to '{session_id}'")
    
    def get_conversation_context(self, session_id: Optional[str] = None) -> List[BaseMessage]:
        """Get conversation context for LLM"""
        session_id = session_id or self.current_session_id
        session = self._get_or_create_session(session_id)
        return session.messages
    
    def add_exchange(self, user_message: str, ai_response: str, session_id: Optional[str] = None):
        """Add user-AI exchange to history"""
        session_id = session_id or self.current_session_id
        session = self._get_or_create_session(session_id)
        
        session.add_message(HumanMessage(content=user_message))
        session.add_message(AIMessage(content=ai_response))
    
    def auto_track_conversation(self, func: Callable) -> Callable:
        """Decorator for automatic conversation tracking"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user input and session from args/kwargs
            user_input = kwargs.get('user_input') or kwargs.get('prompt') or (args[1] if len(args) > 1 else None)
            session_id = kwargs.get('session_id', self.current_session_id)
            
            if not user_input:
                return await func(*args, **kwargs)
            
            # Call the original function
            result = await func(*args, **kwargs)
            
            # Extract AI response from result
            if isinstance(result, dict) and result.get('success') and 'response' in result:
                ai_response = result['response']
                self.add_exchange(user_input, ai_response, session_id)
                logger.debug(f"Auto-tracked conversation in session '{session_id}'")
            
            return result
        
        return wrapper
    
    def get_session_info(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed session information"""
        session_id = session_id or self.current_session_id
        session = self._get_or_create_session(session_id)
        return session.get_session_stats()
    
    def list_sessions(self) -> List[str]:
        """List all available sessions"""
        return SQLiteChatHistoryBackend.list_sessions(self.config["db_path"])
    
    def delete_session(self, session_id: str):
        """Delete a session and its history"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        SQLiteChatHistoryBackend.delete_session(session_id, self.config["db_path"])
        
        # Switch to default session if current session was deleted
        if session_id == self.current_session_id:
            self.current_session_id = self.config["default_session"]
    
    def clear_current_session(self):
        """Clear current session history"""
        session = self.get_current_session()
        session.clear()
