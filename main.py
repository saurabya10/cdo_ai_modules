#!/usr/bin/env python3
"""
Intent Analysis System
A focused system for analyzing user intent and maintaining chat history
"""
import asyncio
import logging
import sys
from pathlib import Path

from config import load_config
from agents.intent_agent import IntentAgent
from agents.rag_agent import RAGAgent
from services.embedding_service import EmbeddingService
from core import ChatHistory
from graph import AgentGraph

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('intent_analysis.log')
    ]
)

logger = logging.getLogger(__name__)


class AIAgentApp:
    """Main application for the AI Agent"""
    
    def __init__(self):
        """Initialize the application"""
        self.config = None
        self.intent_agent = None
        self.rag_agent = None
        self.chat_history = None
        self.embedding_service = None
        self.agent_graph = None
        self._initialize()
    
    def _initialize(self):
        """Initialize all components"""
        try:
            # Load configuration
            self.config = load_config()
            logger.info("Configuration loaded successfully")
            
            # Initialize chat history
            self.chat_history = ChatHistory(
                db_path=self.config.database.path,
                max_conversations=self.config.database.max_conversations
            )
            logger.info(f"Chat history initialized (max conversations: {self.config.database.max_conversations})")
            
            # Initialize intent agent
            self.intent_agent = IntentAgent(self.config)
            logger.info("Intent agent initialized")

            # Initialize EmbeddingService and create embeddings
            self.embedding_service = EmbeddingService(self.config)
            self.embedding_service.create_and_store_embeddings()
            logger.info("Embedding service initialized and embeddings created")
            
            # Initialize RAG agent
            retriever = self.embedding_service.get_retriever()
            self.rag_agent = RAGAgent(self.config, retriever)
            logger.info("RAG agent initialized")

            # Initialize AgentGraph
            self.agent_graph = AgentGraph(self.intent_agent, self.rag_agent)
            logger.info("Agent graph initialized")
            
            # Validate LLM credentials
            self._validate_credentials()
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            raise
    
    def _validate_credentials(self):
        """Validate that required LLM credentials are provided"""
        required_fields = ['client_id', 'client_secret', 'app_key']
        missing_fields = []
        
        for field in required_fields:
            if not getattr(self.config.llm, field):
                missing_fields.append(field.upper())
        
        if missing_fields:
            logger.error(f"Missing required LLM credentials: {', '.join(missing_fields)}")
            print(f"\n❌ Missing required environment variables: {', '.join(missing_fields)}")
            print("Please set the following environment variables:")
            for field in missing_fields:
                print(f"  export {field}=your_value_here")
            print("\nOr add them to your .env file")
            sys.exit(1)
    
    def display_welcome(self):
        """Display welcome message and system info"""
        print("\n" + "="*60)
        print("🧠 AI AGENT SYSTEM")
        print("="*60)
        print(f"📊 Max conversations stored: {self.config.database.max_conversations}")
        print(f"💾 Database: {self.config.database.path}")
        print(f"🤖 LLM Model: {self.config.llm.model}")
        
        # Show conversation summary
        summary = self.chat_history.get_conversation_summary()
        if summary.get('total_conversations', 0) > 0:
            print(f"📈 Total conversations: {summary['total_conversations']}")
            print(f"🎯 Average confidence: {summary['average_confidence']}")
            print("📋 Intent distribution:")
            for intent, count in summary.get('intent_distribution', {}).items():
                print(f"   • {intent}: {count}")
        else:
            print("📝 No previous conversations found")
        
        print("\n💡 Available intents:")
        for intent, description in self.intent_agent.get_available_intents().items():
            print(f"   • {intent}: {description}")
        
        print("\n" + "="*60)
        print("Type your message (or 'quit' to exit, 'history' to view recent conversations)")
        print("="*60)
    
    async def process_user_input(self, user_input: str) -> dict:
        """Process user input using the agent graph."""
        try:
            logger.info(f"Processing user input with AgentGraph: {user_input[:50]}...")
            result = await self.agent_graph.invoke(user_input)
            
            intent_result = result.get('intent', {})
            if intent_result.get('success'):
                # Store in chat history
                conversation_id = self.chat_history.add_conversation(
                    user_input=user_input,
                    intent_action=intent_result.get('action'),
                    intent_confidence=intent_result.get('confidence'),
                    intent_reasoning=intent_result.get('reasoning')
                )
                result['conversation_id'] = conversation_id
                logger.info(f"Stored conversation {conversation_id} with intent: {intent_result.get('action')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing user input with AgentGraph: {e}")
            return {
                'success': False,
                'error': str(e),
                'action': 'general_chat',
                'confidence': 0.0,
                'reasoning': f'Error: {str(e)}'
            }
    
    def display_result(self, result: dict):
        """Display the analysis result from the agent graph."""
        intent_result = result.get('intent', {})
        if intent_result.get('success'):
            confidence = intent_result.get('confidence', 0.0)
            action = intent_result.get('action', 'general_chat')
            reasoning = intent_result.get('reasoning', 'N/A')
            
            # Color coding based on confidence
            if confidence >= 0.8:
                confidence_indicator = "🟢"
            elif confidence >= 0.6:
                confidence_indicator = "🟡"
            else:
                confidence_indicator = "🔴"
            
            print(f"\n📊 INTENT ANALYSIS RESULT:")
            print(f"   🎯 Intent: {action}")
            print(f"   {confidence_indicator} Confidence: {confidence:.2f}")
            print(f"   💭 Reasoning: {reasoning}")
            
            if 'conversation_id' in result:
                print(f"   💾 Stored as conversation #{result['conversation_id']}")
        
        final_response = result.get('final_response')
        if final_response:
            print(f"\nAssistant: {final_response}")
        elif not intent_result.get('success'):
            print(f"\n❌ Analysis failed: {intent_result.get('error', 'Unknown error')}")
    
    def show_recent_history(self, limit: int = 5):
        """Show recent conversation history"""
        conversations = self.chat_history.get_recent_conversations(limit)
        
        if not conversations:
            print("\n📝 No conversation history found")
            return
        
        print(f"\n📚 RECENT CONVERSATIONS (last {len(conversations)}):")
        print("-" * 80)
        
        for conv in conversations:
            timestamp = conv['timestamp'][:19].replace('T', ' ')  # Format timestamp
            confidence_indicator = "🟢" if conv['intent_confidence'] >= 0.8 else "🟡" if conv['intent_confidence'] >= 0.6 else "🔴"
            
            print(f"#{conv['id']} | {timestamp}")
            print(f"   📝 Input: {conv['user_input'][:60]}{'...' if len(conv['user_input']) > 60 else ''}")
            print(f"   🎯 Intent: {conv['intent_action']} {confidence_indicator} ({conv['intent_confidence']:.2f})")
            print(f"   💭 Reasoning: {conv['intent_reasoning'][:80]}{'...' if len(conv['intent_reasoning']) > 80 else ''}")
            print("-" * 80)
    
    async def run(self):
        """Run the main application loop"""
        self.display_welcome()
        
        try:
            while True:
                try:
                    # Get user input
                    user_input = input("\n💬 Your message: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Handle special commands
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        print("\n👋 Goodbye! Your conversation history has been saved.")
                        break
                    elif user_input.lower() in ['history', 'hist', 'h']:
                        self.show_recent_history()
                        continue
                    elif user_input.lower() in ['clear', 'cls']:
                        try:
                            self.chat_history.clear_history()
                            print("\n🗑️ Chat history cleared successfully!")
                        except Exception as e:
                            print(f"\n❌ Failed to clear history: {e}")
                        continue
                    elif user_input.lower() in ['summary', 'stats']:
                        summary = self.chat_history.get_conversation_summary()
                        print(f"\n📊 CONVERSATION SUMMARY:")
                        print(f"   Total: {summary.get('total_conversations', 0)}")
                        print(f"   Avg Confidence: {summary.get('average_confidence', 0):.3f}")
                        print(f"   Intent Distribution: {summary.get('intent_distribution', {})}")
                        continue
                    
                    # Process the input
                    print("\n🤔 Analyzing intent...")
                    result = await self.process_user_input(user_input)
                    self.display_result(result)
                    
                except KeyboardInterrupt:
                    print("\n\n👋 Goodbye! Your conversation history has been saved.")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    print(f"\n❌ An error occurred: {e}")
                    
        except Exception as e:
            logger.error(f"Fatal error in main loop: {e}")
            print(f"\n💥 Fatal error: {e}")
            sys.exit(1)


async def main():
    """Main entry point"""
    try:
        app = AIAgentApp()
        await app.run()
    except KeyboardInterrupt:
        print("\n👋 Application interrupted by user")
    except Exception as e:
        logger.error(f"Application failed: {e}")
        print(f"\n💥 Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())