"""
Storage service for conversation persistence using SQLite
"""

import sqlite3
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from ..config.settings import Settings
from ..models.conversation import (
    ConversationSession, 
    Message, 
    MessageType,
    ConversationStatus,
    ConversationSummary
)
from ..exceptions import (
    StorageError, 
    DatabaseError, 
    SessionNotFoundError,
    DatabaseConnectionError
)

logger = logging.getLogger(__name__)


class StorageService:
    """
    SQLite-based storage service for conversation persistence
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.db_path = Path(settings.database.path)
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"StorageService initialized with database: {self.db_path}")
    
    def _init_database(self):
        """Initialize SQLite database with required schema"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Enable WAL mode for better concurrent access
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA foreign_keys=ON")
                
                # Create sessions table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_sessions (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        user_id TEXT,
                        status TEXT NOT NULL DEFAULT 'active',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        metadata TEXT DEFAULT '{}'
                    )
                """)
                
                # Create messages table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_messages (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        message_type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        metadata TEXT DEFAULT '{}',
                        FOREIGN KEY (session_id) REFERENCES conversation_sessions (id) ON DELETE CASCADE
                    )
                """)
                
                # Create indexes for better performance
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sessions_user_status 
                    ON conversation_sessions(user_id, status, updated_at)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_messages_session_timestamp 
                    ON conversation_messages(session_id, timestamp)
                """)
                
                conn.commit()
                logger.debug("Database schema initialized successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}")
            raise DatabaseConnectionError(f"Failed to initialize database: {e}", str(self.db_path))
    
    async def create_session(
        self, 
        name: str = None, 
        user_id: str = None
    ) -> ConversationSession:
        """Create a new conversation session"""
        try:
            session = ConversationSession(
                name=name or f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                user_id=user_id
            )
            
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    INSERT INTO conversation_sessions 
                    (id, name, user_id, status, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session.id,
                    session.name,
                    session.user_id,
                    session.status.value,
                    session.created_at.isoformat(),
                    session.updated_at.isoformat(),
                    json.dumps(session.metadata)
                ))
                conn.commit()
            
            logger.info(f"Created session: {session.id} ({session.name})")
            return session
            
        except sqlite3.Error as e:
            logger.error(f"Failed to create session: {e}")
            raise DatabaseError(f"Failed to create session: {e}", operation="create", table="conversation_sessions")
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get conversation session by ID"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT id, name, user_id, status, created_at, updated_at, metadata
                    FROM conversation_sessions 
                    WHERE id = ? AND status != 'deleted'
                """, (session_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Get messages for this session
                messages = await self.get_messages(session_id)
                
                session = ConversationSession(
                    id=row['id'],
                    name=row['name'],
                    user_id=row['user_id'],
                    messages=messages,
                    status=ConversationStatus(row['status']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    metadata=json.loads(row['metadata'])
                )
                
                return session
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            raise DatabaseError(f"Failed to get session: {e}", operation="select", table="conversation_sessions")
    
    async def get_or_create_session(
        self, 
        session_id: str, 
        user_id: str = None
    ) -> ConversationSession:
        """Get existing session or create new one with specified ID"""
        session = await self.get_session(session_id)
        if session:
            return session
        
        # Create new session with the specified ID
        try:
            session = ConversationSession(
                id=session_id,
                name=f"Session {session_id[:8]}",
                user_id=user_id
            )
            
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    INSERT INTO conversation_sessions 
                    (id, name, user_id, status, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session.id,
                    session.name,
                    session.user_id,
                    session.status.value,
                    session.created_at.isoformat(),
                    session.updated_at.isoformat(),
                    json.dumps(session.metadata)
                ))
                conn.commit()
            
            logger.info(f"Created new session with specified ID: {session_id}")
            return session
            
        except sqlite3.Error as e:
            logger.error(f"Failed to create session with ID {session_id}: {e}")
            raise DatabaseError(f"Failed to create session: {e}", operation="create", table="conversation_sessions")
    
    async def list_sessions(self, user_id: str = None) -> List[ConversationSession]:
        """List conversation sessions"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                
                if user_id:
                    cursor = conn.execute("""
                        SELECT id, name, user_id, status, created_at, updated_at, metadata
                        FROM conversation_sessions 
                        WHERE user_id = ? AND status != 'deleted'
                        ORDER BY updated_at DESC
                    """, (user_id,))
                else:
                    cursor = conn.execute("""
                        SELECT id, name, user_id, status, created_at, updated_at, metadata
                        FROM conversation_sessions 
                        WHERE status != 'deleted'
                        ORDER BY updated_at DESC
                    """)
                
                sessions = []
                for row in cursor.fetchall():
                    # Don't load messages for list view (performance)
                    session = ConversationSession(
                        id=row['id'],
                        name=row['name'],
                        user_id=row['user_id'],
                        messages=[],
                        status=ConversationStatus(row['status']),
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at']),
                        metadata=json.loads(row['metadata'])
                    )
                    sessions.append(session)
                
                return sessions
                
        except sqlite3.Error as e:
            logger.error(f"Failed to list sessions: {e}")
            raise DatabaseError(f"Failed to list sessions: {e}", operation="select", table="conversation_sessions")
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete conversation session (soft delete)"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute("""
                    UPDATE conversation_sessions 
                    SET status = 'deleted', updated_at = ?
                    WHERE id = ? AND status != 'deleted'
                """, (datetime.now().isoformat(), session_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Deleted session: {session_id}")
                    return True
                else:
                    logger.warning(f"Session not found for deletion: {session_id}")
                    return False
                    
        except sqlite3.Error as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise DatabaseError(f"Failed to delete session: {e}", operation="update", table="conversation_sessions")
    
    async def add_message(self, session_id: str, message: Message) -> Message:
        """Add message to session"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Insert message
                conn.execute("""
                    INSERT INTO conversation_messages 
                    (id, session_id, message_type, content, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    message.id,
                    session_id,
                    message.message_type.value,
                    message.content,
                    message.timestamp.isoformat(),
                    json.dumps(message.metadata)
                ))
                
                # Update session timestamp
                conn.execute("""
                    UPDATE conversation_sessions 
                    SET updated_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), session_id))
                
                # Enforce message limit if configured
                if self.settings.database.max_messages > 0:
                    conn.execute("""
                        DELETE FROM conversation_messages 
                        WHERE session_id = ? 
                        AND id NOT IN (
                            SELECT id FROM conversation_messages 
                            WHERE session_id = ?
                            ORDER BY timestamp DESC 
                            LIMIT ?
                        )
                    """, (session_id, session_id, self.settings.database.max_messages))
                
                conn.commit()
            
            logger.debug(f"Added message to session {session_id}: {message.message_type.value}")
            return message
            
        except sqlite3.Error as e:
            logger.error(f"Failed to add message to session {session_id}: {e}")
            raise DatabaseError(f"Failed to add message: {e}", operation="insert", table="conversation_messages")
    
    async def get_messages(self, session_id: str, limit: int = None) -> List[Message]:
        """Get messages from session"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                
                if limit:
                    cursor = conn.execute("""
                        SELECT id, message_type, content, timestamp, metadata
                        FROM conversation_messages 
                        WHERE session_id = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (session_id, limit))
                else:
                    cursor = conn.execute("""
                        SELECT id, message_type, content, timestamp, metadata
                        FROM conversation_messages 
                        WHERE session_id = ?
                        ORDER BY timestamp ASC
                    """, (session_id,))
                
                messages = []
                rows = cursor.fetchall()
                
                # Reverse if we used LIMIT (to maintain chronological order)
                if limit:
                    rows = reversed(rows)
                
                for row in rows:
                    message = Message(
                        id=row['id'],
                        content=row['content'],
                        message_type=MessageType(row['message_type']),
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        metadata=json.loads(row['metadata'])
                    )
                    messages.append(message)
                
                return messages
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get messages for session {session_id}: {e}")
            raise DatabaseError(f"Failed to get messages: {e}", operation="select", table="conversation_messages")
    
    async def get_recent_messages(self, session_id: str, limit: int = 10) -> List[Message]:
        """Get recent messages from session in chronological order"""
        return await self.get_messages(session_id, limit)
    
    async def clear_session_messages(self, session_id: str) -> bool:
        """Clear all messages from session"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute("""
                    DELETE FROM conversation_messages 
                    WHERE session_id = ?
                """, (session_id,))
                
                # Update session timestamp
                conn.execute("""
                    UPDATE conversation_sessions 
                    SET updated_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), session_id))
                
                conn.commit()
                
                logger.info(f"Cleared {cursor.rowcount} messages from session {session_id}")
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            logger.error(f"Failed to clear messages for session {session_id}: {e}")
            raise DatabaseError(f"Failed to clear messages: {e}", operation="delete", table="conversation_messages")
    
    async def get_summary(self) -> ConversationSummary:
        """Get conversation analytics summary"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get session statistics
                session_cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_sessions,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_sessions,
                        COUNT(CASE WHEN status = 'archived' THEN 1 END) as archived_sessions,
                        MAX(updated_at) as recent_activity
                    FROM conversation_sessions 
                    WHERE status != 'deleted'
                """)
                
                session_stats = session_cursor.fetchone()
                
                # Get message statistics
                message_cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_messages,
                        COUNT(CASE WHEN message_type = 'user' THEN 1 END) as user_messages,
                        COUNT(CASE WHEN message_type = 'assistant' THEN 1 END) as assistant_messages
                    FROM conversation_messages cm
                    JOIN conversation_sessions cs ON cm.session_id = cs.id
                    WHERE cs.status != 'deleted'
                """)
                
                message_stats = message_cursor.fetchone()
                
                # Calculate averages
                total_sessions = session_stats['total_sessions'] or 0
                total_messages = message_stats['total_messages'] or 0
                
                avg_messages = total_messages / total_sessions if total_sessions > 0 else 0
                
                # Find most active session
                most_active_cursor = conn.execute("""
                    SELECT cs.id, COUNT(cm.id) as message_count
                    FROM conversation_sessions cs
                    LEFT JOIN conversation_messages cm ON cs.id = cm.session_id
                    WHERE cs.status != 'deleted'
                    GROUP BY cs.id
                    ORDER BY message_count DESC
                    LIMIT 1
                """)
                
                most_active_row = most_active_cursor.fetchone()
                most_active_session = most_active_row['id'] if most_active_row else None
                
                # Parse recent activity
                recent_activity = None
                if session_stats['recent_activity']:
                    try:
                        recent_activity = datetime.fromisoformat(session_stats['recent_activity'])
                    except ValueError:
                        pass
                
                return ConversationSummary(
                    total_sessions=total_sessions,
                    active_sessions=session_stats['active_sessions'] or 0,
                    archived_sessions=session_stats['archived_sessions'] or 0,
                    total_messages=total_messages,
                    total_user_messages=message_stats['user_messages'] or 0,
                    total_assistant_messages=message_stats['assistant_messages'] or 0,
                    avg_messages_per_session=avg_messages,
                    most_active_session_id=most_active_session,
                    recent_activity_timestamp=recent_activity
                )
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get summary: {e}")
            raise DatabaseError(f"Failed to get summary: {e}", operation="select")
    
    def close(self):
        """Close any open connections (cleanup)"""
        # SQLite connections are closed automatically with context managers
        logger.info("StorageService closed")
