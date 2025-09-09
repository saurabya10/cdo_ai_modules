"""
Conversation and message data models with comprehensive validation
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json


class MessageType(Enum):
    """Types of messages in a conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatus(Enum):
    """Status of conversation sessions"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass
class Message:
    """Individual message in a conversation with comprehensive metadata"""
    content: str
    message_type: MessageType
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate message content"""
        if not self.content.strip():
            raise ValueError("Message content cannot be empty")
        
        if len(self.content) > 50000:  # 50KB limit
            raise ValueError("Message content exceeds maximum length")
    
    @property
    def age_minutes(self) -> float:
        """Get message age in minutes"""
        return (datetime.now() - self.timestamp).total_seconds() / 60
    
    @property
    def is_recent(self, minutes: int = 30) -> bool:
        """Check if message is recent (within specified minutes)"""
        return self.age_minutes <= minutes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "id": self.id,
            "content": self.content,
            "message_type": self.message_type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "age_minutes": self.age_minutes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create instance from dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            content=data["content"],
            message_type=MessageType(data["message_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )
    
    def to_langchain_format(self):
        """Convert to LangChain message format for LLM integration"""
        from langchain.schema import HumanMessage, AIMessage, SystemMessage
        
        message_classes = {
            MessageType.USER: HumanMessage,
            MessageType.ASSISTANT: AIMessage,
            MessageType.SYSTEM: SystemMessage
        }
        
        message_class = message_classes.get(self.message_type, HumanMessage)
        return message_class(content=self.content, additional_kwargs=self.metadata)
    
    @classmethod
    def create_user_message(cls, content: str, **metadata) -> 'Message':
        """Create a user message"""
        return cls(content=content, message_type=MessageType.USER, metadata=metadata)
    
    @classmethod
    def create_assistant_message(cls, content: str, **metadata) -> 'Message':
        """Create an assistant message"""
        return cls(content=content, message_type=MessageType.ASSISTANT, metadata=metadata)
    
    @classmethod
    def create_system_message(cls, content: str, **metadata) -> 'Message':
        """Create a system message"""
        return cls(content=content, message_type=MessageType.SYSTEM, metadata=metadata)


@dataclass
class ConversationSession:
    """
    Conversation session containing multiple messages with comprehensive management
    """
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    messages: List[Message] = field(default_factory=list)
    status: ConversationStatus = ConversationStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and initialize session"""
        if not self.name.strip():
            self.name = f"Session {self.id[:8]}"
        
        # Ensure updated_at is not before created_at
        if self.updated_at < self.created_at:
            self.updated_at = self.created_at
    
    @property
    def message_count(self) -> int:
        """Get total number of messages"""
        return len(self.messages)
    
    @property
    def user_message_count(self) -> int:
        """Get number of user messages"""
        return sum(1 for msg in self.messages if msg.message_type == MessageType.USER)
    
    @property
    def assistant_message_count(self) -> int:
        """Get number of assistant messages"""
        return sum(1 for msg in self.messages if msg.message_type == MessageType.ASSISTANT)
    
    @property
    def duration_hours(self) -> float:
        """Get session duration in hours"""
        return (self.updated_at - self.created_at).total_seconds() / 3600
    
    @property
    def is_active(self) -> bool:
        """Check if session is active"""
        return self.status == ConversationStatus.ACTIVE
    
    @property
    def last_activity(self) -> Optional[datetime]:
        """Get timestamp of last message"""
        if self.messages:
            return max(msg.timestamp for msg in self.messages)
        return None
    
    @property
    def is_stale(self, hours: int = 24) -> bool:
        """Check if session is stale (no activity for specified hours)"""
        if not self.last_activity:
            return (datetime.now() - self.created_at).total_seconds() / 3600 > hours
        return (datetime.now() - self.last_activity).total_seconds() / 3600 > hours
    
    def add_message(self, message: Message) -> None:
        """Add a message to the session"""
        self.messages.append(message)
        self.updated_at = datetime.now()
        
        # Update metadata
        self.metadata["last_message_type"] = message.message_type.value
        self.metadata["total_messages"] = len(self.messages)
    
    def add_user_message(self, content: str, **metadata) -> Message:
        """Add a user message and return it"""
        message = Message.create_user_message(content, **metadata)
        self.add_message(message)
        return message
    
    def add_assistant_message(self, content: str, **metadata) -> Message:
        """Add an assistant message and return it"""
        message = Message.create_assistant_message(content, **metadata)
        self.add_message(message)
        return message
    
    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Get recent messages (most recent first)"""
        if limit <= 0:
            return list(reversed(self.messages))
        return list(reversed(self.messages[-limit:]))
    
    def get_messages_by_type(self, message_type: MessageType) -> List[Message]:
        """Get all messages of a specific type"""
        return [msg for msg in self.messages if msg.message_type == message_type]
    
    def get_context_messages(self, limit: int = 20) -> List[Message]:
        """Get messages for LLM context (chronological order)"""
        if limit <= 0:
            return self.messages
        return self.messages[-limit:]
    
    def clear_messages(self) -> None:
        """Clear all messages from the session"""
        self.messages.clear()
        self.updated_at = datetime.now()
        self.metadata["total_messages"] = 0
    
    def archive(self) -> None:
        """Archive the session"""
        self.status = ConversationStatus.ARCHIVED
        self.updated_at = datetime.now()
        self.metadata["archived_at"] = datetime.now().isoformat()
    
    def reactivate(self) -> None:
        """Reactivate an archived session"""
        self.status = ConversationStatus.ACTIVE
        self.updated_at = datetime.now()
        if "archived_at" in self.metadata:
            del self.metadata["archived_at"]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive session statistics"""
        return {
            "session_id": self.id,
            "name": self.name,
            "user_id": self.user_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "duration_hours": round(self.duration_hours, 2),
            "total_messages": self.message_count,
            "user_messages": self.user_message_count,
            "assistant_messages": self.assistant_message_count,
            "is_stale": self.is_stale(),
            "is_active": self.is_active,
            "metadata": self.metadata
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "id": self.id,
            "name": self.name,
            "user_id": self.user_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": [msg.to_dict() for msg in self.messages],
            "metadata": self.metadata,
            "statistics": self.get_statistics()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationSession':
        """Create instance from dictionary"""
        messages = [Message.from_dict(msg_data) for msg_data in data.get("messages", [])]
        
        return cls(
            id=data["id"],
            name=data["name"],
            user_id=data.get("user_id"),
            messages=messages,
            status=ConversationStatus(data.get("status", "active")),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {})
        )


@dataclass
class ConversationSummary:
    """Summary statistics for conversation analysis"""
    total_sessions: int = 0
    active_sessions: int = 0
    archived_sessions: int = 0
    total_messages: int = 0
    total_user_messages: int = 0
    total_assistant_messages: int = 0
    avg_messages_per_session: float = 0.0
    avg_session_duration_hours: float = 0.0
    most_active_session_id: Optional[str] = None
    recent_activity_timestamp: Optional[datetime] = None
    stale_sessions: int = 0
    
    @property
    def session_activity_rate(self) -> float:
        """Calculate session activity rate (active / total)"""
        if self.total_sessions == 0:
            return 0.0
        return self.active_sessions / self.total_sessions
    
    @property
    def message_distribution(self) -> Dict[str, float]:
        """Get message distribution percentages"""
        if self.total_messages == 0:
            return {"user": 0.0, "assistant": 0.0}
        
        return {
            "user": (self.total_user_messages / self.total_messages) * 100,
            "assistant": (self.total_assistant_messages / self.total_messages) * 100
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "total_sessions": self.total_sessions,
            "active_sessions": self.active_sessions,
            "archived_sessions": self.archived_sessions,
            "stale_sessions": self.stale_sessions,
            "total_messages": self.total_messages,
            "total_user_messages": self.total_user_messages,
            "total_assistant_messages": self.total_assistant_messages,
            "averages": {
                "messages_per_session": round(self.avg_messages_per_session, 2),
                "session_duration_hours": round(self.avg_session_duration_hours, 2)
            },
            "activity": {
                "most_active_session_id": self.most_active_session_id,
                "recent_activity": self.recent_activity_timestamp.isoformat() if self.recent_activity_timestamp else None,
                "session_activity_rate": round(self.session_activity_rate, 2)
            },
            "message_distribution": {
                "user_percentage": round(self.message_distribution["user"], 1),
                "assistant_percentage": round(self.message_distribution["assistant"], 1)
            }
        }
