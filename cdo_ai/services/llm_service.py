"""
LLM Service with enterprise integration and comprehensive error handling
"""

import time
import json
import base64
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

import httpx
import requests
import certifi
from langchain_openai import AzureChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage, BaseMessage

from ..config.settings import Settings
from ..models.intent import IntentCategory, IntentAnalysisResult
from ..models.conversation import Message, MessageType
from ..exceptions import (
    LLMError, 
    LLMConnectionError, 
    LLMAuthenticationError,
    LLMTimeoutError,
    IntentAnalysisError,
    IntentParsingError
)

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Standardized response from LLM service"""
    success: bool
    content: str = ""
    error_message: str = ""
    usage: Dict[str, Any] = None
    model: str = ""
    processing_time_ms: float = 0.0
    
    def __post_init__(self):
        if self.usage is None:
            self.usage = {}


class LLMService:
    """
    Enterprise LLM service with authentication, error handling, and retry logic
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._auth_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None
        
        logger.info(f"LLMService initialized with endpoint: {settings.llm.endpoint}")
    
    async def _get_auth_token(self) -> str:
        """Get authentication token with caching and refresh logic"""
        current_time = time.time()
        
        # Check if token is still valid (with 5-minute buffer)
        if (self._auth_token and 
            self._token_expires_at and 
            current_time < (self._token_expires_at - 300)):
            return self._auth_token
        
        try:
            logger.debug("Requesting new authentication token")
            
            url = "https://id.cisco.com/oauth2/default/v1/token"
            payload = "grant_type=client_credentials"
            
            credentials = base64.b64encode(
                f"{self.settings.llm.client_id}:{self.settings.llm.client_secret}".encode("utf-8")
            ).decode("utf-8")
            
            headers = {
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {credentials}",
            }
            
            response = requests.post(
                url, 
                headers=headers, 
                data=payload, 
                verify=certifi.where(),
                timeout=self.settings.llm.timeout
            )
            response.raise_for_status()
            
            token_data = response.json()
            self._auth_token = token_data.get("access_token")
            
            if not self._auth_token:
                raise LLMAuthenticationError("No access token received from auth endpoint")
            
            # Set expiration time (default to 1 hour if not provided)
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = current_time + expires_in
            
            logger.info("Successfully authenticated with LLM service")
            return self._auth_token
            
        except requests.RequestException as e:
            logger.error(f"Authentication request failed: {e}")
            raise LLMAuthenticationError(f"Authentication failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected authentication error: {e}")
            raise LLMAuthenticationError(f"Authentication error: {e}")
    
    async def _make_llm_request(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.3,
        max_tokens: int = 1500,
        retry_count: int = 0
    ) -> LLMResponse:
        """Make request to LLM endpoint with retry logic"""
        start_time = time.time()
        
        try:
            token = await self._get_auth_token()
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'messages': messages,
                'max_tokens': max_tokens,
                'temperature': temperature,
                'stream': False,
                'model': self.settings.llm.model
            }
            
            completion_url = f"{self.settings.llm.endpoint}/chat/completions"
            
            async with httpx.AsyncClient(timeout=self.settings.llm.timeout) as client:
                response = await client.post(completion_url, json=payload, headers=headers)
                
                # Handle token expiration with retry
                if response.status_code == 401 and retry_count < self.settings.llm.max_retries:
                    logger.warning("Token expired, re-authenticating and retrying...")
                    self._auth_token = None  # Force re-authentication
                    return await self._make_llm_request(messages, temperature, max_tokens, retry_count + 1)
                
                response.raise_for_status()
                data = response.json()
                
                # Extract content
                choices = data.get('choices', [])
                if not choices:
                    return LLMResponse(
                        success=False,
                        error_message="No response choices returned from LLM",
                        processing_time_ms=(time.time() - start_time) * 1000
                    )
                
                content = choices[0].get('message', {}).get('content', '').strip()
                
                return LLMResponse(
                    success=True,
                    content=content,
                    usage=data.get('usage', {}),
                    model=data.get('model', self.settings.llm.model),
                    processing_time_ms=(time.time() - start_time) * 1000
                )
                
        except httpx.TimeoutException:
            error_msg = f"LLM request timed out after {self.settings.llm.timeout} seconds"
            logger.error(error_msg)
            raise LLMTimeoutError(error_msg, timeout_seconds=self.settings.llm.timeout)
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            raise LLMConnectionError(error_msg, endpoint=completion_url)
            
        except Exception as e:
            logger.error(f"Unexpected LLM request error: {e}")
            raise LLMError(f"LLM request failed: {e}")
    
    async def analyze_intent(
        self, 
        user_input: str, 
        context_messages: List[Message] = None
    ) -> IntentAnalysisResult:
        """
        Analyze user intent with comprehensive error handling and validation
        """
        start_time = time.time()
        
        try:
            logger.debug(f"Analyzing intent for input: {user_input[:100]}...")
            
            # Build system prompt
            system_prompt = self._build_intent_analysis_prompt()
            
            # Prepare messages
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add context if provided
            if context_messages:
                context_summary = self._build_context_summary(context_messages[-6:])  # Last 6 messages
                if context_summary:
                    messages.append({"role": "system", "content": f"CONVERSATION CONTEXT: {context_summary}"})
            
            # Add user input
            messages.append({"role": "user", "content": f"ANALYZE THIS INPUT: {user_input}"})
            
            # Make LLM request
            response = await self._make_llm_request(
                messages,
                temperature=self.settings.llm.intent_temperature,
                max_tokens=self.settings.llm.intent_max_tokens
            )
            
            if not response.success:
                raise IntentAnalysisError(f"LLM request failed: {response.error_message}")
            
            # Parse and validate response
            result = self._parse_intent_response(response.content, user_input)
            result.processing_time_ms = (time.time() - start_time) * 1000
            result.model_version = response.model
            
            logger.info(f"Intent analysis completed: {result.category.value} (confidence: {result.confidence:.2f})")
            return result
            
        except (LLMError, IntentAnalysisError):
            # Re-raise known exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error in intent analysis: {e}")
            # Return fallback result instead of raising
            return IntentAnalysisResult(
                category=IntentCategory.GENERAL_CHAT,
                confidence=0.5,
                reasoning=f"Analysis failed due to error: {str(e)}",
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    def _build_intent_analysis_prompt(self) -> str:
        """Build comprehensive system prompt for intent analysis"""
        categories = IntentCategory.get_descriptions()
        category_list = "\n".join([f"- {cat}: {desc}" for cat, desc in categories.items()])
        
        return f"""You are an expert intent analysis system. Analyze user input and determine their intent with high accuracy.

INTENT CATEGORIES:
{category_list}

RESPONSE FORMAT:
Respond with ONLY a valid JSON object in this exact format:
{{
    "category": "intent_category",
    "confidence": 0.85,
    "reasoning": "Clear explanation of why this intent was chosen",
    "entities": {{"key": "value", "extracted_info": "relevant_data"}},
    "follow_up_needed": false,
    "context_dependent": false,
    "suggested_actions": ["action1", "action2"]
}}

GUIDELINES:
- Be precise and consistent in classification
- Higher confidence for clear, specific requests
- Lower confidence for ambiguous or unclear input
- Extract all relevant entities mentioned
- Consider conversation flow and context
- Provide clear reasoning for your classification
- Suggest relevant follow-up actions when appropriate

EXAMPLES:

Input: "Hello there!"
Output: {{"category": "greeting", "confidence": 0.95, "reasoning": "Clear greeting with friendly tone", "entities": {{}}, "follow_up_needed": false, "context_dependent": false, "suggested_actions": ["respond_warmly", "ask_how_to_help"]}}

Input: "What's the weather like?"
Output: {{"category": "information_seeking", "confidence": 0.90, "reasoning": "Direct request for weather information", "entities": {{"topic": "weather"}}, "follow_up_needed": true, "context_dependent": false, "suggested_actions": ["ask_location", "provide_weather_info"]}}

Input: "Can you explain what we discussed earlier?"
Output: {{"category": "clarification", "confidence": 0.88, "reasoning": "Request for clarification about previous conversation", "entities": {{"reference": "earlier discussion"}}, "follow_up_needed": false, "context_dependent": true, "suggested_actions": ["review_context", "summarize_previous"]}}
"""
    
    def _build_context_summary(self, messages: List[Message]) -> str:
        """Build concise context summary from recent messages"""
        if not messages:
            return ""
        
        context_parts = []
        for msg in messages:
            role = "User" if msg.message_type == MessageType.USER else "Assistant"
            content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            context_parts.append(f"{role}: {content_preview}")
        
        return " | ".join(context_parts)
    
    def _parse_intent_response(self, response_content: str, original_input: str) -> IntentAnalysisResult:
        """Parse and validate LLM response into structured format"""
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
            try:
                analysis_data = json.loads(cleaned_content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}, content: {cleaned_content[:200]}")
                raise IntentParsingError(f"Invalid JSON response: {e}", cleaned_content)
            
            # Validate required fields
            required_fields = ["category", "confidence", "reasoning"]
            missing_fields = [field for field in required_fields if field not in analysis_data]
            if missing_fields:
                raise IntentParsingError(f"Missing required fields: {missing_fields}")
            
            # Validate and convert category
            category_str = analysis_data["category"]
            try:
                category = IntentCategory(category_str)
            except ValueError:
                logger.warning(f"Invalid category: {category_str}, defaulting to general_chat")
                category = IntentCategory.GENERAL_CHAT
                analysis_data["reasoning"] += f" (Note: Invalid category '{category_str}' was corrected)"
            
            # Validate confidence
            confidence = float(analysis_data["confidence"])
            if not 0.0 <= confidence <= 1.0:
                logger.warning(f"Invalid confidence: {confidence}, clamping to valid range")
                confidence = max(0.0, min(1.0, confidence))
            
            # Create result
            return IntentAnalysisResult(
                category=category,
                confidence=confidence,
                reasoning=analysis_data["reasoning"],
                entities=analysis_data.get("entities", {}),
                follow_up_needed=analysis_data.get("follow_up_needed", False),
                context_dependent=analysis_data.get("context_dependent", False),
                suggested_actions=analysis_data.get("suggested_actions", [])
            )
            
        except IntentParsingError:
            # Re-raise parsing errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error parsing intent response: {e}")
            # Return fallback result with keyword-based classification
            return self._fallback_intent_classification(original_input)
    
    def _fallback_intent_classification(self, user_input: str) -> IntentAnalysisResult:
        """Fallback intent classification using simple keyword matching"""
        user_input_lower = user_input.lower()
        
        # Simple keyword-based classification
        if any(word in user_input_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
            return IntentAnalysisResult(
                category=IntentCategory.GREETING,
                confidence=0.7,
                reasoning="Fallback classification based on greeting keywords"
            )
        elif any(word in user_input_lower for word in ["bye", "goodbye", "see you", "farewell"]):
            return IntentAnalysisResult(
                category=IntentCategory.GOODBYE,
                confidence=0.7,
                reasoning="Fallback classification based on goodbye keywords"
            )
        elif user_input.strip().endswith("?"):
            return IntentAnalysisResult(
                category=IntentCategory.QUESTION_ANSWERING,
                confidence=0.6,
                reasoning="Fallback classification based on question format"
            )
        else:
            return IntentAnalysisResult(
                category=IntentCategory.GENERAL_CHAT,
                confidence=0.5,
                reasoning="Fallback classification - default to general chat"
            )
    
    async def generate_response(
        self, 
        user_input: str,
        intent_result: IntentAnalysisResult,
        context_messages: List[Message] = None
    ) -> LLMResponse:
        """Generate contextual response based on intent and conversation history"""
        try:
            # Build system prompt based on intent
            system_prompt = self._build_response_system_prompt(intent_result)
            
            # Prepare messages
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (limit to recent context)
            if context_messages:
                recent_messages = context_messages[-10:] if len(context_messages) > 10 else context_messages
                for msg in recent_messages:
                    role = "user" if msg.message_type == MessageType.USER else "assistant"
                    messages.append({"role": role, "content": msg.content})
            
            # Add current user message
            messages.append({"role": "user", "content": user_input})
            
            # Generate response
            return await self._make_llm_request(
                messages,
                temperature=self.settings.llm.response_temperature,
                max_tokens=self.settings.llm.response_max_tokens
            )
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return LLMResponse(
                success=False,
                error_message=str(e)
            )
    
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
            IntentCategory.TASK_REQUEST: "Acknowledge the task request. Explain what you understand and discuss next steps.",
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
