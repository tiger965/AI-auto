"""
Performance Testing Framework for System Components
-------------------------------------------------
This module provides comprehensive performance testing capabilities for CPU, memory,
I/O, network, and integrated system testing. It includes both individual test cases
and test suite management functionality.

Classes:
- BaseTestCase: Abstract base class for all test cases
- CPUTestCase: Tests CPU performance under various loads
- MemoryTestCase: Tests memory allocation, access, and bandwidth
- IOTestCase: Tests file system operations performance
- NetworkTestCase: Tests network throughput and latency
- IntegrationTestCase: Combines multiple resource tests with cache operations
- TestSuite: Manages collections of test cases with aggregated reporting

Functions:
- run_test_suite: Executes a named or custom test suite
- get_available_test_suites: Returns list of predefined test suites
- create_custom_test_suite: Creates a new test suite with specified test cases
"""

import os
import time
import random
import socket
import multiprocessing
import tempfile
import statistics
import json
import logging
import datetime
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional, Union, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('performance_tests')

class BaseTestCase(ABC):
    """Base class for all performance test cases."""
    
    def __init__(self, name: str, duration: int = 10, iterations: int = 3):
        """
        Initialize a test case.
        
        Args:
            name: Identifier for the test case
            duration: Duration of each test iteration in seconds
            iterations: Number of times to repeat the test
        """
        self.name = name
        self.duration = duration
        self.iterations = iterations
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    def run(self) -> Dict[str, Any]:
        """
        Execute the test case and return results.
        
        Returns:
            Dictionary containing test results and metrics
        """
        logger.info(f"Starting test: {self.name}")
        self.results = {
            'name': self.name,
            'start_time': datetime.datetime.now().isoformat(),
            'metrics': [],
            'summary': {},
            'duration': self.duration,
            'iterations': self.iterations
        }
        
        try:
            # Run test iterations
            iteration_results = []
            for i in range(self.iterations):
                logger.info(f"Running iteration {i+1}/{self.iterations}")
                self.start_time = time.time()
                iteration_result = self._run_test()
                self.end_time = time.time()
                elapsed = self.end_time - self.start_time
                
                iteration_result['elapsed_time'] = elapsed
                iteration_result['iteration'] = i + 1
                iteration_results.append(iteration_result)
                self.results['metrics'].append(iteration_result)
                
                logger.info(f"Iteration {i+1} completed in {elapsed:.2f}s")
            
            # Calculate summary statistics
            self._calculate_summary(iteration_results)
            self.results['end_time'] = datetime.datetime.now().isoformat()
            self.results['success'] = True
            
        except Exception as e:
            logger.error(f"Test {self.name} failed: {str(e)}")
            self.results['success'] = False
            self.results['error'] = str(e)
            
        return self.results
    
    def _calculate_summary(self, iteration_results: List[Dict[str, Any]]) -> None:
        """
        Calculate summary statistics from iteration results.
        
        Args:
            iteration_results: List of results from each test iteration
        """
        # Extract main performance metric for summary
        main_metrics = {}
        
        # Process all metric keys across iterations
        for result in iteration_results:
            for key, value in result.items():
                if isinstance(value, (int, float)) and key != 'iteration':
                    if key not in main_metrics:
                        main_metrics[key] = []
                    main_metrics[key].append(value)
        
        # Calculate statistics for each metric
        summary = {}
        for metric, values in main_metrics.items():
            if len(values) > 0:
                summary[metric] = {
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'min': min(values),
                    'max': max(values),
                    'stddev': statistics.stdev(values) if len(values) > 1 else 0
                }
        
        self.results['summary'] = summary
    
    @abstractmethod
    def _run_test(self) -> Dict[str, Any]:
        """
        Implement the actual test logic.
        
        Returns:
            Dictionary with test metrics
        """
        pass


class CPUTestCase(BaseTestCase):
    """Test case for CPU performance evaluation."""
    
    def __init__(self, name: str = "CPU Performance Test", 
                 duration: int = 10, 
                 iterations: int = 3,
                 num_processes: int = None):
        """
        Initialize CPU test case.
        
        Args:
            name: Test identifier
            duration: Duration of each test iteration in seconds
            iterations: Number of test iterations
            num_processes: Number of CPU processes to use (defaults to CPU count)
        """
        super().__init__(name, duration, iterations)
        self.num_processes = num_processes or multiprocessing.cpu_count()
    
    def _cpu_intensive_task(self, duration: int) -> Dict[str, float]:
        """
        Execute a CPU-intensive calculation.
        
        Args:
            duration: How long to run the task in seconds
            
        Returns:
            Dictionary with performance metrics
        """
        operations = 0
        start_time = time.time()
        end_time = start_time + duration
        
        # Prime number calculation as CPU-intensive task
        while time.time() < end_time:
            # Find prime numbers to stress CPU
            for i in range(2, 10000):
                is_prime = True
                for j in range(2, int(i ** 0.5) + 1):
                    if i % j == 0:
                        is_prime = False
                        break
                if is_prime:
                    operations += 1
        
        elapsed = time.time() - start_time
        ops_per_sec = operations / elapsed
        
        return {
            'operations': operations,
            'ops_per_second': ops_per_sec
        }
    
    def _run_test(self) -> Dict[str, Any]:
        """
        Run CPU performance test using multiple processes.
        
        Returns:
            Dictionary with test metrics
        """
        # Create process pool
        with multiprocessing.Pool(processes=self.num_processes) as pool:
            # Run CPU-intensive tasks across processes
            results = pool.map(self._cpu_intensive_task, [self.duration] * self.num_processes)
        
        # Aggregate results from all processes
        total_operations = sum(r['operations'] for r in results)
        total_ops_per_sec = sum(r['ops_per_second'] for r in results)
        avg_ops_per_sec_per_core = total_ops_per_sec / self.num_processes
        
        return {
            'total_operations': total_operations,
            'total_ops_per_second': total_ops_per_sec,
            'avg_ops_per_second_per_core': avg_ops_per_sec_per_core,
            'num_cores_used': self.num_processes
        }


