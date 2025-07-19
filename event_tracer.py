import time
import json
import os
import logging
import datetime
from typing import Dict, Any, List, Optional, Union
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EventTracer")

class CircuitEvent:
    """
    Represents a circuit breaking event with detailed information.
    """
    
    EVENT_TYPES = {
        "MEMORY_WARNING": 10,
        "CIRCUIT_BREAK": 20,
        "RESOURCE_RELEASE": 30,
        "RECOVERY_ATTEMPT": 40,
        "RECOVERY_SUCCESS": 50,
        "RECOVERY_FAILURE": 60
    }
    
    def __init__(self, 
                 event_type: str,
                 source: str,
                 details: Dict[str, Any] = None,
                 timestamp: float = None):
        """
        Initialize a circuit event.
        
        Args:
            event_type: Type of event (use EVENT_TYPES constants)
            source: Component that generated this event
            details: Additional event details
            timestamp: Event time (defaults to now)
        """
        self.event_type = event_type
        self.source = source
        self.details = details or {}
        self.timestamp = timestamp or time.time()
        self.event_id = f"{int(self.timestamp)}_{event_type}_{hash(str(details))}"
        self.related_events: List[str] = []  # IDs of related events
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "details": self.details,
            "timestamp": self.timestamp,
            "datetime": datetime.datetime.fromtimestamp(self.timestamp).isoformat(),
            "related_events": self.related_events
        }
        
    def relate_to(self, other_event: Union[str, 'CircuitEvent']):
        """Mark this event as related to another event."""
        event_id = other_event if isinstance(other_event, str) else other_event.event_id
        if event_id not in self.related_events:
            self.related_events.append(event_id)
            
    def __str__(self):
        timestamp_str = datetime.datetime.fromtimestamp(self.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        return f"[{timestamp_str}] {self.source} - {self.event_type}"


class EventTracer:
    """
    Traces and analyzes circuit breaking events.
    """
    
    def __init__(self, 
                 log_dir: str = "circuit_event_logs",
                 max_events_in_memory: int = 1000,
                 auto_persist: bool = True):
        """
        Initialize the event tracer.
        
        Args:
            log_dir: Directory to store event logs
            max_events_in_memory: Maximum number of events to keep in memory
            auto_persist: Whether to automatically persist events to disk
        """
        self.log_dir = log_dir
        self.max_events_in_memory = max_events_in_memory
        self.auto_persist = auto_persist
        
        self.events: List[CircuitEvent] = []
        self.event_map: Dict[str, CircuitEvent] = {}  # For quick lookup by ID
        
        self.session_id = f"session_{int(time.time())}"
        self.last_persist_time = 0
        self.persist_lock = threading.Lock()
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
    def record_event(self, 
                    event_type: str,
                    source: str,
                    details: Dict[str, Any] = None,
                    related_to: Optional[Union[str, CircuitEvent]] = None) -> CircuitEvent:
        """
        Record a new circuit breaking event.
        
        Args:
            event_type: Type of event (use CircuitEvent.EVENT_TYPES)
            source: Component that generated this event
            details: Additional event details
            related_to: Optional event this one is related to
            
        Returns:
            The created CircuitEvent
        """
        event = CircuitEvent(
            event_type=event_type,
            source=source,
            details=details
        )
        
        # Add relation if specified
        if related_to:
            event.relate_to(related_to)
            
            # If we have the related event, add reverse relation
            if isinstance(related_to, CircuitEvent):
                related_to.relate_to(event)
            elif related_to in self.event_map:
                self.event_map[related_to].relate_to(event)
                
        # Store the event
        self.events.append(event)
        self.event_map[event.event_id] = event
        
        # Log the event
        if event_type == CircuitEvent.EVENT_TYPES["CIRCUIT_BREAK"]:
            logger.warning(f"Circuit break event: {source} - {details}")
        else:
            logger.info(f"Event: {event}")
            
        # Clean up old events if needed
        if len(self.events) > self.max_events_in_memory:
            excess = len(self.events) - self.max_events_in_memory
            if self.auto_persist:
                # Persist events before removing
                self._persist_events(self.events[:excess])
                
            # Remove oldest events
            removed = self.events[:excess]
            for e in removed:
                self.event_map.pop(e.event_id, None)
            self.events = self.events[excess:]
            
        # Auto-persist if enabled
        if self.auto_persist and time.time() - self.last_persist_time > 60:  # Every minute
            self.persist_events()
            
        return event
        
    def find_events(self, 
                   event_type: Optional[str] = None,
                   source: Optional[str] = None,
                   time_start: Optional[float] = None,
                   time_end: Optional[float] = None) -> List[CircuitEvent]:
        """
        Find events matching specified criteria.
        
        Args:
            event_type: Filter by event type
            source: Filter by source component
            time_start: Filter by start time
            time_end: Filter by end time
            
        Returns:
            List of matching events
        """
        results = []
        for event in self.events:
            # Apply filters
            if event_type and event.event_type != event_type:
                continue
                
            if source and event.source != source:
                continue
                
            if time_start and event.timestamp < time_start:
                continue
                
            if time_end and event.timestamp > time_end:
                continue
                
            results.append(event)
            
        return results
        
    def get_event_by_id(self, event_id: str) -> Optional[CircuitEvent]:
        """Get an event by its ID."""
        return self.event_map.get(event_id)
        
    def find_related_events(self, event: Union[str, CircuitEvent]) -> List[CircuitEvent]:
        """Find all events related to the given event."""
        if isinstance(event, str):
            event = self.get_event_by_id(event)
            if not event:
                return []
                
        related = []
        for rel_id in event.related_events:
            rel_event = self.get_event_by_id(rel_id)
            if rel_event:
                related.append(rel_event)
                
        return related
        
    def get_event_timeline(self, 
                         time_window: float = 3600,  # 1 hour
                         max_events: int = 100) -> List[Dict[str, Any]]:
        """
        Get a timeline of events for visualization.
        
        Args:
            time_window: How far back to look in seconds
            max_events: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        now = time.time()
        start_time = now - time_window
        
        # Get events in the time window, sorted by timestamp
        events = self.find_events(time_start=start_time)
        events.sort(key=lambda e: e.timestamp)
        
        # Limit to max_events
        if len(events) > max_events:
            events = events[-max_events:]
            
        # Convert to dicts for serialization
        return [e.to_dict() for e in events]
        
    def persist_events(self):
        """Persist all events to disk."""
        with self.persist_lock:
            self._persist_events(self.events)
            self.last_persist_time = time.time()
            
    def _persist_events(self, events: List[CircuitEvent]):
        """
        Persist a list of events to disk.
        
        Args:
            events: List of events to persist
        """
        if not events:
            return
            
        # Create a batch file name with timestamp
        timestamp = int(time.time())
        filename = os.path.join(
            self.log_dir,
            f"{self.session_id}_events_{timestamp}.json"
        )
        
        try:
            # Convert events to dictionaries
            event_dicts = [e.to_dict() for e in events]
            
            # Write to file
            with open(filename, 'w') as f:
                json.dump(event_dicts, f, indent=2)
                
            logger.info(f"Persisted {len(events)} events to {filename}")
        except Exception as e:
            logger.error(f"Failed to persist events: {e}")
            
    def load_events_from_disk(self, 
                            session_id: Optional[str] = None,
                            max_age: Optional[float] = None) -> int:
        """
        Load events from disk into memory.
        
        Args:
            session_id: Optional specific session to load
            max_age: Maximum age of event files to load in seconds
            
        Returns:
            Number of events loaded
        """
        files_pattern = f"{session_id}_events_*.json" if session_id else "*.json"
        log_files = []
        
        # Find matching log files
        for filename in os.listdir(self.log_dir):
            if filename.endswith(".json") and (not session_id or filename.startswith(session_id)):
                filepath = os.path.join(self.log_dir, filename)
                file_mtime = os.path.getmtime(filepath)
                
                # Check age if specified
                if max_age and (time.time() - file_mtime) > max_age:
                    continue
                    
                log_files.append((filepath, file_mtime))
                
        # Sort by modification time (oldest first)
        log_files.sort(key=lambda x: x[1])
        
        # Load events
        count = 0
        for filepath, _ in log_files:
            try:
                with open(filepath, 'r') as f:
                    event_dicts = json.load(f)
                    
                for event_dict in event_dicts:
                    # Create CircuitEvent from dict
                    event = CircuitEvent(
                        event_type=event_dict["event_type"],
                        source=event_dict["source"],
                        details=event_dict["details"],
                        timestamp=event_dict["timestamp"]
                    )
                    event.event_id = event_dict["event_id"]
                    event.related_events = event_dict.get("related_events", [])
                    
                    # Add to our collections if not already present
                    if event.event_id not in self.event_map:
                        self.events.append(event)
                        self.event_map[event.event_id] = event
                        count += 1
                        
            except Exception as e:
                logger.error(f"Error loading events from {filepath}: {e}")
                
        logger.info(f"Loaded {count} events from disk")
        return count
        
    def analyze_circuit_breaks(self, 
                             time_window: float = 86400  # 24 hours
                             ) -> Dict[str, Any]:
        """
        Analyze circuit breaking patterns over a time period.
        
        Args:
            time_window: How far back to analyze in seconds
            
        Returns:
            Analysis results
        """
        start_time = time.time() - time_window
        
        # Get circuit break events
        breaks = self.find_events(
            event_type=CircuitEvent.EVENT_TYPES["CIRCUIT_BREAK"],
            time_start=start_time
        )
        
        if not breaks:
            return {
                "count": 0,
                "frequency_per_hour": 0,
                "sources": {},
                "recovery_success_rate": 0,
                "avg_recovery_time": 0
            }
            
        # Analyze sources
        sources = {}
        for event in breaks:
            source = event.source
            if source not in sources:
                sources[source] = 0
            sources[source] += 1
            
        # Analyze recovery success
        recovery_times = []
        recovery_success_count = 0
        
        for break_event in breaks:
            # Find related recovery events
            related = self.find_related_events(break_event)
            
            recovery_attempt = None
            recovery_success = None
            
            for rel in related:
                if rel.event_type == CircuitEvent.EVENT_TYPES["RECOVERY_ATTEMPT"]:
                    recovery_attempt = rel
                elif rel.event_type == CircuitEvent.EVENT_TYPES["RECOVERY_SUCCESS"]:
                    recovery_success = rel
                    
            if recovery_success:
                recovery_success_count += 1
                if recovery_attempt:
                    recovery_time = recovery_success.timestamp - break_event.timestamp
                    recovery_times.append(recovery_time)
                    
        # Calculate stats
        hours = time_window / 3600
        frequency = len(breaks) / hours if hours > 0 else 0
        recovery_rate = (recovery_success_count / len(breaks) * 100 
                        if breaks else 0)
        avg_recovery_time = (sum(recovery_times) / len(recovery_times) 
                           if recovery_times else 0)
        
        return {
            "count": len(breaks),
            "frequency_per_hour": frequency,
            "sources": sources,
            "recovery_success_rate": recovery_rate,
            "avg_recovery_time": avg_recovery_time
        }
        
    def get_event_stats(self) -> Dict[str, Any]:
        """Get statistics about recorded events."""
        # Count events by type
        type_counts = {}
        for event in self.events:
            if event.event_type not in type_counts:
                type_counts[event.event_type] = 0
            type_counts[event.event_type] += 1
            
        # Count events by source
        source_counts = {}
        for event in self.events:
            if event.source not in source_counts:
                source_counts[event.source] = 0
            source_counts[event.source] += 1
            
        # Get time range
        timestamps = [e.timestamp for e in self.events]
        time_range = (min(timestamps), max(timestamps)) if timestamps else (0, 0)
        
        return {
            "total_events": len(self.events),
            "events_by_type": type_counts,
            "events_by_source": source_counts,
            "time_range": time_range
        } 