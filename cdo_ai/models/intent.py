"""
Intent analysis data models with comprehensive type hints and validation
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import uuid


class IntentCategory(Enum):
    """Supported intent categories for user message classification"""
    GENERAL_CHAT = "general_chat"
    QUESTION_ANSWERING = "question_answering"
    TASK_REQUEST = "task_request"
    INFORMATION_SEEKING = "information_seeking"
    CLARIFICATION = "clarification"
    GREETING = "greeting"
    GOODBYE = "goodbye"
    
    @classmethod
    def get_descriptions(cls) -> Dict[str, str]:
        """Get human-readable descriptions for each intent category"""
        return {
            cls.GENERAL_CHAT.value: "Casual conversation and small talk",
            cls.QUESTION_ANSWERING.value: "Direct factual questions seeking specific answers",
            cls.TASK_REQUEST.value: "Requests to perform specific actions or tasks",
            cls.INFORMATION_SEEKING.value: "Looking for information on particular topics",
            cls.CLARIFICATION.value: "Asking for clarification or explanation of previous content",
            cls.GREETING.value: "Greetings, introductions, and conversation starters",
            cls.GOODBYE.value: "Farewells, conversation endings, and sign-offs"
        }
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """Get all intent category values as strings"""
        return [intent.value for intent in cls]


@dataclass
class IntentAnalysisResult:
    """
    Comprehensive result from intent analysis with validation and metadata
    """
    category: IntentCategory
    confidence: float
    reasoning: str
    entities: Dict[str, Any] = field(default_factory=dict)
    follow_up_needed: bool = False
    context_dependent: bool = False
    suggested_actions: List[str] = field(default_factory=list)
    processing_time_ms: Optional[float] = None
    model_version: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate the intent analysis result"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        
        if not self.reasoning.strip():
            raise ValueError("Reasoning cannot be empty")
    
    @property
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if the confidence is above the given threshold"""
        return self.confidence >= threshold
    
    @property 
    def is_ambiguous(self, threshold: float = 0.6) -> bool:
        """Check if the intent is ambiguous (low confidence)"""
        return self.confidence < threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for serialization"""
        return {
            "category": self.category.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "entities": self.entities,
            "follow_up_needed": self.follow_up_needed,
            "context_dependent": self.context_dependent,
            "suggested_actions": self.suggested_actions,
            "processing_time_ms": self.processing_time_ms,
            "model_version": self.model_version,
            "timestamp": self.timestamp.isoformat(),
            "metadata": {
                "is_high_confidence": self.is_high_confidence(),
                "is_ambiguous": self.is_ambiguous()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IntentAnalysisResult':
        """Create instance from dictionary"""
        return cls(
            category=IntentCategory(data["category"]),
            confidence=data["confidence"],
            reasoning=data["reasoning"],
            entities=data.get("entities", {}),
            follow_up_needed=data.get("follow_up_needed", False),
            context_dependent=data.get("context_dependent", False),
            suggested_actions=data.get("suggested_actions", []),
            processing_time_ms=data.get("processing_time_ms"),
            model_version=data.get("model_version"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now()
        )
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'IntentAnalysisResult':
        """Create instance from JSON string"""
        return cls.from_dict(json.loads(json_str))


@dataclass
class IntentRequest:
    """Request for intent analysis"""
    user_input: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    context_messages: Optional[List[Dict[str, str]]] = None
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the request"""
        if not self.user_input.strip():
            raise ValueError("User input cannot be empty")
        
        if len(self.user_input) > 10000:  # 10KB limit
            raise ValueError("User input exceeds maximum length of 10,000 characters")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "user_input": self.user_input,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "context_messages": self.context_messages,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class IntentResponse:
    """Response from intent analysis service"""
    success: bool
    request_id: str
    result: Optional[IntentAnalysisResult] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    processing_time_ms: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        response_dict = {
            "success": self.success,
            "request_id": self.request_id,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp.isoformat()
        }
        
        if self.success and self.result:
            response_dict["result"] = self.result.to_dict()
        else:
            response_dict["error"] = {
                "message": self.error_message,
                "code": self.error_code
            }
        
        return response_dict
    
    @classmethod
    def success_response(
        cls, 
        request_id: str, 
        result: IntentAnalysisResult,
        processing_time_ms: Optional[float] = None
    ) -> 'IntentResponse':
        """Create a successful response"""
        return cls(
            success=True,
            request_id=request_id,
            result=result,
            processing_time_ms=processing_time_ms
        )
    
    @classmethod
    def error_response(
        cls,
        request_id: str,
        error_message: str,
        error_code: Optional[str] = None,
        processing_time_ms: Optional[float] = None
    ) -> 'IntentResponse':
        """Create an error response"""
        return cls(
            success=False,
            request_id=request_id,
            error_message=error_message,
            error_code=error_code,
            processing_time_ms=processing_time_ms
        )
