#!/usr/bin/env python
"""
Performance Testing Framework Runner
-------------------------------------------------
This module provides command-line interface and usage examples for the 
performance testing framework defined in test_cases.py.

Usage:
    python test_runner.py [options]

Options:
    --suite=SUITE       Run a predefined test suite (default: quick)
    --custom            Create and run a custom test suite
    --list              List available predefined test suites
    --output=FILE       Specify output file for results
    --no-save           Don't save results to file
    --help              Show this help message
"""

import sys
import getopt
import json
from typing import List, Dict, Any

# Import test_cases module
import test_cases as tc


def print_help():
    """Print help message."""
    print(__doc__)


def list_available_suites():
    """Print available predefined test suites."""
    suites = tc.get_available_test_suites()
    print("Available predefined test suites:")
    for suite in suites:
        print(f"  - {suite}")


def run_predefined_suite(suite_name: str, save_results: bool = True, output_file: str = None):
    """Run a predefined test suite."""
    print(f"Running predefined test suite: {suite_name}")
    try:
        results = tc.run_test_suite(suite_name=suite_name, save_results=save_results, output_file=output_file)
        print_summary(results)
    except ValueError as e:
        print(f"Error: {str(e)}")
        list_available_suites()
        sys.exit(1)


def create_and_run_custom_suite(save_results: bool = True, output_file: str = None):
    """Create and run a custom test suite with user input."""
    print("Creating custom test suite:")
    
    # Get test suite name and description
    name = input("Test suite name: ")
    description = input("Test suite description: ")
    
    # Create test configuration
    test_config = []
    add_more = "y"
    
    while add_more.lower() == "y":
        print("\nAdd a test case to the suite:")
        print("Available test types: cpu, memory, io, network, integration")
        test_type = input("Test type: ").lower()
        
        if test_type not in ["cpu", "memory", "io", "network", "integration"]:
            print(f"Invalid test type: {test_type}")
            continue
        
        # Get common parameters
        config = {"type": test_type}
        
        try:
            config["name"] = input("Test name (leave empty for default): ")
            if not config["name"]:
                del config["name"]
                
            duration = input("Test duration in seconds (leave empty for default): ")
            if duration:
                config["duration"] = int(duration)
                
            iterations = input("Number of iterations (leave empty for default): ")
            if iterations:
                config["iterations"] = int(iterations)
        except ValueError:
            print("Error: Invalid input. Please enter numeric values where required.")
            continue
        
        # Get type-specific parameters
        if test_type == "cpu":
            num_processes = input("Number of CPU processes (leave empty for default): ")
            if num_processes:
                try:
                    config["num_processes"] = int(num_processes)
                except ValueError:
                    print("Error: Invalid input for number of processes.")
                    continue
        
        elif test_type == "memory":
            try:
                allocation_size = input("Allocation size in MB (leave empty for default): ")
                if allocation_size:
                    config["allocation_size_mb"] = int(allocation_size)
                    
                allocation_count = input("Number of allocations (leave empty for default): ")
                if allocation_count:
                    config["allocation_count"] = int(allocation_count)
            except ValueError:
                print("Error: Invalid input. Please enter numeric values.")
                continue
        
        elif test_type == "io":
            try:
                file_size = input("File size in MB (leave empty for default): ")
                if file_size:
                    config["file_size_mb"] = int(file_size)
                    
                block_size = input("Block size in KB (leave empty for default): ")
                if block_size:
                    config["block_size_kb"] = int(block_size)
            except ValueError:
                print("Error: Invalid input. Please enter numeric values.")
                continue
        
        elif test_type == "network":
            protocol = input("Protocol (tcp/udp, leave empty for default): ").lower()
            if protocol in ["tcp", "udp"]:
                config["protocol"] = protocol
                
            try:
                packet_size = input("Packet size in KB (leave empty for default): ")
                if packet_size:
                    config["packet_size_kb"] = int(packet_size)
            except ValueError:
                print("Error: Invalid input. Please enter numeric values.")
                continue
        
        elif test_type == "integration":
            try:
                cache_size = input("Cache size in MB (leave empty for default): ")
                if cache_size:
                    config["cache_size_mb"] = int(cache_size)
                    
                cache_ops = input("Number of cache operations (leave empty for default): ")
                if cache_ops:
                    config["cache_operations"] = int(cache_ops)
            except ValueError:
                print("Error: Invalid input. Please enter numeric values.")
                continue
        
        # Add test to configuration
        test_config.append(config)
        print(f"Added {test_type} test to suite")
        
        # Ask to add more tests
        add_more = input("\nAdd another test case? (y/n): ")
    
    # Create and run the custom suite
    if not test_config:
        print("Error: No test cases added to suite")
        return
    
    print("\nCreating and running custom test suite...")
    custom_suite = tc.create_custom_test_suite(name, description, test_config)
    results = tc.run_test_suite(custom_suite=custom_suite, save_results=save_results, output_file=output_file)
    print_summary(results)


