# -*- coding: utf-8 -*-
"""
Production-grade Conversation Management System
Orchestrates intent analysis with persistent chat history using SQLite
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import asdict

from langchain_openai import AzureChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage, BaseMessage

from .chat_history_manager import ChatHistoryManager
from .intent_analyzer import ConversationalIntentAnalyzer, IntentAnalysisResult, IntentCategory
from settings import get_api_key, llm_model, llm_endpoint, api_version, app_key

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Production-grade conversation orchestrator that automatically handles:
    - Intent analysis with context
    - Persistent SQLite conversation history
    - LLM response generation with memory
    - Automatic conversation tracking
    
    This is the main interface for the intent analysis system.
    """
    
    def __init__(self, config_path: str = "chat_config.json"):
        """
        Initialize conversation manager with integrated components.
        
        Args:
            config_path: Path to chat configuration file
        """
        # Initialize chat history manager
        self.chat_history = ChatHistoryManager(config_path)
        
        # Initialize intent analyzer with history integration
        self.intent_analyzer = ConversationalIntentAnalyzer(
            chat_history_manager=self.chat_history,
            temperature=0.1,
            max_tokens=500
        )
        
        # LLM settings for response generation
        self.response_temperature = 0.3
        self.response_max_tokens = 1500
        
        logger.info("ConversationManager initialized with SQLite persistence and intent analysis")
    
    def _get_response_llm(self) -> AzureChatOpenAI:
        """Get configured LLM client for response generation"""
        api_key = get_api_key()
        return AzureChatOpenAI(
            model=llm_model,
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=llm_endpoint,
            temperature=self.response_temperature,
            max_tokens=self.response_max_tokens,
            model_kwargs=dict(user='{"appkey": "' + app_key + '", "user": "user1"}'),
        )
    
    async def process_message(
        self, 
        user_input: str, 
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user message with automatic intent analysis and conversation tracking.
        
        Args:
            user_input: User's message
            session_id: Optional session ID (uses default if not provided)
            
        Returns:
            Dictionary with success status, response, intent analysis, and metadata
        """
        try:
            session_id = session_id or self.chat_history.current_session_id
            
            # Step 1: Analyze intent with conversation context
            logger.info(f"Processing message in session '{session_id}': {user_input[:100]}...")
            intent_result = await self.intent_analyzer.analyze_with_context(user_input, session_id)
            
            # Step 2: Generate contextual response based on intent
            response_content = await self._generate_response(user_input, intent_result, session_id)
            
            # Step 3: Automatically save conversation to SQLite
            self.chat_history.add_exchange(user_input, response_content, session_id)
            
            # Step 4: Return comprehensive result
            return {
                "success": True,
                "response": response_content,
                "intent_analysis": asdict(intent_result),
                "session_id": session_id,
                "conversation_tracked": True,
                "metadata": {
                    "response_length": len(response_content),
                    "confidence": intent_result.confidence,
                    "context_used": intent_result.context_dependent,
                    "follow_up_suggested": intent_result.follow_up_needed
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I encountered an error processing your message. Please try again.",
                "session_id": session_id,
                "conversation_tracked": False
            }
    
    async def _generate_response(
        self, 
        user_input: str, 
        intent_result: IntentAnalysisResult, 
        session_id: str
    ) -> str:
        """
        Generate contextual response based on intent analysis and conversation history.
        
        Args:
            user_input: Original user message
            intent_result: Intent analysis results
            session_id: Session ID for context
            
        Returns:
            Generated AI response
        """
        try:
            llm = self._get_response_llm()
            
            # Get conversation history for context
            conversation_history = self.chat_history.get_conversation_context(session_id)
            
            # Build system prompt based on intent
            system_prompt = self._build_response_system_prompt(intent_result)
            
            # Prepare messages with conversation history
            messages = [SystemMessage(content=system_prompt)]
            
            # Add conversation history (limit to recent context for efficiency)
            if conversation_history:
                # Include last 10 messages for context
                recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
                messages.extend(recent_history)
            
            # Add current user message
            messages.append(HumanMessage(content=user_input))
            
            # Generate response
            response = llm.invoke(messages)
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            return self._get_fallback_response(intent_result.category)
    
    def _build_response_system_prompt(self, intent_result: IntentAnalysisResult) -> str:
        """Build system prompt tailored to detected intent"""
        base_prompt = """You are a helpful AI assistant engaged in a natural conversation. You maintain context from previous messages and provide thoughtful, relevant responses.

CONVERSATION GUIDELINES:
- Be conversational and engaging
- Reference previous context when relevant
- Ask clarifying questions when needed
- Provide helpful and accurate information
- Maintain a friendly, professional tone
- Stay focused on the user's intent
"""
        
        # Add intent-specific guidance
        intent_guidance = {
            IntentCategory.GENERAL_CHAT: "Engage in natural conversation. Be friendly and show interest in what the user is sharing.",
            IntentCategory.QUESTION_ANSWERING: "Provide clear, accurate answers. If you're unsure, say so and suggest alternatives.",
            IntentCategory.TASK_REQUEST: "Acknowledge the task request. Since you're focused on conversation, explain what you understand and discuss next steps.",
            IntentCategory.INFORMATION_SEEKING: "Provide helpful information on the requested topic. Be thorough but concise.",
            IntentCategory.CLARIFICATION: "Provide clear explanations and examples. Reference the conversation context appropriately.",
            IntentCategory.GREETING: "Respond warmly to greetings. Set a positive tone for the conversation.",
            IntentCategory.GOODBYE: "Acknowledge farewells appropriately. Offer to help again in the future."
        }
        
        specific_guidance = intent_guidance.get(
            intent_result.category, 
            "Respond appropriately to the user's message with consideration for their intent."
        )
        
        # Add context information
        context_note = ""
        if intent_result.context_dependent:
            context_note = "\n\nIMPORTANT: This message depends on previous conversation context. Review the conversation history carefully."
        
        if intent_result.follow_up_needed:
            context_note += "\n\nNOTE: The user's intent may need clarification. Consider asking follow-up questions."
        
        return f"{base_prompt}\n\nSPECIFIC GUIDANCE: {specific_guidance}{context_note}\n\nINTENT DETECTED: {intent_result.category.value} (confidence: {intent_result.confidence:.2f})\nREASONING: {intent_result.reasoning}"
    
    def _get_fallback_response(self, intent_category: IntentCategory) -> str:
        """Generate fallback response when LLM fails"""
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
            intent_category, 
            "I'm here to help! Could you tell me more about what you're looking for?"
        )
    
    # Session Management Methods
    
    def get_current_session_id(self) -> str:
        """Get current active session ID"""
        return self.chat_history.current_session_id
    
    def switch_session(self, session_id: str) -> Dict[str, Any]:
        """Switch to different conversation session"""
        try:
            old_session = self.chat_history.current_session_id
            self.chat_history.switch_session(session_id)
            
            return {
                "success": True,
                "message": f"Switched from '{old_session}' to '{session_id}'",
                "old_session": old_session,
                "new_session": session_id
            }
        except Exception as e:
            logger.error(f"Session switch failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_sessions(self) -> List[str]:
        """List all available conversation sessions"""
        return self.chat_history.list_sessions()
    
    def get_session_info(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed information about a session"""
        return self.chat_history.get_session_info(session_id)
    
    def clear_current_session(self) -> Dict[str, Any]:
        """Clear current session conversation history"""
        try:
            session_id = self.chat_history.current_session_id
            self.chat_history.clear_current_session()
            
            return {
                "success": True,
                "message": f"Cleared conversation history for session '{session_id}'",
                "session_id": session_id
            }
        except Exception as e:
            logger.error(f"Session clear failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Delete a conversation session"""
        try:
            if session_id == self.chat_history.current_session_id:
                return {
                    "success": False,
                    "error": "Cannot delete current active session. Switch to another session first."
                }
            
            self.chat_history.delete_session(session_id)
            
            return {
                "success": True,
                "message": f"Deleted session '{session_id}'",
                "deleted_session": session_id
            }
        except Exception as e:
            logger.error(f"Session deletion failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Analytics and Monitoring
    
    def get_conversation_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive conversation summary"""
        session_info = self.get_session_info(session_id)
        
        return {
            "session_stats": session_info,
            "supported_intents": self.intent_analyzer.get_supported_categories(),
            "total_sessions": len(self.list_sessions()),
            "current_session": self.get_current_session_id(),
            "configuration": {
                "db_path": self.chat_history.config["db_path"],
                "max_messages": self.chat_history.config["max_messages"]
            }
        }


# Factory function for easy initialization
def create_conversation_manager(config_path: str = "chat_config.json") -> ConversationManager:
    """
    Factory function to create and configure conversation manager.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configured ConversationManager instance
    """
    return ConversationManager(config_path)
