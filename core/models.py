"""Core data models and validation."""

from typing import Dict, List, Any, Optional, Union, Type, TypeVar, Generic, Callable
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum
from datetime import datetime
import uuid
import json
from pathlib import Path
import logging
from .config.config_loader import ConfigLoader

# Configure logging
logger = logging.getLogger("core.models")

# Type definitions
T = TypeVar("T")
ModelT = TypeVar("ModelT", bound="BaseModel")


# Common enums
class Status(str, Enum):
    """Common status enum for various models."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(int, Enum):
    """Priority levels for requests and tasks."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


# Base model for all core models
class CoreModel(BaseModel):
    """Base model for all core data models."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        """Pydantic model configuration."""

        validate_assignment = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

    @root_validator
    def update_timestamps(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Update the updated_at timestamp on validation."""
        values["updated_at"] = datetime.now()
        return values

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return self.dict()

    def to_json(self) -> str:
        """Convert model to JSON string."""
        return self.json()

    @classmethod
    def from_dict(cls: Type[ModelT], data: Dict[str, Any]) -> ModelT:
        """Create model instance from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls: Type[ModelT], json_str: str) -> ModelT:
        """Create model instance from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


# Request model
class Request(CoreModel):
    """Model for system requests."""

    user_id: Optional[str] = None
    type: str
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: Status = Status.PENDING
    priority: Priority = Priority.NORMAL

    @validator("type")
    def validate_request_type(cls, v: str) -> str:
        """Validate request type."""
        # Load valid request types from configuration
        config_loader = ConfigLoader()
        config = config_loader.get_config("request_types")
        valid_types = config.get("valid_types", [])

        if valid_types and v not in valid_types:
            logger.warning(f"Invalid request type: {v}")
            raise ValueError(
                f"Invalid request type. Must be one of: {', '.join(valid_types)}"
            )

        return v


# Response model
class Response(CoreModel):
    """Model for system responses."""

    request_id: str
    success: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @root_validator
    def validate_error_status(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure error field is set appropriately."""
        success = values.get("success", True)
        error = values.get("error")

        if success and error:
            values["error"] = None
        elif not success and not error:
            values["error"] = "Unknown error"

        return values


# User model
class User(CoreModel):
    """Model for system users."""

    username: str
    email: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)

    @validator("username")
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if not v.isalnum() and not any(c in "_-." for c in v):
            raise ValueError(
                "Username can only contain alphanumeric characters, underscore, dash, or period"
            )
        return v

    @validator("email")
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format if provided."""
        if v is None:
            return v

        if "@" not in v:
            raise ValueError("Invalid email format")

        return v


# Plugin model
class PluginInfo(CoreModel):
    """Model for plugin information."""

    name: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    entry_point: str
    dependencies: List[str] = Field(default_factory=list)
    enabled: bool = True

    @validator("version")
    def validate_version(cls, v: str) -> str:
        """Validate version format."""
        parts = v.split(".")
        if len(parts) < 2:
            raise ValueError("Version must be in format X.Y or X.Y.Z")

        for part in parts:
            if not part.isdigit():
                raise ValueError("Version parts must be numeric")

        return v


# Event model
class Event(CoreModel):
    """Model for system events."""

    type: str
    source: str
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


# Audit log entry model
class AuditLogEntry(CoreModel):
    """Model for audit log entries."""

    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    success: bool = True

    @validator("action")
    def validate_action(cls, v: str) -> str:
        """Validate action type."""
        valid_actions = [
            "create",
            "read",
            "update",
            "delete",
            "login",
            "logout",
            "export",
            "import",
            "execute",
        ]

        if v not in valid_actions:
            logger.warning(f"Unusual audit action: {v}")

        return v


# Model registry for managing model types
class ModelRegistry:
    """Registry for model types."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelRegistry, cls).__new__(cls)
            cls._instance._models = {}
            cls._instance._logger = logging.getLogger("core.models.registry")
        return cls._instance

    def register(self, name: str, model_class: Type[CoreModel]) -> None:
        """Register a model class."""
        if name in self._models:
            self._logger.warning(
                f"Overriding existing model registration for {name}")

        self._models[name] = model_class
        self._logger.debug(f"Registered model class: {name}")

    def get(self, name: str) -> Optional[Type[CoreModel]]:
        """Get a model class by name."""
        return self._models.get(name)

    def list_models(self) -> List[str]:
        """List all registered model names."""
        return list(self._models.keys())


# Initialize model registry and register core models
registry = ModelRegistry()
except Exception as e:
    print(f"错误: {str(e)}")
registry.register("request", Request)
registry.register("response", Response)
registry.register("user", User)
registry.register("plugin_info", PluginInfo)
registry.register("event", Event)
registry.register("audit_log_entry", AuditLogEntry)