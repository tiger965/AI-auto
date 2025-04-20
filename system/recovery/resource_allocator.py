"""
Resource Allocator Module for AI System Recovery.

This module implements resource allocation and management for the system,
ensuring optimal distribution of computing resources like CPU, memory,
and storage based on component requirements and priorities.

Classes:
    ResourceAllocator: Manager for system resource allocation.
    ResourceRequirement: Representation of a resource requirement.
    ResourcePool: Container for available system resources.

Functions:
    allocate_resources(requirements): Allocate resources based on requirements.
    release_resources(resource_id): Release previously allocated resources.
    get_resource_usage(): Get current resource usage statistics.
"""

import logging
import time
import threading
import json
from typing import Dict, List, Optional, Any, Set, Tuple
import os
import sys
import uuid

# Import local system modules
from .. import monitor

# Configure logging
logger = logging.getLogger(__name__)


class ResourceRequirement:
    """
    Representation of a resource requirement.
    
    Attributes:
        component (str): The component requesting resources.
        cpu (Optional[float]): CPU cores required.
        memory (Optional[int]): Memory required in bytes.
        disk (Optional[int]): Disk space required in bytes.
        network (Optional[int]): Network bandwidth required in bytes/s.
        gpu (Optional[int]): GPU memory required in bytes.
        priority (int): Priority level (higher values indicate higher priority).
        exclusive (bool): Whether the resources should be exclusive.
    """
    
    def __init__(self, 
                 component: str,
                 cpu: Optional[float] = None,
                 memory: Optional[int] = None,
                 disk: Optional[int] = None,
                 network: Optional[int] = None,
                 gpu: Optional[int] = None,
                 priority: int = 5,
                 exclusive: bool = False):
        """
        Initialize a new ResourceRequirement.
        
        Args:
            component (str): The component requesting resources.
            cpu (Optional[float]): CPU cores required.
            memory (Optional[int]): Memory required in bytes.
            disk (Optional[int]): Disk space required in bytes.
            network (Optional[int]): Network bandwidth required in bytes/s.
            gpu (Optional[int]): GPU memory required in bytes.
            priority (int): Priority level (1-10, higher values indicate higher priority).
            exclusive (bool): Whether the resources should be exclusive.
        """
        self.component = component
        self.cpu = cpu
        self.memory = memory
        self.disk = disk
        self.network = network
        self.gpu = gpu
        self.priority = max(1, min(10, priority))  # Clamp to 1-10
        self.exclusive = exclusive
        self.timestamp = time.time()
        self.id = str(uuid.uuid4())
        
    def to_dict(self) -> Dict:
        """Convert the requirement to a dictionary."""
        return {
            "id": self.id,
            "component": self.component,
            "cpu": self.cpu,
            "memory": self.memory,
            "disk": self.disk,
            "network": self.network,
            "gpu": self.gpu,
            "priority": self.priority,
            "exclusive": self.exclusive,
            "timestamp": self.timestamp
        }


