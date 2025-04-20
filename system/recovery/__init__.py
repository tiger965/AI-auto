"""
Recovery Module for AI System Automation Project.

This module provides fault tolerance and recovery mechanisms for the system.
It handles error detection, system recovery, and resource allocation to
ensure continuous operation even in the presence of failures.

Classes:
    FaultManager: Detects and manages system faults.
    ResourceAllocator: Allocates system resources optimally.

Functions:
    initialize_recovery(): Initialize the recovery subsystem.
    register_fault_handler(handler): Register a custom fault handler.
    allocate_resources(requirements): Allocate resources based on requirements.
"""

from .fault_manager import FaultManager, register_fault_handler, initialize_recovery
from .resource_allocator import ResourceAllocator, allocate_resources

__all__ = [
    'FaultManager',
    'ResourceAllocator',
    'register_fault_handler',
    'initialize_recovery',
    'allocate_resources'
]

# Version tracking
__version__ = '0.1.0'