# Intent Analysis System

A focused system for analyzing user intent using LLM and maintaining conversation history in SQLite database.

## 🚀 Features

- **Intent Analysis**: Classifies user input into 6 predefined categories using LLM
- **Chat History**: Persistent SQLite storage with configurable conversation limits
- **Easy Extension**: Simple design to add/modify intents
- **Comprehensive Testing**: Full test suite included
- **Configuration**: Environment-based configuration with defaults

## 📁 Project Structure

```
cdo_ai_modules/
├── main.py                    # Main application entry point
├── config/                    # Configuration management
│   ├── __init__.py
│   └── settings.py           # Config loading and validation (with .env support)
├── core/                     # Core functionality
│   ├── __init__.py
│   └── chat_history.py       # SQLite chat history management
├── services/                 # Business logic
│   ├── __init__.py
│   └── intent_analyzer.py    # LLM-based intent analysis
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_chat_history.py
│   └── test_intent_analyzer.py
├── run_tests.py              # Test runner
├── env.example               # Environment variables template
├── .env                      # Your environment variables (create from env.example)
├── config.json               # Configuration file (auto-created)
├── chat_history.db           # SQLite database (auto-created)
├── intent_analysis.log       # Application logs
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🎯 Supported Intents

1. **file_read** - Reading, analyzing, or searching in CSV/text files
2. **dynamodb_query** - Querying or searching DynamoDB tables
3. **scc_query** - Querying Cisco Security Cloud Control for firewall devices
4. **rest_api** - Making REST API calls to external endpoints
5. **sal_troubleshoot** - Troubleshooting SAL event streaming from firewall devices
6. **general_chat** - General conversation or questions not requiring specific tools

## ⚙️ Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

**Option A: Create a `.env` file (Recommended):**
```bash
# Copy the example file and edit with your credentials
cp env.example .env
# Then edit .env with your actual values
```

Or create manually:
```bash
# Create .env file in project root
cat > .env << 'EOF'
CLIENT_ID=your_azure_client_id
CLIENT_SECRET=your_azure_client_secret
APP_KEY=your_app_key

# Optional configurations
LLM_ENDPOINT=https://your-llm-endpoint.com
DB_PATH=custom_chat_history.db
MAX_CONVERSATIONS=50
EOF
```

**Option B: Set environment variables directly:**
```bash
export CLIENT_ID=your_azure_client_id
export CLIENT_SECRET=your_azure_client_secret
export APP_KEY=your_app_key
```

### 3. Run the Application
```bash
python3 main.py
```

## 🎮 Usage

### Interactive Mode
The application runs in interactive mode by default. Simply type your messages and the system will:
1. Analyze the intent of your message
2. Display the result with confidence score
3. Store the conversation in SQLite database
4. Remember previous conversations (default: 25 conversations)

### Special Commands
- `quit` / `exit` / `q` - Exit the application
- `history` / `hist` / `h` - Show recent conversation history
- `clear` / `cls` - Clear all conversation history
- `summary` / `stats` - Show conversation statistics

### Sample Prompts for Testing

#### File Operations (file_read)
```
Read the sales data from report.csv
Analyze the customer data in users.txt
Search for errors in the application log file
Parse the JSON configuration file
```

#### Database Operations (dynamodb_query)
```
Find user with ID 12345 in the user table
Query the orders table for purchases from last week
Search for items in the inventory database
Get all records from the customer table
```

#### Security Operations (scc_query)
```
List all firewall devices
Find firewall device named Paradise
Show me the security policies
Get device status for all firewalls
```

#### API Operations (rest_api)
```
Call the API endpoint https://api.example.com/users
Make a GET request to the weather API
Send POST data to the webhook
Fetch data from the external service
```

#### Troubleshooting (sal_troubleshoot)
```
Find firewall device Paradise and check if it's sending events to SAL
Check if all devices are sending events
When was the last event sent for device Paradise
Troubleshoot event streaming issues
```

#### General Chat (general_chat)
```
Hello, how are you today?
What's the weather like?
Tell me a joke
How does machine learning work?
```

## 🧪 Running Tests

### Run All Tests
```bash
python3 run_tests.py
```

### Run Individual Test Files
```bash
python3 -m unittest tests.test_config
python3 -m unittest tests.test_chat_history
python3 -m unittest tests.test_intent_analyzer
```

## 🔧 Extending the System

### Adding New Intents
The system is designed for easy extension. To add new intents:

1. **Edit `services/intent_analyzer.py`**:
```python
# Add to INTENTS dictionary
INTENTS = {
    # ... existing intents ...
    "new_intent": "Description of the new intent"
}

# Add examples to INTENT_EXAMPLES
INTENT_EXAMPLES = {
    # ... existing examples ...
    "new_intent": [
        "Example phrase 1",
        "Example phrase 2"
    ]
}
```

2. **Update fallback classification if needed**:
```python
def _fallback_classification(self, user_input: str, llm_response: str):
    # Add keywords for new intent
    for intent, keywords in {
        # ... existing mappings ...
        'new_intent': ['keyword1', 'keyword2', 'keyword3']
    }.items():
```