class ResourceAllocator:
    """
    Manager for system resource allocation.
    
    This class coordinates resource allocation across the system,
    handling requests for resources, managing priorities, and
    ensuring optimal resource distribution.
    
    Attributes:
        resource_pool (ResourcePool): The available system resources.
        allocations (Dict[str, ResourceAllocation]): Active resource allocations.
        pending_requests (List[ResourceRequirement]): Pending resource requests.
    """
    
    def __init__(self):
        """Initialize a new ResourceAllocator."""
        self.resource_pool = ResourcePool()
        self.allocations = {}
        self.pending_requests = []
        self.lock = threading.RLock()
        self.allocation_history = []
        self.initialized = False
        
    def request_resources(self, requirement: ResourceRequirement) -> Optional[str]:
        """
        Request resources based on a requirement.
        
        Args:
            requirement (ResourceRequirement): The resource requirement.
            
        Returns:
            Optional[str]: Allocation ID if successful, None otherwise.
        """
        with self.lock:
            # Check if the resource pool can allocate immediately
            if self.resource_pool.can_allocate(requirement):
                # Allocate resources
                allocation = self.resource_pool.allocate(requirement)
                if allocation:
                    self.allocations[allocation.id] = allocation
                    self.allocation_history.append(allocation.to_dict())
                    logger.info(f"Allocated resources for {requirement.component}: {allocation.id}")
                    return allocation.id
            
            # If allocation failed, add to pending requests queue
            self.pending_requests.append(requirement)
            # Sort by priority (highest first)
            self.pending_requests.sort(key=lambda r: r.priority, reverse=True)
            logger.info(f"Resource request from {requirement.component} queued (priority {requirement.priority})")
            
            # Try to free up resources for high-priority requests
            if requirement.priority >= 8:  # High priority threshold
                self._preempt_for_high_priority(requirement)
                
            return None
            
    def release_resources(self, allocation_id: str) -> bool:
        """
        Release allocated resources.
        
        Args:
            allocation_id (str): ID of the allocation to release.
            
        Returns:
            bool: True if the resources were released, False otherwise.
        """
        with self.lock:
            if allocation_id not in self.allocations:
                logger.warning(f"Attempted to release unknown allocation: {allocation_id}")
                return False
                
            allocation = self.allocations[allocation_id]
            self.resource_pool.release(allocation)
            
            # Remove from active allocations
            del self.allocations[allocation_id]
            
            # Update allocation history
            for history_item in self.allocation_history:
                if history_item["id"] == allocation_id:
                    history_item["status"] = "released"
                    history_item["release_time"] = time.time()
                    break
            
            # Process pending requests
            self._process_pending_requests()
            
            return True
            
    def _preempt_for_high_priority(self, high_priority_req: ResourceRequirement):
        """
        Attempt to free resources for a high-priority request by
        preempting lower-priority allocations.
        
        Args:
            high_priority_req (ResourceRequirement): The high-priority request.
        """
        # Find low-priority allocations that could be preempted
        low_priority_allocations = sorted(
            [a for a in self.allocations.values() if a.requirement.priority < high_priority_req.priority - 2],
            key=lambda a: a.requirement.priority
        )
        
        # Required resources
        required = {
            "cpu": high_priority_req.cpu or 0,
            "memory": high_priority_req.memory or 0,
            "disk": high_priority_req.disk or 0,
            "network": high_priority_req.network or 0,
            "gpu": high_priority_req.gpu or 0
        }
        
        # Available resources
        available = self.resource_pool.get_available()
        
        # Calculate deficit
        deficit = {
            "cpu": max(0, required["cpu"] - available["cpu"]),
            "memory": max(0, required["memory"] - available["memory"]),
            "disk": max(0, required["disk"] - available["disk"]),
            "network": max(0, required["network"] - available["network"]),
            "gpu": max(0, required["gpu"] - available["gpu"])
        }
        
        # Check if preemption is needed
        if all(v == 0 for v in deficit.values()):
            return
            
        # Find allocations to preempt
        to_preempt = []
        for allocation in low_priority_allocations:
            # Skip if already marked for preemption
            if allocation.id in [p.id for p in to_preempt]:
                continue
                
            # Check if this allocation would help reduce the deficit
            helps_deficit = False
            if deficit["cpu"] > 0 and allocation.allocated_cpu:
                helps_deficit = True
            if deficit["memory"] > 0 and allocation.allocated_memory:
                helps_deficit = True
            if deficit["disk"] > 0 and allocation.allocated_disk:
                helps_deficit = True
            if deficit["network"] > 0 and allocation.allocated_network:
                helps_deficit = True
            if deficit["gpu"] > 0 and allocation.allocated_gpu:
                helps_deficit = True
                
            if helps_deficit:
                to_preempt.append(allocation)
                
                # Update deficit
                if allocation.allocated_cpu:
                    deficit["cpu"] = max(0, deficit["cpu"] - allocation.allocated_cpu)
                if allocation.allocated_memory:
                    deficit["memory"] = max(0, deficit["memory"] - allocation.allocated_memory)
                if allocation.allocated_disk:
                    deficit["disk"] = max(0, deficit["disk"] - allocation.allocated_disk)
                if allocation.allocated_network:
                    deficit["network"] = max(0, deficit["network"] - allocation.allocated_network)
                if allocation.allocated_gpu:
                    deficit["gpu"] = max(0, deficit["gpu"] - allocation.allocated_gpu)
                    
                # Check if we've resolved the deficit
                if all(v == 0 for v in deficit.values()):
                    break
        
        # Preempt the identified allocations
        for allocation in to_preempt:
            logger.warning(f"Preempting allocation {allocation.id} for high-priority request from {high_priority_req.component}")
            self.release_resources(allocation.id)
            
            # Notify the component about preemption
            # In a real system, this would send a notification or signal
            # For now, we just log it
            logger.warning(f"Component {allocation.requirement.component} was preempted due to high-priority request")
            
    def _process_pending_requests(self):
        """Process pending resource requests."""
        if not self.pending_requests:
            return
            
        # Try to allocate resources for pending requests
        allocated_indices = []
        for i, requirement in enumerate(self.pending_requests):
            if self.resource_pool.can_allocate(requirement):
                allocation = self.resource_pool.allocate(requirement)
                if allocation:
                    self.allocations[allocation.id] = allocation
                    self.allocation_history.append(allocation.to_dict())
                    allocated_indices.append(i)
                    logger.info(f"Processed pending request for {requirement.component}: {allocation.id}")
        
        # Remove allocated requests from the pending queue
        for i in sorted(allocated_indices, reverse=True):
            del self.pending_requests[i]
            
    def get_allocation(self, allocation_id: str) -> Optional[ResourceAllocation]:
        """
        Get information about a specific allocation.
        
        Args:
            allocation_id (str): ID of the allocation.
            
        Returns:
            Optional[ResourceAllocation]: The allocation if found, None otherwise.
        """
        with self.lock:
            return self.allocations.get(allocation_id)
            
    def get_active_allocations(self, component: Optional[str] = None) -> List[ResourceAllocation]:
        """
        Get active resource allocations.
        
        Args:
            component (Optional[str]): Filter by component.
            
        Returns:
            List[ResourceAllocation]: Active allocations matching the filter.
        """
        with self.lock:
            allocations = list(self.allocations.values())
            if component:
                allocations = [a for a in allocations if a.requirement.component == component]
            return allocations
            
    def get_pending_requests(self, component: Optional[str] = None) -> List[ResourceRequirement]:
        """
        Get pending resource requests.
        
        Args:
            component (Optional[str]): Filter by component.
            
        Returns:
            List[ResourceRequirement]: Pending requests matching the filter.
        """
        with self.lock:
            if component:
                return [r for r in self.pending_requests if r.component == component]
            return list(self.pending_requests)
            
    def get_allocation_history(self, limit: int = 100) -> List[Dict]:
        """
        Get resource allocation history.
        
        Args:
            limit (int): Maximum number of records to return.
            
        Returns:
            List[Dict]: Allocation history records.
        """
        with self.lock:
            return list(reversed(self.allocation_history[-limit:]))
            
    def get_overall_usage(self) -> Dict:
        """
        Get overall resource usage statistics.
        
        Returns:
            Dict: Resource usage statistics.
        """
        with self.lock:
            usage = self.resource_pool.get_usage()
            usage["allocations_count"] = len(self.allocations)
            usage["pending_requests_count"] = len(self.pending_requests)
            
            # Add high-priority stats
            high_priority_allocations = [a for a in self.allocations.values() if a.requirement.priority >= 8]
            usage["high_priority_allocations"] = len(high_priority_allocations)
            
            # Add component stats
            components = {}
            for allocation in self.allocations.values():
                component = allocation.requirement.component
                if component not in components:
                    components[component] = 0
                components[component] += 1
            usage["components"] = components
            
            return usage
            
    def check_expired_allocations(self):
        """Check for and release expired allocations."""
        with self.lock:
            expired_ids = [aid for aid, alloc in self.allocations.items() if alloc.is_expired()]
            for allocation_id in expired_ids:
                logger.info(f"Releasing expired allocation: {allocation_id}")
                self.release_resources(allocation_id)


