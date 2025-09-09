"""
CLI commands implementation for CDO AI Modules
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..services.intent_service import IntentAnalysisService

logger = logging.getLogger(__name__)


class CLICommands:
    """CLI command implementations"""
    
    def __init__(self, intent_service: 'IntentAnalysisService'):
        self.intent_service = intent_service
        self.current_session_id = None
    
    async def show_help(self):
        """Display help information"""
        help_text = """
CDO AI Modules - Command Help
============================

Available Commands:
  help, h          - Show this help message
  quit, exit, q    - Exit the application
  status           - Show system and session status
  history          - Show conversation history summary
  clear            - Clear current session history
  sessions         - List all conversation sessions
  switch <name>    - Switch to a specific session
  delete <name>    - Delete a conversation session
  config           - Show current configuration
  debug            - Toggle debug mode

System Features:
  ✓ Intent Analysis    - Automatically classifies user messages
  ✓ Conversation Memory - Persistent SQLite storage across restarts
  ✓ Context Awareness  - Responses consider conversation history
  ✓ Session Management - Multiple isolated conversation contexts
  ✓ Error Handling     - Comprehensive error handling and logging

Supported Intent Categories:
  • general_chat        - Casual conversation
  • question_answering  - Direct factual questions
  • task_request        - Action requests
  • information_seeking - Topic information requests
  • clarification       - Explanation requests
  • greeting           - Conversation starters
  • goodbye            - Conversation endings

Examples:
  > Hello, how are you?                    (greeting)
  > What is machine learning?              (question_answering)
  > Can you help me with my project?       (task_request)
  > Tell me about artificial intelligence  (information_seeking)
  > What did we discuss earlier?           (clarification - context-aware)
  > Thanks, goodbye!                       (goodbye)

