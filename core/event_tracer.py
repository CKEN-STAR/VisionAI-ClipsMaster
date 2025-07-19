import logging
import json
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80


# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EventTracer")

class EventTracer:
    """
    EventTracer records circuit-breaking events and provides analytics
    for understanding memory-related issues in the application.
    """
    
    def __init__(self, 
                 log_directory: str = "logs",
                 max_events_in_memory: int = 1000,
                 auto_save_count: int = 100):
        """
        Initialize the EventTracer.
        
        Args:
            log_directory: Directory to store log files
            max_events_in_memory: Maximum number of events to keep in memory
            auto_save_count: Number of events after which to auto-save
        """
        self.log_directory = log_directory
        self.max_events_in_memory = max_events_in_memory
        self.auto_save_count = auto_save_count
        
        # Create log directory if it doesn't exist
        os.makedirs(log_directory, exist_ok=True)
        
        # Initialize events list
        self.events: List[Dict[str, Any]] = []
        self.events_since_save = 0
        
        # Generate log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_directory, f"circuit_events_{timestamp}.json")
        
        logger.info(f"EventTracer initialized with log file: {self.log_file}")
    
    def record_event(self, event_type: str, **kwargs) -> None:
        """
        Record a generic event with custom data.
        
        Args:
            event_type: Type of event
            **kwargs: Additional event data
        """
        event = {
            "type": event_type,
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            **kwargs
        }
        
        self.events.append(event)
        self.events_since_save += 1
        
        # Trim events if exceeding max limit
        if len(self.events) > self.max_events_in_memory:
            self.events = self.events[-self.max_events_in_memory:]
        
        # Auto-save if needed
        if self.events_since_save >= self.auto_save_count:
            self.save_events()
    
    def record_circuit_break_event(self, memory_usage: float, threshold: float, **kwargs) -> None:
        """
        Record a circuit-break event.
        
        Args:
            memory_usage: Current memory usage in MB
            threshold: Memory threshold in MB
            **kwargs: Additional event data
        """
        self.record_event(
            event_type="circuit_break",
            memory_usage_mb=memory_usage,
            threshold_mb=threshold,
            **kwargs
        )
        logger.info(f"Recorded circuit break event: {memory_usage:.2f}MB/{threshold:.2f}MB")
    
    def record_circuit_reset_event(self, memory_usage: float, threshold: float, **kwargs) -> None:
        """
        Record a circuit-reset event.
        
        Args:
            memory_usage: Current memory usage in MB
            threshold: Memory threshold in MB
            **kwargs: Additional event data
        """
        self.record_event(
            event_type="circuit_reset",
            memory_usage_mb=memory_usage,
            threshold_mb=threshold,
            **kwargs
        )
        logger.info(f"Recorded circuit reset event: {memory_usage:.2f}MB/{threshold:.2f}MB")
    
    def record_memory_leak_event(self, function_name: str, leak_amount: float, **kwargs) -> None:
        """
        Record a memory leak detection event.
        
        Args:
            function_name: Name of function with potential leak
            leak_amount: Amount of memory leaked in MB
            **kwargs: Additional event data
        """
        self.record_event(
            event_type="memory_leak",
            function_name=function_name,
            leak_amount_mb=leak_amount,
            **kwargs
        )
        logger.info(f"Recorded memory leak event: {function_name} leaked {leak_amount:.2f}MB")
    
    def record_recovery_event(self, checkpoint_id: str, success: bool, **kwargs) -> None:
        """
        Record a recovery attempt event.
        
        Args:
            checkpoint_id: ID of the checkpoint used for recovery
            success: Whether recovery was successful
            **kwargs: Additional event data
        """
        self.record_event(
            event_type="recovery_attempt",
            checkpoint_id=checkpoint_id,
            success=success,
            **kwargs
        )
        
        status = "successful" if success else "failed"
        logger.info(f"Recorded {status} recovery event from checkpoint {checkpoint_id}")
    
    def save_events(self) -> None:
        """
        Save events to the log file.
        """
        try:
            # Load existing events if file exists
            existing_events = []
            if os.path.exists(self.log_file):
                try:
                    with open(self.log_file, 'r') as f:
                        existing_events = json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse existing log file: {self.log_file}")
            
            # Combine existing and new events
            all_events = existing_events + self.events
            
            # Write to file
            with open(self.log_file, 'w') as f:
                json.dump(all_events, f, indent=2)
            
            self.events_since_save = 0
            logger.debug(f"Saved {len(self.events)} events to log file")
        except Exception as e:
            logger.error(f"Failed to save events: {e}")
    
    def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """
        Get events of a specific type.
        
        Args:
            event_type: Type of events to get
            
        Returns:
            List of events of the specified type
        """
        return [e for e in self.events if e["type"] == event_type]
    
    def get_circuit_break_frequency(self, time_window_seconds: Optional[float] = None) -> float:
        """
        Calculate the frequency of circuit breaks.
        
        Args:
            time_window_seconds: Time window to consider, or None for all time
            
        Returns:
            Frequency of circuit breaks per hour
        """
        circuit_breaks = self.get_events_by_type("circuit_break")
        
        if not circuit_breaks:
            return 0.0
        
        now = time.time()
        
        if time_window_seconds:
            # Filter events within time window
            circuit_breaks = [e for e in circuit_breaks if now - e["timestamp"] <= time_window_seconds]
            
            if not circuit_breaks:
                return 0.0
            
            # Calculate frequency within window
            return len(circuit_breaks) / (time_window_seconds / 3600)  # per hour
        
        # Calculate all-time frequency
        oldest = min(e["timestamp"] for e in circuit_breaks)
        time_span = now - oldest
        
        if time_span <= 0:
            return 0.0
            
        return len(circuit_breaks) / (time_span / 3600)  # per hour
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of recorded events.
        
        Returns:
            Dictionary with event statistics
        """
        circuit_breaks = self.get_events_by_type("circuit_break")
        resets = self.get_events_by_type("circuit_reset")
        leaks = self.get_events_by_type("memory_leak")
        recoveries = self.get_events_by_type("recovery_attempt")
        
        successful_recoveries = [r for r in recoveries if r.get("success", False)]
        
        return {
            "total_events": len(self.events),
            "circuit_breaks": len(circuit_breaks),
            "circuit_resets": len(resets),
            "memory_leaks": len(leaks),
            "recovery_attempts": len(recoveries),
            "successful_recoveries": len(successful_recoveries),
            "recovery_success_rate": len(successful_recoveries) / len(recoveries) if recoveries else 0,
            "circuit_break_frequency_1h": self.get_circuit_break_frequency(3600),
            "circuit_break_frequency_24h": self.get_circuit_break_frequency(86400),
            "circuit_break_frequency_all": self.get_circuit_break_frequency()
        } 