# Global resource allocator instance
_resource_allocator = None

def get_resource_allocator() -> ResourceAllocator:
    """
    Get the global resource allocator instance.
    
    Returns:
        ResourceAllocator: The global resource allocator.
    """
    global _resource_allocator
    if _resource_allocator is None:
        _resource_allocator = ResourceAllocator()
    return _resource_allocator

def allocate_resources(requirements: Dict) -> Optional[str]:
    """
    Allocate resources based on requirements.
    
    Args:
        requirements (Dict): Resource requirements. Can include 'cpu', 'memory',
                            'disk', 'network', 'gpu', 'priority', 'component',
                            and 'exclusive'.
                            
    Returns:
        Optional[str]: Allocation ID if successful, None otherwise.
    """
    allocator = get_resource_allocator()
    
    # Extract component name from caller if not provided
    component = requirements.get("component")
    if not component:
        frame = inspect.currentframe().f_back
        module = inspect.getmodule(frame)
        component = module.__name__ if module else "unknown"
    
    # Create resource requirement
    requirement = ResourceRequirement(
        component=component,
        cpu=requirements.get("cpu"),
        memory=requirements.get("memory"),
        disk=requirements.get("disk"),
        network=requirements.get("network"),
        gpu=requirements.get("gpu"),
        priority=requirements.get("priority", 5),
        exclusive=requirements.get("exclusive", False)
    )
    
    # Request resources
    return allocator.request_resources(requirement)

