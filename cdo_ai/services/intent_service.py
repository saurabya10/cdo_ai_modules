"""
Main Intent Analysis Service - Orchestrates all components
"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from ..config.settings import Settings
from ..models.intent import IntentRequest, IntentResponse, IntentAnalysisResult
from ..models.conversation import Message, MessageType, ConversationSession
from ..services.llm_service import LLMService
from ..services.storage_service import StorageService
from ..exceptions import CDOAIError, IntentAnalysisError

logger = logging.getLogger(__name__)


class IntentAnalysisService:
    """
    Main service orchestrating intent analysis, conversation management, and storage
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm_service = LLMService(settings)
        self.storage_service = StorageService(settings)
        
        logger.info("IntentAnalysisService initialized successfully")
    
    async def process_user_input(
        self,
        user_input: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        include_response: bool = True
    ) -> Dict[str, Any]:
        """
        Process user input with intent analysis and optional response generation
        
        Args:
            user_input: User's message
            session_id: Conversation session ID (creates new if not provided)
            user_id: User identifier
            include_response: Whether to generate AI response
            
        Returns:
            Dictionary with processing results
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # Validate input
            if not user_input or not user_input.strip():
                return {
                    "success": False,
                    "error": "Empty input provided",
                    "error_code": "EMPTY_INPUT",
                    "request_id": request_id,
                    "processing_time_ms": (time.time() - start_time) * 1000
                }
            
            user_input = user_input.strip()
            
            # Get or create session
            if not session_id:
                session = await self.storage_service.create_session(
                    name=f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    user_id=user_id
                )
                session_id = session.id
            else:
                session = await self.storage_service.get_or_create_session(session_id, user_id)
            
            # Get conversation context
            context_messages = await self.storage_service.get_recent_messages(
                session_id, 
                limit=20
            )
            
            # Analyze intent
            intent_result = await self.llm_service.analyze_intent(user_input, context_messages)
            
            # Add user message to conversation
            user_message = await self.storage_service.add_message(
                session_id,
                Message.create_user_message(
                    user_input,
                    request_id=request_id,
                    intent_analysis=intent_result.to_dict()
                )
            )
            
            result = {
                "success": True,
                "session_id": session_id,
                "intent_analysis": intent_result.to_dict(),
                "user_message_id": user_message.id,
                "request_id": request_id,
                "processing_time_ms": (time.time() - start_time) * 1000
            }
            
            # Generate response if requested
            if include_response:
                try:
                    response_content = await self._generate_contextual_response(
                        user_input,
                        intent_result,
                        context_messages
                    )
                    
                    # Add assistant message to conversation
                    assistant_message = await self.storage_service.add_message(
                        session_id,
                        Message.create_assistant_message(
                            response_content,
                            request_id=request_id,
                            intent_category=intent_result.category.value,
                            confidence=intent_result.confidence
                        )
                    )
                    
                    result.update({
                        "response": response_content,
                        "assistant_message_id": assistant_message.id,
                        "conversation_tracked": True
                    })
                    
                except Exception as e:
                    logger.error(f"Response generation failed: {e}")
                    # Still return success with intent analysis, but note response failure
                    result.update({
                        "response": self._get_fallback_response(intent_result),
                        "response_generation_failed": True,
                        "response_error": str(e)
                    })
            
            # Update processing time
            result["processing_time_ms"] = (time.time() - start_time) * 1000
            
            logger.info(
                f"Processed input successfully: {intent_result.category.value} "
                f"(confidence: {intent_result.confidence:.2f}, time: {result['processing_time_ms']:.1f}ms)"
            )
            return result
            
        except CDOAIError as e:
            logger.error(f"CDO AI error processing input: {e}")
            return {
                "success": False,
                "error": e.message,
                "error_code": e.error_code,
                "details": e.details,
                "request_id": request_id,
                "processing_time_ms": (time.time() - start_time) * 1000,
                "session_id": session_id
            }
        except Exception as e:
            logger.error(f"Unexpected error processing input: {e}")
            return {
                "success": False,
                "error": "Internal service error",
                "error_code": "INTERNAL_ERROR",
                "details": {"exception": str(e)},
                "request_id": request_id,
                "processing_time_ms": (time.time() - start_time) * 1000,
                "session_id": session_id
            }
    
    async def _generate_contextual_response(
        self,
        user_input: str,
        intent_result: IntentAnalysisResult,
        context_messages: list = None
    ) -> str:
        """Generate contextual response based on intent and conversation history"""
        try:
            llm_response = await self.llm_service.generate_response(
                user_input,
                intent_result,
                context_messages or []
            )
            
            if llm_response.success:
                return llm_response.content
            else:
                logger.warning(f"LLM response generation failed: {llm_response.error_message}")
                return self._get_fallback_response(intent_result)
                
        except Exception as e:
            logger.error(f"Error generating contextual response: {e}")
            return self._get_fallback_response(intent_result)
    
    def _get_fallback_response(self, intent_result: IntentAnalysisResult) -> str:
        """Generate fallback response when LLM fails"""
        from ..models.intent import IntentCategory
        
        fallbacks = {
            IntentCategory.GENERAL_CHAT: "I'd be happy to chat! Could you tell me more about what's on your mind?",
            IntentCategory.QUESTION_ANSWERING: "I'd like to help answer your question, but I'm having trouble processing it right now. Could you rephrase it?",
            IntentCategory.TASK_REQUEST: "I understand you're looking for assistance with a task. Let me know more details about what you need help with.",
            IntentCategory.INFORMATION_SEEKING: "I'd be glad to help you find information. What specific topic are you interested in?",
            IntentCategory.CLARIFICATION: "I want to make sure I give you a clear explanation. Could you help me understand what specifically needs clarification?",
            IntentCategory.GREETING: "Hello! It's great to meet you. How can I help you today?",
            IntentCategory.GOODBYE: "Thank you for our conversation! Feel free to reach out anytime you need assistance."
        }
        
        return fallbacks.get(
            intent_result.category,
            "I'm here to help! Could you tell me more about what you're looking for?"
        )
    
    async def analyze_intent_only(
        self,
        user_input: str,
        session_id: Optional[str] = None
    ) -> IntentResponse:
        """Analyze intent without generating response or updating conversation"""
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            if not user_input or not user_input.strip():
                return IntentResponse.error_response(
                    request_id=request_id,
                    error_message="Empty input provided",
                    error_code="EMPTY_INPUT",
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # Get conversation context if session provided
            context_messages = []
            if session_id:
                try:
                    context_messages = await self.storage_service.get_recent_messages(session_id, limit=10)
                except Exception as e:
                    logger.warning(f"Failed to get context for session {session_id}: {e}")
            
            # Analyze intent
            intent_result = await self.llm_service.analyze_intent(user_input.strip(), context_messages)
            
            return IntentResponse.success_response(
                request_id=request_id,
                result=intent_result,
                processing_time_ms=(time.time() - start_time) * 1000
            )
            
        except CDOAIError as e:
            logger.error(f"CDO AI error analyzing intent: {e}")
            return IntentResponse.error_response(
                request_id=request_id,
                error_message=e.message,
                error_code=e.error_code,
                processing_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            logger.error(f"Unexpected error analyzing intent: {e}")
            return IntentResponse.error_response(
                request_id=request_id,
                error_message="Internal service error",
                error_code="INTERNAL_ERROR",
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    # Session Management Methods
    
    async def create_session(self, name: str = None, user_id: str = None) -> Dict[str, Any]:
        """Create new conversation session"""
        try:
            session = await self.storage_service.create_session(name, user_id)
            return {
                "success": True,
                "session": session.to_dict(),
                "message": f"Created session '{session.name}'"
            }
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "SESSION_CREATE_ERROR"
            }
    
    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get session information and statistics"""
        try:
            session = await self.storage_service.get_session(session_id)
            if not session:
                return {
                    "success": False,
                    "error": "Session not found",
                    "error_code": "SESSION_NOT_FOUND"
                }
            
            return {
                "success": True,
                "session": session.to_dict(),
                "statistics": session.get_statistics()
            }
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "SESSION_INFO_ERROR"
            }
    
    async def list_sessions(self, user_id: str = None) -> Dict[str, Any]:
        """List conversation sessions"""
        try:
            sessions = await self.storage_service.list_sessions(user_id)
            
            return {
                "success": True,
                "sessions": [session.to_dict() for session in sessions],
                "total_sessions": len(sessions),
                "message": f"Found {len(sessions)} session(s)"
            }
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "SESSION_LIST_ERROR"
            }
    
    async def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Delete conversation session"""
        try:
            success = await self.storage_service.delete_session(session_id)
            
            if success:
                return {
                    "success": True,
                    "message": f"Deleted session '{session_id}'"
                }
            else:
                return {
                    "success": False,
                    "error": "Session not found or could not be deleted",
                    "error_code": "SESSION_DELETE_FAILED"
                }
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "SESSION_DELETE_ERROR"
            }
    
    async def clear_session(self, session_id: str) -> Dict[str, Any]:
        """Clear session messages"""
        try:
            success = await self.storage_service.clear_session_messages(session_id)
            
            if success:
                return {
                    "success": True,
                    "message": f"Cleared messages for session '{session_id}'"
                }
            else:
                return {
                    "success": False,
                    "error": "Session not found or could not be cleared",
                    "error_code": "SESSION_CLEAR_FAILED"
                }
        except Exception as e:
            logger.error(f"Error clearing session: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "SESSION_CLEAR_ERROR"
            }
    
    # Service Health and Status
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status"""
        try:
            storage_summary = await self.storage_service.get_summary()
            
            return {
                "success": True,
                "status": "healthy",
                "version": self.settings.version,
                "environment": self.settings.environment,
                "service_info": {
                    "intent_analysis": "operational",
                    "conversation_management": "operational",
                    "storage": "operational",
                    "llm_integration": "operational"
                },
                "storage_summary": storage_summary.to_dict(),
                "configuration": {
                    "llm_model": self.settings.llm.model,
                    "llm_endpoint": self.settings.llm.endpoint,
                    "database_path": self.settings.database.path,
                    "max_messages": self.settings.database.max_messages
                },
                "supported_intents": [intent.value for intent in IntentCategory],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {
                "success": False,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Simple health check endpoint"""
        try:
            # Test basic functionality
            test_result = await self.analyze_intent_only("Health check test message")
            
            return {
                "status": "healthy" if test_result.success else "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "version": self.settings.version,
                "checks": {
                    "intent_analysis": "ok" if test_result.success else "failed",
                    "storage": "ok",
                    "configuration": "ok"
                }
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "checks": {
                    "intent_analysis": "failed",
                    "storage": "unknown",
                    "configuration": "unknown"
                }
            }
