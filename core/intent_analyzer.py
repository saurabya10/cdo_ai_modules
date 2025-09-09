# -*- coding: utf-8 -*-
"""
Production-grade Intent Analysis System
Focuses solely on understanding user intent from natural language input
"""

import json
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass

from langchain_openai import AzureChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, BaseMessage
from settings import get_api_key, llm_model, llm_endpoint, api_version, app_key

logger = logging.getLogger(__name__)


class IntentCategory(Enum):
    """Supported intent categories"""
    GENERAL_CHAT = "general_chat"
    QUESTION_ANSWERING = "question_answering"
    TASK_REQUEST = "task_request"
    INFORMATION_SEEKING = "information_seeking"
    CLARIFICATION = "clarification"
    GREETING = "greeting"
    GOODBYE = "goodbye"


@dataclass
class IntentAnalysisResult:
    """Structured result from intent analysis"""
    category: IntentCategory
    confidence: float
    reasoning: str
    entities: Dict[str, Any]
    follow_up_needed: bool = False
    context_dependent: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "category": self.category.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "entities": self.entities,
            "follow_up_needed": self.follow_up_needed,
            "context_dependent": self.context_dependent
        }


class IntentAnalyzer:
    """
    Production-grade intent analysis system using Azure OpenAI.
    
    Features:
    - Structured intent classification
    - Entity extraction
    - Confidence scoring
    - Context awareness
    - Conversation history integration
    """
    
    def __init__(self, temperature: float = 0.1, max_tokens: int = 500):
        """
        Initialize intent analyzer.
        
        Args:
            temperature: LLM temperature for consistency
            max_tokens: Maximum tokens for analysis response
        """
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._system_prompt = self._build_system_prompt()
        logger.info("IntentAnalyzer initialized with Azure OpenAI")
    
    def _get_llm_client(self) -> AzureChatOpenAI:
        """Get configured LLM client"""
        api_key = get_api_key()
        return AzureChatOpenAI(
            model=llm_model,
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=llm_endpoint,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            model_kwargs=dict(user='{"appkey": "' + app_key + '", "user": "user1"}'),
        )
    
    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt for intent analysis"""
        intent_categories = [intent.value for intent in IntentCategory]
        
        return f"""You are an expert intent analysis system. Your task is to analyze user input and determine their intent with high accuracy.

INTENT CATEGORIES:
{chr(10).join(f"- {cat}: {self._get_category_description(cat)}" for cat in intent_categories)}

ANALYSIS REQUIREMENTS:
1. Classify the user's primary intent into one of the above categories
2. Provide a confidence score (0.0 to 1.0) based on clarity of intent
3. Extract relevant entities (names, dates, topics, etc.)
4. Determine if follow-up questions are needed for clarification
5. Assess if the intent depends on conversation context

RESPONSE FORMAT:
Respond with ONLY a valid JSON object in this exact format:
{{
    "category": "intent_category",
    "confidence": 0.85,
    "reasoning": "Clear explanation of why this intent was chosen",
    "entities": {{"key": "value", "extracted_info": "relevant_data"}},
    "follow_up_needed": false,
    "context_dependent": false
}}

GUIDELINES:
- Be precise and consistent in classification
- Higher confidence for clear, specific requests
- Lower confidence for ambiguous or unclear input
- Extract all relevant entities mentioned
- Consider conversation flow and context
- Provide clear reasoning for your classification

EXAMPLES:

Input: "Hello there!"
Output: {{"category": "greeting", "confidence": 0.95, "reasoning": "Clear greeting with friendly tone", "entities": {{}}, "follow_up_needed": false, "context_dependent": false}}

Input: "What's the weather like?"
Output: {{"category": "information_seeking", "confidence": 0.90, "reasoning": "Direct request for weather information", "entities": {{"topic": "weather"}}, "follow_up_needed": true, "context_dependent": false}}

