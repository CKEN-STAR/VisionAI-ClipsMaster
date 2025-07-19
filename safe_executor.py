import os
import psutil
import time
import logging
import gc
from typing import Callable, Dict, Any, Optional, List, Tuple

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80


# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SafeExecutor")

class ResourceTracker:
    """Tracks resources and their dependencies for proper cleanup."""
    
    def __init__(self):
        self.resources: Dict[str, Any] = {}
        self.dependencies: Dict[str, List[str]] = {}
        self.cleanup_handlers: Dict[str, Callable] = {}
        
    def register(self, 
                 resource_id: str, 
                 resource: Any, 
                 cleanup_handler: Callable,
                 dependencies: List[str] = None):
        """Register a resource with its cleanup handler and dependencies."""
        self.resources[resource_id] = resource
        self.cleanup_handlers[resource_id] = cleanup_handler
        self.dependencies[resource_id] = dependencies or []
        
    def get_resource(self, resource_id: str) -> Any:
        """Get a registered resource by ID."""
        return self.resources.get(resource_id)
    
    def get_dependent_resources(self, resource_id: str) -> List[str]:
        """Get all resources that depend on the given resource."""
        return [rid for rid, deps in self.dependencies.items() 
                if resource_id in deps]
    
    def get_cleanup_order(self) -> List[str]:
        """Get resources in cleanup order (reverse dependency order)."""
        result = []
        visited = set()
        
        def visit(resource_id):
            if resource_id in visited:
                return
            visited.add(resource_id)
            
            # Visit all dependent resources first
            for dep_id in self.get_dependent_resources(resource_id):
                visit(dep_id)
                
            result.append(resource_id)
            
        for rid in self.resources:
            visit(rid)
            
        return result
    
    def cleanup_resource(self, resource_id: str) -> bool:
        """Clean up a specific resource."""
        try:
            if resource_id in self.cleanup_handlers:
                handler = self.cleanup_handlers[resource_id]
                handler(self.resources[resource_id])
                
                # Remove from tracking
                self.resources.pop(resource_id, None)
                self.cleanup_handlers.pop(resource_id, None)
                self.dependencies.pop(resource_id, None)
                
                # Force garbage collection
                gc.collect()
                return True
        except Exception as e:
            logger.error(f"Error cleaning up resource {resource_id}: {e}")
            return False
        return False