class MemoryTestCase(BaseTestCase):
    """Test case for memory performance evaluation."""
    
    def __init__(self, name: str = "Memory Performance Test", 
                 duration: int = 10, 
                 iterations: int = 3,
                 allocation_size_mb: int = 100,
                 allocation_count: int = 10):
        """
        Initialize memory test case.
        
        Args:
            name: Test identifier
            duration: Duration of each test iteration in seconds
            iterations: Number of test iterations
            allocation_size_mb: Size of each memory block in MB
            allocation_count: Number of memory blocks to allocate
        """
        super().__init__(name, duration, iterations)
        self.allocation_size_mb = allocation_size_mb
        self.allocation_count = allocation_count
    
    def _run_test(self) -> Dict[str, Any]:
        """
        Run memory allocation and access tests.
        
        Returns:
            Dictionary with test metrics
        """
        memory_blocks = []
        allocation_times = []
        access_times = []
        
        # Convert MB to bytes
        block_size_bytes = self.allocation_size_mb * 1024 * 1024
        
        # Test memory allocation speed
        for i in range(self.allocation_count):
            # Time the allocation of a large memory block
            start_time = time.time()
            memory_block = bytearray(block_size_bytes)
            end_time = time.time()
            
            memory_blocks.append(memory_block)
            allocation_times.append(end_time - start_time)
        
        # Test memory access speed
        num_access_tests = 1000
        for i in range(min(len(memory_blocks), 5)):  # Test access on up to 5 blocks
            block = memory_blocks[i]
            start_time = time.time()
            
            # Perform random memory accesses
            for _ in range(num_access_tests):
                idx = random.randint(0, len(block) - 1)
                block[idx] = random.randint(0, 255)
            
            end_time = time.time()
            access_times.append((end_time - start_time) / num_access_tests)
        
        # Calculate memory bandwidth approximation
        total_mb_allocated = self.allocation_size_mb * len(memory_blocks)
        total_allocation_time = sum(allocation_times)
        
        if total_allocation_time > 0:
            allocation_bandwidth_mbps = total_mb_allocated / total_allocation_time
        else:
            allocation_bandwidth_mbps = 0
        
        # Clear memory blocks before exit
        memory_blocks = None
        
        return {
            'allocation_size_mb': self.allocation_size_mb,
            'total_allocated_mb': total_mb_allocated,
            'avg_allocation_time_sec': statistics.mean(allocation_times) if allocation_times else 0,
            'avg_access_time_sec': statistics.mean(access_times) if access_times else 0,
            'allocation_bandwidth_mbps': allocation_bandwidth_mbps,
            'allocation_count': self.allocation_count
        }


