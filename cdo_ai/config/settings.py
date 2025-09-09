"""
Configuration settings management with environment variable support
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

from ..exceptions import ConfigurationError, MissingConfigurationError


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    path: str = "intent_conversations.db"
    max_messages: int = 100
    backup_enabled: bool = True
    connection_timeout: int = 30
    
    def __post_init__(self):
        # Ensure database directory exists
        db_path = Path(self.path)
        db_path.parent.mkdir(parents=True, exist_ok=True)


@dataclass 
class LLMConfig:
    """LLM service configuration"""
    endpoint: str = "https://chat-ai.cisco.com"
    client_id: str = ""
    client_secret: str = ""
    app_key: str = ""
    model: str = "gpt-4o"
    api_version: str = "2025-04-01-preview"
    timeout: int = 30
    max_retries: int = 3
    
    # Intent analysis specific settings
    intent_temperature: float = 0.1
    intent_max_tokens: int = 500
    confidence_threshold: float = 0.7
    
    # Response generation settings
    response_temperature: float = 0.3
    response_max_tokens: int = 1500
    
    def __post_init__(self):
        if not self.client_id:
            raise MissingConfigurationError("CLIENT_ID")
        if not self.client_secret:
            raise MissingConfigurationError("CLIENT_SECRET")
        if not self.app_key:
            raise MissingConfigurationError("APP_KEY")


@dataclass
class SessionConfig:
    """Session management configuration"""
    default_session: str = "main_session"
    timeout_hours: int = 24
    auto_cleanup: bool = True
    max_sessions: int = 100


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    file_path: str = "intent_analysis.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class Settings:
    """Main application settings"""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Application metadata
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Settings':
        """Create Settings from dictionary"""
        return cls(
            database=DatabaseConfig(**data.get("database", {})),
            llm=LLMConfig(**data.get("llm", {})),
            session=SessionConfig(**data.get("session", {})),
            logging=LoggingConfig(**data.get("logging", {})),
            version=data.get("version", "1.0.0"),
            environment=data.get("environment", "development"),
            debug=data.get("debug", False)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Settings to dictionary"""
        return {
            "database": {
                "path": self.database.path,
                "max_messages": self.database.max_messages,
                "backup_enabled": self.database.backup_enabled,
                "connection_timeout": self.database.connection_timeout
            },
            "llm": {
                "endpoint": self.llm.endpoint,
                "model": self.llm.model,
                "api_version": self.llm.api_version,
                "timeout": self.llm.timeout,
                "max_retries": self.llm.max_retries,
                "intent_temperature": self.llm.intent_temperature,
                "intent_max_tokens": self.llm.intent_max_tokens,
                "confidence_threshold": self.llm.confidence_threshold,
                "response_temperature": self.llm.response_temperature,
                "response_max_tokens": self.llm.response_max_tokens
            },
            "session": {
                "default_session": self.session.default_session,
                "timeout_hours": self.session.timeout_hours,
                "auto_cleanup": self.session.auto_cleanup,
                "max_sessions": self.session.max_sessions
            },
            "logging": {
                "level": self.logging.level,
                "file_path": self.logging.file_path,
                "max_file_size": self.logging.max_file_size,
                "backup_count": self.logging.backup_count,
                "format": self.logging.format
            },
            "version": self.version,
            "environment": self.environment,
            "debug": self.debug
        }


def load_environment_variables() -> Dict[str, Any]:
    """Load configuration from environment variables"""
    config = {}
    
    # LLM configuration
    llm_config = {}
    if os.getenv("CLIENT_ID"):
        llm_config["client_id"] = os.getenv("CLIENT_ID")
    if os.getenv("CLIENT_SECRET"):
        llm_config["client_secret"] = os.getenv("CLIENT_SECRET")
    if os.getenv("APP_KEY"):
        llm_config["app_key"] = os.getenv("APP_KEY")
    if os.getenv("LLM_ENDPOINT"):
        llm_config["endpoint"] = os.getenv("LLM_ENDPOINT")
    if os.getenv("LLM_MODEL"):
        llm_config["model"] = os.getenv("LLM_MODEL")
    
    if llm_config:
        config["llm"] = llm_config
    
    # Database configuration
    db_config = {}
    if os.getenv("DB_PATH"):
        db_config["path"] = os.getenv("DB_PATH")
    if os.getenv("DB_MAX_MESSAGES"):
        try:
            db_config["max_messages"] = int(os.getenv("DB_MAX_MESSAGES"))
        except ValueError:
            pass
    
    if db_config:
        config["database"] = db_config
    
    # Logging configuration
    logging_config = {}
    if os.getenv("LOG_LEVEL"):
        logging_config["level"] = os.getenv("LOG_LEVEL")
    if os.getenv("LOG_FILE"):
        logging_config["file_path"] = os.getenv("LOG_FILE")
    
    if logging_config:
        config["logging"] = logging_config
    
    # Application configuration
    if os.getenv("ENVIRONMENT"):
        config["environment"] = os.getenv("ENVIRONMENT")
    if os.getenv("DEBUG"):
        config["debug"] = os.getenv("DEBUG").lower() in ("true", "1", "yes")
    
    return config


def load_config_file(config_path: str = "chat_config.json") -> Dict[str, Any]:
    """Load configuration from JSON file"""
    config_file = Path(config_path)
    
    if not config_file.exists():
        return {}
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        raise ConfigurationError(f"Failed to load config file {config_path}: {e}")


def create_default_config_file(config_path: str = "chat_config.json") -> None:
    """Create default configuration file"""
    default_settings = Settings()
    config_file = Path(config_path)
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_settings.to_dict(), f, indent=2)
    except IOError as e:
        raise ConfigurationError(f"Failed to create config file {config_path}: {e}")


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple configuration dictionaries"""
    merged = {}
    
    for config in configs:
        for key, value in config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = merge_configs(merged[key], value)
            else:
                merged[key] = value
    
    return merged


def load_config(config_path: str = "chat_config.json") -> Settings:
    """
    Load configuration from multiple sources in order of precedence:
    1. Environment variables (highest priority)
    2. Configuration file
    3. Defaults (lowest priority)
    """
    # Load from different sources
    env_config = load_environment_variables()
    
    # Create default config file if it doesn't exist
    if not Path(config_path).exists():
        create_default_config_file(config_path)
    
    file_config = load_config_file(config_path)
    
    # Merge configurations (env variables override file config)
    final_config = merge_configs(file_config, env_config)
    
    return Settings.from_dict(final_config)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings(config_path: str = "chat_config.json") -> Settings:
    """Get global settings instance (singleton pattern)"""
    global _settings
    
    if _settings is None:
        _settings = load_config(config_path)
    
    return _settings


def reload_settings(config_path: str = "chat_config.json") -> Settings:
    """Reload settings from configuration sources"""
    global _settings
    _settings = None
    return get_settings(config_path)
