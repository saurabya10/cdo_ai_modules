# CDO AI Modules - Intent Analysis System

A production-grade conversational AI system that provides intelligent intent analysis with persistent conversation history. Built with LangChain, SQLite persistence, and enterprise LLM integration.

## 🚀 Features

- **🧠 Intent Analysis**: Automatically classifies user messages into meaningful categories
- **💬 Conversational AI**: Context-aware responses that consider conversation history
- **💾 Persistent Memory**: SQLite-based storage that survives restarts
- **🔄 Session Management**: Multiple isolated conversation contexts
- **📊 Analytics**: Built-in conversation tracking and statistics
- **🎯 Context Awareness**: Responses consider previous interactions
- **🛠 CLI Interface**: Easy-to-use command-line interface

## 📋 Supported Intent Categories

- **general_chat** - Casual conversation and small talk
- **question_answering** - Direct factual questions
- **task_request** - Action requests and task assignments
- **information_seeking** - Topic information requests
- **clarification** - Explanation requests about previous content
- **greeting** - Conversation starters and introductions
- **goodbye** - Conversation endings and farewells

## 🛠 Installation & Setup

### Prerequisites

- Python 3.8+ (tested with Python 3.12.4)
- pip package manager

### 1. Clone the Repository

```bash
git clone <repository-url>
cd cdo_ai_modules
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration (Optional)

Copy the environment template and configure your settings:

```bash
cp env.template .env
# Edit .env with your API keys and configuration
```

**Required Environment Variables:**
- `CLIENT_ID` - Your LLM service client ID
- `CLIENT_SECRET` - Your LLM service client secret  
- `APP_KEY` - Your application key
- `LLM_ENDPOINT` - LLM service endpoint (default: https://chat-ai.cisco.com)

### 4. First Run

**New Modular Structure (Recommended):**
```bash
# Set required environment variables
export CLIENT_ID=your_client_id
export CLIENT_SECRET=your_client_secret
export APP_KEY=your_app_key

# Run the application
python3 main_new.py
```

**Legacy Structure:**
```bash
python3 main.py
```

The system will automatically:
- Initialize SQLite database (`intent_conversations.db`)
- Create default configuration (`chat_config.json`)
- Start in interactive mode

## 🎮 Usage

### Interactive Mode (Primary Usage)

**New Modular Structure (Recommended):**
```bash
python3 main_new.py
```

**Legacy Structure:**
```bash
python3 main.py
```

You'll see:
```
Intent Analysis System - Interactive Mode
=========================================
✓ SQLite conversation persistence enabled
✓ Context-aware intent analysis active
Type 'help' for commands or 'quit' to exit
--------------------------------------------------

> 
```

### Sample Conversation Demonstrating Features

Here's a sample conversation that showcases the conversational and chat history features:

```bash
> Hello there!
[Intent: greeting (confidence: 0.95)]
Hello! It's great to meet you. How can I help you today?

> What is machine learning?
[Intent: information_seeking (confidence: 0.92)]
Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed for every task...

> Can you give me a simple example?
[Intent: clarification (confidence: 0.88)]
Certainly! Since we were just discussing machine learning, here's a simple example: 
Email spam detection. Instead of programming rules for every possible spam email, you feed the system thousands of emails labeled as "spam" or "not spam"...

> That makes sense. What did we talk about before this example?
[Intent: clarification (confidence: 0.91)]
Before I gave you the email spam detection example, we were discussing machine learning in general. You had asked "What is machine learning?" and I explained that it's a subset of artificial intelligence that enables computers to learn from data...

> Thanks, that's helpful. Goodbye!
[Intent: goodbye (confidence: 0.94)]
You're very welcome! I'm glad I could help explain machine learning and provide that example. Feel free to come back anytime if you have more questions. Goodbye!
```

**Key Features Demonstrated:**
1. **Intent Classification** - Each message shows detected intent and confidence
2. **Context Awareness** - "Can you give me a simple example?" understands it's about ML
3. **Conversation Memory** - "What did we talk about before?" recalls previous discussion
4. **Persistent Storage** - All conversations are saved and can be resumed

### More Sample Prompts

**Testing Different Intent Categories:**

```bash
# Greeting
> Hi, how's it going?

# Question Answering  
> What's the capital of France?

# Task Request
> Can you help me plan a project timeline?

# Information Seeking
> Tell me about quantum computing

# Context-Dependent Clarification
> What do you mean by that?
> Can you explain the last point again?

# Conversation History Testing
> What was the first thing I asked you?
> Summarize our conversation so far
```

### Built-in Commands

While in interactive mode, use these commands:

```bash
> help           # Show all available commands
> status         # Display system and session status  
> history        # Show conversation summary
> sessions       # List all conversation sessions
> switch work    # Switch to "work" session
> clear          # Clear current session history
> delete old     # Delete "old" session
> quit           # Exit the application
```

### Command Line Usage

**Single Message Processing:**
```bash
# New modular structure
python3 main_new.py process "What is artificial intelligence?"

