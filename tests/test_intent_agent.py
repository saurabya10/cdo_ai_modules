"""
Tests for intent analyzer functionality
"""
import unittest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from cdo_ai_modules.config.settings import Config, DatabaseConfig, LLMConfig, EmbeddingConfig
from cdo_ai_modules.agents.intent_agent import IntentAgent


class TestIntentAgent(unittest.TestCase):
    """Test intent agent functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = Config(
            database=DatabaseConfig(),
            llm=LLMConfig(
                client_id="test_id",
                client_secret="test_secret",
                app_key="test_key"
            ),
            embedding=EmbeddingConfig()
        )
        
        # Mock the LLM to avoid actual API calls
        with patch('cdo_ai_modules.agents.intent_agent.AzureChatOpenAI') as mock_llm_class:
            self.mock_llm = Mock()
            mock_llm_class.return_value = self.mock_llm
            
            # Also mock the API key method to avoid real authentication
            with patch('cdo_ai_modules.agents.intent_agent.get_api_key', return_value='mock_api_key'):
                self.agent = IntentAgent(self.config)
    
    def tearDown(self):
        """Clean up after each test"""
        # Reset intents to original state by removing any test intents
        test_intents = set(self.agent.INTENTS.keys()) - {
            "file_read", "dynamodb_query", "scc_query", "rest_api", "sal_troubleshoot", "general_chat"
        }
        for intent in test_intents:
            self.agent.remove_intent(intent)
    
    def test_initialization(self):
        """Test that agent initializes correctly"""
        self.assertIsNotNone(self.agent)
        # Should have 6 predefined intents
        expected_intents = {'file_read', 'dynamodb_query', 'scc_query', 'rest_api', 'sal_troubleshoot', 'general_chat'}
        actual_intents = set(self.agent.INTENTS.keys())
        self.assertEqual(actual_intents, expected_intents)
        self.assertIn('general_chat', self.agent.INTENTS)
        self.assertIn('file_read', self.agent.INTENTS)
    
    def test_get_available_intents(self):
        """Test getting available intents"""
        intents = self.agent.get_available_intents()
        
        self.assertIsInstance(intents, dict)
        self.assertIn('general_chat', intents)
        self.assertIn('file_read', intents)
        self.assertIn('dynamodb_query', intents)
        # Check that we have the expected intents
        expected_intents = {'file_read', 'dynamodb_query', 'scc_query', 'rest_api', 'sal_troubleshoot', 'general_chat'}
        self.assertEqual(set(intents.keys()), expected_intents)
    
    def test_add_intent(self):
        """Test adding a new intent"""
        initial_count = len(self.agent.INTENTS)
        
        self.agent.add_intent(
            "test_intent", 
            "Test intent for testing", 
            ["test example 1", "test example 2"]
        )
        
        self.assertEqual(len(self.agent.INTENTS), initial_count + 1)
        self.assertIn('test_intent', self.agent.INTENTS)
        self.assertEqual(self.agent.INTENTS['test_intent'], "Test intent for testing")
        self.assertIn('test_intent', self.agent.INTENT_EXAMPLES)
    
    def test_remove_intent(self):
        """Test removing an intent"""
        # First add a test intent
        self.agent.add_intent("temp_intent", "Temporary intent")
        self.assertIn('temp_intent', self.agent.INTENTS)
        
        # Then remove it
        self.agent.remove_intent("temp_intent")
        self.assertNotIn('temp_intent', self.agent.INTENTS)
    
    async def test_analyze_intent_success(self):
        """Test successful intent analysis"""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = '{"action": "file_read", "confidence": 0.9, "reasoning": "User wants to read a file"}'
        self.mock_llm.invoke = Mock(return_value=mock_response)  # Remove AsyncMock
        
        result = await self.agent.analyze_intent("Read the sales report.csv")
        
        self.assertTrue(result['success'])
        self.assertEqual(result['action'], 'file_read')
        self.assertEqual(result['confidence'], 0.9)
        self.assertEqual(result['reasoning'], 'User wants to read a file')
    
    async def test_analyze_intent_empty_input(self):
        """Test analysis with empty input"""
        result = await self.agent.analyze_intent("")
        
        self.assertFalse(result['success'])
        self.assertEqual(result['action'], 'general_chat')
        self.assertEqual(result['confidence'], 0.0)
        self.assertIn('Empty input', result['error'])
    
    async def test_analyze_intent_invalid_json(self):
        """Test analysis with invalid JSON response from LLM"""
        # Mock LLM response with invalid JSON
        mock_response = Mock()
        mock_response.content = 'This is not valid JSON but contains file keywords'
        self.mock_llm.invoke = Mock(return_value=mock_response)
        
        result = await self.agent.analyze_intent("Read the data file")
        
        self.assertTrue(result['success'])  # Should fallback successfully
        self.assertEqual(result['action'], 'file_read')  # Should detect file keywords
        self.assertEqual(result['confidence'], 0.7)  # Fallback confidence
        self.assertIn('Fallback classification', result['reasoning'])
    
    async def test_analyze_intent_invalid_action(self):
        """Test analysis with invalid action from LLM"""
        # Mock LLM response with invalid action
        mock_response = Mock()
        mock_response.content = '{"action": "invalid_action", "confidence": 0.8, "reasoning": "Invalid action"}'
        self.mock_llm.invoke = Mock(return_value=mock_response)
        
        result = await self.agent.analyze_intent("Test input")
        
        self.assertTrue(result['success'])
        self.assertEqual(result['action'], 'general_chat')  # Should default to general_chat
        self.assertEqual(result['confidence'], 0.5)  # Should reset confidence
        self.assertIn('Invalid action', result['reasoning'])
    
    async def test_fallback_classification(self):
        """Test fallback classification with different keywords"""
        test_cases = [
            ("read the csv file", "file_read"),
            ("query the dynamodb table", "dynamodb_query"),
            ("list firewall devices", "scc_query"),
            ("call the REST API", "rest_api"),
            ("troubleshoot SAL events", "sal_troubleshoot"),
            ("how are you today", "general_chat")  # No specific keywords
        ]
        
        for user_input, expected_intent in test_cases:
            result = self.agent._fallback_classification(user_input, "")
            self.assertEqual(result['action'], expected_intent)
            self.assertEqual(result['confidence'], 0.7 if expected_intent != 'general_chat' else 0.5)
    
    def test_build_system_message(self):
        """Test building system message"""
        system_message = self.agent._build_system_message()
        
        self.assertIsInstance(system_message, str)
        self.assertIn('intent classifier', system_message.lower())
        self.assertIn('JSON object', system_message)
        
        # Should contain all intents
        for intent in self.agent.INTENTS:
            self.assertIn(intent, system_message)
    
    async def test_analyze_intent_llm_error(self):
        """Test analysis when LLM throws an error"""
        # Mock LLM to raise an exception
        self.mock_llm.invoke = Mock(side_effect=Exception("LLM connection failed"))
        
        result = await self.agent.analyze_intent("Test input")
        
        self.assertFalse(result['success'])
        self.assertEqual(result['action'], 'general_chat')
        self.assertEqual(result['confidence'], 0.0)
        self.assertIn('LLM connection failed', result['reasoning'])


# Helper to run async tests
def async_test(coro):
    def wrapper(self):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro(self))
        finally:
            loop.close()
    return wrapper


# Apply async_test decorator to async test methods
for name, method in list(TestIntentAgent.__dict__.items()):
    if name.startswith('test_') and asyncio.iscoroutinefunction(method):
        setattr(TestIntentAgent, name, async_test(method))


if __name__ == '__main__':
    unittest.main()
