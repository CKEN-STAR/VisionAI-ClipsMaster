import logging
from typing import Dict, List, Set, Tuple, Optional
import time

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80


# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EffectValidator")

class EffectValidator:
    """
    EffectValidator validates the effectiveness of resource release operations.
    It tracks memory usage patterns and identifies potential memory leaks.
    """
    
    def __init__(self, 
                 leak_threshold_mb: float = 10.0,
                 tracking_window: int = 50,
                 leak_detection_consecutive: int = 3):
        """
        Initialize the EffectValidator.
        
        Args:
            leak_threshold_mb: Threshold in MB to consider memory difference as potential leak
            tracking_window: Number of function calls to track for patterns
            leak_detection_consecutive: Number of consecutive increases to identify a leak
        """
        self.leak_threshold_mb = leak_threshold_mb
        self.tracking_window = tracking_window
        self.leak_detection_consecutive = leak_detection_consecutive
        
        # Track memory usage by function
        self.memory_usage_history: Dict[str, List[Tuple[float, float, float]]] = {}
        
        # Set of functions with potential memory leaks
        self.potential_leakers: Set[str] = set()
        
        logger.info(f"EffectValidator initialized with leak threshold: {leak_threshold_mb}MB")
    
    def validate_resource_release(self, 
                                 memory_before: float, 
                                 memory_after: float, 
                                 function_name: str) -> bool:
        """
        Validate if a function properly releases resources after execution.
        
        Args:
            memory_before: Memory usage before function execution (MB)
            memory_after: Memory usage after function execution (MB)
            function_name: Name of the function
            
        Returns:
            True if resource release is effective, False otherwise
        """
        memory_diff = memory_after - memory_before
        current_time = time.time()
        
        # Initialize tracking for new functions
        if function_name not in self.memory_usage_history:
            self.memory_usage_history[function_name] = []
        
        # Add current usage to history
        self.memory_usage_history[function_name].append(
            (memory_before, memory_after, current_time))
        
        # Keep history within tracking window
        if len(self.memory_usage_history[function_name]) > self.tracking_window:
            self.memory_usage_history[function_name].pop(0)
        
        # Check for potential memory leak
        if memory_diff > self.leak_threshold_mb:
            logger.warning(f"Function {function_name} increased memory by {memory_diff:.2f}MB")
            
            # Check for consecutive memory increases
            history = self.memory_usage_history[function_name]
            if len(history) >= self.leak_detection_consecutive:
                consecutive_increases = 0
                for i in range(len(history) - 1, 0, -1):
                    if history[i][1] - history[i][0] > 0:  # Memory increased
                        consecutive_increases += 1
                    else:
                        break
                    
                    if consecutive_increases >= self.leak_detection_consecutive:
                        if function_name not in self.potential_leakers:
                            self.potential_leakers.add(function_name)
                            logger.error(f"POTENTIAL MEMORY LEAK detected in {function_name}: "
                                       f"{consecutive_increases} consecutive increases")
                        return False
        
        # Check if a previously leaky function is now behaving well
        if function_name in self.potential_leakers:
            history = self.memory_usage_history[function_name]
            if len(history) >= self.leak_detection_consecutive:
                consecutive_stable = 0
                for i in range(len(history) - 1, 0, -1):
                    if history[i][1] - history[i][0] <= self.leak_threshold_mb:
                        consecutive_stable += 1
                    else:
                        break
                    
                    if consecutive_stable >= self.leak_detection_consecutive:
                        self.potential_leakers.remove(function_name)
                        logger.info(f"Function {function_name} no longer shows leak patterns")
        
        return memory_diff <= self.leak_threshold_mb
    
    def get_leak_report(self) -> Dict[str, Dict[str, float]]:
        """
        Generate a report of potential memory leaks.
        
        Returns:
            Dictionary with function names and their leak statistics
        """
        report = {}
        
        for func_name, history in self.memory_usage_history.items():
            if not history:
                continue
                
            total_diff = 0
            max_diff = 0
            count = 0
            
            for before, after, _ in history:
                diff = after - before
                total_diff += diff
                max_diff = max(max_diff, diff)
                count += 1
            
            avg_diff = total_diff / count if count > 0 else 0
            
            if func_name in self.potential_leakers or avg_diff > self.leak_threshold_mb:
                report[func_name] = {
                    "average_increase_mb": avg_diff,
                    "max_increase_mb": max_diff,
                    "call_count": count,
                    "is_flagged": func_name in self.potential_leakers
                }
        
        return report
    
    def reset_tracking(self, function_name: Optional[str] = None) -> None:
        """
        Reset tracking for a specific function or all functions.
        
        Args:
            function_name: Name of function to reset, or None to reset all
        """
        if function_name:
            if function_name in self.memory_usage_history:
                self.memory_usage_history[function_name] = []
            if function_name in self.potential_leakers:
                self.potential_leakers.remove(function_name)
        else:
            self.memory_usage_history = {}
            self.potential_leakers = set() 