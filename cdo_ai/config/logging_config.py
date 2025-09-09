"""
Logging configuration setup
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from .settings import LoggingConfig


def setup_logging(config: Optional[LoggingConfig] = None) -> None:
    """
    Setup logging configuration
    
    Args:
        config: Logging configuration. If None, uses default settings.
    """
    if config is None:
        config = LoggingConfig()
    
    # Create logs directory if it doesn't exist
    log_file = Path(config.file_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level.upper(), logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(config.format)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        config.file_path,
        maxBytes=config.max_file_size,
        backupCount=config.backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, config.level.upper(), logging.INFO))
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    logging.info(f"Logging configured: level={config.level}, file={config.file_path}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)