def release_resources(allocation_id: str) -> bool:
    """
    Release previously allocated resources.
    
    Args:
        allocation_id (str): ID of the allocation to release.
        
    Returns:
        bool: True if the resources were released, False otherwise.
    """
    return get_resource_allocator().release_resources(allocation_id)

def get_resource_usage() -> Dict:
    """
    Get current resource usage statistics.
    
    Returns:
        Dict: Resource usage statistics.
    """
    return get_resource_allocator().get_overall_usage()

def initialize_resource_allocator():
    """Initialize the resource allocator."""
    allocator = get_resource_allocator()
    if allocator.initialized:
        return
    
    # Start periodic check for expired allocations
    def check_expired_task():
        while True:
            try:
                allocator.check_expired_allocations()
            except Exception as e:
                logger.error(f"Error in check_expired_task: {str(e)}")
            time.sleep(60)  # Check every minute
    
    # Start the monitoring thread
    threading.Thread(target=check_expired_task, daemon=True).start()
    
    # Mark as initialized
    allocator.initialized = True
    logger.info("Resource allocator initialized")

# Initialize the resource allocator
initialize_resource_allocator()
        
    def __str__(self) -> str:
        """String representation of the requirement."""
        resources = []
        if self.cpu is not None:
            resources.append(f"CPU: {self.cpu}")
        if self.memory is not None:
            resources.append(f"Memory: {self.memory / 1024 / 1024:.1f}MB")
        if self.disk is not None:
            resources.append(f"Disk: {self.disk / 1024 / 1024:.1f}MB")
        if self.network is not None:
            resources.append(f"Network: {self.network / 1024:.1f}KB/s")
        if self.gpu is not None:
            resources.append(f"GPU: {self.gpu / 1024 / 1024:.1f}MB")
            
        return (f"ResourceRequirement({self.component}, "
                f"priority={self.priority}, resources=[{', '.join(resources)}])")


class ResourceAllocation:
    """
    Representation of an active resource allocation.
    
    Attributes:
        id (str): Unique identifier for the allocation.
        requirement (ResourceRequirement): The original requirement.
        allocated_cpu (Optional[float]): Allocated CPU cores.
        allocated_memory (Optional[int]): Allocated memory in bytes.
        allocated_disk (Optional[int]): Allocated disk space in bytes.
        allocated_network (Optional[int]): Allocated network bandwidth in bytes/s.
        allocated_gpu (Optional[int]): Allocated GPU memory in bytes.
        start_time (float): When the allocation was made.
        expiry_time (Optional[float]): When the allocation expires (if temporary).
    """
    
    def __init__(self, requirement: ResourceRequirement):
        """
        Initialize a new ResourceAllocation.
        
        Args:
            requirement (ResourceRequirement): The original requirement.
        """
        self.id = requirement.id
        self.requirement = requirement
        self.allocated_cpu = None
        self.allocated_memory = None
        self.allocated_disk = None
        self.allocated_network = None
        self.allocated_gpu = None
        self.start_time = time.time()
        self.expiry_time = None
        self.status = "pending"
        
    def set_allocation(self, 
                       cpu: Optional[float] = None,
                       memory: Optional[int] = None,
                       disk: Optional[int] = None,
                       network: Optional[int] = None,
                       gpu: Optional[int] = None):
        """
        Set the allocated resources.
        
        Args:
            cpu (Optional[float]): Allocated CPU cores.
            memory (Optional[int]): Allocated memory in bytes.
            disk (Optional[int]): Allocated disk space in bytes.
            network (Optional[int]): Allocated network bandwidth in bytes/s.
            gpu (Optional[int]): Allocated GPU memory in bytes.
        """
        self.allocated_cpu = cpu
        self.allocated_memory = memory
        self.allocated_disk = disk
        self.allocated_network = network
        self.allocated_gpu = gpu
        self.status = "active"
        
    def set_expiry(self, duration: float):
        """
        Set the allocation to expire after a duration.
        
        Args:
            duration (float): Duration in seconds.
        """
        self.expiry_time = time.time() + duration
        
    def is_expired(self) -> bool:
        """Check if the allocation has expired."""
        if self.expiry_time is None:
            return False
        return time.time() > self.expiry_time
        
    def to_dict(self) -> Dict:
        """Convert the allocation to a dictionary."""
        return {
            "id": self.id,
            "component": self.requirement.component,
            "allocated_cpu": self.allocated_cpu,
            "allocated_memory": self.allocated_memory,
            "allocated_disk": self.allocated_disk,
            "allocated_network": self.allocated_network,
            "allocated_gpu": self.allocated_gpu,
            "start_time": self.start_time,
            "expiry_time": self.expiry_time,
            "status": self.status,
            "priority": self.requirement.priority
        }
        
    def __str__(self) -> str:
        """String representation of the allocation."""
        resources = []
        if self.allocated_cpu is not None:
            resources.append(f"CPU: {self.allocated_cpu}")
        if self.allocated_memory is not None:
            resources.append(f"Memory: {self.allocated_memory / 1024 / 1024:.1f}MB")
        if self.allocated_disk is not None:
            resources.append(f"Disk: {self.allocated_disk / 1024 / 1024:.1f}MB")
        if self.allocated_network is not None:
            resources.append(f"Network: {self.allocated_network / 1024:.1f}KB/s")
        if self.allocated_gpu is not None:
            resources.append(f"GPU: {self.allocated_gpu / 1024 / 1024:.1f}MB")
            
        status_str = f"status={self.status}"
        if self.expiry_time:
            time_left = max(0, self.expiry_time - time.time())
            status_str += f", expires in {time_left:.1f}s"
            
        return (f"ResourceAllocation({self.requirement.component}, "
                f"{status_str}, resources=[{', '.join(resources)}])")