# Legacy structure  
python3 main.py process "What is artificial intelligence?"
```

**Quick Status Check:**
```bash
# New modular structure
python3 main_new.py status

# Legacy structure
python3 main.py status
```

**List All Sessions:**
```bash
# New modular structure
python3 main_new.py sessions

# Legacy structure
python3 main.py sessions
```

**Show Help:**
```bash
# New modular structure
python3 main_new.py help

# Legacy structure
python3 main.py help
```

## 🗃 Data Persistence

The system uses SQLite for conversation persistence:

- **Database File**: `intent_conversations.db`
- **Automatic Backups**: WAL mode enabled
- **Session Isolation**: Multiple conversation contexts
- **Conversation History**: Full message history with timestamps
- **Intent Tracking**: All intent analyses are stored

### Session Management

Create and manage multiple conversation sessions:

```bash
> sessions                    # List all sessions
> switch personal            # Switch to "personal" session  
> switch work               # Switch to "work" session
> delete old_project        # Delete unwanted session
```

Each session maintains its own conversation history and context.

## 📊 System Architecture

### New Modular Architecture (main_new.py)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI Interface │    │  Intent Analysis │    │ LLM Integration │
│   (cdo_ai.cli)  │───▶│     Service      │───▶│   Service       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ Storage Service  │    │ SQLite Database │
                       │ (cdo_ai.services)│───▶│ (Persistent)    │
                       └──────────────────┘    └─────────────────┘
```

**Production-Ready Components:**
- **CLI Module** (`cdo_ai.cli`) - Command-line interface with comprehensive commands
- **Intent Service** (`cdo_ai.services.intent_service`) - Main orchestration service
- **LLM Service** (`cdo_ai.services.llm_service`) - Enterprise LLM integration with error handling
- **Storage Service** (`cdo_ai.services.storage_service`) - SQLite persistence with proper indexing
- **Configuration System** (`cdo_ai.config`) - Environment-based configuration management
- **Exception Hierarchy** (`cdo_ai.exceptions`) - Comprehensive error handling
- **Data Models** (`cdo_ai.models`) - Type-safe data models with validation
- **Utilities** (`cdo_ai.utils`) - Validation, formatting, and helper functions

### Legacy Architecture (main.py)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI Interface │    │  Intent Analysis │    │ LLM Integration │
│   (main.py)     │───▶│     Server       │───▶│ (Cisco/Azure)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ Conversation     │    │ SQLite Database │
                       │ Manager          │───▶│ (Persistent)    │
                       └──────────────────┘    └─────────────────┘
```

**Legacy Components:**
- **Intent Analyzer** - Classifies user messages using LLM
- **Conversation Manager** - Orchestrates chat flow and context
- **Chat History Manager** - SQLite persistence layer
- **LLM Service** - Enterprise LLM integration

## 🔧 Configuration

### Default Configuration (`chat_config.json`)

```json
{
  "db_path": "intent_conversations.db",
  "max_messages": 100,
  "default_session": "main_session",
  "auto_backup": true,
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
```

### Environment Variables

```bash
# LLM Configuration
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
APP_KEY=your_app_key
LLM_ENDPOINT=https://chat-ai.cisco.com

# Optional Settings
LOG_LEVEL=INFO
AWS_REGION=us-east-1
```

## 📁 Project Structure

```
cdo_ai_modules/
├── main.py                    # CLI interface and entry point
├── intent_analysis_server.py  # Main server orchestrator
├── client.py                  # Legacy LLM client
├── settings.py               # Configuration management
├── core/                     # Core modules
│   ├── intent_analyzer.py    # Intent classification logic
│   ├── conversation_manager.py # Conversation orchestration
│   └── chat_history_manager.py # SQLite persistence
├── llm/                      # LLM integration
│   └── client.py            # LLM service client
├── requirements.txt          # Python dependencies
├── env.template             # Environment template
└── README.md               # This file
```

## 🐛 Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Make sure you're using Python 3
python3 main.py

# Install dependencies
pip install -r requirements.txt
```

**2. Database Permission Issues**
```bash
# Check file permissions
ls -la intent_conversations.db*

# Reset database (will lose history)
rm intent_conversations.db*
python3 main.py
```

**3. LLM Connection Issues**
- Verify your `.env` file has correct credentials
- Check network connectivity to LLM endpoint
- Review logs in `intent_analysis.log`

### Logging

Check the log file for detailed information:
```bash
tail -f intent_analysis.log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [LangChain](https://langchain.com/) for LLM orchestration
- Uses SQLite for reliable data persistence
- Integrates with enterprise LLM services
- Inspired by modern conversational AI patterns

---

**Need Help?** 
- Check the logs: `tail -f intent_analysis.log`
- Use the built-in help: `python3 main.py help`
- Review sample conversations above
- Open an issue for bugs or feature requests