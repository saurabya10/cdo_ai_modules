# -*- coding: utf-8 -*-
"""
Production-grade Intent Analysis Server
Clean, focused implementation for intent analysis with persistent SQLite conversation history
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from core.conversation_manager import ConversationManager, create_conversation_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('intent_analysis.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class IntentAnalysisServer:
    """
    Production-grade intent analysis server with persistent conversation history.
    
    Features:
    - Clean intent analysis focused architecture
    - Automatic SQLite conversation persistence
    - Session-based conversation management
    - Production-ready error handling and logging
    """
    
    def __init__(self, config_path="chat_config.json"):
        """
        Initialize intent analysis server.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.conversation_manager: Optional[ConversationManager] = None
        self._initialize_server()
        
        logger.info("IntentAnalysisServer initialized successfully")
    
    def _initialize_server(self):
        """Initialize server components"""
        try:
            # Create configuration file if it doesn't exist
            self._ensure_config_exists()
            
            # Initialize conversation manager
            self.conversation_manager = create_conversation_manager(self.config_path)
            
            logger.info("Server components initialized successfully")
            
        except Exception as e:
            logger.error(f"Server initialization failed: {str(e)}")
            raise
    
    def _ensure_config_exists(self):
        """Create default configuration file if it doesn't exist"""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            import json
            
            default_config = {
                "db_path": "intent_conversations.db",
                "max_messages": 100,
                "default_session": "main_session",
                "auto_backup": True,
                "session_timeout_hours": 24,
                "intent_analysis": {
                    "temperature": 0.1,
                    "max_tokens": 500,
                    "confidence_threshold": 0.7
                },
                "response_generation": {
                    "temperature": 0.3,
                    "max_tokens": 1500
                }
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            
            logger.info(f"Created default configuration at {config_file}")
    
    async def process_user_input(self, user_input, session_id=None):
        """
        Process user input through intent analysis with conversation context.
        
        Args:
            user_input: User's message to process
            session_id: Optional session ID for conversation context
            
        Returns:
            Comprehensive result with intent analysis and response
        """
        try:
            if not self.conversation_manager:
                raise RuntimeError("Server not properly initialized")
            
            # Validate input
            if not user_input or not user_input.strip():
                return {
                    "success": False,
                    "error": "Empty input provided",
                    "response": "Please provide a message for me to analyze."
                }
            
            # Process message through conversation manager
            result = await self.conversation_manager.process_message(
                user_input.strip(), 
                session_id
            )
            
            # Add server-level metadata
            result.update({
                "server_version": "1.0.0",
                "processing_mode": "intent_analysis_only",
                "timestamp": self._get_current_timestamp()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing user input: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "server_error": True,
                "timestamp": self._get_current_timestamp()
            }
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    # Session Management Interface
    
    def get_current_session(self) -> str:
        """Get current active session ID"""
        return self.conversation_manager.get_current_session_id()
    
    def switch_session(self, session_id):
        """Switch to different conversation session"""
        return self.conversation_manager.switch_session(session_id)
    
    def list_sessions(self) -> Dict[str, Any]:
        """List all available sessions with metadata"""
        try:
            sessions = self.conversation_manager.list_sessions()
            current_session = self.get_current_session()
            
            return {
                "success": True,
                "sessions": sessions,
                "current_session": current_session,
                "total_sessions": len(sessions),
                "message": f"Found {len(sessions)} conversation session(s)"
            }
        except Exception as e:
            logger.error(f"Error listing sessions: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_session_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive session information"""
        try:
            summary = self.conversation_manager.get_conversation_summary(session_id)
            summary.update({
                "success": True,
                "server_mode": "intent_analysis_only"
            })
            return summary
        except Exception as e:
            logger.error(f"Error getting session summary: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def clear_current_session(self) -> Dict[str, Any]:
        """Clear current session conversation history"""
        return self.conversation_manager.clear_current_session()
    
    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Delete a conversation session"""
        return self.conversation_manager.delete_session(session_id)
    
    # Server Status and Health
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get comprehensive server status"""
        try:
            session_summary = self.get_session_summary()
            
            return {
                "success": True,
                "server_status": "healthy",
                "mode": "intent_analysis_only",
                "version": "1.0.0",
                "configuration": {
                    "config_path": self.config_path,
                    "database_path": session_summary.get("configuration", {}).get("db_path"),
                    "max_messages": session_summary.get("configuration", {}).get("max_messages")
                },
                "session_info": {
                    "current_session": self.get_current_session(),
                    "total_sessions": len(self.list_sessions().get("sessions", [])),
                    "current_session_stats": session_summary.get("session_stats", {})
                },
                "capabilities": [
                    "intent_analysis",
                    "conversation_history",
                    "session_management",
                    "context_aware_responses"
                ],
                "supported_intents": session_summary.get("supported_intents", []),
                "timestamp": self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error getting server status: {str(e)}")
            return {
                "success": False,
                "server_status": "error",
                "error": str(e),
                "timestamp": self._get_current_timestamp()
            }
    
    # Cleanup and Shutdown
    
    async def shutdown(self):
        """Gracefully shutdown server"""
        try:
            logger.info("Shutting down IntentAnalysisServer...")
            # Add any cleanup logic here if needed
            logger.info("Server shutdown completed successfully")
        except Exception as e:
            logger.error(f"Error during server shutdown: {str(e)}")


# Factory function for easy server creation
def create_intent_analysis_server(config_path: str = "chat_config.json") -> IntentAnalysisServer:
    """
    Factory function to create and configure intent analysis server.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configured IntentAnalysisServer instance
    """
    return IntentAnalysisServer(config_path)


# Development and testing utilities

async def test_server_functionality():
    """Test basic server functionality"""
    print("Testing IntentAnalysisServer...")
    
    server = create_intent_analysis_server()
    
    # Test basic processing
    test_messages = [
        "Hello, how are you today?",
        "What's the weather like?",
        "Can you help me understand machine learning?",
        "Thank you for your help!",
        "Goodbye!"
    ]
    
    print(f"\n=== Testing {len(test_messages)} messages ===")
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Test {i}: {message} ---")
        result = await server.process_user_input(message)
        
        if result["success"]:
            intent = result["intent_analysis"]
            print(f"Intent: {intent['category']} (confidence: {intent['confidence']:.2f})")
            print(f"Response: {result['response'][:100]}...")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    
    # Test session info
    print(f"\n=== Session Information ===")
    status = server.get_server_status()
    if status["success"]:
        print(f"Current session: {status['session_info']['current_session']}")
        print(f"Total messages: {status['session_info']['current_session_stats'].get('total_messages', 0)}")
    
    await server.shutdown()
    print("\nTesting completed!")


if __name__ == "__main__":
    # Run basic functionality test
    asyncio.run(test_server_functionality())
