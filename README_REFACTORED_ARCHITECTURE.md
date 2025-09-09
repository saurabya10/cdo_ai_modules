# Intent Analysis System - Refactored Architecture

## 🎯 **Overview**

This is a production-grade **Intent Analysis System** with persistent SQLite conversation history. The system has been completely refactored to focus solely on intent analysis while maintaining clean, modular architecture with automatic conversation tracking.

## 🏗️ **Architecture**

### **Core Components**

```
Intent Analysis System
├── core/                          # Core framework modules
│   ├── chat_history_manager.py    # SQLite conversation persistence
│   ├── intent_analyzer.py         # Intent classification engine
│   ├── conversation_manager.py    # Orchestration layer
│   └── __init__.py                # Package exports
├── intent_analysis_server.py      # Main server implementation
├── main.py                        # CLI interface
└── chat_config.json               # Configuration file
```

### **Key Features**

✅ **Intent Analysis Only** - Clean focus on intent classification  
✅ **SQLite Persistence** - Automatic conversation history across restarts  
✅ **Session Management** - Multiple isolated conversation contexts  
✅ **Context Awareness** - Responses consider conversation history  
✅ **Automatic Tracking** - No manual conversation saving needed  
✅ **Production Architecture** - Proper separation of concerns  

## 🔧 **Quick Start**

### **Requirements**
- Python 3.7+ (tested with Python 3.12.4)
- LangChain and dependencies (see `requirements.txt`)
- Azure OpenAI access (configured via `settings.py`)

### **Installation**
```bash
# Use Python 3 (not Python 2.7)
python3 -m pip install -r requirements.txt
```

### **Usage Examples**

#### **Interactive Mode**
```bash
python3 main.py interactive
```

#### **Single Message Processing**
```bash
python3 main.py process "Hello, how are you?"
```

#### **Server Status**
```bash
python3 main.py status
```

#### **Session Management**
```bash
python3 main.py sessions
```

## 🎯 **Intent Categories**

The system supports 7 intent categories:

| Category | Description | Example |
|----------|-------------|---------|
| `greeting` | Conversation starters | "Hello, how are you?" |
| `question_answering` | Direct factual questions | "What is Python?" |
| `task_request` | Action requests | "Can you help me with X?" |
| `information_seeking` | Topic information | "Tell me about AI" |
| `clarification` | Explanation requests | "What did we discuss?" |
| `general_chat` | Casual conversation | "Thanks for your help!" |
| `goodbye` | Conversation endings | "Goodbye!" |

## 🗄️ **SQLite Database Schema**

```sql
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,           -- Conversation session
    message_type TEXT NOT NULL,         -- HumanMessage/AIMessage
    content TEXT NOT NULL,              -- Message content
    additional_kwargs TEXT DEFAULT '{}', -- JSON metadata
    timestamp TEXT NOT NULL,            -- ISO timestamp
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_session_created ON chat_messages(session_id, created_at);
```

## ⚙️ **Configuration**

**`chat_config.json`**:
```json
{
  "db_path": "intent_conversations.db",
  "max_messages": 100,
  "default_session": "main_session",
  "intent_analysis": {
    "temperature": 0.1,
    "confidence_threshold": 0.7
  },
  "response_generation": {
    "temperature": 0.3,
    "max_tokens": 1500
  }
}
```

## 🔍 **API Overview**

### **Core Classes**

#### **IntentAnalysisServer**
```python
from intent_analysis_server import create_intent_analysis_server

server = create_intent_analysis_server()
result = await server.process_user_input("Hello there!")
```

#### **ConversationManager** 
```python
from core.conversation_manager import create_conversation_manager

manager = create_conversation_manager()
result = await manager.process_message("What is AI?")
```

#### **ChatHistoryManager**
```python
from core.chat_history_manager import ChatHistoryManager

chat_history = ChatHistoryManager()
chat_history.add_exchange("Hi", "Hello!")
history = chat_history.get_conversation_context()
```

### **Response Format**

```python
{
    "success": True,
    "response": "Hello! How can I help you today?",
    "intent_analysis": {
        "category": "greeting",
        "confidence": 0.95,
        "reasoning": "Clear greeting with friendly tone",
        "entities": {},
        "follow_up_needed": False,
        "context_dependent": False
    },
    "session_id": "main_session",
    "conversation_tracked": True,
    "metadata": {
        "response_length": 35,
        "confidence": 0.95,
        "context_used": False
    }
}
```

## 🚀 **What Changed from Original**

### **Removed Components**
- ❌ All tool integrations (DynamoDB, SCC, File handling, REST API, SAL troubleshoot)
- ❌ Complex routing logic
- ❌ Multiple service dependencies
- ❌ Manual conversation tracking calls

### **New Components**
- ✅ Clean intent analysis focus
- ✅ Automatic SQLite conversation persistence
- ✅ Production-grade modular architecture  
- ✅ Context decorators for seamless integration
- ✅ Session-based conversation management
- ✅ Comprehensive error handling and logging

### **Architectural Improvements**
- 🏗️ **Separation of Concerns**: Each module has single responsibility
- 🔄 **Automatic Tracking**: No manual `add_to_conversation()` calls
- 💾 **Persistent Storage**: SQLite replaces volatile memory
- 🎯 **Focused Scope**: Intent analysis only (tools can be re-added later)
- 📊 **Production Ready**: Proper logging, error handling, configuration

## 🛠️ **Development**

### **Adding New Intent Categories**
```python
# In core/intent_analyzer.py
class IntentCategory(Enum):
    NEW_CATEGORY = "new_category"
```

### **Custom Session Logic**
```python
chat_history = ChatHistoryManager()
chat_history.switch_session("project_alpha")
```

### **Testing**
```bash
# Run built-in functionality test
python3 intent_analysis_server.py
```

## 📊 **Performance**

- **SQLite Operations**: ~1ms per message insert/retrieve
- **Intent Analysis**: ~2-3s per message (Azure OpenAI)
- **Memory Usage**: Minimal (history stored in SQLite)
- **Concurrency**: Thread-safe SQLite operations
- **Scalability**: Configurable message limits per session

## 🔮 **Future Extensions**

The current architecture supports easy extension:

1. **Tool Integration**: Add tool modules in `core/tools/`
2. **Custom Intents**: Extend `IntentCategory` enum
3. **Multiple LLMs**: Add provider abstraction layer
4. **API Server**: Add FastAPI wrapper around `IntentAnalysisServer`
5. **Analytics**: Add conversation analytics and reporting

## 💡 **Key Benefits**

1. **Clean Architecture**: Production-grade modular design
2. **Automatic Persistence**: No conversation data loss across restarts  
3. **Context Awareness**: Responses improve with conversation history
4. **Session Isolation**: Multiple conversation contexts
5. **Zero Manual Tracking**: Conversation automatically saved
6. **Intent Insights**: Understand user intent with confidence scores
7. **Easy Extension**: Add tools and features incrementally

---

**Ready to use with `python3 main.py interactive`** 🚀