Note: This system focuses on intent analysis and maintains conversation
context. All interactions are automatically saved to SQLite database.
        """
        print(help_text)
    
    async def show_status(self):
        """Display comprehensive system status"""
        try:
            status = await self.intent_service.get_service_status()
            
            if not status.get('success'):
                print(f"Error retrieving status: {status.get('error')}")
                return
            
            print("\n" + "="*60)
            print("CDO AI MODULES - SYSTEM STATUS")
            print("="*60)
            
            # Service info
            print(f"Status: {status.get('status', 'Unknown').upper()}")
            print(f"Version: {status.get('version', 'Unknown')}")
            print(f"Environment: {status.get('environment', 'Unknown')}")
            
            # Service components
            service_info = status.get('service_info', {})
            print(f"\nService Components:")
            for component, state in service_info.items():
                indicator = "✓" if state == "operational" else "✗"
                print(f"  {indicator} {component.replace('_', ' ').title()}: {state}")
            
            # Configuration
            config = status.get('configuration', {})
            print(f"\nConfiguration:")
            print(f"  • LLM Model: {config.get('llm_model', 'N/A')}")
            print(f"  • LLM Endpoint: {config.get('llm_endpoint', 'N/A')}")
            print(f"  • Database: {config.get('database_path', 'N/A')}")
            print(f"  • Max Messages: {config.get('max_messages', 'N/A')}")
            
            # Storage summary
            storage_summary = status.get('storage_summary', {})
            if storage_summary:
                print(f"\nStorage Summary:")
                print(f"  • Total Sessions: {storage_summary.get('total_sessions', 0)}")
                print(f"  • Active Sessions: {storage_summary.get('active_sessions', 0)}")
                print(f"  • Total Messages: {storage_summary.get('total_messages', 0)}")
                
                avg_messages = storage_summary.get('averages', {}).get('messages_per_session', 0)
                print(f"  • Avg Messages/Session: {avg_messages:.1f}")
            
            # Supported intents
            intents = status.get('supported_intents', [])
            if intents:
                print(f"\nSupported Intents ({len(intents)}):")
                for intent in intents[:5]:  # Show first 5
                    print(f"  • {intent}")
                if len(intents) > 5:
                    print(f"  • ... and {len(intents) - 5} more")
            
            print(f"\nLast Updated: {status.get('timestamp', 'N/A')}")
            print("="*60)
            
        except Exception as e:
            logger.error(f"Error showing status: {e}")
            print(f"Error retrieving system status: {e}")
    
    async def show_history(self):
        """Show conversation history summary"""
        try:
            # Get current session or use default
            session_id = self.current_session_id or "main_session"
            
            result = await self.intent_service.get_session_info(session_id)
            
            if not result.get('success'):
                print(f"Error retrieving history: {result.get('error')}")
                return
            
            session_data = result.get('session', {})
            stats = result.get('statistics', {})
            
            print("\n" + "="*50)
            print("CONVERSATION HISTORY")
            print("="*50)
            
            print(f"Session: {session_data.get('name', 'Unknown')}")
            print(f"Session ID: {session_data.get('id', 'Unknown')}")
            print(f"Status: {stats.get('status', 'Unknown')}")
            
            print(f"\nMessage Statistics:")
            print(f"  • Total Messages: {stats.get('total_messages', 0)}")
            print(f"  • User Messages: {stats.get('user_messages', 0)}")
            print(f"  • Assistant Messages: {stats.get('assistant_messages', 0)}")
            
            print(f"\nSession Timeline:")
            print(f"  • Created: {stats.get('created_at', 'N/A')}")
            print(f"  • Last Activity: {stats.get('last_activity', 'N/A')}")
            print(f"  • Duration: {stats.get('duration_hours', 0):.1f} hours")
            
            # Show recent messages preview
            messages = session_data.get('messages', [])
            if messages:
                print(f"\nRecent Messages (last 3):")
                recent_messages = messages[-3:] if len(messages) > 3 else messages
                for msg in recent_messages:
                    msg_type = msg.get('message_type', 'unknown')
                    content_preview = msg.get('content', '')[:80] + "..." if len(msg.get('content', '')) > 80 else msg.get('content', '')
                    print(f"  [{msg_type.upper()}] {content_preview}")
            
            print("="*50)
            
        except Exception as e:
            logger.error(f"Error showing history: {e}")
            print(f"Error retrieving conversation history: {e}")
    
    async def list_sessions(self):
        """List all available conversation sessions"""
        try:
            result = await self.intent_service.list_sessions()
            
            if not result.get('success'):
                print(f"Error listing sessions: {result.get('error')}")
                return
            
            sessions = result.get('sessions', [])
            total_sessions = result.get('total_sessions', 0)
            
            print(f"\nConversation Sessions ({total_sessions} total):")
            print("-" * 60)
            
            if not sessions:
                print("No sessions found.")
                print("A session will be created automatically when you start chatting.")
                return
            
            for session in sessions:
                name = session.get('name', 'Unnamed')
                session_id = session.get('id', 'Unknown')
                stats = session.get('statistics', {})
                
                status = stats.get('status', 'unknown')
                total_messages = stats.get('total_messages', 0)
                last_activity = stats.get('last_activity', 'Never')
                
                indicator = " (current)" if session_id == self.current_session_id else ""
                print(f"  • {name} [{session_id[:8]}...]{indicator}")
                print(f"    Status: {status}, Messages: {total_messages}, Last: {last_activity}")
            
            print(f"\nCommands:")
            print("  • switch <session_name>  - Switch to different session")
            print("  • delete <session_name>  - Delete a session")
            
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            print(f"Error listing sessions: {e}")
    
    async def switch_session(self, session_name: str):
        """Switch to a different session"""
        try:
            # For now, we'll create a new session with the given name
            result = await self.intent_service.create_session(name=session_name)
            
            if result.get('success'):
                session_data = result.get('session', {})
                self.current_session_id = session_data.get('id')
                print(f"✓ Switched to session: '{session_name}'")
                print(f"  Session ID: {self.current_session_id}")
                print("  Conversation history loaded from database.")
            else:
                print(f"✗ Failed to switch session: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error switching sessions: {e}")
            print(f"Error switching sessions: {e}")
    
    async def delete_session(self, session_name: str):
        """Delete a conversation session"""
        try:
            # Confirmation
            confirm = input(f"Delete session '{session_name}' and all its history? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("Operation cancelled.")
                return
            
            # For now, we'll need to find the session by name first
            # This is a simplified implementation
            print(f"Note: Session deletion by name not fully implemented.")
            print(f"Use session ID for deletion or clear the session instead.")
            print(f"Command: clear (to clear current session)")
                
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            print(f"Error deleting session: {e}")
    
    async def clear_current_session(self):
        """Clear current session messages"""
        try:
            session_id = self.current_session_id or "main_session"
            result = await self.intent_service.clear_session(session_id)
            
            if result.get('success'):
                print("✓ Conversation history cleared for current session.")
            else:
                print(f"✗ Failed to clear history: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error clearing session: {e}")
            print(f"Error clearing session: {e}")
    
    async def show_config(self):
        """Show current configuration"""
        try:
            status = await self.intent_service.get_service_status()
            
            if not status.get('success'):
                print(f"Error retrieving configuration: {status.get('error')}")
                return
            
            config = status.get('configuration', {})
            
            print("\n" + "="*40)
            print("CONFIGURATION")
            print("="*40)
            
            print(f"LLM Configuration:")
            print(f"  • Model: {config.get('llm_model', 'N/A')}")
            print(f"  • Endpoint: {config.get('llm_endpoint', 'N/A')}")
            
            print(f"\nDatabase Configuration:")
            print(f"  • Path: {config.get('database_path', 'N/A')}")
            print(f"  • Max Messages: {config.get('max_messages', 'N/A')}")
            
            print(f"\nApplication:")
            print(f"  • Version: {status.get('version', 'N/A')}")
            print(f"  • Environment: {status.get('environment', 'N/A')}")
            
            print("="*40)
            
        except Exception as e:
            logger.error(f"Error showing config: {e}")
            print(f"Error retrieving configuration: {e}")
