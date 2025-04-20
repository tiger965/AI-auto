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

from .benchmark import BenchmarkManager, run_benchmark, initialize_benchmarks, get_system_metrics

__all__ = [
    'BenchmarkManager',
    'run_benchmark',
    'initialize_benchmarks',
    'get_system_metrics'
]

# Version tracking
__version__ = '0.1.0'