"""
Benchmark Module for AI System Performance Testing.

This module implements a comprehensive performance benchmarking framework for
measuring and analyzing the system's performance metrics. It provides tools to run
standardized tests, collect metrics, and generate performance reports.

Classes:
    BenchmarkManager: Coordinates benchmark tests and manages results.
    BenchmarkTest: Base class for individual benchmark test implementations.
    BenchmarkResult: Container for benchmark test results and analysis.

Functions:
    run_benchmark(test_name, **kwargs): Execute a specific benchmark test.
    initialize_benchmarks(): Set up the benchmarking environment.
    get_system_metrics(): Collect current system performance metrics.
"""

import time
import logging
import threading
import statistics
from typing import Dict, List, Optional, Any, Tuple, Callable
import json
import os
import sys
import inspect

# Import local system modules
from .. import monitor
from .. import cache

# Configure logging
logger = logging.getLogger(__name__)

class BenchmarkResult:
    """
    Container for benchmark test results.
    
    Attributes:
        test_name (str): Name of the benchmark test.
        execution_time (float): Time taken to execute the test in seconds.
        memory_usage (Dict): Memory usage statistics during the test.
        cpu_usage (Dict): CPU usage statistics during the test.
        throughput (Optional[float]): Operations per second if applicable.
        latency (Optional[Dict]): Latency statistics if applicable.
        timestamp (float): When the benchmark was run.
        custom_metrics (Dict): Any test-specific metrics.
        status (str): Status of the benchmark (success, failed, etc.).
    """
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.execution_time = 0.0
        self.memory_usage = {}
        self.cpu_usage = {}
        self.throughput = None
        self.latency = {}
        self.timestamp = time.time()
        self.custom_metrics = {}
        self.status = "initialized"
        
    def add_metric(self, name: str, value: Any):
        """Add a custom metric to the result."""
        self.custom_metrics[name] = value
        
    def set_status(self, status: str):
        """Update the status of the benchmark test."""
        self.status = status
        
    def to_dict(self) -> Dict:
        """Convert the benchmark result to a dictionary."""
        return {
            "test_name": self.test_name,
            "execution_time": self.execution_time,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "throughput": self.throughput,
            "latency": self.latency,
            "timestamp": self.timestamp,
            "custom_metrics": self.custom_metrics,
            "status": self.status
        }
    
    def to_json(self) -> str:
        """Convert the benchmark result to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def __str__(self) -> str:
        """String representation of the benchmark result."""
        return f"BenchmarkResult({self.test_name}, status={self.status}, time={self.execution_time:.4f}s)"


class BenchmarkTest:
    """
    Base class for all benchmark tests.
    
    This serves as a template for creating specific benchmark tests.
    Subclasses must implement the run() method.
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.result = BenchmarkResult(name)
        
    def setup(self):
        """Prepare the environment for the benchmark test."""
        pass
        
    def run(self) -> BenchmarkResult:
        """
        Execute the benchmark test.
        
        Must be implemented by subclasses.
        
        Returns:
            BenchmarkResult: The result of the benchmark test.
        """
        raise NotImplementedError("Subclasses must implement run()")
        
    def teardown(self):
        """Clean up after the benchmark test."""
        pass
    
    def execute(self) -> BenchmarkResult:
        """
        Full execution of the benchmark test, including setup and teardown.
        
        Returns:
            BenchmarkResult: The result of the benchmark test.
        """
        try:
            self.setup()
            
            # Record system state before test
            initial_metrics = get_system_metrics()
            
            # Run the benchmark and time it
            start_time = time.time()
            self.result = self.run()
            end_time = time.time()
            
            # Record system state after test
            final_metrics = get_system_metrics()
            
            # Update result with execution time
            self.result.execution_time = end_time - start_time
            
            # Calculate resource usage
            self.result.memory_usage = {
                "peak": final_metrics["memory"]["peak"],
                "diff": final_metrics["memory"]["used"] - initial_metrics["memory"]["used"]
            }
            
            self.result.cpu_usage = {
                "average": statistics.mean(monitor.get_cpu_history(seconds=int(end_time - start_time))),
                "peak": max(monitor.get_cpu_history(seconds=int(end_time - start_time)))
            }
            
            self.result.set_status("success")
            
        except Exception as e:
            logger.error(f"Benchmark {self.name} failed: {str(e)}")
            self.result.set_status("failed")
            self.result.add_metric("error", str(e))
        finally:
            self.teardown()
            
        return self.result