class SafeExecutor:
    """Monitors memory usage and manages resource lifecycle with circuit breaking."""
    
    def __init__(self, 
                 memory_threshold_pct: float = 85.0,
                 critical_threshold_pct: float = 95.0,
                 check_interval_sec: float = 0.5):
        """
        Initialize SafeExecutor with configurable memory thresholds.
        
        Args:
            memory_threshold_pct: Percentage of memory usage to trigger warning
            critical_threshold_pct: Percentage of memory usage to trigger circuit breaking
            check_interval_sec: Interval in seconds to check memory usage
        """
        self.memory_threshold_pct = memory_threshold_pct
        self.critical_threshold_pct = critical_threshold_pct
        self.check_interval_sec = check_interval_sec
        self.resource_tracker = ResourceTracker()
        self.last_check_time = 0
        self.circuit_broken = False
        self.memory_readings = []  # Store recent memory readings
        self.max_readings = 10     # Number of readings to store
        
    def register_resource(self, 
                         resource_id: str, 
                         resource: Any, 
                         cleanup_handler: Callable,
                         dependencies: List[str] = None):
        """Register a resource to be managed by the SafeExecutor."""
        self.resource_tracker.register(
            resource_id=resource_id,
            resource=resource,
            cleanup_handler=cleanup_handler,
            dependencies=dependencies
        )
        
    def get_resource(self, resource_id: str) -> Any:
        """Get a registered resource."""
        return self.resource_tracker.get_resource(resource_id)
    
    def get_memory_info(self) -> Tuple[float, float]:
        """Get current memory usage as percentage and absolute MB."""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_usage_bytes = memory_info.rss
        memory_usage_mb = memory_usage_bytes / (1024 * 1024)
        
        system_memory = psutil.virtual_memory()
        memory_percent = system_memory.percent
        
        # Store reading
        self.memory_readings.append((time.time(), memory_percent, memory_usage_mb))
        if len(self.memory_readings) > self.max_readings:
            self.memory_readings.pop(0)
            
        return memory_percent, memory_usage_mb
    
    def is_memory_pressure_rising(self) -> bool:
        """Determine if memory pressure is on an upward trend."""
        if len(self.memory_readings) < 3:
            return False
            
        # Simple linear regression on recent readings
        recent = self.memory_readings[-3:]
        x = [r[0] for r in recent]  # timestamps
        y = [r[1] for r in recent]  # percentages
        
        # Normalize x values
        x_base = x[0]
        x_norm = [xi - x_base for xi in x]
        
        # Calculate slope
        if sum(x_norm) == 0:
            return False
            
        slope = sum(x_i * y_i for x_i, y_i in zip(x_norm, y)) / sum(x_i**2 for x_i in x_norm)
        return slope > 0.5  # Consider rising if slope is significant
    
    def check_memory(self) -> Tuple[bool, float, float]:
        """
        Check memory usage and determine if circuit breaking is needed.
        
        Returns:
            Tuple of (should_break_circuit, memory_percent, memory_mb)
        """
        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval_sec:
            if self.memory_readings:
                last_reading = self.memory_readings[-1]
                return self.circuit_broken, last_reading[1], last_reading[2]
            return self.circuit_broken, 0, 0
            
        self.last_check_time = current_time
        memory_percent, memory_mb = self.get_memory_info()
        
        # Check if we need to break the circuit
        if memory_percent > self.critical_threshold_pct:
            logger.warning(f"CRITICAL MEMORY PRESSURE: {memory_percent:.1f}% ({memory_mb:.1f} MB)")
            self.circuit_broken = True
            return True, memory_percent, memory_mb
        
        # Check for trend-based circuit breaking
        if (memory_percent > self.memory_threshold_pct and 
            self.is_memory_pressure_rising()):
            logger.warning(f"RISING MEMORY PRESSURE: {memory_percent:.1f}% ({memory_mb:.1f} MB)")
            self.circuit_broken = True
            return True, memory_percent, memory_mb
            
        # Regular threshold warning
        if memory_percent > self.memory_threshold_pct:
            logger.info(f"HIGH MEMORY USAGE: {memory_percent:.1f}% ({memory_mb:.1f} MB)")
            
        return False, memory_percent, memory_mb
    
    def release_resources(self, resource_ids: List[str] = None) -> Dict[str, bool]:
        """
        Release specific resources or all if none specified.
        
        Returns:
            Dictionary mapping resource IDs to success status
        """
        results = {}
        
        # If no specific resources, release all in proper order
        if not resource_ids:
            cleanup_order = self.resource_tracker.get_cleanup_order()
        else:
            # For specific resources, first find all their dependents
            cleanup_order = []
            for rid in resource_ids:
                dependents = self.resource_tracker.get_dependent_resources(rid)
                for d in dependents:
                    if d not in cleanup_order:
                        cleanup_order.append(d)
                if rid not in cleanup_order:
                    cleanup_order.append(rid)
        
        # Execute cleanup in order
        for rid in cleanup_order:
            success = self.resource_tracker.cleanup_resource(rid)
            results[rid] = success
            logger.info(f"Released resource {rid}: {'success' if success else 'failed'}")
            
        # Force garbage collection
        gc.collect()
        
        return results
    
    def execute_safely(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with memory safety monitoring.
        Will release resources if memory pressure is detected.
        """
        should_break, memory_pct, memory_mb = self.check_memory()
        
        if should_break:
            # Record state before circuit breaking for potential recovery
            circuit_break_data = {
                "memory_percent": memory_pct,
                "memory_mb": memory_mb,
                "time": time.time()
            }
            logger.warning(f"Circuit breaking triggered at {memory_pct:.1f}% memory usage")
            self.release_resources()
            return None, circuit_break_data
            
        try:
            result = func(*args, **kwargs)
            return result, None
        except MemoryError:
            logger.error("MemoryError caught during execution")
            self.circuit_broken = True
            self.release_resources()
            return None, {"error": "MemoryError", "time": time.time()}
            
    def reset_circuit(self):
        """Reset the circuit breaker state."""
        self.circuit_broken = False
        
    def get_memory_pressure_stats(self) -> Dict[str, Any]:
        """Get statistics about memory pressure for monitoring."""
        if not self.memory_readings:
            return {
                "current": 0,
                "average": 0,
                "max": 0,
                "trend": "stable",
                "readings": []
            }
            
        current = self.memory_readings[-1][1]  # Current percentage
        values = [r[1] for r in self.memory_readings]
        average = sum(values) / len(values)
        maximum = max(values)
        
        # Determine trend
        trend = "stable"
        if len(self.memory_readings) >= 3:
            if self.is_memory_pressure_rising():
                trend = "rising"
            elif values[-1] < values[-2] < values[-3]:
                trend = "falling"
                
        return {
            "current": current,
            "average": average,
            "max": maximum,
            "trend": trend,
            "readings": self.memory_readings
        } 