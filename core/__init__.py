"""Core module initialization and version information."""
from ..config.config_loader import ConfigLoader

# Load configuration once at module initialization
_config_loader = ConfigLoader()
_core_config = _config_loader.get_config('core')

# Export version information from configuration
__version__ = _core_config.get('version', '0.1.0')
__author__ = _core_config.get('author', 'AI Team')

# Export core components
from .engine import Engine
from .context import Context, ContextManager
from .workflow import Workflow, WorkflowStep

# Export event system components
from .event_system import EventType, Event, EventBus, event_handler, get_event_bus

# Define default constants from configuration
DEFAULT_TIMEOUT = _core_config.get('timeout', 30)
DEFAULT_RETRY_COUNT = _core_config.get('retry_count', 3)
DEFAULT_BUFFER_SIZE = _core_config.get('buffer_size', 1024)

# Initialize logging
import logging
log_level = _core_config.get('log_level', 'INFO')
logging.getLogger('core').setLevel(getattr(logging, log_level))