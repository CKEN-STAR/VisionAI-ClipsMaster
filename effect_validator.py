import time
import logging
import psutil
import gc
from typing import Dict, Any, List, Tuple, Callable, Optional

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80


# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EffectValidator")

class ReleaseEffect:
    """Stores information about a resource release effect."""
    
    def __init__(self, 
                 resource_id: str,
                 before_memory_mb: float,
                 after_memory_mb: float,
                 timestamp: float):
        self.resource_id = resource_id
        self.before_memory_mb = before_memory_mb
        self.after_memory_mb = after_memory_mb
        self.memory_delta_mb = before_memory_mb - after_memory_mb
        self.release_percent = (self.memory_delta_mb / before_memory_mb * 100 
                               if before_memory_mb > 0 else 0)
        self.timestamp = timestamp
        self.success = self.memory_delta_mb > 0
        
    def __str__(self):
        return (f"Release of {self.resource_id}: "
                f"{self.before_memory_mb:.2f}MB → {self.after_memory_mb:.2f}MB "
                f"(Δ {self.memory_delta_mb:.2f}MB, {self.release_percent:.1f}%)")


class EffectValidator:
    """
    Validates the effectiveness of resource releases during circuit breaking.
    Implements multiple backup strategies for when primary release fails.
    """
    
    def __init__(self, 
                min_release_mb: float = 50.0,
                min_release_percent: float = 5.0,
                validation_delay_sec: float = 0.2):
        """
        Initialize the effect validator.
        
        Args:
            min_release_mb: Minimum expected memory release in MB to consider successful
            min_release_percent: Minimum percentage of memory to release
            validation_delay_sec: Seconds to wait after release before measuring effect
        """
        self.min_release_mb = min_release_mb
        self.min_release_percent = min_release_percent
        self.validation_delay_sec = validation_delay_sec
        self.effects_log: List[ReleaseEffect] = []
        self.backup_strategies: Dict[str, Callable] = {}
        
    def register_backup_strategy(self, 
                               strategy_id: str,
                               strategy_func: Callable,
                               priority: int = 0):
        """
        Register a backup strategy to try when primary resource release fails.
        
        Args:
            strategy_id: Unique identifier for this strategy
            strategy_func: Function to call for this strategy, should take resource_id
            priority: Priority of this strategy (higher = try first)
        """
        self.backup_strategies[strategy_id] = {
            "func": strategy_func,
            "priority": priority
        }
        
    def get_current_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_usage_mb = memory_info.rss / (1024 * 1024)
        return memory_usage_mb
        
    def validate_release(self, 
                        resource_id: str,
                        before_memory_mb: Optional[float] = None) -> ReleaseEffect:
        """
        Validate the effect of a resource release.
        
        Args:
            resource_id: ID of the resource that was released
            before_memory_mb: Memory usage before release (if already measured)
            
        Returns:
            ReleaseEffect object with release statistics
        """
        # If before measurement not provided, use the stored value
        if before_memory_mb is None:
            # No previous measurement, so we can't validate properly
            logger.warning(f"No pre-release memory measurement for {resource_id}")
            before_memory_mb = 0
            
        # Wait a moment for memory to be reclaimed
        time.sleep(self.validation_delay_sec)
        
        # Force garbage collection to ensure released memory is reclaimed
        gc.collect()
        
        # Measure after memory usage
        after_memory_mb = self.get_current_memory_usage()
        
        # Create effect record
        effect = ReleaseEffect(
            resource_id=resource_id,
            before_memory_mb=before_memory_mb,
            after_memory_mb=after_memory_mb,
            timestamp=time.time()
        )
        
        # Log the effect
        self.effects_log.append(effect)
        
        # Log message about the release
        if effect.success:
            if effect.memory_delta_mb >= self.min_release_mb:
                logger.info(str(effect))
            else:
                logger.warning(f"{str(effect)} - Small release")
        else:
            logger.warning(f"{str(effect)} - Failed release")
            
        return effect
        
    def is_release_effective(self, effect: ReleaseEffect) -> bool:
        """
        Determine if a release was effective based on configured thresholds.
        
        Args:
            effect: The ReleaseEffect to evaluate
            
        Returns:
            True if the release met the minimum thresholds
        """
        # Check absolute release size
        if effect.memory_delta_mb >= self.min_release_mb:
            return True
            
        # Check percentage release
        if (effect.release_percent >= self.min_release_percent and 
            effect.memory_delta_mb > 0):
            return True
            
        return False
        
    def try_backup_strategies(self,
                            resource_id: str,
                            failed_effect: ReleaseEffect) -> Tuple[bool, ReleaseEffect]:
        """
        Try backup strategies when a primary release fails.
        
        Args:
            resource_id: ID of the resource to release
            failed_effect: The failed release effect
            
        Returns:
            Tuple of (success, best_effect)
        """
        if not self.backup_strategies:
            return False, failed_effect
            
        # Sort strategies by priority
        sorted_strategies = sorted(
            self.backup_strategies.items(),
            key=lambda x: x[1]["priority"],
            reverse=True
        )
        
        best_effect = failed_effect
        success = False
        
        # Try each strategy in order
        for strategy_id, strategy_info in sorted_strategies:
            logger.info(f"Trying backup strategy {strategy_id} for {resource_id}")
            
            # Measure memory before this strategy
            before_mb = self.get_current_memory_usage()
            
            try:
                # Call the strategy function
                strategy_info["func"](resource_id)
                
                # Force garbage collection
                gc.collect()
                
                # Validate the effect
                effect = self.validate_release(resource_id, before_mb)
                
                # If this strategy was effective, update our best effect
                if self.is_release_effective(effect):
                    best_effect = effect
                    success = True
                    logger.info(f"Backup strategy {strategy_id} was effective")
                    break
                else:
                    logger.warning(f"Backup strategy {strategy_id} was not effective")
                    
            except Exception as e:
                logger.error(f"Error in backup strategy {strategy_id}: {e}")
                
        return success, best_effect
        
    def get_resource_release_history(self, resource_id: str) -> List[ReleaseEffect]:
        """Get the release history for a specific resource."""
        return [e for e in self.effects_log if e.resource_id == resource_id]
        
    def get_average_release_size(self, resource_id: str = None) -> float:
        """Get the average memory release size in MB."""
        if resource_id:
            effects = self.get_resource_release_history(resource_id)
        else:
            effects = self.effects_log
            
        if not effects:
            return 0.0
            
        total_delta = sum(e.memory_delta_mb for e in effects)
        return total_delta / len(effects)
        
    def get_total_released_memory(self) -> float:
        """Get the total amount of memory released in MB."""
        return sum(e.memory_delta_mb for e in self.effects_log if e.memory_delta_mb > 0)
        
    def get_release_effectiveness_stats(self) -> Dict[str, Any]:
        """Get statistics about release effectiveness."""
        if not self.effects_log:
            return {
                "total_releases": 0,
                "successful_releases": 0,
                "success_rate": 0,
                "total_memory_released_mb": 0,
                "average_release_mb": 0,
                "largest_release_mb": 0,
            }
            
        successful = [e for e in self.effects_log 
                     if self.is_release_effective(e)]
        
        return {
            "total_releases": len(self.effects_log),
            "successful_releases": len(successful),
            "success_rate": len(successful) / len(self.effects_log) * 100,
            "total_memory_released_mb": self.get_total_released_memory(),
            "average_release_mb": self.get_average_release_size(),
            "largest_release_mb": max([e.memory_delta_mb for e in self.effects_log], default=0),
        }


