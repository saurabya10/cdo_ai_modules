"""
Tests for chat history functionality
"""
import unittest
import tempfile
import os
from pathlib import Path

from core.chat_history import ChatHistory


class TestChatHistory(unittest.TestCase):
    """Test chat history functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_chat.db"
        self.chat_history = ChatHistory(str(self.db_path), max_conversations=5)
    
    def tearDown(self):
        """Clean up test environment"""
        if self.db_path.exists():
            os.unlink(self.db_path)
    
    def test_database_initialization(self):
        """Test that database is properly initialized"""
        self.assertTrue(self.db_path.exists())
        
        # Test that we can get conversation count (should be 0 initially)
        count = self.chat_history.get_conversation_count()
        self.assertEqual(count, 0)
    
    def test_add_conversation(self):
        """Test adding a conversation"""
        conversation_id = self.chat_history.add_conversation(
            user_input="Hello world",
            intent_action="general_chat",
            intent_confidence=0.9,
            intent_reasoning="Greeting detected"
        )
        
        self.assertIsInstance(conversation_id, int)
        self.assertGreater(conversation_id, 0)
        
        # Check that conversation count increased
        count = self.chat_history.get_conversation_count()
        self.assertEqual(count, 1)
    
    def test_get_recent_conversations(self):
        """Test retrieving recent conversations"""
        # Add multiple conversations
        conversations_data = [
            ("Hello", "general_chat", 0.9, "Greeting"),
            ("Read file.csv", "file_read", 0.8, "File operation"),
            ("Query database", "dynamodb_query", 0.7, "Database operation")
        ]
        
        for user_input, action, confidence, reasoning in conversations_data:
            self.chat_history.add_conversation(user_input, action, confidence, reasoning)
        
        # Get recent conversations
        recent = self.chat_history.get_recent_conversations(limit=2)
        
        self.assertEqual(len(recent), 2)
        # Should be in reverse chronological order (most recent first)
        self.assertEqual(recent[0]['user_input'], "Query database")
        self.assertEqual(recent[1]['user_input'], "Read file.csv")
    
    def test_max_conversations_limit(self):
        """Test that old conversations are cleaned up when limit is exceeded"""
        # Add more conversations than the limit (5)
        for i in range(7):
            self.chat_history.add_conversation(
                user_input=f"Message {i}",
                intent_action="general_chat",
                intent_confidence=0.8,
                intent_reasoning=f"Test message {i}"
            )
        
        # Should only have 5 conversations (the limit)
        count = self.chat_history.get_conversation_count()
        self.assertEqual(count, 5)
        
        # The oldest conversations should be removed
        recent = self.chat_history.get_recent_conversations(limit=10)
        self.assertEqual(len(recent), 5)
        
        # Should have messages 2-6 (0 and 1 should be deleted)
        user_inputs = [conv['user_input'] for conv in reversed(recent)]
        expected_inputs = ["Message 2", "Message 3", "Message 4", "Message 5", "Message 6"]
        self.assertEqual(user_inputs, expected_inputs)
    
    def test_clear_history(self):
        """Test clearing all conversation history"""
        # Add some conversations
        self.chat_history.add_conversation("Test 1", "general_chat", 0.8, "Test")
        self.chat_history.add_conversation("Test 2", "file_read", 0.9, "Test")
        
        # Verify they were added
        self.assertEqual(self.chat_history.get_conversation_count(), 2)
        
        # Clear history
        self.chat_history.clear_history()
        
        # Verify history is empty
        self.assertEqual(self.chat_history.get_conversation_count(), 0)
        recent = self.chat_history.get_recent_conversations()
        self.assertEqual(len(recent), 0)
    
    def test_conversation_summary(self):
        """Test getting conversation summary statistics"""
        # Add conversations with different intents
        conversations = [
            ("Hello", "general_chat", 0.9),
            ("Read file", "file_read", 0.8),
            ("Query DB", "dynamodb_query", 0.7),
            ("Another chat", "general_chat", 0.85)
        ]
        
        for user_input, action, confidence in conversations:
            self.chat_history.add_conversation(user_input, action, confidence, "Test")
        
        summary = self.chat_history.get_conversation_summary()
        
        self.assertEqual(summary['total_conversations'], 4)
        self.assertAlmostEqual(summary['average_confidence'], 0.8125, places=3)
        self.assertEqual(summary['intent_distribution']['general_chat'], 2)
        self.assertEqual(summary['intent_distribution']['file_read'], 1)
        self.assertEqual(summary['intent_distribution']['dynamodb_query'], 1)
        self.assertEqual(summary['max_conversations_limit'], 5)


if __name__ == '__main__':
    unittest.main()
