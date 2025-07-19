import os
import psutil
import time
import logging
from typing import Callable, Dict, Any, Optional
from functools import wraps

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SafeExecutor")

class MemoryThresholdExceeded(Exception):

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """Exception raised when memory usage exceeds the threshold."""
    pass

class SafeExecutor:
    """
    SafeExecutor monitors memory usage and implements circuit-breaking pattern
    to prevent application crashes under memory pressure.
    """
    
    def __init__(self, 
                 memory_threshold_mb: int = 3500,
                 critical_threshold_mb: int = 3800,
                 sampling_interval_sec: float = 0.1,
                 recovery_manager = None,
                 effect_validator = None,
                 event_tracer = None):
        """
        Initialize the SafeExecutor with configurable thresholds.
        
        Args:
            memory_threshold_mb: Memory usage threshold in MB that triggers warnings
            critical_threshold_mb: Memory usage threshold in MB that triggers circuit breaking
            sampling_interval_sec: Interval in seconds for checking memory usage
            recovery_manager: Reference to the RecoveryManager instance
            effect_validator: Reference to the EffectValidator instance
            event_tracer: Reference to the EventTracer instance
        """
        self.memory_threshold_mb = memory_threshold_mb
        self.critical_threshold_mb = critical_threshold_mb
        self.sampling_interval_sec = sampling_interval_sec
        self.recovery_manager = recovery_manager
        self.effect_validator = effect_validator
        self.event_tracer = event_tracer
        self.circuit_open = False
        self.process = psutil.Process(os.getpid())
        logger.info(f"SafeExecutor initialized with threshold: {memory_threshold_mb}MB, "
                   f"critical: {critical_threshold_mb}MB")
    
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024
    
    def check_memory_threshold(self) -> bool:
        """
        Check if memory usage exceeds the threshold.
        
        Returns:
            bool: True if memory usage is below threshold, False otherwise
        """
        memory_usage_mb = self.get_memory_usage_mb()
        
        if memory_usage_mb >= self.critical_threshold_mb:
            if not self.circuit_open:
                logger.warning(f"CIRCUIT BREAKER ACTIVATED: Memory usage is {memory_usage_mb}MB, "
                               f"exceeding critical threshold of {self.critical_threshold_mb}MB")
                self.circuit_open = True
                
                if self.event_tracer:
                    self.event_tracer.record_circuit_break_event(
                        memory_usage=memory_usage_mb,
                        threshold=self.critical_threshold_mb,
                        timestamp=time.time()
                    )
            
            return False
        
        elif memory_usage_mb >= self.memory_threshold_mb:
            logger.warning(f"Memory usage warning: {memory_usage_mb}MB (threshold: {self.memory_threshold_mb}MB)")
            return True
        
        # If we were in circuit-open state but now memory is below threshold, close the circuit
        if self.circuit_open and memory_usage_mb < self.memory_threshold_mb:
            logger.info(f"Circuit breaker reset: Memory usage down to {memory_usage_mb}MB")
            self.circuit_open = False
            
            if self.event_tracer:
                self.event_tracer.record_circuit_reset_event(
                    memory_usage=memory_usage_mb,
                    threshold=self.memory_threshold_mb,
                    timestamp=time.time()
                )
        
        return True
    
    def safe_execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with memory safety controls.
        
        Args:
            func: The function to execute
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            The result of the function execution
            
        Raises:
            MemoryThresholdExceeded: If memory usage exceeds critical threshold
        """
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            checkpoint_data = None
            if self.recovery_manager:
                checkpoint_data = self.recovery_manager.create_checkpoint()
            
            # Check memory before execution
            if not self.check_memory_threshold():
                if self.recovery_manager and checkpoint_data:
                    self.recovery_manager.restore_from_checkpoint(checkpoint_data)
                raise MemoryThresholdExceeded(
                    f"Memory usage exceeded critical threshold of {self.critical_threshold_mb}MB")
            
            start_time = time.time()
            memory_before = self.get_memory_usage_mb()
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Check memory after execution
                if not self.check_memory_threshold():
                    if self.recovery_manager and checkpoint_data:
                        self.recovery_manager.restore_from_checkpoint(checkpoint_data)
                    raise MemoryThresholdExceeded(
                        f"Memory usage exceeded critical threshold of {self.critical_threshold_mb}MB")
                
                end_time = time.time()
                memory_after = self.get_memory_usage_mb()
                
                # Log execution stats
                logger.info(f"Function {func.__name__} executed in {end_time - start_time:.2f}s, "
                           f"memory delta: {memory_after - memory_before:.2f}MB")
                
                if self.effect_validator:
                    self.effect_validator.validate_resource_release(memory_before, memory_after, func.__name__)
                
                return result
                
            except Exception as e:
                logger.error(f"Error in safe_execute for {func.__name__}: {str(e)}")
                
                if self.recovery_manager and checkpoint_data:
                    logger.info(f"Attempting recovery for {func.__name__}")
                    self.recovery_manager.restore_from_checkpoint(checkpoint_data)
                
                raise
        
        return wrapped_func(*args, **kwargs)
    
    def memory_safe(self, func: Optional[Callable] = None, custom_threshold_mb: Optional[int] = None):
        """
        Decorator for memory-safe function execution.
        
        Usage:
            @safe_executor.memory_safe
            def my_function():
                ...
                
            @safe_executor.memory_safe(custom_threshold_mb=2000)
            def my_heavy_function():
                ...
        """
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                old_threshold = self.critical_threshold_mb
                if custom_threshold_mb:
                    self.critical_threshold_mb = custom_threshold_mb
                
                try:
                    return self.safe_execute(f, *args, **kwargs)
                finally:
                    if custom_threshold_mb:
                        self.critical_threshold_mb = old_threshold
            
            return wrapped
        
        if func is None:
            return decorator
        return decorator(func) 