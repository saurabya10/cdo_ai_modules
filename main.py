# -*- coding: utf-8 -*-
"""
Main CLI Interface for Intent Analysis System with SQLite Conversation Persistence
"""
import asyncio
import signal
import sys
from pathlib import Path
import logging
from intent_analysis_server import IntentAnalysisServer, create_intent_analysis_server

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


class IntentAnalysisCLI:
    """Command Line Interface for Intent Analysis System"""
    
    def __init__(self):
        self.server = create_intent_analysis_server()
        self.running = False
    
    def _show_help(self):
        """Display help information"""
        help_text = """
Intent Analysis System - Command Help
====================================

Available Commands:
  help, h          - Show this help message
  quit, exit, q    - Exit the application
  status           - Show server and session status
  history          - Show conversation history summary
  clear            - Clear current session history
  sessions         - List all conversation sessions
  switch <name>    - Switch to a specific session
  delete <name>    - Delete a conversation session

System Features:
  ✓ Intent Analysis    - Automatically classifies user messages
  ✓ Conversation Memory - Persistent SQLite storage across restarts
  ✓ Context Awareness  - Responses consider conversation history
  ✓ Session Management - Multiple isolated conversation contexts

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
    
    def _show_conversation_summary(self):
        """Show detailed conversation summary"""
        try:
            summary = self.server.get_session_summary()
            
            if not summary.get('success'):
                print(f"Error retrieving summary: {summary.get('error')}")
                return
            
            print("\n" + "="*60)
            print("CONVERSATION SUMMARY")
            print("="*60)
            
            # Current session stats
            session_stats = summary.get('session_stats', {})
            print(f"Current Session: {session_stats.get('session_id', 'Unknown')}")
            print(f"Total Messages: {session_stats.get('total_messages', 0)}")
            print(f"  • User Messages: {session_stats.get('user_messages', 0)}")
            print(f"  • AI Messages: {session_stats.get('ai_messages', 0)}")
            
            # Database information
            print(f"\nPersistent Storage:")
            print(f"  • Database: {session_stats.get('db_path', 'N/A')}")
            print(f"  • Max Messages/Session: {session_stats.get('max_messages', 'N/A')}")
            print(f"  • Storage Type: SQLite (survives restarts)")
            
            # Session timeline
            if session_stats.get('first_message'):
                print(f"\nSession Timeline:")
                print(f"  • First Message: {session_stats.get('first_message')}")
            if session_stats.get('last_message'):
                print(f"  • Last Message: {session_stats.get('last_message')}")
            
            # All sessions info
            total_sessions = summary.get('total_sessions', 0)
            print(f"\nSession Management:")
            print(f"  • Total Sessions: {total_sessions}")
            print(f"  • Current Session: {summary.get('current_session', 'N/A')}")
            
            # Supported capabilities
            supported_intents = summary.get('supported_intents', [])
            print(f"\nSupported Intent Categories ({len(supported_intents)}):")
            for intent in supported_intents:
                print(f"  • {intent}")
            
            print("="*60)
            
        except Exception as e:
            logger.error(f"Error showing conversation summary: {str(e)}")
            print(f"Error retrieving conversation summary: {str(e)}")
    
    def _list_sessions(self):
        """List all available conversation sessions"""
        try:
            result = self.server.list_sessions()
            
            if not result.get('success'):
                print(f"Error listing sessions: {result.get('error')}")
                return
            
            sessions = result.get('sessions', [])
            current_session = result.get('current_session')
            total_sessions = result.get('total_sessions', 0)
            
            print(f"\nConversation Sessions ({total_sessions} total):")
            print("-" * 50)
            
            if not sessions:
                print("No sessions found.")
                print("A session will be created automatically when you start chatting.")
                return
            
            for session in sessions:
                indicator = " (current)" if session == current_session else ""
                print(f"  • {session}{indicator}")
            
            print(f"\nCurrent Active Session: {current_session}")
            print("Commands:")
            print("  • switch <session_name>  - Switch to different session")
            print("  • delete <session_name>  - Delete a session")
            
        except Exception as e:
            logger.error(f"Error listing sessions: {str(e)}")
            print(f"Error listing sessions: {str(e)}")
    
    def _switch_session(self, session_name: str):
        """Switch to a different session"""
        try:
            result = self.server.switch_session(session_name)
            
            if result.get('success'):
                print(f"✓ Switched to session: '{session_name}'")
                if result.get('old_session'):
                    print(f"  Previous session: '{result.get('old_session')}'")
                print("  Conversation history loaded from SQLite database.")
            else:
                print(f"✗ Failed to switch session: {result.get('error')}")
                print("  Note: New sessions are created automatically when you chat.")
                
        except Exception as e:
            logger.error(f"Error switching sessions: {str(e)}")
            print(f"Error switching sessions: {str(e)}")
    
    def _delete_session(self, session_name: str):
        """Delete a conversation session"""
        try:
            # Confirmation
            confirm = input(f"Delete session '{session_name}' and all its history? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("Operation cancelled.")
                return
            
            result = self.server.delete_session(session_name)
            
            if result.get('success'):
                print(f"✓ Deleted session: '{session_name}'")
                print("  All conversation history for this session has been removed.")
            else:
                print(f"✗ Failed to delete session: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")
            print(f"Error deleting session: {str(e)}")
    
    def _show_status(self):
        """Display comprehensive server status"""
        try:
            status = self.server.get_server_status()
            
            if not status.get('success'):
                print(f"Error retrieving status: {status.get('error')}")
                return
            
            print("\n" + "="*50)
            print("INTENT ANALYSIS SERVER STATUS")
            print("="*50)
            
            # Server info
            print(f"Status: {status.get('server_status', 'Unknown').upper()}")
            print(f"Mode: {status.get('mode', 'Unknown')}")
            print(f"Version: {status.get('version', 'Unknown')}")
            
            # Configuration
            config = status.get('configuration', {})
            print(f"\nConfiguration:")
            print(f"  • Config File: {config.get('config_path', 'N/A')}")
            print(f"  • Database: {config.get('database_path', 'N/A')}")
            print(f"  • Max Messages: {config.get('max_messages', 'N/A')}")
            
            # Session info
            session_info = status.get('session_info', {})
            print(f"\nSession Information:")
            print(f"  • Current Session: {session_info.get('current_session', 'N/A')}")
            print(f"  • Total Sessions: {session_info.get('total_sessions', 0)}")
            
            current_stats = session_info.get('current_session_stats', {})
            if current_stats:
                print(f"  • Current Session Messages: {current_stats.get('total_messages', 0)}")
            
            # Capabilities
            capabilities = status.get('capabilities', [])
            print(f"\nSystem Capabilities:")
            for cap in capabilities:
                print(f"  ✓ {cap.replace('_', ' ').title()}")
            
            # Supported intents
            intents = status.get('supported_intents', [])
            if intents:
                print(f"\nSupported Intents ({len(intents)}):")
                for intent in intents[:5]:  # Show first 5
                    print(f"  • {intent}")
                if len(intents) > 5:
                    print(f"  • ... and {len(intents) - 5} more")
            
            print(f"\nLast Updated: {status.get('timestamp', 'N/A')}")
            print("="*50)
            
        except Exception as e:
            logger.error(f"Error showing status: {str(e)}")
            print(f"Error retrieving status: {str(e)}")
    
    async def run_interactive(self):
        """Run interactive CLI session"""
        self.running = True
        
        print("Intent Analysis System - Interactive Mode")
        print("=========================================")
        print("✓ SQLite conversation persistence enabled")
        print("✓ Context-aware intent analysis active")
        print("Type 'help' for commands or 'quit' to exit")
        print("-" * 50)
        
        try:
            while self.running:
                try:
                    user_input = input("\n> ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Handle special commands
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        print("Goodbye! Your conversation has been saved to SQLite database.")
                        break
                    elif user_input.lower() in ['help', 'h']:
                        self._show_help()
                    elif user_input.lower() == 'status':
                        self._show_status()
                    elif user_input.lower() == 'history':
                        self._show_conversation_summary()
                    elif user_input.lower() == 'clear':
                        result = self.server.clear_current_session()
                        if result.get('success'):
                            print("✓ Conversation history cleared for current session.")
                        else:
                            print(f"✗ Failed to clear history: {result.get('error')}")
                    elif user_input.lower() == 'sessions':
                        self._list_sessions()
                    elif user_input.lower().startswith('switch '):
                        session_name = user_input[7:].strip()
                        if session_name:
                            self._switch_session(session_name)
                        else:
                            print("Usage: switch <session_name>")
                    elif user_input.lower().startswith('delete '):
                        session_name = user_input[7:].strip()
                        if session_name:
                            self._delete_session(session_name)
                        else:
                            print("Usage: delete <session_name>")
                    else:
                        # Process user input through intent analysis server
                        result = await self.server.process_user_input(user_input)
                        
                        if result.get('success'):
                            # Show response
                            print(f"\n{result.get('response', 'No response')}")
                            
                            # Show intent analysis (optional debug info)
                            intent_analysis = result.get('intent_analysis', {})
                            if intent_analysis:
                                confidence = intent_analysis.get('confidence', 0)
                                category = intent_analysis.get('category', 'unknown')
                                
                                # Show intent info for low confidence or unclear intents
                                if confidence < 0.8:
                                    print(f"\n[Intent: {category}, Confidence: {confidence:.2f}]")
                        else:
                            print(f"\nError: {result.get('error', 'Unknown error')}")
                
                except KeyboardInterrupt:
                    print("\nUse 'quit' to exit gracefully and save conversation.")
                except Exception as e:
                    logger.error(f"Error in interactive mode: {str(e)}")
                    print(f"Error: {str(e)}")
        
        finally:
            self.running = False
    
    async def process_single_request(self, request: str):
        """Process a single request and return result"""
        try:
            result = await self.server.process_user_input(request)
            return result
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return {'success': False, 'error': str(e)}


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print("\nShutting down gracefully... Conversation saved to SQLite.")
    sys.exit(0)


async def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    cli = IntentAnalysisCLI()
    
    if len(sys.argv) > 1:
        # Process command line arguments
        if sys.argv[1] == "interactive":
            await cli.run_interactive()
        elif sys.argv[1] == "process":
            if len(sys.argv) > 2:
                request = " ".join(sys.argv[2:])
                result = await cli.process_single_request(request)
                if result.get('success'):
                    print(result.get('response', ''))
                    
                    # Show intent analysis in CLI mode
                    intent_analysis = result.get('intent_analysis', {})
                    if intent_analysis:
                        print(f"\n[Intent: {intent_analysis.get('category', 'unknown')} "
                              f"(confidence: {intent_analysis.get('confidence', 0):.2f})]")
                else:
                    print(f"Error: {result.get('error', '')}")
                    sys.exit(1)
            else:
                print("Usage: python main.py process '<your message>'")
                sys.exit(1)
        elif sys.argv[1] == "status":
            # Show status and exit
            cli._show_status()
        elif sys.argv[1] == "sessions":
            # List sessions and exit
            cli._list_sessions()
        elif sys.argv[1] == "help":
            # Show help and exit
            cli._show_help()
        else:
            # Process as single message
            request = " ".join(sys.argv[1:])
            result = await cli.process_single_request(request)
            if result.get('success'):
                print(result.get('response', ''))
            else:
                print(f"Error: {result.get('error', '')}")
                sys.exit(1)
    else:
        # Default to interactive mode
        await cli.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())