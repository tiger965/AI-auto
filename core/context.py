"""Context management module implementation."""
from typing import Dict, Any, Optional, List, Generic, TypeVar
from ..config.config_loader import ConfigLoader
import logging
import json
import os
import time
from pathlib import Path
import uuid

T = TypeVar('T')

class PersistenceHandler:
    """Base class for context persistence handlers."""
    
    def save(self, context_id: str, data: Dict[str, Any]) -> bool:
        """Save context data."""
        raise NotImplementedError("Persistence handlers must implement save()")
    
    def load(self, context_id: str) -> Optional[Dict[str, Any]]:
        """Load context data."""
        raise NotImplementedError("Persistence handlers must implement load()")
    
    def delete(self, context_id: str) -> bool:
        """Delete context data."""
        raise NotImplementedError("Persistence handlers must implement delete()")

class FileSystemPersistenceHandler(PersistenceHandler):
    """File system implementation of persistence handler."""
    
    def __init__(self, storage_dir: str = None):
        """Initialize with configuration.
        
        Args:
            storage_dir: Directory to store context files
        """
        self._logger = logging.getLogger('core.context.persistence')
        self._config_loader = ConfigLoader()
        config = self._config_loader.get_config('context')
        
        # Use provided storage_dir or load from config
        self._storage_dir = storage_dir or config.get('storage_dir', 'storage/contexts')
        
        # Create directory if it doesn't exist
        os.makedirs(self._storage_dir, exist_ok=True)
        self._logger.debug(f"Persistence handler using storage directory: {self._storage_dir}")
    
    def _get_context_path(self, context_id: str) -> Path:
        """Get the file path for a context ID."""
        return Path(self._storage_dir) / f"{context_id}.json"
    
    def save(self, context_id: str, data: Dict[str, Any]) -> bool:
        """Save context data to file system."""
        try:
            # Filter sensitive information before saving
            filtered_data = self._filter_sensitive_data(data)
            
            file_path = self._get_context_path(context_id)
            with open(file_path, 'w') as f:
                json.dump(filtered_data, f, indent=2)
                
            self._logger.debug(f"Saved context {context_id} to {file_path}")
            return True
        except Exception as e:
            self._logger.error(f"Error saving context {context_id}: {e}")
            return False
    
    def load(self, context_id: str) -> Optional[Dict[str, Any]]:
        """Load context data from file system."""
        file_path = self._get_context_path(context_id)
        
        if not file_path.exists():
            self._logger.debug(f"Context {context_id} not found at {file_path}")
            return None
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            self._logger.debug(f"Loaded context {context_id} from {file_path}")
            return data
        except Exception as e:
            self._logger.error(f"Error loading context {context_id}: {e}")
            return None
    
    def delete(self, context_id: str) -> bool:
        """Delete context data from file system."""
        file_path = self._get_context_path(context_id)
        
        if not file_path.exists():
            return False
            
        try:
            os.remove(file_path)
            self._logger.debug(f"Deleted context {context_id} from {file_path}")
            return True
        except Exception as e:
            self._logger.error(f"Error deleting context {context_id}: {e}")
            return False
    
    def _filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter sensitive information before persistence."""
        # Load sensitive field configuration
        config = self._config_loader.get_config('security')
        sensitive_fields = config.get('sensitive_fields', ['password', 'token', 'key', 'secret'])
        
        filtered = data.copy()
        
        # Recursively filter sensitive fields
        def filter_dict(d):
            for k, v in list(d.items()):
                if isinstance(k, str) and any(field in k.lower() for field in sensitive_fields):
                    d[k] = "[REDACTED]"
                elif isinstance(v, dict):
                    filter_dict(v)
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            filter_dict(item)
        
        filter_dict(filtered)
        return filtered

class Context:
    """Context for request processing."""
    
    def __init__(self, context_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None):
        """Initialize a new context.
        
        Args:
            context_id: Unique identifier for this context
            data: Initial data for the context
        """
        self._id = context_id or str(uuid.uuid4())
        self._data = data or {}
        self._created_at = time.time()
        self._modified_at = self._created_at
        self._logger = logging.getLogger('core.context')
        
        # Initialize with standard metadata
        self._metadata = {
            'created_at': self._created_at,
            'modified_at': self._modified_at
        }
    
    def get_id(self) -> str:
        """Get the context ID."""
        return self._id
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in the context."""
        self._data[key] = value
        self._modified_at = time.time()
        self._metadata['modified_at'] = self._modified_at
        self._logger.debug(f"Context {self._id}: Set {key}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the context."""
        return self._data.get(key, default)
    
    def delete(self, key: str) -> bool:
        """Delete a value from the context."""
        if key in self._data:
            del self._data[key]
            self._modified_at = time.time()
            self._metadata['modified_at'] = self._modified_at
            self._logger.debug(f"Context {self._id}: Deleted {key}")
            return True
        return False
    
    def has(self, key: str) -> bool:
        """Check if a key exists in the context."""
        return key in self._data
    
    def get_all(self) -> Dict[str, Any]:
        """Get all context data."""
        return self._data.copy()
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get context metadata."""
        return self._metadata.copy()
    
    def clear(self) -> None:
        """Clear all data from the context."""
        self._data = {}
        self._modified_at = time.time()
        self._metadata['modified_at'] = self._modified_at
        self._logger.debug(f"Context {self._id}: Cleared all data")
    
    def merge(self, data: Dict[str, Any]) -> None:
        """Merge data into the context."""
        self._data.update(data)
        self._modified_at = time.time()
        self._metadata['modified_at'] = self._modified_at
        self._logger.debug(f"Context {self._id}: Merged {len(data)} keys")

class ContextManager:
    """Manager for context objects."""
    
    def __init__(self, config_section: str = 'context'):
        """Initialize with configuration.
        
        Args:
            config_section: Configuration section to load
        """
        self._logger = logging.getLogger('core.context.manager')
        self._config_loader = ConfigLoader()
        self.reload_config(config_section)
        
        # Setup persistence handler
        persistence_type = self._config.get('persistence_type', 'file')
        
        if persistence_type == 'file':
            storage_dir = self._config.get('storage_dir')
            self._persistence = FileSystemPersistenceHandler(storage_dir)
        else:
            raise ValueError(f"Unsupported persistence type: {persistence_type}")
            
        # Active contexts cache
        self._active_contexts: Dict[str, Context] = {}
        
        self._logger.info(f"Context manager initialized with {persistence_type} persistence")
    
    def reload_config(self, config_section: str = 'context') -> None:
        """Reload configuration from specified section."""
        self._config = self._config_loader.get_config(config_section)
        self._validate_config()
        self._logger.debug(f"Context manager configuration reloaded from section: {config_section}")
    
    def _validate_config(self) -> None:
        """Validate the loaded configuration."""
        required_keys = ['persistence_type', 'max_context_age']
        missing_keys = [key for key in required_keys if key not in self._config]
        
        if missing_keys:
            msg = f"Missing required configuration keys: {', '.join(missing_keys)}"
            self._logger.error(msg)
            raise ValueError(msg)
    
    def create_context(self, context_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> Context:
        """Create a new context."""
        context = Context(context_id, data)
        self._active_contexts[context.get_id()] = context
        self._logger.debug(f"Created new context: {context.get_id()}")
        return context
    
    def get_context(self, context_id: str, load_if_needed: bool = True) -> Optional[Context]:
        """Get a context by ID, optionally loading from persistence."""
        # Check active contexts first
        if context_id in self._active_contexts:
            return self._active_contexts[context_id]
            
        # If not active and loading is enabled, try to load from persistence
        if load_if_needed:
            data = self._persistence.load(context_id)
            if data:
                context = Context(context_id, data)
                self._active_contexts[context_id] = context
                self._logger.debug(f"Loaded context from persistence: {context_id}")
                return context
                
        self._logger.debug(f"Context not found: {context_id}")
        return None
    
    def save_context(self, context: Context) -> bool:
        """Save a context to persistence."""
        context_id = context.get_id()
        data = {
            'data': context.get_all(),
            'metadata': context.get_metadata()
        }
        
        success = self._persistence.save(context_id, data)
        if success:
            self._logger.debug(f"Saved context to persistence: {context_id}")
        else:
            self._logger.error(f"Failed to save context: {context_id}")
            
        return success
    
    def delete_context(self, context_id: str) -> bool:
        """Delete a context from both cache and persistence."""
        # Remove from active contexts
        if context_id in self._active_contexts:
            del self._active_contexts[context_id]
            
        # Remove from persistence
        success = self._persistence.delete(context_id)
        if success:
            self._logger.debug(f"Deleted context: {context_id}")
        else:
            self._logger.warning(f"Failed to delete context: {context_id}")
            
        return success
    
    def cleanup_old_contexts(self) -> int:
        """Clean up contexts older than max_context_age."""
        max_age = self._config.get('max_context_age', 86400)  # Default: 1 day
        current_time = time.time()
        count = 0
        
        # Check active contexts
        for context_id, context in list(self._active_contexts.items()):
            metadata = context.get_metadata()
            modified_at = metadata.get('modified_at', 0)
            
            if current_time - modified_at > max_age:
                self.delete_context(context_id)
                count += 1
                
        self._logger.info(f"Cleaned up {count} old contexts")
        return count