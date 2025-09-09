"""Storage-related exceptions"""

from .base import CDOAIError


class StorageError(CDOAIError):
    """Base exception for storage-related errors"""
    
    def __init__(self, message: str, storage_type: str = None):
        super().__init__(
            message,
            error_code="STORAGE_ERROR",
            details={"storage_type": storage_type} if storage_type else {}
        )
        self.storage_type = storage_type


class DatabaseError(StorageError):
    """Raised when database operations fail"""
    
    def __init__(self, message: str, operation: str = None, table: str = None):
        super().__init__(message, storage_type="database")
        self.error_code = "DATABASE_ERROR"
        if operation:
            self.details["operation"] = operation
        if table:
            self.details["table"] = table


class SessionNotFoundError(StorageError):
    """Raised when a conversation session is not found"""
    
    def __init__(self, session_id: str):
        super().__init__(
            f"Session not found: {session_id}",
            storage_type="session"
        )
        self.error_code = "SESSION_NOT_FOUND"
        self.details["session_id"] = session_id
        self.session_id = session_id


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails"""
    
    def __init__(self, message: str, database_path: str = None):
        super().__init__(message, operation="connect")
        self.error_code = "DB_CONNECTION_ERROR"
        if database_path:
            self.details["database_path"] = database_path
