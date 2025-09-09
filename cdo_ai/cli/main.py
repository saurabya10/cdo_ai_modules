"""
Main CLI application for CDO AI Modules
Production-ready with comprehensive error handling and logging
"""

import asyncio
import signal
import sys
import logging
from typing import Optional, Dict, Any

from ..config import setup_logging, get_settings
from ..services.intent_service import IntentAnalysisService
from ..exceptions import CDOAIError
from .commands import CLICommands

logger = logging.getLogger(__name__)


class CDOAIApplication:
    """
    Main CLI application for CDO AI Modules with production-ready features
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.intent_service: Optional[IntentAnalysisService] = None
        self.cli_commands: Optional[CLICommands] = None
        self.running = False
        
        # Setup logging
        setup_logging(self.settings.logging)
        
        logger.info(f"CDO AI Application initialized (version {self.settings.version})")
    
    async def initialize(self):
        """Initialize application services"""
        try:
            logger.info("Initializing application services...")
            
            # Initialize intent service
            self.intent_service = IntentAnalysisService(self.settings)
            
            # Initialize CLI commands
            self.cli_commands = CLICommands(self.intent_service)
            
            logger.info("Application services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            raise
    
    async def run_interactive(self):
        """Run interactive CLI mode"""
        if not self.intent_service or not self.cli_commands:
            await self.initialize()
        
        self.running = True
        
        # Display welcome message
        await self._show_welcome()
        
        try:
            while self.running:
                try:
                    user_input = input("\n> ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Handle special commands
                    if await self._handle_special_commands(user_input):
                        continue
                    
                    # Process user input through intent analysis
                    result = await self.intent_service.process_user_input(user_input)
                    
                    if result.get('success'):
                        # Show response
                        response = result.get('response', 'No response generated')
                        print(f"\n{response}")
                        
                        # Show intent analysis (optional debug info)
                        if self.settings.debug:
                            intent_analysis = result.get('intent_analysis', {})
                            if intent_analysis:
                                confidence = intent_analysis.get('confidence', 0)
                                category = intent_analysis.get('category', 'unknown')
                                print(f"\n[Debug] Intent: {category}, Confidence: {confidence:.2f}")
                    else:
                        error_msg = result.get('error', 'Unknown error occurred')
                        print(f"\nError: {error_msg}")
                        
                        if self.settings.debug:
                            error_code = result.get('error_code')
                            if error_code:
                                print(f"[Debug] Error Code: {error_code}")
                
                except KeyboardInterrupt:
                    print("\nUse 'quit' to exit gracefully.")
                except EOFError:
                    print("\nGoodbye!")
                    break
                except Exception as e:
                    logger.error(f"Error in interactive mode: {e}")
                    print(f"An unexpected error occurred: {e}")
        
        finally:
            self.running = False
            await self._cleanup()
    
    async def _show_welcome(self):
        """Display welcome message and system status"""
        print("CDO AI Modules - Intent Analysis System")
        print("=" * 50)
        print(f"Version: {self.settings.version}")
        print(f"Environment: {self.settings.environment}")
        
        # Show system status
        try:
            status = await self.intent_service.health_check()
            if status.get("status") == "healthy":
                print("✓ System Status: Healthy")
                print("✓ SQLite conversation persistence enabled")
                print("✓ Context-aware intent analysis active")
            else:
                print("⚠ System Status: Degraded")
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            print("⚠ System Status: Unknown")
        
        print("\nType 'help' for commands or 'quit' to exit")
        print("-" * 50)
    
    async def _handle_special_commands(self, user_input: str) -> bool:
        """Handle special CLI commands"""
        command = user_input.lower()
        
        if command in ['quit', 'exit', 'q']:
            print("Goodbye! Your conversation has been saved.")
            self.running = False
            return True
        
        elif command in ['help', 'h']:
            await self.cli_commands.show_help()
            return True
        
        elif command == 'status':
            await self.cli_commands.show_status()
            return True
        
        elif command == 'history':
            await self.cli_commands.show_history()
            return True
        
        elif command == 'clear':
            await self.cli_commands.clear_current_session()
            return True
        
        elif command == 'sessions':
            await self.cli_commands.list_sessions()
            return True
        
        elif command.startswith('switch '):
            session_name = command[7:].strip()
            if session_name:
                await self.cli_commands.switch_session(session_name)
            else:
                print("Usage: switch <session_name>")
            return True
        
        elif command.startswith('delete '):
            session_name = command[7:].strip()
            if session_name:
                await self.cli_commands.delete_session(session_name)
            else:
                print("Usage: delete <session_name>")
            return True
        
        elif command == 'config':
            await self.cli_commands.show_config()
            return True
        
        elif command == 'debug':
            self.settings.debug = not self.settings.debug
            print(f"Debug mode: {'enabled' if self.settings.debug else 'disabled'}")
            return True
        
        return False
    
    async def process_single_request(self, request: str) -> Dict[str, Any]:
        """Process a single request and return result"""
        if not self.intent_service:
            await self.initialize()
        
        try:
            result = await self.intent_service.process_user_input(request)
            return result
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                'success': False, 
                'error': str(e),
                'error_code': 'PROCESSING_ERROR'
            }
    
    async def _cleanup(self):
        """Cleanup resources"""
        try:
            logger.info("Cleaning up application resources...")
            # Add any cleanup logic here
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            print("\nShutting down gracefully... Conversation saved.")
            self.running = False
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main entry point"""
    app = CDOAIApplication()
    app.setup_signal_handlers()
    
    if len(sys.argv) > 1:
        # Process command line arguments
        command = sys.argv[1]
        
        if command == "interactive":
            await app.run_interactive()
            
        elif command == "process":
            if len(sys.argv) > 2:
                request = " ".join(sys.argv[2:])
                result = await app.process_single_request(request)
                
                if result.get('success'):
                    print(result.get('response', ''))
                    
                    # Show intent analysis in CLI mode
                    intent_analysis = result.get('intent_analysis', {})
                    if intent_analysis:
                        category = intent_analysis.get('category', 'unknown')
                        confidence = intent_analysis.get('confidence', 0)
                        print(f"\n[Intent: {category} (confidence: {confidence:.2f})]")
                else:
                    print(f"Error: {result.get('error', '')}")
                    sys.exit(1)
            else:
                print("Usage: python -m cdo_ai process '<your message>'")
                sys.exit(1)
        
        elif command == "status":
            await app.initialize()
            await app.cli_commands.show_status()
        
        elif command == "sessions":
            await app.initialize()
            await app.cli_commands.list_sessions()
        
        elif command == "help":
            await app.initialize()
            await app.cli_commands.show_help()
        
        else:
            # Process as single message
            request = " ".join(sys.argv[1:])
            result = await app.process_single_request(request)
            
            if result.get('success'):
                print(result.get('response', ''))
            else:
                print(f"Error: {result.get('error', '')}")
                sys.exit(1)
    else:
        # Default to interactive mode
        await app.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())