Input: "Can you help me understand what we discussed earlier?"
Output: {{"category": "clarification", "confidence": 0.85, "reasoning": "Request for clarification about previous conversation", "entities": {{"reference": "earlier discussion"}}, "follow_up_needed": false, "context_dependent": true}}
"""
    
    def _get_category_description(self, category: str) -> str:
        """Get description for intent category"""
        descriptions = {
            "general_chat": "Casual conversation, small talk, open-ended discussion",
            "question_answering": "Direct questions seeking specific factual answers",
            "task_request": "Requests to perform specific actions or tasks",
            "information_seeking": "Looking for information on particular topics",
            "clarification": "Asking for clarification or explanation of previous content",
            "greeting": "Greetings, introductions, conversation starters",
            "goodbye": "Farewells, conversation endings, sign-offs"
        }
        return descriptions.get(category, "General category")
    
    async def analyze_intent(
        self, 
        user_input: str, 
        conversation_history: Optional[List[BaseMessage]] = None
    ) -> IntentAnalysisResult:
        """
        Analyze user intent with optional conversation context.
        
        Args:
            user_input: The user's message to analyze
            conversation_history: Previous conversation messages for context
            
        Returns:
            IntentAnalysisResult with detailed analysis
        """
        try:
            llm = self._get_llm_client()
            
            # Build messages for analysis
            messages = [SystemMessage(content=self._system_prompt)]
            
            # Add conversation context if provided
            if conversation_history:
                # Include recent context (last 6 messages for efficiency)
                recent_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
                
                context_summary = self._summarize_context(recent_history)
                if context_summary:
                    messages.append(SystemMessage(content=f"CONVERSATION CONTEXT: {context_summary}"))
            
            # Add current user input
            messages.append(HumanMessage(content=f"ANALYZE THIS INPUT: {user_input}"))
            
            # Get LLM analysis
            response = llm.invoke(messages)
            
            # Parse structured response
            analysis_data = self._parse_analysis_response(response.content)
            
            # Create structured result
            result = IntentAnalysisResult(
                category=IntentCategory(analysis_data["category"]),
                confidence=analysis_data["confidence"],
                reasoning=analysis_data["reasoning"],
                entities=analysis_data.get("entities", {}),
                follow_up_needed=analysis_data.get("follow_up_needed", False),
                context_dependent=analysis_data.get("context_dependent", False)
            )
            
            logger.info(f"Intent analysis complete: {result.category.value} (confidence: {result.confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Intent analysis failed: {str(e)}")
            # Return fallback result
            return IntentAnalysisResult(
                category=IntentCategory.GENERAL_CHAT,
                confidence=0.5,
                reasoning=f"Analysis failed, defaulting to general chat: {str(e)}",
                entities={},
                follow_up_needed=False,
                context_dependent=False
            )
    
    def _summarize_context(self, history: List[BaseMessage]) -> str:
        """Create concise context summary from conversation history"""
        if not history:
            return ""
        
        context_parts = []
        for i, message in enumerate(history):
            role = "User" if message.__class__.__name__ == "HumanMessage" else "Assistant"
            content_preview = message.content[:100] + "..." if len(message.content) > 100 else message.content
            context_parts.append(f"{role}: {content_preview}")
        
        return " | ".join(context_parts)
    
    def _parse_analysis_response(self, response_content: str) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        try:
            # Clean up response content
            cleaned_content = response_content.strip()
            
            # Handle code blocks
            if "```json" in cleaned_content:
                start = cleaned_content.find("```json") + 7
                end = cleaned_content.find("```", start)
                cleaned_content = cleaned_content[start:end].strip()
            elif "```" in cleaned_content:
                start = cleaned_content.find("```") + 3
                end = cleaned_content.find("```", start)
                cleaned_content = cleaned_content[start:end].strip()
            
            # Parse JSON
            analysis_data = json.loads(cleaned_content)
            
            # Validate required fields
            required_fields = ["category", "confidence", "reasoning"]
            for field in required_fields:
                if field not in analysis_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate category
            if analysis_data["category"] not in [intent.value for intent in IntentCategory]:
                logger.warning(f"Invalid category: {analysis_data['category']}, defaulting to general_chat")
                analysis_data["category"] = IntentCategory.GENERAL_CHAT.value
            
            # Validate confidence
            confidence = float(analysis_data["confidence"])
            if not 0.0 <= confidence <= 1.0:
                logger.warning(f"Invalid confidence: {confidence}, clamping to valid range")
                analysis_data["confidence"] = max(0.0, min(1.0, confidence))
            
            return analysis_data
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse analysis response: {str(e)}")
            logger.debug(f"Raw response: {response_content}")
            
            # Return fallback structure
            return {
                "category": IntentCategory.GENERAL_CHAT.value,
                "confidence": 0.5,
                "reasoning": f"Failed to parse analysis response: {str(e)}",
                "entities": {},
                "follow_up_needed": False,
                "context_dependent": False
            }
    
    def get_supported_categories(self) -> List[str]:
        """Get list of supported intent categories"""
        return [intent.value for intent in IntentCategory]
    
    def validate_confidence_threshold(self, result: IntentAnalysisResult, threshold: float = 0.7) -> bool:
        """Check if analysis result meets confidence threshold"""
        return result.confidence >= threshold


class ConversationalIntentAnalyzer(IntentAnalyzer):
    """
    Extended intent analyzer with built-in conversation history integration
    """
    
    def __init__(self, chat_history_manager, temperature: float = 0.1, max_tokens: int = 500):
        """
        Initialize with chat history manager integration.
        
        Args:
            chat_history_manager: ChatHistoryManager instance for context
            temperature: LLM temperature
            max_tokens: Maximum tokens for response
        """
        super().__init__(temperature, max_tokens)
        self.chat_history_manager = chat_history_manager
        logger.info("ConversationalIntentAnalyzer initialized with history integration")
    
    async def analyze_with_context(self, user_input: str, session_id: Optional[str] = None) -> IntentAnalysisResult:
        """
        Analyze intent with automatic conversation context integration.
        
        Args:
            user_input: User's message to analyze
            session_id: Optional session ID for context
            
        Returns:
            IntentAnalysisResult with context-aware analysis
        """
        # Get conversation history from chat manager
        conversation_history = self.chat_history_manager.get_conversation_context(session_id)
        
        # Perform analysis with context
        return await self.analyze_intent(user_input, conversation_history)
