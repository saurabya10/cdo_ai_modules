"""
Intent Analysis Service
Analyzes user input to determine intent using LLM
"""
import json
import logging
import base64
import requests
import certifi
from typing import Dict, Any
from langchain_openai import AzureChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from core.auth import get_api_key

logger = logging.getLogger(__name__)


class IntentAgent:
    """Analyzes user intent using LLM"""
    
    # Define available intents - easy to modify and extend
    INTENTS = {
        "file_read": "User wants to read, analyze, or search in CSV/text files",
        "dynamodb_query": "User wants to query or search DynamoDB tables", 
        "scc_query": "User wants to query Cisco Security Cloud Control for firewall devices",
        "rest_api": "User wants to make REST API calls to external endpoints",
        "sal_troubleshoot": "User wants to troubleshoot SAL (Secure Analytics and Logging) \
        event streaming from firewall devices",
        "general_chat": "General conversation or questions not requiring specific tools"
    }
    
    # Example mappings for each intent - easy to modify
    INTENT_EXAMPLES = {
        "file_read": [
            "Read the sales data from report.csv",
            "Analyze the data in users.txt",
            "Search for errors in log file"
        ],
        "dynamodb_query": [
            "Find user with ID 12345 in user table",
            "Query the orders table for recent purchases",
            "Search for items in the inventory database"
        ],
        "scc_query": [
            "List all firewall devices",
            "Find firewall device named Paradise",
            "Show me security policies"
        ],
        "rest_api": [
            "Call the API endpoint https://api.example.com",
            "Make a GET request to the weather API",
            "Send POST data to the webhook"
        ],
        "sal_troubleshoot": [
            "Find firewall device Paradise and check if it's sending events to SAL",
            "Check if all devices are sending events",
            "When was last event sent for device Paradise"
        ],
        "general_chat": [
            "What's the weather like?",
            "How are you today?",
            "Tell me a joke"
        ]
    }
    
    def __init__(self, config):
        """Initialize the intent agent"""
        self.config = config
        self.llm = None
        self._setup_llm()
    
    def _setup_llm(self):
        """Setup the LLM client"""
        try:
            # Get fresh API token using the same method as the working code
            api_key = get_api_key(self.config)
            
            self.llm = AzureChatOpenAI(
                model=self.config.llm.model,
                api_key=api_key,
                api_version=self.config.llm.api_version,
                azure_endpoint=self.config.llm.endpoint,
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
                model_kwargs=dict(user='{"appkey": "' + self.config.llm.app_key + '", "user": "user1"}')
            )
            logger.info("LLM client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            raise
    
    def _build_system_message(self) -> str:
        """Build the system message for intent classification"""
        intent_descriptions = "\n".join([
            f'{i+1}. "{intent}" - {description}' 
            for i, (intent, description) in enumerate(self.INTENTS.items())
        ])
        
        examples = []
        for intent, example_list in self.INTENT_EXAMPLES.items():
            for example in example_list[:1]:  # Take first example for each intent
                examples.append(f'- "{example}" -> {intent}')
        
        examples_text = "\n".join(examples)
        
        return f"""
        You are an intent classifier. Analyze the user's input and determine what action they want to perform.
        
        Available actions:
        {intent_descriptions}
        
        Respond with ONLY a JSON object in this format:
        {{
            "action": "intent_name",
            "confidence": 0.0-1.0,
            "reasoning": "brief explanation"
        }}
        
        Examples:
        {examples_text}
        """
    
    async def analyze_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Analyze user intent and return structured result
        
        Args:
            user_input: The user's input text
            
        Returns:
            Dict containing success, action, confidence, and reasoning
        """
        try:
            if not user_input or not user_input.strip():
                return {
                    'success': False,
                    'error': 'Empty input provided',
                    'action': 'general_chat',
                    'confidence': 0.0,
                    'reasoning': 'No input to analyze'
                }
            
            # Build messages for LLM
            system_message = self._build_system_message()
            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=user_input.strip())
            ]
            
            # Get LLM response
            response = self.llm.invoke(messages)
            response_content = response.content.strip()
            if response_content.startswith('```json'):
                response_content = response_content[7:-4]

            print("LLM Response:", response_content)  # Debug log
            # Try to parse JSON response
            try:
                intent_data = json.loads(response_content)
                
                # Validate the response
                action = intent_data.get('action', 'general_chat')
                confidence = float(intent_data.get('confidence', 0.5))
                reasoning = intent_data.get('reasoning', '')
                
                # Ensure action is valid
                if action not in self.INTENTS:
                    logger.warning(f"Invalid action '{action}' returned by LLM, defaulting to general_chat")
                    action = 'general_chat'
                    confidence = 0.5
                    reasoning = f"Invalid action '{action}' corrected to general_chat"
                
                # Ensure confidence is in valid range
                confidence = max(0.0, min(1.0, confidence))
                
                return {
                    'success': True,
                    'action': action,
                    'confidence': confidence,
                    'reasoning': reasoning
                }
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse LLM response as JSON: {e}")
                # Fallback to keyword-based classification
                return self._fallback_classification(user_input, response.content)
                
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            return {
                'success': False,
                'error': str(e),
                'action': 'general_chat',
                'confidence': 0.0,
                'reasoning': f'Error during analysis: {str(e)}'
            }
    
    def _fallback_classification(self, user_input: str, llm_response: str) -> Dict[str, Any]:
        """Fallback classification using keyword matching"""
        user_input_lower = user_input.lower()
        llm_response_lower = llm_response.lower()
        
        # Check for keywords in user input and LLM response
        for intent, keywords in {
            'file_read': ['file', 'csv', 'text', 'read', 'analyze', 'data'],
            'dynamodb_query': ['dynamodb', 'table', 'query', 'database', 'find', 'search'],
            'scc_query': ['firewall', 'device', 'security', 'cisco', 'scc', 'policy'],
            'rest_api': ['api', 'endpoint', 'http', 'get', 'post', 'request', 'call'],
            'sal_troubleshoot': ['sal', 'event', 'streaming', 'troubleshoot', 'logs', 'analytics']
        }.items():
            if any(keyword in user_input_lower or keyword in llm_response_lower for keyword in keywords):
                return {
                    'success': True,
                    'action': intent,
                    'confidence': 0.7,
                    'reasoning': f'Fallback classification based on keywords: {keywords}'
                }
        
        # Default to general chat
        return {
            'success': True,
            'action': 'general_chat',
            'confidence': 0.5,
            'reasoning': 'Fallback to general chat - no specific intent detected'
        }
    
    def get_available_intents(self) -> Dict[str, str]:
        """Get all available intents and their descriptions"""
        return self.INTENTS.copy()
    
    def add_intent(self, intent_name: str, description: str, examples: list = None):
        """
        Add a new intent (for future extensibility)
        
        Args:
            intent_name: Name of the new intent
            description: Description of what this intent represents
            examples: List of example phrases for this intent
        """
        self.INTENTS[intent_name] = description
        if examples:
            self.INTENT_EXAMPLES[intent_name] = examples
        logger.info(f"Added new intent: {intent_name}")
    
    def remove_intent(self, intent_name: str):
        """Remove an intent"""
        if intent_name in self.INTENTS:
            del self.INTENTS[intent_name]
            if intent_name in self.INTENT_EXAMPLES:
                del self.INTENT_EXAMPLES[intent_name]
            logger.info(f"Removed intent: {intent_name}")
        else:
            logger.warning(f"Intent '{intent_name}' not found")