class IOTestCase(BaseTestCase):
    """Test case for file I/O performance evaluation."""
    
    def __init__(self, name: str = "I/O Performance Test", 
                 duration: int = 10, 
                 iterations: int = 3,
                 file_size_mb: int = 100,
                 block_size_kb: int = 64,
                 test_dir: str = None):
        """
        Initialize I/O test case.
        
        Args:
            name: Test identifier
            duration: Duration of each test iteration in seconds
            iterations: Number of test iterations
            file_size_mb: Size of test file in MB
            block_size_kb: Size of each I/O operation in KB
            test_dir: Directory to use for testing (uses temp dir if None)
        """
        super().__init__(name, duration, iterations)
        self.file_size_mb = file_size_mb
        self.block_size_kb = block_size_kb
        self.block_size_bytes = self.block_size_kb * 1024
        self.test_dir = test_dir
        
    def _run_test(self) -> Dict[str, Any]:
        """
        Run file I/O performance tests.
        
        Returns:
            Dictionary with test metrics
        """
        results = {}
        
        # Use specified directory or temp directory
        with tempfile.TemporaryDirectory() if not self.test_dir else self._dummy_context(self.test_dir) as test_dir:
            test_file = os.path.join(test_dir if not self.test_dir else self.test_dir, 
                                     f"io_test_{int(time.time())}.dat")
            
            # Test sequential write performance
            write_start = time.time()
            write_size = self._sequential_write(test_file)
            write_time = time.time() - write_start
            
            # Test sequential read performance
            read_start = time.time()
            read_size = self._sequential_read(test_file)
            read_time = time.time() - read_start
            
            # Test random access performance
            random_start = time.time()
            random_ops = self._random_access(test_file)
            random_time = time.time() - random_start
            
            # Calculate metrics
            results['write_size_mb'] = write_size / (1024 * 1024)
            results['read_size_mb'] = read_size / (1024 * 1024)
            
            if write_time > 0:
                results['write_throughput_mbps'] = results['write_size_mb'] / write_time
            else:
                results['write_throughput_mbps'] = 0
                
            if read_time > 0:
                results['read_throughput_mbps'] = results['read_size_mb'] / read_time
            else:
                results['read_throughput_mbps'] = 0
                
            if random_time > 0:
                results['random_iops'] = random_ops / random_time
            else:
                results['random_iops'] = 0
            
            # Clean up test file if we're using our own directory
            if self.test_dir and os.path.exists(test_file):
                try:
                    os.remove(test_file)
                except:
                    pass
        
        return results
    
    def _dummy_context(self, directory):
        """
        Create a dummy context manager for use with 'with' statement.
        
        Args:
            directory: Directory name to return
            
        Returns:
            A context manager that yields the directory
        """
        class DummyContext:
            def __enter__(self):
                # Ensure the directory exists
                os.makedirs(directory, exist_ok=True)
                return directory
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        
        return DummyContext()
    
    def _sequential_write(self, filename: str) -> int:
        """
        Perform sequential write test.
        
        Args:
            filename: Path to test file
            
        Returns:
            Number of bytes written
        """
        # Calculate number of blocks to write
        target_bytes = self.file_size_mb * 1024 * 1024
        total_written = 0
        
        # Random data block to write
        data_block = os.urandom(self.block_size_bytes)
        
        with open(filename, 'wb') as f:
            while total_written < target_bytes:
                bytes_written = f.write(data_block)
                total_written += bytes_written
                
        return total_written
    
    def _sequential_read(self, filename: str) -> int:
        """
        Perform sequential read test.
        
        Args:
            filename: Path to test file
            
        Returns:
            Number of bytes read
        """
        total_read = 0
        
        with open(filename, 'rb') as f:
            while True:
                data = f.read(self.block_size_bytes)
                if not data:
                    break
                total_read += len(data)
                
        return total_read
    
    def _random_access(self, filename: str) -> int:
        """
        Perform random access I/O test.
        
        Args:
            filename: Path to test file
            
        Returns:
            Number of I/O operations performed
        """
        # Get file size
        file_size = os.path.getsize(filename)
        if file_size <= 0:
            return 0
            
        operations = 0
        start_time = time.time()
        end_time = start_time + self.duration / 3  # Use 1/3 of test duration for random I/O
        
        with open(filename, 'rb+') as f:
            while time.time() < end_time:
                # Pick random position in file
                position = random.randint(0, max(0, file_size - self.block_size_bytes))
                f.seek(position)
                
                # 50% chance of read or write
                if random.random() < 0.5:
                    # Read
                    f.read(min(self.block_size_bytes, file_size - position))
                else:
                    # Write
                    f.write(os.urandom(min(self.block_size_bytes, file_size - position)))
                
                operations += 1
                
        return operations