def print_summary(results: Dict[str, Any]):
    """Print a summary of test results."""
    if 'summary' not in results:
        print("Error: Invalid results format")
        return
    
    summary = results['summary']
    
    print("\nTest Suite Summary:")
    print(f"  Name: {results.get('name', 'Unknown')}")
    print(f"  Description: {results.get('description', '')}")
    print(f"  Total tests: {summary.get('total_tests', 0)}")
    print(f"  Successful tests: {summary.get('successful_tests', 0)}")
    print(f"  Failed tests: {summary.get('failed_tests', 0)}")
    
    if 'total_duration_seconds' in summary:
        print(f"  Total duration: {summary['total_duration_seconds']:.2f} seconds")
    
    # Print component metrics if available
    if 'component_metrics' in summary and summary['component_metrics']:
        print("\nComponent Performance Metrics:")
        for component, metrics in summary['component_metrics'].items():
            print(f"  {component.capitalize()}:")
            for metric, value in metrics.items():
                if isinstance(value, (int, float)):
                    print(f"    {metric}: {value:.2f}" if isinstance(value, float) else f"    {metric}: {value}")


def main(argv: List[str]):
    """Main function to parse arguments and run tests."""
    try:
        opts, args = getopt.getopt(argv, "hs:co:n", ["help", "suite=", "custom", "output=", "no-save", "list"])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    
    # Default values
    suite_name = "quick"
    save_results = True
    output_file = None
    run_custom = False
    
    # Parse options
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_help()
            sys.exit()
        elif opt == "--list":
            list_available_suites()
            sys.exit()
        elif opt in ("-s", "--suite"):
            suite_name = arg
        elif opt in ("-c", "--custom"):
            run_custom = True
        elif opt in ("-o", "--output"):
            output_file = arg
        elif opt in ("-n", "--no-save"):
            save_results = False
    
    # Run tests
    if run_custom:
        create_and_run_custom_suite(save_results, output_file)
    else:
        run_predefined_suite(suite_name, save_results, output_file)


if __name__ == "__main__":
    main(sys.argv[1:])


# Example programmatic usage:

def example_usage():
    """Example programmatic usage of the test framework."""
    
    # Example 1: Run a predefined test suite
    print("\nExample 1: Running a predefined quick test suite")
    results = tc.run_test_suite("quick")
    
    # Example 2: Create and run a custom test suite
    print("\nExample 2: Creating and running a custom test suite")
    custom_config = [
        {'type': 'cpu', 'duration': 5, 'iterations': 1},
        {'type': 'memory', 'allocation_size_mb': 50, 'allocation_count': 5}
    ]
    custom_suite = tc.create_custom_test_suite(
        "Custom Example Suite", 
        "Example custom suite with CPU and memory tests", 
        custom_config
    )
    results = tc.run_test_suite(custom_suite=custom_suite)
    
    # Example 3: Running CPU-intensive tests
    print("\nExample 3: Running CPU-intensive tests")
    results = tc.run_test_suite("cpu_intensive")
    
    # Example 4: Create a test suite for specific performance investigation
    print("\nExample 4: Creating a custom test suite for cache performance analysis")
    cache_test_config = [
        {
            'type': 'integration',
            'name': 'Cache Performance Analysis',
            'duration': 15,
            'iterations': 1,
            'cpu_load_percent': 20,
            'memory_load_percent': 20,
            'io_load_percent': 10,
            'network_load_percent': 10,
            'cache_size_mb': 100,
            'cache_operations': 5000
        }
    ]
    cache_suite = tc.create_custom_test_suite(
        "Cache Analysis", 
        "Test suite for analyzing cache performance", 
        cache_test_config
    )
    results = tc.run_test_suite(custom_suite=cache_suite)
    
    # Example 5: Get performance benchmark data for comparison
    print("\nExample 5: Getting baseline performance data")
    baseline_results = tc.run_test_suite("comprehensive", output_file="baseline_results.json")
    
    # Later, you could compare new results to this baseline
    # comparison_results = tc.run_test_suite("comprehensive", output_file="comparison_results.json")
    # Then use the saved JSON files to compare performance metrics


# Uncomment the following line to run the examples
# example_usage()