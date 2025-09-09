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

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install SQLite (Required for Database)

> **Note:** Python includes the `sqlite3` module by default, but the SQLite binary may not be available on all systems (especially Windows). The application will work with Python's built-in module, but having the SQLite command-line tool is useful for database inspection and troubleshooting.

**On Windows:**
SQLite command-line tool is not included by default. Choose one of these options:

**Option A: Using Conda (Recommended)**
```bash
# If you have Anaconda/Miniconda installed
conda install sqlite
```

**Option B: Download SQLite Binary**
1. Download SQLite tools from: https://www.sqlite.org/download.html
2. Extract to a folder (e.g., `C:\sqlite`)
3. Add the folder to your system PATH

**Option C: Using Windows Subsystem for Linux (WSL)**
```bash
# Install WSL first, then in WSL terminal:
sudo apt update
sudo apt install sqlite3
```

**On macOS:**
```bash
# SQLite comes pre-installed, but you can update via Homebrew:
brew install sqlite
```

**On Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install sqlite3
```

**On Linux (CentOS/RHEL):**
```bash
sudo yum install sqlite
# or for newer versions:
sudo dnf install sqlite
```

**Verify Installation:**
```bash
sqlite3 --version
```

### 3. Set Environment Variables

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

### 4. Verify Setup (Optional)
Test that everything is working:
```bash
# Quick test - should show SQLite version
python3 -c "import sqlite3; print('SQLite version:', sqlite3.sqlite_version)"

# Run tests to verify functionality
python3 run_tests.py
```

### 5. Run the Application
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

## 🔧 Troubleshooting

### SQLite Issues

**Error: `sqlite3.OperationalError: no such table`**
- **Solution**: Delete the database file and restart the application:
```bash
rm chat_history.db
python3 main.py
```

**Error: `sqlite3.OperationalError: database is locked`**
- **Solution**: Close any SQLite browser tools and restart the application
- Or delete lock files:
```bash
rm chat_history.db-wal chat_history.db-shm
```

**Windows: `sqlite3` command not found**
- **Solution**: Follow the SQLite installation steps above for Windows
- **Alternative**: Use Python to inspect the database:
```bash
python3 -c "import sqlite3; conn = sqlite3.connect('chat_history.db'); print(conn.execute('SELECT * FROM conversations LIMIT 5').fetchall())"
```

### Authentication Issues

**Error: `401 Unauthorized`**
- **Solution**: Check your `.env` file credentials:
```bash
# Verify your .env file has correct values
cat .env
```
- Ensure `CLIENT_ID`, `CLIENT_SECRET`, and `APP_KEY` are correct
- Contact your admin for valid credentials

**Error: `Failed to get API key`**
- **Solution**: Verify network connectivity and credentials
- Check if your organization's firewall allows access to the LLM endpoint

### Configuration Issues

**Error: `Missing required configuration`**
- **Solution**: Ensure `.env` file exists and contains required variables
- Copy from template: `cp env.example .env`

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
