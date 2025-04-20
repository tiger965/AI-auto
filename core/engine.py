"""Core engine implementation."""
from typing import Dict, List, Any, Optional, Callable, TypeVar, Generic
from ..config.config_loader import ConfigLoader
import logging
from .context import Context

# Type definitions
T = TypeVar('T')
PluginT = TypeVar('PluginT', bound='Plugin')
MiddlewareT = TypeVar('MiddlewareT', bound='Middleware')

class Engine:
    """Core engine singleton implementation."""
    
    _instance = None
    
    def __new__(cls, config_section: str = 'engine'):
        if cls._instance is None:
            cls._instance = super(Engine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_section: str = 'engine'):
        """Initialize the engine with configuration.
        
        Args:
            config_section: The configuration section to load.
        """
        # Skip initialization if already done
        if self._initialized:
            return
            
        self._logger = logging.getLogger('core.engine')
        self._config_loader = ConfigLoader()
        self.reload_config(config_section)
        
        # Initialize plugin system
        self._plugins: Dict[str, PluginT] = {}
        self._middleware_stack: List[MiddlewareT] = []
        self._event_subscribers: Dict[str, List[Callable]] = {}
        
        self._initialized = True
        self._logger.info(f"Engine initialized with config from section: {config_section}")
    
    def reload_config(self, config_section: str = 'engine') -> None:
        """Reload configuration from specified section.
        
        Args:
            config_section: The configuration section to load.
        """
        self._config = self._config_loader.get_config(config_section)
        self._validate_config()
        self._logger.debug(f"Engine configuration reloaded from section: {config_section}")
    
    def _validate_config(self) -> None:
        """Validate the loaded configuration."""
        required_keys = ['max_plugins', 'enable_middleware', 'event_timeout']
        missing_keys = [key for key in required_keys if key not in self._config]
        
        if missing_keys:
            msg = f"Missing required configuration keys: {', '.join(missing_keys)}"
            self._logger.error(msg)
            raise ValueError(msg)
            
        # Set defaults for optional configuration
        defaults = {
            'plugin_directory': 'plugins',
            'max_middleware': 10,
            'error_retry_count': 3
        }
        
        for key, value in defaults.items():
            if key not in self._config:
                self._config[key] = value
                self._logger.debug(f"Using default value for {key}: {value}")

    # Plugin management methods
    def register_plugin(self, plugin: PluginT) -> None:
        """Register a plugin with the engine."""
        max_plugins = self._config.get('max_plugins', 10)
        
        if len(self._plugins) >= max_plugins:
            raise ValueError(f"Cannot register more than {max_plugins} plugins")
            
        plugin_id = plugin.get_id()
        if plugin_id in self._plugins:
            raise ValueError(f"Plugin with ID {plugin_id} already registered")
            
        self._plugins[plugin_id] = plugin
        self._logger.info(f"Registered plugin: {plugin_id}")
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginT]:
        """Get a registered plugin by ID."""
        return self._plugins.get(plugin_id)
    
    def unregister_plugin(self, plugin_id: str) -> bool:
        """Unregister a plugin by ID."""
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]
            self._logger.info(f"Unregistered plugin: {plugin_id}")
            return True
        return False
    
    # Middleware system methods
    def use_middleware(self, middleware: MiddlewareT) -> None:
        """Add middleware to the processing stack."""
        max_middleware = self._config.get('max_middleware', 10)
        
        if len(self._middleware_stack) >= max_middleware:
            raise ValueError(f"Cannot add more than {max_middleware} middleware components")
            
        self._middleware_stack.append(middleware)
        self._logger.info(f"Added middleware: {middleware.__class__.__name__}")
    
    def build_middleware_chain(self, final_handler: Callable[[Context], Any]) -> Callable[[Context], Any]:
        """Build the middleware processing chain."""
        if not self._config.get('enable_middleware', True):
            return final_handler
            
        handler = final_handler
        for middleware in reversed(self._middleware_stack):
            handler = lambda ctx, m=middleware, h=handler: m.process(ctx, h)
            
        return handler
    
    # Event system methods
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to an event type."""
        if event_type not in self._event_subscribers:
            self._event_subscribers[event_type] = []
        self._event_subscribers[event_type].append(callback)
        self._logger.debug(f"Added subscriber to event: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable) -> bool:
        """Unsubscribe from an event type."""
        if event_type in self._event_subscribers and callback in self._event_subscribers[event_type]:
            self._event_subscribers[event_type].remove(callback)
            self._logger.debug(f"Removed subscriber from event: {event_type}")
            return True
        return False
    
    def emit(self, event_type: str, data: Any = None) -> int:
        """Emit an event to all subscribers."""
        if event_type not in self._event_subscribers:
            return 0
            
        subscribers = self._event_subscribers[event_type]
        count = 0
        
        for callback in subscribers:
            try:
                callback(event_type, data)
                count += 1
            except Exception as e:
                self._logger.error(f"Error in event subscriber: {e}")
                
        self._logger.debug(f"Emitted event {event_type} to {count} subscribers")
        return count
    
    # Resource management methods
    def check_resources(self) -> Dict[str, Any]:
        """Check system resources and return availability."""
        # Implementation for resource monitoring
        resource_status = {
            'memory_available': True,
            'cpu_load': 0.5,  # Example value
            'thread_pool_size': self._config.get('thread_pool_size', 10),
            'active_threads': 3  # Example value
        }
        
        # Log if resources are constrained
        if resource_status['cpu_load'] > 0.8:
            self._logger.warning("CPU load is high: {:.2f}".format(resource_status['cpu_load']))
            
        return resource_status

    # Processing methods
    def process(self, context: Context) -> Any:
        """Process a request context through the middleware chain."""
        resources = self.check_resources()
        
        # Check if system is overloaded
        if resources['cpu_load'] > 0.9:
            self._logger.error("System overloaded, rejecting request")
            raise ResourceWarning("System currently overloaded, try again later")
            
        # Create the middleware chain and process
        chain = self.build_middleware_chain(self._handle_request)
        
        # Track processing metrics
        import time
        start_time = time.time()
        
        try:
            result = chain(context)
            # Emit completion event
            self.emit('request_processed', {'context_id': context.get_id(), 'success': True})
            return result
        except Exception as e:
            # Emit error event
            self.emit('request_error', {'context_id': context.get_id(), 'error': str(e)})
            raise
        finally:
            elapsed = time.time() - start_time
            self._logger.info(f"Request processing completed in {elapsed:.3f}s")
    
    def _handle_request(self, context: Context) -> Any:
        """Internal request handler (after middleware)."""
        # Core request handling logic
        return {'status': 'success', 'context_id': context.get_id()}