class ResourceReleaseExecutor:
    """
    Executes resource release with validation and backup strategies.
    """
    
    def __init__(self, effect_validator: EffectValidator):
        self.effect_validator = effect_validator
        self.primary_handlers: Dict[str, Callable] = {}
        
    def register_primary_handler(self, 
                                resource_type: str, 
                                handler_func: Callable):
        """
        Register a primary release handler for a resource type.
        
        Args:
            resource_type: Type of resource this handler can release
            handler_func: Function that takes a resource object and releases it
        """
        self.primary_handlers[resource_type] = handler_func
        
    def release_with_validation(self,
                               resource_id: str,
                               resource: Any,
                               resource_type: str) -> Tuple[bool, ReleaseEffect]:
        """
        Release a resource with validation and fallback strategies.
        
        Args:
            resource_id: ID of the resource to release
            resource: The resource object to release
            resource_type: Type of the resource
            
        Returns:
            Tuple of (success, effect)
        """
        # Find the appropriate handler
        handler = self.primary_handlers.get(resource_type)
        if not handler:
            logger.error(f"No release handler found for resource type {resource_type}")
            return False, None
            
        # Measure memory before release
        before_mb = self.effect_validator.get_current_memory_usage()
        
        try:
            # Attempt primary release
            handler(resource)
            
            # Force garbage collection
            gc.collect()
            
            # Validate the effect
            effect = self.effect_validator.validate_release(resource_id, before_mb)
            
            # Check if the release was effective
            if self.effect_validator.is_release_effective(effect):
                return True, effect
                
            # If not effective, try backup strategies
            logger.warning(f"Primary release of {resource_id} was not effective")
            return self.effect_validator.try_backup_strategies(resource_id, effect)
            
        except Exception as e:
            logger.error(f"Error in primary release of {resource_id}: {e}")
            
            # Create a failed effect record
            failed_effect = ReleaseEffect(
                resource_id=resource_id,
                before_memory_mb=before_mb,
                after_memory_mb=before_mb,  # No change
                timestamp=time.time()
            )
            
            # Try backup strategies
            return self.effect_validator.try_backup_strategies(resource_id, failed_effect) 