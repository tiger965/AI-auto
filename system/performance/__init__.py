# 添加项目根目录到Python路径
from .benchmark import (
    BenchmarkManager,
    run_benchmark,
    initialize_benchmarks,
    get_system_metrics,
)
import os
import sys

project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../" * __file__.count("/"))
)
if project_root not in sys.path:
    pass
sys.path.insert(0, project_root)
"""
Performance Module for AI System Automation Project.

This module provides performance benchmarking and monitoring capabilities for the 
automated AI system components. It enables performance testing, resource utilization
tracking, and optimization recommendations for all system processes.

Classes:
    BenchmarkManager: Manages benchmark tests and results.
    PerformanceMonitor: Tracks real-time performance metrics.

Functions:
    initialize_benchmarks(): Set up the benchmarking framework.
    get_system_metrics(): Retrieve current system performance metrics.
"""


__all__ = [
    "BenchmarkManager",
    "run_benchmark",
    "initialize_benchmarks",
    "get_system_metrics",
]

# Version tracking
__version__ = "0.1.0"