class BenchmarkManager:
    """
    Manages benchmark tests and results.
    
    This class coordinates the execution of benchmark tests and
    stores their results for analysis.
    
    Attributes:
        registered_tests (Dict): Mapping of test names to BenchmarkTest instances.
        results (List): List of benchmark results.
    """
    
    def __init__(self):
        self.registered_tests = {}
        self.results = []
        self.config = {}
        self.initialized = False
        
    def register_test(self, test: BenchmarkTest):
        """
        Register a benchmark test with the manager.
        
        Args:
            test (BenchmarkTest): The benchmark test to register.
        """
        self.registered_tests[test.name] = test
        logger.info(f"Registered benchmark test: {test.name}")
        
    def run_test(self, test_name: str, **kwargs) -> BenchmarkResult:
        """
        Run a specific benchmark test.
        
        Args:
            test_name (str): Name of the test to run.
            **kwargs: Additional parameters to pass to the test.
            
        Returns:
            BenchmarkResult: The result of the benchmark test.
            
        Raises:
            ValueError: If the test is not registered.
        """
        if not self.initialized:
            initialize_benchmarks()
            
        if test_name not in self.registered_tests:
            raise ValueError(f"Benchmark test '{test_name}' not registered")
            
        test = self.registered_tests[test_name]
        
        # Apply any overrides from kwargs
        for key, value in kwargs.items():
            if hasattr(test, key):
                setattr(test, key, value)
                
        # Execute the test
        result = test.execute()
        
        # Store the result
        self.results.append(result)
        
        return result
        
    def run_all_tests(self) -> List[BenchmarkResult]:
        """
        Run all registered benchmark tests.
        
        Returns:
            List[BenchmarkResult]: Results of all benchmark tests.
        """
        results = []
        for test_name in self.registered_tests:
            results.append(self.run_test(test_name))
        return results
        
    def get_results(self, test_name: Optional[str] = None) -> List[BenchmarkResult]:
        """
        Get benchmark results.
        
        Args:
            test_name (Optional[str]): Filter results by test name.
            
        Returns:
            List[BenchmarkResult]: Filtered benchmark results.
        """
        if test_name:
            return [r for r in self.results if r.test_name == test_name]
        return self.results
        
    def export_results(self, filepath: str):
        """
        Export benchmark results to a file.
        
        Args:
            filepath (str): Path to the output file.
        """
        with open(filepath, 'w') as f:
            json.dump([r.to_dict() for r in self.results], f, indent=2)
        logger.info(f"Exported benchmark results to {filepath}")
        
    def import_results(self, filepath: str):
        """
        Import benchmark results from a file.
        
        Args:
            filepath (str): Path to the input file.
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        for result_data in data:
            result = BenchmarkResult(result_data["test_name"])
            for key, value in result_data.items():
                setattr(result, key, value)
            self.results.append(result)
            
        logger.info(f"Imported {len(data)} benchmark results from {filepath}")
        
    def compare_results(self, result1: BenchmarkResult, result2: BenchmarkResult) -> Dict:
        """
        Compare two benchmark results.
        
        Args:
            result1 (BenchmarkResult): First benchmark result.
            result2 (BenchmarkResult): Second benchmark result.
            
        Returns:
            Dict: Comparison metrics.
        """
        comparison = {}
        
        # Compare execution time
        time_diff = result2.execution_time - result1.execution_time
        time_pct = (time_diff / result1.execution_time) * 100 if result1.execution_time > 0 else float('inf')
        comparison["execution_time"] = {
            "diff": time_diff,
            "percent": time_pct,
            "improved": time_diff < 0
        }
        
        # Compare memory usage
        if "peak" in result1.memory_usage and "peak" in result2.memory_usage:
            memory_diff = result2.memory_usage["peak"] - result1.memory_usage["peak"]
            memory_pct = (memory_diff / result1.memory_usage["peak"]) * 100 if result1.memory_usage["peak"] > 0 else float('inf')
            comparison["memory_usage"] = {
                "diff": memory_diff,
                "percent": memory_pct,
                "improved": memory_diff < 0
            }
            
        # Compare throughput if available
        if result1.throughput and result2.throughput:
            throughput_diff = result2.throughput - result1.throughput
            throughput_pct = (throughput_diff / result1.throughput) * 100 if result1.throughput > 0 else float('inf')
            comparison["throughput"] = {
                "diff": throughput_diff,
                "percent": throughput_pct,
                "improved": throughput_diff > 0  # Higher throughput is better
            }
            
        return comparison


# Global benchmark manager instance
_benchmark_manager = None

def get_benchmark_manager() -> BenchmarkManager:
    """
    Get the global benchmark manager instance.
    
    Returns:
        BenchmarkManager: The global benchmark manager.
    """
    global _benchmark_manager
    if _benchmark_manager is None:
        _benchmark_manager = BenchmarkManager()
    return _benchmark_manager

def run_benchmark(test_name: str, **kwargs) -> BenchmarkResult:
    """
    Run a specific benchmark test using the global manager.
    
    Args:
        test_name (str): Name of the test to run.
        **kwargs: Additional parameters to pass to the test.
        
    Returns:
        BenchmarkResult: The result of the benchmark test.
    """
    return get_benchmark_manager().run_test(test_name, **kwargs)

def initialize_benchmarks():
    """
    Initialize the benchmarking framework.
    
    This function sets up default benchmark tests and configures
    the benchmarking environment.
    """
    manager = get_benchmark_manager()
    if manager.initialized:
        return
    
    # Register core system benchmark tests
    from .. import monitor
    
    # Load configuration if available
    try:
        from .. import config_loader
        manager.config = config_loader.load_config("benchmark")
        logger.info("Loaded benchmark configuration")
    except (ImportError, Exception) as e:
        logger.warning(f"Could not load benchmark configuration: {str(e)}")
        manager.config = {}
    
    # Mark as initialized
    manager.initialized = True
    logger.info("Benchmark framework initialized")

def get_system_metrics() -> Dict:
    """
    Collect current system performance metrics.
    
    Returns:
        Dict: Current system metrics including CPU, memory, and I/O.
    """
    metrics = {
        "timestamp": time.time(),
        "cpu": {
            "usage": monitor.get_cpu_usage(),
            "count": monitor.get_cpu_count()
        },
        "memory": {
            "total": monitor.get_memory_total(),
            "used": monitor.get_memory_used(),
            "peak": monitor.get_memory_peak()
        },
        "io": {
            "disk_read": monitor.get_disk_read(),
            "disk_write": monitor.get_disk_write(),
            "net_sent": monitor.get_net_sent(),
            "net_recv": monitor.get_net_recv()
        }
    }
    return metrics


# Standard benchmark test implementations
class LatencyBenchmark(BenchmarkTest):
    """
    Benchmark test for measuring operation latency.
    """
    
    def __init__(self, operation: Callable, iterations: int = 1000, name: str = "latency_benchmark"):
        super().__init__(name)
        self.operation = operation
        self.iterations = iterations
        
    def run(self) -> BenchmarkResult:
        """
        Execute the latency benchmark.
        
        Returns:
            BenchmarkResult: The benchmark result.
        """
        result = BenchmarkResult(self.name)
        latencies = []
        
        for _ in range(self.iterations):
            start_time = time.time()
            self.operation()
            end_time = time.time()
            latencies.append((end_time - start_time) * 1000)  # Convert to ms
            
        result.latency = {
            "min": min(latencies),
            "max": max(latencies),
            "avg": statistics.mean(latencies),
            "median": statistics.median(latencies),
            "p95": statistics.quantiles(latencies, n=20)[18],  # 95th percentile
            "p99": statistics.quantiles(latencies, n=100)[98]  # 99th percentile
        }
        
        result.throughput = self.iterations / sum(latencies) * 1000  # ops/second
        result.set_status("success")
        return result


class ThroughputBenchmark(BenchmarkTest):
    """
    Benchmark test for measuring operation throughput.
    """
    
    def __init__(self, operation: Callable, duration: float = 5.0, name: str = "throughput_benchmark"):
        super().__init__(name)
        self.operation = operation
        self.duration = duration
        
    def run(self) -> BenchmarkResult:
        """
        Execute the throughput benchmark.
        
        Returns:
            BenchmarkResult: The benchmark result.
        """
        result = BenchmarkResult(self.name)
        operations_count = 0
        end_time = time.time() + self.duration
        
        while time.time() < end_time:
            self.operation()
            operations_count += 1
            
        result.throughput = operations_count / self.duration
        result.set_status("success")
        return result


class ResourceUsageBenchmark(BenchmarkTest):
    """
    Benchmark test for measuring resource usage during an operation.
    """
    
    def __init__(self, operation: Callable, name: str = "resource_benchmark"):
        super().__init__(name)
        self.operation = operation
        
    def run(self) -> BenchmarkResult:
        """
        Execute the resource usage benchmark.
        
        Returns:
            BenchmarkResult: The benchmark result.
        """
        result = BenchmarkResult(self.name)
        
        # Get initial metrics
        initial_metrics = get_system_metrics()
        
        # Run the operation
        self.operation()
        
        # Get final metrics
        final_metrics = get_system_metrics()
        
        # Calculate resource usage
        result.memory_usage = {
            "initial": initial_metrics["memory"]["used"],
            "final": final_metrics["memory"]["used"],
            "diff": final_metrics["memory"]["used"] - initial_metrics["memory"]["used"],
            "peak": final_metrics["memory"]["peak"]
        }
        
        result.cpu_usage = {
            "average": statistics.mean(monitor.get_cpu_history(seconds=5)),
            "peak": max(monitor.get_cpu_history(seconds=5))
        }
        
        result.add_metric("io_read", final_metrics["io"]["disk_read"] - initial_metrics["io"]["disk_read"])
        result.add_metric("io_write", final_metrics["io"]["disk_write"] - initial_metrics["io"]["disk_write"])
        result.add_metric("net_sent", final_metrics["io"]["net_sent"] - initial_metrics["io"]["net_sent"])
        result.add_metric("net_recv", final_metrics["io"]["net_recv"] - initial_metrics["io"]["net_recv"])
        
        result.set_status("success")
        return result


# Register standard benchmark tests
def register_standard_tests():
    """Register the standard benchmark tests with the global manager."""
    manager = get_benchmark_manager()
    
    # Define a simple no-op function for testing
    def noop():
        pass
    
    # Register standard tests
    manager.register_test(LatencyBenchmark(noop, name="system_latency_baseline"))
    manager.register_test(ThroughputBenchmark(noop, name="system_throughput_baseline"))
    manager.register_test(ResourceUsageBenchmark(noop, name="system_resource_baseline"))
    
    # Register cache benchmarks if available
    try:
        from .. import cache
        
        def cache_op():
            key = f"benchmark_{time.time()}"
            cache.set(key, {"data": "benchmark"})
            result = cache.get(key)
            cache.delete(key)
            return result
            
        manager.register_test(LatencyBenchmark(cache_op, name="cache_latency"))
        manager.register_test(ThroughputBenchmark(cache_op, name="cache_throughput"))
        manager.register_test(ResourceUsageBenchmark(cache_op, name="cache_resource_usage"))
    except (ImportError, Exception) as e:
        logger.warning(f"Could not register cache benchmarks: {str(e)}")