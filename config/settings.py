"""
Configuration settings for the intent analysis system
"""
import os
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class DatabaseConfig:
    """Database configuration"""
    path: str = "chat_history.db"
    max_conversations: int = 25


@dataclass
class LLMConfig:
    """LLM configuration"""
    endpoint: str = "https://chat-ai.cisco.com"
    client_id: str = ""
    client_secret: str = ""
    app_key: str = ""
    model: str = "gpt-4.1"
    api_version: str = "2025-04-01-preview"
    timeout: int = 30
    max_retries: int = 3
    temperature: float = 0.1
    max_tokens: int = 200


@dataclass
class Config:
    """Main configuration class"""
    database: DatabaseConfig
    llm: LLMConfig
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Config':
        """Create config from dictionary"""
        return cls(
            database=DatabaseConfig(**data.get('database', {})),
            llm=LLMConfig(**data.get('llm', {}))
        )
    
    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        return {
            'database': {
                'path': self.database.path,
                'max_conversations': self.database.max_conversations
            },
            'llm': {
                'endpoint': self.llm.endpoint,
                'model': self.llm.model,
                'api_version': self.llm.api_version,
                'timeout': self.llm.timeout,
                'max_retries': self.llm.max_retries,
                'temperature': self.llm.temperature,
                'max_tokens': self.llm.max_tokens
            }
        }


def load_config(config_file: str = "config.json") -> Config:
    """Load configuration from file and environment variables"""
    config_path = Path(config_file)
    
    # Default configuration
    config_data = {
        'database': {
            'path': 'chat_history.db',
            'max_conversations': 25
        },
        'llm': {
            'endpoint': 'https://chat-ai.cisco.com',
            'model': 'gpt-4o',
            'api_version': '2025-04-01-preview',
            'timeout': 30,
            'max_retries': 3,
            'temperature': 0.1,
            'max_tokens': 200
        }
    }
    
    # Load from file if exists
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                # Merge file config with defaults
                config_data.update(file_config)
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
    
    # Override with environment variables
    env_overrides = {
        'llm': {}
    }
    
    if os.getenv('CLIENT_ID'):
        env_overrides['llm']['client_id'] = os.getenv('CLIENT_ID')
    if os.getenv('CLIENT_SECRET'):
        env_overrides['llm']['client_secret'] = os.getenv('CLIENT_SECRET')
    if os.getenv('APP_KEY'):
        env_overrides['llm']['app_key'] = os.getenv('APP_KEY')
    if os.getenv('LLM_ENDPOINT'):
        env_overrides['llm']['endpoint'] = os.getenv('LLM_ENDPOINT')
    if os.getenv('DB_PATH'):
        env_overrides['database'] = {'path': os.getenv('DB_PATH')}
    if os.getenv('MAX_CONVERSATIONS'):
        try:
            max_conv = int(os.getenv('MAX_CONVERSATIONS'))
            env_overrides['database'] = env_overrides.get('database', {})
            env_overrides['database']['max_conversations'] = max_conv
        except ValueError:
            pass
    
    # Apply environment overrides
    for section, values in env_overrides.items():
        if values:
            config_data[section].update(values)
    
    # Create default config file if it doesn't exist
    if not config_path.exists():
        try:
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            print(f"Created default config file: {config_file}")
        except Exception as e:
            print(f"Warning: Could not create config file: {e}")
    
    return Config.from_dict(config_data)
