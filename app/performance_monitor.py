#!/usr/bin/env python3
"""
Performance monitoring and optimization utilities.
"""

import time
import os
import sys
from typing import Dict, Any
from contextlib import contextmanager


class PerformanceMonitor:
    """Monitor application performance and resource usage."""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    @contextmanager
    def measure(self, operation_name: str):
        """Context manager to measure operation time."""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = self._get_memory_usage()
            
            duration = end_time - start_time
            memory_delta = end_memory - start_memory
            
            if operation_name not in self.metrics:
                self.metrics[operation_name] = {
                    'count': 0,
                    'total_time': 0,
                    'min_time': float('inf'),
                    'max_time': 0,
                    'total_memory_delta': 0
                }
            
            metrics = self.metrics[operation_name]
            metrics['count'] += 1
            metrics['total_time'] += duration
            metrics['min_time'] = min(metrics['min_time'], duration)
            metrics['max_time'] = max(metrics['max_time'], duration)
            metrics['total_memory_delta'] += memory_delta
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = {}
        
        for operation, metrics in self.metrics.items():
            if metrics['count'] > 0:
                avg_time = metrics['total_time'] / metrics['count']
                avg_memory = metrics['total_memory_delta'] / metrics['count']
                
                stats[operation] = {
                    'count': metrics['count'],
                    'avg_time_ms': round(avg_time * 1000, 2),
                    'min_time_ms': round(metrics['min_time'] * 1000, 2),
                    'max_time_ms': round(metrics['max_time'] * 1000, 2),
                    'total_time_s': round(metrics['total_time'], 2),
                    'avg_memory_delta_mb': round(avg_memory, 2)
                }
        
        # Add system stats
        stats['system'] = {
            'current_memory_mb': self._get_memory_usage(),
            'process_id': os.getpid()
        }
        
        return stats
    
    def reset_stats(self):
        """Reset all performance statistics."""
        self.metrics.clear()
        self.start_times.clear()
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB (simplified version)."""
        try:
            # Simple memory tracking using sys.getsizeof for basic monitoring
            # This is a simplified version without external dependencies
            return 0.0  # Placeholder - could be enhanced with platform-specific code
        except Exception:
            return 0.0
    
    def print_stats(self):
        """Print performance statistics to console."""
        stats = self.get_stats()
        
        print("\n=== Performance Statistics ===")
        
        for operation, metrics in stats.items():
            if operation == 'system':
                continue
                
            print(f"\n{operation}:")
            print(f"  Count: {metrics['count']}")
            print(f"  Average time: {metrics['avg_time_ms']} ms")
            print(f"  Min time: {metrics['min_time_ms']} ms")
            print(f"  Max time: {metrics['max_time_ms']} ms")
            print(f"  Total time: {metrics['total_time_s']} s")
            if metrics['avg_memory_delta_mb'] != 0:
                print(f"  Avg memory delta: {metrics['avg_memory_delta_mb']} MB")
        
        if 'system' in stats:
            sys_stats = stats['system']
            print(f"\nSystem:")
            print(f"  Process ID: {sys_stats['process_id']}")
            print(f"  Current memory: {sys_stats['current_memory_mb']:.1f} MB")
        
        print("==============================\n")


# Global performance monitor instance
_global_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return _global_monitor


def measure_performance(operation_name: str):
    """Decorator to measure function performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with _global_monitor.measure(operation_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator
