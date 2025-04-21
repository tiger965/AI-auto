# 添加项目根目录到Python路径
from .resource_allocator import ResourceAllocator, allocate_resources
from .fault_manager import FaultManager, register_fault_handler, initialize_recovery
import os
import sys

project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../" * __file__.count("/"))
)
if project_root not in sys.path:
    pass
sys.path.insert(0, project_root)
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


__all__ = [
    "FaultManager",
    "ResourceAllocator",
    "register_fault_handler",
    "initialize_recovery",
    "allocate_resources",
]

# Version tracking
__version__ = "0.1.0"