class ResourcePool:
    """
    Container for available system resources.
    
    This class tracks all available resources and their current allocation status.
    
    Attributes:
        total_cpu (float): Total available CPU cores.
        total_memory (int): Total available memory in bytes.
        total_disk (int): Total available disk space in bytes.
        total_network (int): Total available network bandwidth in bytes/s.
        total_gpu (int): Total available GPU memory in bytes.
        reserved_cpu (float): Reserved CPU cores for system use.
        reserved_memory (int): Reserved memory for system use.
        reserved_disk (int): Reserved disk space for system use.
    """
    
    def __init__(self):
        """Initialize a new ResourcePool based on system capabilities."""
        # Get system resources
        self.total_cpu = float(monitor.get_cpu_count())
        self.total_memory = monitor.get_memory_total()
        self.total_disk = monitor.get_disk_total()
        self.total_network = 1_000_000_000  # 1 GB/s as default
        self.total_gpu = 0  # Default to no GPU
        
        # Try to detect GPU
        try:
            gpu_memory = monitor.get_gpu_memory_total() if hasattr(monitor, 'get_gpu_memory_total') else 0
            self.total_gpu = gpu_memory
        except Exception as e:
            logger.debug(f"Could not detect GPU: {str(e)}")
        
        # Reserve resources for system use (20% of each)
        self.reserved_cpu = self.total_cpu * 0.2
        self.reserved_memory = int(self.total_memory * 0.2)
        self.reserved_disk = int(self.total_disk * 0.1)
        
        # Track allocated resources
        self.allocated_cpu = 0.0
        self.allocated_memory = 0
        self.allocated_disk = 0
        self.allocated_network = 0
        self.allocated_gpu = 0
        
        logger.info(f"Initialized resource pool: {self.total_cpu} CPU cores, "
                    f"{self.total_memory / 1024 / 1024 / 1024:.1f} GB memory, "
                    f"{self.total_disk / 1024 / 1024 / 1024:.1f} GB disk, "
                    f"{self.total_gpu / 1024 / 1024 / 1024:.1f if self.total_gpu > 0 else 0} GB GPU")
    
    def get_available(self) -> Dict:
        """
        Get available (unallocated) resources.
        
        Returns:
            Dict: Available resources.
        """
        return {
            "cpu": max(0, self.total_cpu - self.reserved_cpu - self.allocated_cpu),
            "memory": max(0, self.total_memory - self.reserved_memory - self.allocated_memory),
            "disk": max(0, self.total_disk - self.reserved_disk - self.allocated_disk),
            "network": max(0, self.total_network - self.allocated_network),
            "gpu": max(0, self.total_gpu - self.allocated_gpu)
        }
        
    def can_allocate(self, requirement: ResourceRequirement) -> bool:
        """
        Check if the required resources can be allocated.
        
        Args:
            requirement (ResourceRequirement): The resource requirement.
            
        Returns:
            bool: True if the resources can be allocated, False otherwise.
        """
        available = self.get_available()
        
        # Check each resource type
        if requirement.cpu is not None and requirement.cpu > available["cpu"]:
            return False
            
        if requirement.memory is not None and requirement.memory > available["memory"]:
            return False
            
        if requirement.disk is not None and requirement.disk > available["disk"]:
            return False
            
        if requirement.network is not None and requirement.network > available["network"]:
            return False
            
        if requirement.gpu is not None and requirement.gpu > available["gpu"]:
            return False
            
        return True
        
    def allocate(self, requirement: ResourceRequirement) -> Optional[ResourceAllocation]:
        """
        Allocate resources based on a requirement.
        
        Args:
            requirement (ResourceRequirement): The resource requirement.
            
        Returns:
            Optional[ResourceAllocation]: The allocation if successful, None otherwise.
        """
        if not self.can_allocate(requirement):
            return None
            
        # Create allocation
        allocation = ResourceAllocation(requirement)
        
        # Allocate each requested resource
        if requirement.cpu is not None:
            self.allocated_cpu += requirement.cpu
            allocation.allocated_cpu = requirement.cpu
            
        if requirement.memory is not None:
            self.allocated_memory += requirement.memory
            allocation.allocated_memory = requirement.memory
            
        if requirement.disk is not None:
            self.allocated_disk += requirement.disk
            allocation.allocated_disk = requirement.disk
            
        if requirement.network is not None:
            self.allocated_network += requirement.network
            allocation.allocated_network = requirement.network
            
        if requirement.gpu is not None:
            self.allocated_gpu += requirement.gpu
            allocation.allocated_gpu = requirement.gpu
            
        allocation.status = "active"
        logger.info(f"Allocated resources: {allocation}")
        
        return allocation
        
    def release(self, allocation: ResourceAllocation):
        """
        Release allocated resources.
        
        Args:
            allocation (ResourceAllocation): The allocation to release.
        """
        if allocation.allocated_cpu is not None:
            self.allocated_cpu -= allocation.allocated_cpu
            
        if allocation.allocated_memory is not None:
            self.allocated_memory -= allocation.allocated_memory
            
        if allocation.allocated_disk is not None:
            self.allocated_disk -= allocation.allocated_disk
            
        if allocation.allocated_network is not None:
            self.allocated_network -= allocation.allocated_network
            
        if allocation.allocated_gpu is not None:
            self.allocated_gpu -= allocation.allocated_gpu
            
        allocation.status = "released"
        logger.info(f"Released resources: {allocation}")
    
    def get_usage(self) -> Dict:
        """
        Get current resource usage.
        
        Returns:
            Dict: Resource usage statistics.
        """
        return {
            "cpu": {
                "total": self.total_cpu,
                "reserved": self.reserved_cpu,
                "allocated": self.allocated_cpu,
                "available": self.total_cpu - self.reserved_cpu - self.allocated_cpu,
                "percent_used": ((self.reserved_cpu + self.allocated_cpu) / self.total_cpu) * 100 if self.total_cpu > 0 else 0
            },
            "memory": {
                "total": self.total_memory,
                "reserved": self.reserved_memory,
                "allocated": self.allocated_memory,
                "available": self.total_memory - self.reserved_memory - self.allocated_memory,
                "percent_used": ((self.reserved_memory + self.allocated_memory) / self.total_memory) * 100 if self.total_memory > 0 else 0
            },
            "disk": {
                "total": self.total_disk,
                "reserved": self.reserved_disk,
                "allocated": self.allocated_disk,
                "available": self.total_disk - self.reserved_disk - self.allocated_disk,
                "percent_used": ((self.reserved_disk + self.allocated_disk) / self.total_disk) * 100 if self.total_disk > 0 else 0
            },
            "network": {
                "total": self.total_network,
                "allocated": self.allocated_network,
                "available": self.total_network - self.allocated_network,
                "percent_used": (self.allocated_network / self.total_network) * 100 if self.total_network > 0 else 0
            },
            "gpu": {
                "total": self.total_gpu,
                "allocated": self.allocated_gpu,
                "available": self.total_gpu - self.allocated_gpu,
                "percent_used": (self.allocated_gpu / self.total_gpu) * 100 if self.total_gpu > 0 else 0
            }
        }