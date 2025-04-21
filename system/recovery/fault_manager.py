"""
Fault Manager Module for AI System Recovery.

This module implements a comprehensive fault management system that monitors,
detects, and handles various system faults. It provides mechanisms for fault
detection, isolation, and recovery to ensure system resilience.

Classes:
    FaultManager: Central manager for fault detection and recovery.
    FaultHandler: Base class for custom fault handlers.
    SystemFault: Representation of a system fault event.

Functions:
    register_fault_handler(handler): Register a custom fault handler.
    initialize_recovery(): Initialize the recovery subsystem.
    handle_exception(exception): Process an exception and trigger recovery.
"""

import ui
import logging
import time
import threading
import traceback
from typing import Dict, List, Callable, Optional, Any, Type, Set
import inspect
import os
import json
import signal

# Import local system modules
from .. import monitor

# Configure logging
logger = logging.getLogger(__name__)


class SystemFault:
    """
    Representation of a system fault event.

    Attributes:
        fault_id (str): Unique identifier for the fault.
        fault_type (str): Classification of the fault.
        component (str): System component where the fault occurred.
        timestamp (float): When the fault occurred.
        severity (str): Severity level (critical, high, medium, low).
        description (str): Human-readable description of the fault.
        exception (Optional[Exception]): Associated exception if applicable.
        traceback (Optional[str]): Stack trace if applicable.
        data (Dict): Additional fault-specific data.
        status (str): Current status of the fault (detected, handling, resolved).
    """

    # Severity levels
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    # Status values
    DETECTED = "detected"
    HANDLING = "handling"
    RESOLVED = "resolved"
    FAILED = "failed"

    def __init__(self,
                 fault_type: str,
                 component: str,
                 description: str,
                 severity: str = MEDIUM,
                 exception: Optional[Exception] = None):
        """
        Initialize a new SystemFault.

        Args:
            fault_type (str): Classification of the fault.
            component (str): System component where the fault occurred.
            description (str): Human-readable description of the fault.
            severity (str): Severity level.
            exception (Optional[Exception]): Associated exception if applicable.
        """
        self.fault_id = f"{int(time.time())}_{component}_{fault_type}"
        self.fault_type = fault_type
        self.component = component
        self.timestamp = time.time()
        self.severity = severity
        self.description = description
        self.exception = exception
        self.traceback = traceback.format_exc() if exception else None
        self.data = {}
        self.status = self.DETECTED
        self.recovery_attempts = 0
        self.resolution_time = None

    def update_status(self, status: str):
        """Update the status of the fault."""
        self.status = status
        if status == self.RESOLVED:
            self.resolution_time = time.time()

    def add_data(self, key: str, value: Any):
        """Add additional data to the fault record."""
        self.data[key] = value

    def to_dict(self) -> Dict:
        """Convert the fault to a dictionary for serialization."""
        return {
            "fault_id": self.fault_id,
            "fault_type": self.fault_type,
            "component": self.component,
            "timestamp": self.timestamp,
            "severity": self.severity,
            "description": self.description,
            "exception_type": type(self.exception).__name__ if self.exception else None,
            "exception_message": str(self.exception) if self.exception else None,
            "traceback": self.traceback,
            "data": self.data,
            "status": self.status,
            "recovery_attempts": self.recovery_attempts,
            "resolution_time": self.resolution_time
        }

    def __str__(self) -> str:
        """String representation of the fault."""
        return (f"SystemFault({self.fault_id}, type={self.fault_type}, "
                f"component={self.component}, severity={self.severity}, "
                f"status={self.status})")