class NetworkTestCase(BaseTestCase):
    """Test case for network performance evaluation."""
    
    def __init__(self, name: str = "Network Performance Test", 
                 duration: int = 10, 
                 iterations: int = 3,
                 target_host: str = "localhost",
                 target_port: int = 0,  # 0 means auto-assign
                 packet_size_kb: int = 64,
                 protocol: str = "tcp"):
        """
        Initialize network test case.
        
        Args:
            name: Test identifier
            duration: Duration of each test iteration in seconds
            iterations: Number of test iterations
            target_host: Target host for network tests
            target_port: Target port for network tests
            packet_size_kb: Size of network packets in KB
            protocol: Network protocol to test ('tcp' or 'udp')
        """
        super().__init__(name, duration, iterations)
        self.target_host = target_host
        self.target_port = target_port
        self.packet_size_kb = packet_size_kb
        self.packet_size_bytes = self.packet_size_kb * 1024
        self.protocol = protocol.lower()
        self.server_process = None
    
    def _run_test(self) -> Dict[str, Any]:
        """
        Run network performance tests.
        
        Returns:
            Dictionary with test metrics
        """
        if self.target_host == "localhost":
            # Need to run a local server for testing
            self._start_server()
            # Allow server to start
            time.sleep(1)
            
        # Run the appropriate test based on protocol
        if self.protocol == "tcp":
            results = self._test_tcp_performance()
        elif self.protocol == "udp":
            results = self._test_udp_performance()
        else:
            raise ValueError(f"Unsupported protocol: {self.protocol}")
        
        # Cleanup server if we started one
        if self.target_host == "localhost" and self.server_process:
            self.server_process.terminate()
            self.server_process.join(timeout=2)
            self.server_process = None
            
        return results
    
    def _start_server(self) -> None:
        """Start a network test server in a separate process."""
        if self.protocol == "tcp":
            self.server_process = multiprocessing.Process(
                target=self._tcp_server
            )
        else:  # UDP
            self.server_process = multiprocessing.Process(
                target=self._udp_server
            )
            
        self.server_process.daemon = True
        self.server_process.start()
    
    def _tcp_server(self) -> None:
        """Run a TCP echo server for testing."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('localhost', self.target_port))
        server.listen(5)
        
        # Get the assigned port
        _, self.target_port = server.getsockname()
        
        try:
            while True:
                client, _ = server.accept()
                try:
                    while True:
                        data = client.recv(self.packet_size_bytes)
                        if not data:
                            break
                        client.sendall(data)
                except:
                    pass
                finally:
                    client.close()
        except:
            pass
        finally:
            server.close()
    
    def _udp_server(self) -> None:
        """Run a UDP echo server for testing."""
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.bind(('localhost', self.target_port))
        
        # Get the assigned port
        _, self.target_port = server.getsockname()
        
        try:
            while True:
                data, addr = server.recvfrom(self.packet_size_bytes)
                server.sendto(data, addr)
        except:
            pass
        finally:
            server.close()
    
    def _test_tcp_performance(self) -> Dict[str, Any]:
        """
        Test TCP network performance.
        
        Returns:
            Dictionary with test metrics
        """
        packets_sent = 0
        packets_received = 0
        bytes_sent = 0
        bytes_received = 0
        latencies = []
        
        # Create test data
        test_data = os.urandom(self.packet_size_bytes)
        
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((self.target_host, self.target_port))
            
            start_time = time.time()
            end_time = start_time + self.duration
            
            while time.time() < end_time:
                # Measure round-trip time
                packet_start = time.time()
                
                # Send data
                client.sendall(test_data)
                bytes_sent += len(test_data)
                packets_sent += 1
                
                # Receive response
                received = 0
                while received < self.packet_size_bytes:
                    chunk = client.recv(self.packet_size_bytes - received)
                    if not chunk:
                        break
                    received += len(chunk)
                    bytes_received += len(chunk)
                
                if received == self.packet_size_bytes:
                    packets_received += 1
                    
                # Calculate latency
                packet_end = time.time()
                latencies.append((packet_end - packet_start) * 1000)  # Convert to ms
                
        except Exception as e:
            logger.error(f"TCP test error: {str(e)}")
        finally:
            try:
                client.close()
            except:
                pass
            
        # Calculate results
        total_time = time.time() - start_time
        
        if total_time > 0:
            throughput_mbps = (bytes_sent + bytes_received) / (total_time * 1024 * 1024 / 8)
        else:
            throughput_mbps = 0
            
        if packets_sent > 0:
            packet_loss_pct = 100 * (1 - packets_received / packets_sent)
        else:
            packet_loss_pct = 0
            
        return {
            'protocol': 'tcp',
            'throughput_mbps': throughput_mbps,
            'packets_sent': packets_sent,
            'packets_received': packets_received,
            'packet_loss_pct': packet_loss_pct,
            'avg_latency_ms': statistics.mean(latencies) if latencies else 0,
            'min_latency_ms': min(latencies) if latencies else 0,
            'max_latency_ms': max(latencies) if latencies else 0,
            'packet_size_kb': self.packet_size_kb
        }
    
    def _test_udp_performance(self) -> Dict[str, Any]:
        """
        Test UDP network performance.
        
        Returns:
            Dictionary with test metrics
        """
        packets_sent = 0
        packets_received = 0
        bytes_sent = 0
        bytes_received = 0
        latencies = []
        
        # Create test data
        test_data = os.urandom(self.packet_size_bytes)
        
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client.settimeout(0.5)  # Set timeout for UDP receive
            
            start_time = time.time()
            end_time = start_time + self.duration
            
            while time.time() < end_time:
                # Measure round-trip time
                packet_start = time.time()
                
                # Send data
                client.sendto(test_data, (self.target_host, self.target_port))
                bytes_sent += len(test_data)
                packets_sent += 1
                
                # Receive response
                try:
                    data, _ = client.recvfrom(self.packet_size_bytes)
                    bytes_received += len(data)
                    packets_received += 1
                    
                    # Calculate latency
                    packet_end = time.time()
                    latencies.append((packet_end - packet_start) * 1000)  # Convert to ms
                except socket.timeout:
                    # Packet was lost
                    pass
                
        except Exception as e:
            logger.error(f"UDP test error: {str(e)}")
        finally:
            try:
                client.close()
            except:
                pass
            
        # Calculate results
        total_time = time.time() - start_time
        
        if total_time > 0:
            throughput_mbps = (bytes_sent + bytes_received) / (total_time * 1024 * 1024 / 8)
        else:
            throughput_mbps = 0
            
        if packets_sent > 0:
            packet_loss_pct = 100 * (1 - packets_received / packets_sent)
        else:
            packet_loss_pct = 0
            
        return {
            'protocol': 'udp',
            'throughput_mbps': throughput_mbps,
            'packets_sent': packets_sent,
            'packets_received': packets_received, 
            'packet_loss_pct': packet_loss_pct,
            'avg_latency_ms': statistics.mean(latencies) if latencies else 0,
            'min_latency_ms': min(latencies) if latencies else 0,
            'max_latency_ms': max(latencies) if latencies else 0,
            'packet_size_kb': self.packet_size_kb
        }


class IntegrationTestCase(BaseTestCase):
    """Test case for integrated system performance evaluation."""
    
    def __init__(self, name: str = "Integration Test", 
                 duration: int = 30, 
                 iterations: int = 2,
                 cpu_load_percent: int = 30,
                 memory_load_percent: int = 30,
                 io_load_percent: int = 20,
                 network_load_percent: int = 20,
                 cache_size_mb: int = 100,
                 cache_operations: int = 1000):
        """
        Initialize integration test case.
        
        Args:
            name: Test identifier
            duration: Duration of each test iteration in seconds
            iterations: Number of test iterations
            cpu_load_percent: CPU load percentage (0-100)
            memory_load_percent: Memory load percentage (0-100)
            io_load_percent: I/O load percentage (0-100)
            network_load_percent: Network load percentage (0-100)
            cache_size_mb: Cache size in MB for cache testing
            cache_operations: Number of cache operations to perform
        """
        super().__init__(name, duration, iterations)
        self.cpu_load_percent = cpu_load_percent
        self.memory_load_percent = memory_load_percent
        self.io_load_percent = io_load_percent
        self.network_load_percent = network_load_percent
        self.cache_size_mb = cache_size_mb
        self.cache_operations = cache_operations
        
        # Ensure load percentages sum to 100
        total_load = (cpu_load_percent + memory_load_percent + 
                      io_load_percent + network_load_percent)
        
        if total_load != 100:
            # Normalize to 100%
            factor = 100 / total_load
            self.cpu_load_percent *= factor
            self.memory_load_percent *= factor
            self.io_load_percent *= factor
            self.network_load_percent *= factor
    
    def _run_test(self) -> Dict[str, Any]:
        """
        Run integrated performance test with all components.
        
        Returns:
            Dictionary with test metrics
        """
        results = {}
        all_processes = []
        manager = multiprocessing.Manager()
        shared_results = manager.dict()
        
        try:
            # Start CPU load process
            if self.cpu_load_percent > 0:
                cpu_process = multiprocessing.Process(
                    target=self._run_cpu_load,
                    args=(shared_results, self.duration * self.cpu_load_percent / 100)
                )
                cpu_process.start()
                all_processes.append(cpu_process)
            
            # Start memory load process
            if self.memory_load_percent > 0:
                memory_process = multiprocessing.Process(
                    target=self._run_memory_load,
                    args=(shared_results, self.duration * self.memory_load_percent / 100)
                )
                memory_process.start()
                all_processes.append(memory_process)
            
            # Start I/O load process
            if self.io_load_percent > 0:
                io_process = multiprocessing.Process(
                    target=self._run_io_load,
                    args=(shared_results, self.duration * self.io_load_percent / 100)
                )
                io_process.start()
                all_processes.append(io_process)
            
            # Start network load process
            if self.network_load_percent > 0:
                network_process = multiprocessing.Process(
                    target=self._run_network_load,
                    args=(shared_results, self.duration * self.network_load_percent / 100)
                )
                network_process.start()
                all_processes.append(network_process)
            
            # Run cache operations in this process
            cache_results = self._run_cache_operations(self.cache_size_mb, self.cache_operations)
            shared_results['cache'] = cache_results
            
            # Wait for all processes to finish
            for process in all_processes:
                process.join(timeout=self.duration + 10)  # Extra time for safety
                if process.is_alive():
                    process.terminate()
            
            # Collect results
            results = dict(shared_results)
            
        except Exception as e:
            logger.error(f"Integration test error: {str(e)}")
            results['error'] = str(e)
            
            # Ensure all processes are terminated
            for process in all_processes:
                if process.is_alive():
                    process.terminate()
        
        return results
    
    def _run_cpu_load(self, shared_results: Dict, duration: float) -> None:
        """
        Run CPU load test in a separate process.
        
        Args:
            shared_results: Dictionary to store results
            duration: Test duration in seconds
        """
        cpu_test = CPUTestCase(duration=duration, iterations=1)
        result = cpu_test.run()
        shared_results['cpu'] = result
    
    def _run_memory_load(self, shared_results: Dict, duration: float) -> None:
        """
        Run memory load test in a separate process.
        
        Args:
            shared_results: Dictionary to store results
            duration: Test duration in seconds
        """
        memory_test = MemoryTestCase(duration=duration, iterations=1)
        result = memory_test.run()
        shared_results['memory'] = result
    
    def _run_io_load(self, shared_results: Dict, duration: float) -> None:
        """
        Run I/O load test in a separate process.
        
        Args:
            shared_results: Dictionary to store results
            duration: Test duration in seconds
        """
        io_test = IOTestCase(duration=duration, iterations=1)
        result = io_test.run()
        shared_results['io'] = result
    
    def _run_network_load(self, shared_results: Dict, duration: float) -> None:
        """
        Run network load test in a separate process.
        
        Args:
            shared_results: Dictionary to store results
            duration: Test duration in seconds
        """
        network_test = NetworkTestCase(duration=duration, iterations=1)
        result = network_test.run()
        shared_results['network'] = result
    
    def _run_cache_operations(self, cache_size_mb: int, num_operations: int) -> Dict[str, Any]:
        """
        Run cache performance test.
        
        Args:
            cache_size_mb: Cache size in MB
            num_operations: Number of cache operations to perform
            
        Returns:
            Dictionary with cache performance metrics
        """
        # Implementation of the cache operations test
        # This method was approximately 75% complete according to handover notes
        
        # Create a simple in-memory LRU cache
        cache = {}
        cache_max_keys = cache_size_mb * 1024 * 1024 // 1024  # Assuming 1KB per entry avg
        cache_max_size = cache_size_mb * 1024 * 1024  # Cache size in bytes
        cache_current_size = 0
        lru_order = []  # List to track LRU order
        
        # Performance metrics
        hit_count = 0
        miss_count = 0
        insert_times = []
        lookup_times = []
        eviction_times = []
        current_size_history = []
        ops_timestamps = []
        
        # Distribution for key access pattern (to simulate real-world caching)
        # Use Zipf distribution to simulate popularity-based access patterns
        # where some items are much more frequently accessed than others
        alpha = 1.1  # Zipf parameter (higher means more skewed distribution)
        num_unique_keys = min(num_operations // 2, 10000)  # Number of unique keys
        
        # Generate Zipf distribution
        zipf_sum = sum(1 / (i ** alpha) for i in range(1, num_unique_keys + 1))
        zipf_distribution = [(1 / (i ** alpha)) / zipf_sum for i in range(1, num_unique_keys + 1)]
        zipf_cumulative = [sum(zipf_distribution[:i+1]) for i in range(len(zipf_distribution))]
        
        # Function to sample keys according to Zipf
        def sample_key():
            rand = random.random()
            for i, cum_prob in enumerate(zipf_cumulative):
                if rand <= cum_prob:
                    return f"key_{i}"
            return f"key_{num_unique_keys-1}"
        
        # Function to generate a random value of random size
        def generate_value(min_size=512, max_size=4096):
            size = random.randint(min_size, max_size)
            return os.urandom(size), size
        
        # Function to evict least recently used items when cache is full
        def evict_lru():
            eviction_start = time.time()
            
            while cache_current_size > cache_max_size and lru_order:
                # Evict least recently used
                lru_key = lru_order.pop(0)
                if lru_key in cache:
                    cache_value, value_size = cache[lru_key]
                    cache_current_size -= value_size
                    del cache[lru_key]
            
            eviction_end = time.time()
            return eviction_end - eviction_start
        
        start_time = time.time()
        
        # Run operations
        for i in range(num_operations):
            operation_time = time.time() - start_time
            ops_timestamps.append(operation_time)
            
            # Decide on operation (70% lookup, 30% insert)
            operation = "lookup" if random.random() < 0.7 else "insert"
            
            if operation == "lookup":
                # Get a key according to Zipf distribution
                key = sample_key()
                
                # Measure lookup time
                lookup_start = time.time()
                
                if key in cache:
                    # Cache hit - update LRU order
                    value, _ = cache[key]
                    hit_count += 1
                    
                    # Update LRU order
                    if key in lru_order:
                        lru_order.remove(key)
                    lru_order.append(key)
                else:
                    # Cache miss
                    miss_count += 1
                
                lookup_end = time.time()
                lookup_times.append(lookup_end - lookup_start)
                
            else:  # insert
                # Generate new key
                key = f"key_{random.randint(0, num_unique_keys)}"
                
                # Generate value with random size
                value, value_size = generate_value()
                
                # Measure insert time
                insert_start = time.time()
                
                # Check if eviction is needed
                new_cache_size = cache_current_size + value_size
                if new_cache_size > cache_max_size or len(cache) >= cache_max_keys:
                    eviction_time = evict_lru()
                    eviction_times.append(eviction_time)
                
                # Insert into cache
                if key in cache:
                    old_value, old_size = cache[key]
                    cache_current_size -= old_size
                
                cache[key] = (value, value_size)
                cache_current_size += value_size
                
                # Update LRU order
                if key in lru_order:
                    lru_order.remove(key)
                lru_order.append(key)
                
                insert_end = time.time()
                insert_times.append(insert_end - insert_start)
            
            # Record cache size at regular intervals
            if i % (num_operations // 100 or 1) == 0:
                current_size_history.append((operation_time, cache_current_size))
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate hit rate
        total_lookups = hit_count + miss_count
        hit_rate = hit_count / total_lookups if total_lookups > 0 else 0
        
        # Calculate operations per second
        ops_per_second = num_operations / total_time if total_time > 0 else 0
        
        # Calculate average operation times
        avg_lookup_time = statistics.mean(lookup_times) if lookup_times else 0
        avg_insert_time = statistics.mean(insert_times) if insert_times else 0
        avg_eviction_time = statistics.mean(eviction_times) if eviction_times else 0
        
        return {
            'cache_size_mb': cache_size_mb,
            'num_operations': num_operations,
            'hit_count': hit_count,
            'miss_count': miss_count,
            'hit_rate': hit_rate,
            'ops_per_second': ops_per_second,
            'avg_lookup_time_ms': avg_lookup_time * 1000,
            'avg_insert_time_ms': avg_insert_time * 1000,
            'avg_eviction_time_ms': avg_eviction_time * 1000,
            'final_cache_size_mb': cache_current_size / (1024 * 1024),
            'final_cache_entries': len(cache)
        }


class TestSuite:
    """Manages collections of test cases with aggregated reporting."""
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize test suite.
        
        Args:
            name: Identifier for the test suite
            description: Description of the test suite
        """
        self.name = name
        self.description = description
        self.test_cases = []
        self.results = {
            'name': name,
            'description': description,
            'test_results': [],
            'start_time': None,
            'end_time': None,
            'summary': {}
        }
    
    def add_test_case(self, test_case: BaseTestCase) -> None:
        """
        Add a test case to the suite.
        
        Args:
            test_case: Test case instance to add
        """
        self.test_cases.append(test_case)
    
    def run(self) -> Dict[str, Any]:
        """
        Run all test cases in the suite.
        
        Returns:
            Dictionary with aggregated test results
        """
        self.results['start_time'] = datetime.datetime.now().isoformat()
        self.results['test_results'] = []
        
        logger.info(f"Starting test suite: {self.name}")
        
        # Run each test case
        for test_case in self.test_cases:
            try:
                result = test_case.run()
                self.results['test_results'].append(result)
            except Exception as e:
                logger.error(f"Error running test case {test_case.name}: {str(e)}")
                self.results['test_results'].append({
                    'name': test_case.name,
                    'success': False,
                    'error': str(e)
                })
        
        self.results['end_time'] = datetime.datetime.now().isoformat()
        
        # Generate summary statistics
        self._generate_summary()
        
        return self.results
    
    def _generate_summary(self) -> None:
        """Generate summary statistics for all test results."""
        summary = {
            'total_tests': len(self.test_cases),
            'successful_tests': sum(1 for r in self.results['test_results'] if r.get('success', False)),
            'failed_tests': sum(1 for r in self.results['test_results'] if not r.get('success', False)),
            'component_metrics': {}
        }
        
        # Extract component-specific metrics
        for result in self.results['test_results']:
            if 'name' in result:
                component_name = result['name'].split()[0].lower()  # E.g., "CPU", "Memory"
                
                if component_name not in summary['component_metrics']:
                    summary['component_metrics'][component_name] = {}
                
                # Copy summary metrics if available
                if 'summary' in result:
                    for metric, stats in result['summary'].items():
                        if isinstance(stats, dict) and 'mean' in stats:
                            summary['component_metrics'][component_name][metric] = stats['mean']
        
        # Calculate overall execution time
        if self.results['start_time'] and self.results['end_time']:
            start = datetime.datetime.fromisoformat(self.results['start_time'])
            end = datetime.datetime.fromisoformat(self.results['end_time'])
            summary['total_duration_seconds'] = (end - start).total_seconds()
        
        self.results['summary'] = summary
    
    def save_results(self, filename: str = None) -> str:
        """
        Save test results to a JSON file.
        
        Args:
            filename: Output filename (defaults to suite name with timestamp)
            
        Returns:
            Path to saved results file
        """
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.name.replace(' ', '_')}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Test suite results saved to: {filename}")
        return filename
    
    @staticmethod
    def load_results(filename: str) -> Dict[str, Any]:
        """
        Load test results from a JSON file.
        
        Args:
            filename: Path to results file
            
        Returns:
            Dictionary with test results
        """
        with open(filename, 'r') as f:
            results = json.load(f)
        
        return results


