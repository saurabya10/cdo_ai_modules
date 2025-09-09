"""Configuration-related exceptions"""

from .base import CDOAIError


class ConfigurationError(CDOAIError):
    """Raised when there are configuration issues"""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(
            message, 
            error_code="CONFIG_ERROR",
            details={"config_key": config_key} if config_key else {}
        )
        self.config_key = config_key


class MissingConfigurationError(ConfigurationError):
    """Raised when required configuration is missing"""
    
    def __init__(self, config_key: str):
        super().__init__(
            f"Missing required configuration: {config_key}",
            config_key=config_key
        )
        self.error_code = "MISSING_CONFIG"


class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration values are invalid"""
    
    def __init__(self, config_key: str, expected_type: str = None, actual_value: str = None):
        details = {"config_key": config_key}
        if expected_type:
            details["expected_type"] = expected_type
        if actual_value:
            details["actual_value"] = actual_value
            
        message = f"Invalid configuration value for {config_key}"
        if expected_type:
            message += f" (expected {expected_type})"
            
        super().__init__(message, config_key=config_key)
        self.error_code = "INVALID_CONFIG"
        self.details.update(details)