class FaultHandler:
    """
    Base class for fault handlers.

    A fault handler is responsible for determining if it can handle a particular
    fault and attempting to recover from it.
    """

    def __init__(self, name: str, fault_types: List[str] = None):
        """
        Initialize a new FaultHandler.

        Args:
            name (str): Unique name for the handler.
            fault_types (List[str], optional): List of fault types this handler can manage.
        """
        self.name = name
        self.fault_types = fault_types or []

    def can_handle(self, fault: SystemFault) -> bool:
        """
        Determine if this handler can handle the given fault.

        Args:
            fault (SystemFault): The fault to check.

        Returns:
            bool: True if this handler can handle the fault, False otherwise.
        """
        if not self.fault_types:
            return False
        return fault.fault_type in self.fault_types

    def handle(self, fault: SystemFault) -> bool:
        """
        Attempt to recover from the fault.

        Args:
            fault (SystemFault): The fault to handle.

        Returns:
            bool: True if recovery was successful, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement handle()")


class ResourceExhaustionHandler(FaultHandler):
    """Handler for resource exhaustion faults."""

    def __init__(self):
        super().__init__("resource_exhaustion_handler", [
            "memory_exhaustion", "cpu_exhaustion", "disk_exhaustion"])

    def handle(self, fault: SystemFault) -> bool:
        """Handle resource exhaustion by requesting additional resources."""
        from .resource_allocator import allocate_resources

        logger.info(f"Handling resource exhaustion: {fault.fault_type}")

        try:
            # Determine which resource is exhausted
            if fault.fault_type == "memory_exhaustion":
                # Request additional memory or free up memory
                current_memory = monitor.get_memory_used()
                required_memory = current_memory * 1.5  # Request 50% more

                # Try to allocate more memory
                allocate_resources({"memory": required_memory})

                # Try to free up memory by triggering garbage collection
                gc.collect()

            elif fault.fault_type == "cpu_exhaustion":
                # Try to reduce CPU load or request more CPU resources
                current_cpu = monitor.get_cpu_usage()

                # Allocate more CPU resources if possible
                allocate_resources({"cpu": max(1, int(current_cpu * 1.5))})

                # Reduce background tasks
                # (implementation depends on the system architecture)

            elif fault.fault_type == "disk_exhaustion":
                # Try to free up disk space or allocate more
                current_disk = monitor.get_disk_usage()

                # Clean up temporary files
                import tempfile
                temp_dir = tempfile.gettempdir()
                try:
                    for item in os.listdir(temp_dir):
                        item_path = os.path.join(temp_dir, item)
                        # Older than a day
                        if os.path.isfile(item_path) and time.time() - os.path.getctime(item_path) > 86400:
                            os.remove(item_path)
                except Exception as e:
                    logger.warning(f"Error cleaning temp files: {str(e)}")

                # Request more disk space
                allocate_resources({"disk": current_disk * 1.5})

            # Check if resource allocation was successful
            if monitor.check_system_health():
                fault.update_status(SystemFault.RESOLVED)
                return True
            else:
                fault.update_status(SystemFault.FAILED)
                return False

        except Exception as e:
            logger.error(f"Error in ResourceExhaustionHandler: {str(e)}")
            fault.add_data("handler_error", str(e))
            fault.update_status(SystemFault.FAILED)
            return False


class NetworkFaultHandler(FaultHandler):
    """Handler for network-related faults."""

    def __init__(self):
        super().__init__("network_fault_handler", [
            "network_timeout", "connection_refused", "dns_resolution"])

    def handle(self, fault: SystemFault) -> bool:
        """Handle network faults by implementing retry logic with backoff."""
        logger.info(f"Handling network fault: {fault.fault_type}")

        try:
            # Extract the connection details from fault data
            if "url" not in fault.data and "host" not in fault.data:
                logger.error(
                    "Cannot handle network fault: missing connection details")
                fault.update_status(SystemFault.FAILED)
                return False

            # Implement retry logic with exponential backoff
            import socket
            import urllib.request

            max_retries = 3
            base_delay = 1

            for attempt in range(max_retries):
                try:
                    # Calculate backoff delay
                    delay = base_delay * (2 ** attempt)
                    logger.info(
                        f"Retry attempt {attempt + 1} after {delay}s delay")
                    time.sleep(delay)

                    # Attempt to reconnect
                    if "url" in fault.data:
                        urllib.request.urlopen(fault.data["url"], timeout=10)
                    elif "host" in fault.data and "port" in fault.data:
                        socket.create_connection(
                            (fault.data["host"], fault.data["port"]), timeout=10)

                    # If we get here, the connection was successful
                    fault.update_status(SystemFault.RESOLVED)
                    fault.add_data("retry_attempts", attempt + 1)
                    return True

                except Exception as retry_error:
                    logger.warning(
                        f"Retry {attempt + 1} failed: {str(retry_error)}")
                    fault.add_data(
                        f"retry_{attempt + 1}_error", str(retry_error))

            # If we get here, all retries failed
            fault.update_status(SystemFault.FAILED)
            return False

        except Exception as e:
            logger.error(f"Error in NetworkFaultHandler: {str(e)}")
            fault.add_data("handler_error", str(e))
            fault.update_status(SystemFault.FAILED)
            return False


class DatabaseFaultHandler(FaultHandler):
    """Handler for database-related faults."""

    def __init__(self):
        super().__init__("database_fault_handler", [
            "db_connection_lost", "db_constraint_violation", "db_deadlock"])

    def handle(self, fault: SystemFault) -> bool:
        """Handle database faults by implementing reconnection and transaction retry logic."""
        logger.info(f"Handling database fault: {fault.fault_type}")

        try:
            if fault.fault_type == "db_connection_lost":
                # Attempt to reconnect to the database
                # (implementation depends on the database being used)
                logger.info("Attempting database reconnection")

                # Example reconnection logic (placeholder)
                time.sleep(2)  # Wait before reconnecting

                # Check if reconnection was successful
                # (implementation-specific check)
                reconnection_success = True  # Placeholder

                if reconnection_success:
                    fault.update_status(SystemFault.RESOLVED)
                    return True

            elif fault.fault_type == "db_constraint_violation":
                # Log the violation details for debugging
                logger.warning(
                    f"Database constraint violation: {fault.description}")

                # This typically requires application-level handling
                # Mark as handled but not necessarily resolved
                fault.update_status(SystemFault.HANDLING)
                fault.add_data("requires_app_handling", True)
                return False

            elif fault.fault_type == "db_deadlock":
                # Implement deadlock retry logic
                logger.info("Attempting to resolve database deadlock")

                # Example deadlock resolution (placeholder)
                # In a real implementation, would retry the transaction
                time.sleep(1)

                # Check if deadlock was resolved
                deadlock_resolved = True  # Placeholder

                if deadlock_resolved:
                    fault.update_status(SystemFault.RESOLVED)
                    return True

            # If we get here, handling was not successful
            fault.update_status(SystemFault.FAILED)
            return False

        except Exception as e:
            logger.error(f"Error in DatabaseFaultHandler: {str(e)}")
            fault.add_data("handler_error", str(e))
            fault.update_status(SystemFault.FAILED)
            return False


class FaultManager:
    """
    Central manager for fault detection and recovery.
    
    This class coordinates fault handlers, tracks fault history,
    and provides interfaces for reporting and handling faults.
    
    Attributes:
        handlers (List[FaultHandler]): Registered fault handlers.
        fault_history (List[SystemFault]): Record of detected faults.
    """

    def __init__(self):
        """Initialize the FaultManager."""
        self.handlers = []
        self.fault_history = []
        self.active_faults = {}
        self.lock = threading.RLock()
        self.initialized = False

    def register_handler(self, handler: FaultHandler):
        """
        Register a fault handler.
        
        Args:
            handler (FaultHandler): The handler to register.
        """
        with self.lock:
            # Check if a handler with the same name already exists
            for existing in self.handlers:
                if existing.name == handler.name:
                    # Replace the existing handler
                    self.handlers.remove(existing)
                    break

            self.handlers.append(handler)
            logger.info(f"Registered fault handler: {handler.name}")

    def report_fault(self, fault: SystemFault) -> bool:
        """
        Report a fault and attempt to handle it.
        
        Args:
            fault (SystemFault): The fault to report.
            
        Returns:
            bool: True if the fault was handled successfully, False otherwise.
        """
        with self.lock:
            # Record the fault
            self.fault_history.append(fault)
            self.active_faults[fault.fault_id] = fault

            # Log the fault
            log_level = logging.CRITICAL if fault.severity == SystemFault.CRITICAL else \
                logging.ERROR if fault.severity == SystemFault.HIGH else \
                logging.WARNING if fault.severity == SystemFault.MEDIUM else \
                logging.INFO

            logger.log(log_level, f"Fault detected: {fault}")

            # Find appropriate handlers
            suitable_handlers = [
                h for h in self.handlers if h.can_handle(fault)]

            if not suitable_handlers:
                logger.warning(
                    f"No suitable handler found for fault: {fault.fault_type}")
                return False

            # Try each handler until one succeeds
            fault.update_status(SystemFault.HANDLING)
            for handler in suitable_handlers:
                logger.info(f"Attempting to handle fault with {handler.name}")
                fault.recovery_attempts += 1

                try:
                    success = handler.handle(fault)
                    if success:
                        logger.info(
                            f"Fault {fault.fault_id} handled successfully by {handler.name}")
                        if fault.status == SystemFault.RESOLVED:
                            # Remove from active faults if resolved
                            self.active_faults.pop(fault.fault_id, None)
                        return True
                except Exception as e:
                    logger.error(f"Error in handler {handler.name}: {str(e)}")
                    fault.add_data(f"handler_{handler.name}_error", str(e))

            # If we get here, no handler succeeded
            logger.error(f"All handlers failed for fault {fault.fault_id}")
            fault.update_status(SystemFault.FAILED)
            return False

    def report_exception(self, exception: Exception, component: str, severity: str = SystemFault.MEDIUM) -> bool:
        """
        Report an exception as a fault.
        
        Args:
            exception (Exception): The exception to report.
            component (str): The component where the exception occurred.
            severity (str, optional): The severity level.
            
        Returns:
            bool: True if the fault was handled successfully, False otherwise.
        """
        fault_type = type(exception).__name__
        description = str(exception)

        fault = SystemFault(
            fault_type=fault_type,
            component=component,
            description=description,
            severity=severity,
            exception=exception
        )

        return self.report_fault(fault)

    def get_active_faults(self, component: Optional[str] = None, severity: Optional[str] = None) -> List[SystemFault]:
        """
        Get active (unresolved) faults.
        
        Args:
            component (Optional[str]): Filter by component.
            severity (Optional[str]): Filter by severity level.
            
        Returns:
            List[SystemFault]: List of active faults matching the filters.
        """
        with self.lock:
            faults = list(self.active_faults.values())

            if component:
                faults = [f for f in faults if f.component == component]

            if severity:
                faults = [f for f in faults if f.severity == severity]

            return faults

    def get_fault_history(self, limit: int = 100) -> List[SystemFault]:
        """
        Get the fault history.
        
        Args:
            limit (int, optional): Maximum number of faults to return.
            
        Returns:
            List[SystemFault]: List of historical faults.
        """
        with self.lock:
            return list(reversed(self.fault_history[-limit:]))

    def get_statistics(self) -> Dict:
        """
        Get statistics about faults and recovery.
        
        Returns:
            Dict: Fault statistics.
        """
        with self.lock:
            total_faults = len(self.fault_history)
            resolved_faults = len(
                [f for f in self.fault_history if f.status == SystemFault.RESOLVED])
            failed_faults = len(
                [f for f in self.fault_history if f.status == SystemFault.FAILED])
            active_faults = len(self.active_faults)

            # Count by severity
            critical_faults = len(
                [f for f in self.fault_history if f.severity == SystemFault.CRITICAL])
            high_faults = len(
                [f for f in self.fault_history if f.severity == SystemFault.HIGH])
            medium_faults = len(
                [f for f in self.fault_history if f.severity == SystemFault.MEDIUM])
            low_faults = len(
                [f for f in self.fault_history if f.severity == SystemFault.LOW])

            # Count by type
            fault_types = {}
            for fault in self.fault_history:
                fault_types[fault.fault_type] = fault_types.get(
                    fault.fault_type, 0) + 1

            # Calculate resolution time statistics
            resolution_times = [
                fault.resolution_time - fault.timestamp
                for fault in self.fault_history
                if fault.status == SystemFault.RESOLVED and fault.resolution_time is not None
            ]

            avg_resolution_time = sum(
                resolution_times) / len(resolution_times) if resolution_times else 0
            max_resolution_time = max(
                resolution_times) if resolution_times else 0
            min_resolution_time = min(
                resolution_times) if resolution_times else 0

            return {
                "total_faults": total_faults,
                "resolved_faults": resolved_faults,
                "failed_faults": failed_faults,
                "active_faults": active_faults,
                "resolution_rate": (resolved_faults / total_faults) if total_faults > 0 else 0,
                "by_severity": {
                    "critical": critical_faults,
                    "high": high_faults,
                    "medium": medium_faults,
                    "low": low_faults
                },
                "by_type": fault_types,
                "resolution_time": {
                    "average": avg_resolution_time,
                    "max": max_resolution_time,
                    "min": min_resolution_time
                }
            }

    def export_fault_history(self, filepath: str):
        """
        Export the fault history to a file.
        
        Args:
            filepath (str): Path to the output file.
        """
        with self.lock:
            with open(filepath, 'w') as f:
                json.dump([fault.to_dict()
                          for fault in self.fault_history], f, indent=2)
            logger.info(f"Exported fault history to {filepath}")

    def clear_resolved_faults(self):
        """
        Clear resolved faults from history to free up memory.
        Keeps critical and high severity faults regardless.
        """
        with self.lock:
            # Keep important faults and recent ones
            threshold_time = time.time() - (86400 * 7)  # 7 days
            self.fault_history = [
                fault for fault in self.fault_history
                if (fault.status != SystemFault.RESOLVED) or
                   (fault.severity in [SystemFault.CRITICAL, SystemFault.HIGH]) or
                   (fault.timestamp > threshold_time)
            ]
            logger.info(
                f"Cleared resolved faults. History size: {len(self.fault_history)}")


# Global fault manager instance
_fault_manager = None


def get_fault_manager() -> FaultManager:
    """
    Get the global fault manager instance.
    
    Returns:
        FaultManager: The global fault manager.
    """
    global _fault_manager
    if _fault_manager is None:
        _fault_manager = FaultManager()
    return _fault_manager


def register_fault_handler(handler: FaultHandler):
    """
    Register a fault handler with the global manager.
    
    Args:
        handler (FaultHandler): The handler to register.
    """
    get_fault_manager().register_handler(handler)


def handle_exception(exception: Exception, component: str, severity: str = SystemFault.MEDIUM) -> bool:
    """
    Handle an exception using the global fault manager.
    
    Args:
        exception (Exception): The exception to handle.
        component (str): The component where the exception occurred.
        severity (str, optional): The severity level.
        
    Returns:
        bool: True if the exception was handled successfully, False otherwise.
    """
    return get_fault_manager().report_exception(exception, component, severity)


def initialize_recovery():
    """
    Initialize the recovery subsystem.
    
    This function sets up default fault handlers and configures
    the recovery environment.
    """
    manager = get_fault_manager()
    if manager.initialized:
        return

    # Register standard fault handlers
    manager.register_handler(ResourceExhaustionHandler())
    manager.register_handler(NetworkFaultHandler())
    manager.register_handler(DatabaseFaultHandler())

    # Set up exception hook to catch unhandled exceptions
    def global_exception_hook(exc_type, exc_value, exc_traceback):
        # Log the exception
        logger.critical("Unhandled exception", exc_info=(
            exc_type, exc_value, exc_traceback))

        # Try to handle it
        handle_exception(exc_value, "global", SystemFault.CRITICAL)

        # Call the original exception hook
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    # Don't override in development/debug mode
    if not os.environ.get("DEBUG"):
        sys.excepthook = global_exception_hook

    # Set up signal handlers
    def signal_handler(signum, frame):
        if signum == signal.SIGTERM:
            logger.warning("Received SIGTERM signal")
            # Clean shutdown logic
        elif signum == signal.SIGINT:
            logger.warning("Received SIGINT signal")
            # Clean shutdown logic
        elif signum == signal.SIGUSR1:
            # Custom signal for system maintenance
            logger.info("Received SIGUSR1 signal - system maintenance mode")
            # Custom handling

    # Register signal handlers if not in development/debug mode
    if not os.environ.get("DEBUG"):
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGUSR1'):
            signal.signal(signal.SIGUSR1, signal_handler)

    # Mark as initialized
    manager.initialized = True
    logger.info("Recovery subsystem initialized")

# Install default exception handler for use in production


def install_exception_handler():
    """Install the default exception handler for production use."""
    def exception_handler(exc_type, exc_value, exc_traceback):
        logger.error("Uncaught exception", exc_info=(
            exc_type, exc_value, exc_traceback))
        handle_exception(exc_value, "uncaught", SystemFault.HIGH)
        # Call the original handler
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    # Only set if not in debug mode
    if not os.environ.get("DEBUG"):
        sys.excepthook = exception_handler
        logger.info("Installed global exception handler")

# Create a context manager for fault handling


class FaultContext:
    """
    Context manager for fault handling.
    
    Usage:
        with FaultContext("component_name"):
            # Code that might raise exceptions
    """

    def __init__(self, component: str, severity: str = SystemFault.MEDIUM):
        """
        Initialize a new FaultContext.
        
        Args:
            component (str): The component name.
            severity (str, optional): The severity level for any faults.
        """
        self.component = component
        self.severity = severity

    def __enter__(self):
        """Enter the context."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the context and handle any exceptions.
        
        Args:
            exc_type: The exception type.
            exc_value: The exception value.
            traceback: The exception traceback.
            
        Returns:
            bool: True if the exception was handled, False otherwise.
        """
        if exc_value is not None:
            # Handle the exception
            return handle_exception(exc_value, self.component, self.severity)
        return False  # Re-raise the exception if not handled