# Predefined test suites
def create_quick_test_suite() -> TestSuite:
    """
    Create a quick test suite with short-duration tests.
    
    Returns:
        TestSuite instance
    """
    suite = TestSuite("Quick System Check", "Brief system performance check")
    
    suite.add_test_case(CPUTestCase(duration=5, iterations=2))
    suite.add_test_case(MemoryTestCase(duration=5, iterations=2))
    suite.add_test_case(IOTestCase(duration=5, iterations=2, file_size_mb=50))
    suite.add_test_case(NetworkTestCase(duration=5, iterations=2))
    
    return suite

def create_comprehensive_test_suite() -> TestSuite:
    """
    Create a comprehensive test suite with thorough testing.
    
    Returns:
        TestSuite instance
    """
    suite = TestSuite("Comprehensive System Test", "Thorough system performance evaluation")
    
    suite.add_test_case(CPUTestCase(duration=30, iterations=3))
    suite.add_test_case(MemoryTestCase(duration=20, iterations=3, allocation_size_mb=200))
    suite.add_test_case(IOTestCase(duration=20, iterations=3, file_size_mb=200))
    suite.add_test_case(NetworkTestCase(duration=20, iterations=3))
    suite.add_test_case(IntegrationTestCase(duration=60, iterations=2))
    
    return suite

