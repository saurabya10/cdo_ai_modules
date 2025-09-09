"""
Chat history management with SQLite storage
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ChatHistory:
    """Manages chat history with SQLite storage"""
    
    def __init__(self, db_path: str = "chat_history.db", max_conversations: int = 25):
        self.db_path = Path(db_path)
        self.max_conversations = max_conversations
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database"""
        try:
            # Ensure directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        user_input TEXT NOT NULL,
                        intent_action TEXT NOT NULL,
                        intent_confidence REAL NOT NULL,
                        intent_reasoning TEXT NOT NULL,
                        response TEXT,
                        created_at TEXT NOT NULL
                    )
                """)
                
                # Create index for better performance
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_conversations_timestamp 
                    ON conversations(timestamp)
                """)
                
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def add_conversation(
        self, 
        user_input: str, 
        intent_action: str, 
        intent_confidence: float, 
        intent_reasoning: str,
        response: str = ""
    ) -> int:
        """Add a conversation to history"""
        try:
            timestamp = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    INSERT INTO conversations 
                    (timestamp, user_input, intent_action, intent_confidence, intent_reasoning, response, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (timestamp, user_input, intent_action, intent_confidence, intent_reasoning, response, timestamp))
                
                conversation_id = cursor.lastrowid
                
                # Cleanup old conversations if we exceed the limit
                self._cleanup_old_conversations(conn)
                
                conn.commit()
                logger.debug(f"Added conversation {conversation_id}")
                return conversation_id
                
        except Exception as e:
            logger.error(f"Failed to add conversation: {e}")
            raise
    
    def _cleanup_old_conversations(self, conn: sqlite3.Connection):
        """Remove old conversations if we exceed the limit"""
        try:
            # Count current conversations
            cursor = conn.execute("SELECT COUNT(*) FROM conversations")
            count = cursor.fetchone()[0]
            
            if count > self.max_conversations:
                # Delete oldest conversations
                conversations_to_delete = count - self.max_conversations
                conn.execute("""
                    DELETE FROM conversations 
                    WHERE id IN (
                        SELECT id FROM conversations 
                        ORDER BY timestamp ASC 
                        LIMIT ?
                    )
                """, (conversations_to_delete,))
                
                logger.debug(f"Cleaned up {conversations_to_delete} old conversations")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old conversations: {e}")
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversations"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM conversations 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
                
                conversations = []
                for row in cursor.fetchall():
                    conversations.append({
                        'id': row['id'],
                        'timestamp': row['timestamp'],
                        'user_input': row['user_input'],
                        'intent_action': row['intent_action'],
                        'intent_confidence': row['intent_confidence'],
                        'intent_reasoning': row['intent_reasoning'],
                        'response': row['response'],
                        'created_at': row['created_at']
                    })
                
                return conversations
                
        except Exception as e:
            logger.error(f"Failed to get recent conversations: {e}")
            return []
    
    def get_conversation_count(self) -> int:
        """Get total number of conversations"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM conversations")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get conversation count: {e}")
            return 0
    
    def clear_history(self):
        """Clear all conversation history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM conversations")
                conn.commit()
                logger.info("Cleared all conversation history")
        except Exception as e:
            logger.error(f"Failed to clear history: {e}")
            raise
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary statistics of conversations"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get basic stats
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total,
                        AVG(intent_confidence) as avg_confidence,
                        MIN(timestamp) as oldest,
                        MAX(timestamp) as newest
                    FROM conversations
                """)
                
                stats = cursor.fetchone()
                
                # Get intent distribution
                cursor = conn.execute("""
                    SELECT intent_action, COUNT(*) as count
                    FROM conversations
                    GROUP BY intent_action
                    ORDER BY count DESC
                """)
                
                intent_distribution = {row[0]: row[1] for row in cursor.fetchall()}
                
                return {
                    'total_conversations': stats[0],
                    'average_confidence': round(stats[1] or 0, 3),
                    'oldest_conversation': stats[2],
                    'newest_conversation': stats[3],
                    'intent_distribution': intent_distribution,
                    'max_conversations_limit': self.max_conversations
                }
                
        except Exception as e:
            logger.error(f"Failed to get conversation summary: {e}")
            return {}