def create_cpu_intensive_test_suite() -> TestSuite:
    """
    Create a CPU-focused test suite.
    
    Returns:
        TestSuite instance
    """
    suite = TestSuite("CPU Performance Test", "Detailed CPU performance evaluation")
    
    # Add multiple CPU tests with different configurations
    suite.add_test_case(CPUTestCase(name="Single Core CPU Test", 
                                   duration=15, 
                                   iterations=3,
                                   num_processes=1))
    
    suite.add_test_case(CPUTestCase(name="Half Core CPU Test", 
                                   duration=15, 
                                   iterations=3,
                                   num_processes=max(1, multiprocessing.cpu_count() // 2)))
    
    suite.add_test_case(CPUTestCase(name="Full Core CPU Test", 
                                   duration=15, 
                                   iterations=3,
                                   num_processes=multiprocessing.cpu_count()))
    
    return suite

def create_io_intensive_test_suite() -> TestSuite:
    """
    Create an I/O-focused test suite.
    
    Returns:
        TestSuite instance
    """
    suite = TestSuite("I/O Performance Test", "Detailed I/O performance evaluation")
    
    # Add I/O tests with different configurations
    suite.add_test_case(IOTestCase(name="Small File I/O Test", 
                                  duration=15, 
                                  iterations=3,
                                  file_size_mb=50,
                                  block_size_kb=4))
    
    suite.add_test_case(IOTestCase(name="Medium File I/O Test", 
                                  duration=15, 
                                  iterations=3,
                                  file_size_mb=200,
                                  block_size_kb=64))
    
    suite.add_test_case(IOTestCase(name="Large File I/O Test", 
                                  duration=15, 
                                  iterations=3,
                                  file_size_mb=500,
                                  block_size_kb=1024))
    
    return suite

def create_memory_intensive_test_suite() -> TestSuite:
    """
    Create a memory-focused test suite.
    
    Returns:
        TestSuite instance
    """
    suite = TestSuite("Memory Performance Test", "Detailed memory performance evaluation")
    
    # Add memory tests with different configurations
    suite.add_test_case(MemoryTestCase(name="Small Blocks Memory Test", 
                                      duration=15, 
                                      iterations=3,
                                      allocation_size_mb=10,
                                      allocation_count=50))
    
    suite.add_test_case(MemoryTestCase(name="Medium Blocks Memory Test", 
                                      duration=15, 
                                      iterations=3,
                                      allocation_size_mb=50,
                                      allocation_count=20))
    
    suite.add_test_case(MemoryTestCase(name="Large Blocks Memory Test", 
                                      duration=15, 
                                      iterations=3,
                                      allocation_size_mb=200,
                                      allocation_count=5))
    
    return suite

def create_network_intensive_test_suite() -> TestSuite:
    """
    Create a network-focused test suite.
    
    Returns:
        TestSuite instance
    """
    suite = TestSuite("Network Performance Test", "Detailed network performance evaluation")
    
    # Add network tests with different configurations
    suite.add_test_case(NetworkTestCase(name="TCP Small Packet Test", 
                                       duration=15, 
                                       iterations=3,
                                       packet_size_kb=1,
                                       protocol="tcp"))
    
    suite.add_test_case(NetworkTestCase(name="TCP Large Packet Test", 
                                       duration=15, 
                                       iterations=3,
                                       packet_size_kb=64,
                                       protocol="tcp"))
    
    suite.add_test_case(NetworkTestCase(name="UDP Small Packet Test", 
                                       duration=15, 
                                       iterations=3,
                                       packet_size_kb=1,
                                       protocol="udp"))
    
    suite.add_test_case(NetworkTestCase(name="UDP Large Packet Test", 
                                       duration=15, 
                                       iterations=3,
                                       packet_size_kb=64,
                                       protocol="udp"))
    
    return suite

def create_cache_performance_test_suite() -> TestSuite:
    """
    Create a cache-focused test suite.
    
    Returns:
        TestSuite instance
    """
    suite = TestSuite("Cache Performance Test", "Detailed cache performance evaluation")
    
    # Add integration tests with focus on cache operations
    suite.add_test_case(IntegrationTestCase(name="Small Cache Test", 
                                           duration=20, 
                                           iterations=2,
                                           cpu_load_percent=10,
                                           memory_load_percent=10,
                                           io_load_percent=10,
                                           network_load_percent=10,
                                           cache_size_mb=50,
                                           cache_operations=5000))
    
    suite.add_test_case(IntegrationTestCase(name="Medium Cache Test", 
                                           duration=20, 
                                           iterations=2,
                                           cpu_load_percent=10,
                                           memory_load_percent=10,
                                           io_load_percent=10,
                                           network_load_percent=10,
                                           cache_size_mb=200,
                                           cache_operations=10000))
    
    suite.add_test_case(IntegrationTestCase(name="Large Cache Test", 
                                           duration=20, 
                                           iterations=2,
                                           cpu_load_percent=10,
                                           memory_load_percent=10,
                                           io_load_percent=10,
                                           network_load_percent=10,
                                           cache_size_mb=500,
                                           cache_operations=20000))
    
    return suite


# External interface functions
def get_available_test_suites() -> List[str]:
    """
    Get a list of available predefined test suites.
    
    Returns:
        List of test suite names
    """
    return [
        "quick",
        "comprehensive",
        "cpu_intensive",
        "memory_intensive",
        "io_intensive",
        "network_intensive",
        "cache_performance"
    ]

def create_custom_test_suite(name: str, 
                            description: str, 
                            test_config: List[Dict[str, Any]]) -> TestSuite:
    """
    Create a custom test suite with specified test cases.
    
    Args:
        name: Name for the test suite
        description: Description of the test suite
        test_config: List of test case configurations
                     Each dict should include 'type' and other params
    
    Returns:
        Configured TestSuite instance
    """
    suite = TestSuite(name, description)
    
    for config in test_config:
        test_type = config.pop('type', '').lower()
        
        if test_type == 'cpu':
            test_case = CPUTestCase(**config)
        elif test_type == 'memory':
            test_case = MemoryTestCase(**config)
        elif test_type == 'io':
            test_case = IOTestCase(**config)
        elif test_type == 'network':
            test_case = NetworkTestCase(**config)
        elif test_type == 'integration':
            test_case = IntegrationTestCase(**config)
        else:
            raise ValueError(f"Unknown test type: {test_type}")
        
        suite.add_test_case(test_case)
    
    return suite

def run_test_suite(suite_name: str = "quick", 
                  custom_suite: TestSuite = None,
                  save_results: bool = True,
                  output_file: str = None) -> Dict[str, Any]:
    """
    Run a predefined or custom test suite.
    
    Args:
        suite_name: Name of predefined test suite to run
        custom_suite: Custom TestSuite instance (overrides suite_name)
        save_results: Whether to save results to a file
        output_file: Custom filename for results
    
    Returns:
        Dictionary with test results
    """
    if custom_suite:
        suite = custom_suite
    else:
        # Create predefined suite based on name
        suite_name = suite_name.lower()
        if suite_name == "quick":
            suite = create_quick_test_suite()
        elif suite_name == "comprehensive":
            suite = create_comprehensive_test_suite()
        elif suite_name == "cpu_intensive":
            suite = create_cpu_intensive_test_suite()
        elif suite_name == "memory_intensive":
            suite = create_memory_intensive_test_suite()
        elif suite_name == "io_intensive":
            suite = create_io_intensive_test_suite()
        elif suite_name == "network_intensive":
            suite = create_network_intensive_test_suite()
        elif suite_name == "cache_performance":
            suite = create_cache_performance_test_suite()
        else:
            raise ValueError(f"Unknown predefined test suite: {suite_name}")
    
    # Run the suite
    results = suite.run()
    
    # Save results if requested
    if save_results:
        suite.save_results(output_file)
    
    return results


if __name__ == "__main__":
    # Example usage
    results = run_test_suite("quick")
    print(f"Test suite completed with {results['summary']['successful_tests']} successful tests")