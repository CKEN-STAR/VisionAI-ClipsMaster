import os
import pickle
import time
import logging
import gc
from typing import Dict, Any, List, Optional, Tuple, Callable
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RecoveryManager")

class SystemState:
    """Represents a system state snapshot that can be restored."""
    
    def __init__(self, 
                 state_id: str,
                 timestamp: float,
                 metadata: Dict[str, Any] = None):
        self.state_id = state_id
        self.timestamp = timestamp
        self.metadata = metadata or {}
        self.resource_states: Dict[str, Any] = {}
        self.resource_dependencies: Dict[str, List[str]] = {}
        
    def add_resource_state(self, 
                          resource_id: str, 
                          state: Any,
                          dependencies: List[str] = None):
        """Add a resource state to this system state snapshot."""
        self.resource_states[resource_id] = state
        self.resource_dependencies[resource_id] = dependencies or []
        
    def get_restore_order(self) -> List[str]:
        """
        Determine the order in which resources should be restored.
        Resources are restored in dependency order (dependencies first).
        """
        result = []
        visited = set()
        
        def visit(resource_id):
            if resource_id in visited:
                return
            visited.add(resource_id)
            
            # First restore all dependencies
            dependencies = self.resource_dependencies.get(resource_id, [])
            for dep_id in dependencies:
                if dep_id in self.resource_states:
                    visit(dep_id)
            
            result.append(resource_id)
            
        # Start with all resources
        for rid in self.resource_states:
            visit(rid)
            
        return result


class RecoveryPoint:
    """Defines a restoration point with recovery strategy."""
    
    def __init__(self, 
                 point_id: str,
                 state: SystemState,
                 priority: int = 0):
        self.point_id = point_id
        self.state = state
        self.priority = priority  # Higher priority points are attempted first
        self.restoration_attempts = 0
        self.last_attempt_time = 0
        self.success = False
        
    def mark_attempt(self, success: bool):
        """Mark a restoration attempt."""
        self.restoration_attempts += 1
        self.last_attempt_time = time.time()
        self.success = success


class RecoveryManager:
    """Manages system recovery after circuit breaking events."""
    
    def __init__(self, 
                 snapshot_dir: str = "recovery_snapshots",
                 max_snapshots: int = 5,
                 auto_snapshot_interval: int = 300):  # 5 minutes
        """
        Initialize the recovery manager.
        
        Args:
            snapshot_dir: Directory to store snapshot files
            max_snapshots: Maximum number of snapshots to keep
            auto_snapshot_interval: Time between automatic snapshots (seconds)
        """
        self.snapshot_dir = snapshot_dir
        self.max_snapshots = max_snapshots
        self.auto_snapshot_interval = auto_snapshot_interval
        
        self.snapshots: Dict[str, SystemState] = {}
        self.recovery_points: Dict[str, RecoveryPoint] = {}
        self.resource_restorers: Dict[str, Callable] = {}
        
        self.last_auto_snapshot = 0
        self.auto_snapshot_running = False
        
        # Ensure snapshot directory exists
        os.makedirs(snapshot_dir, exist_ok=True)
        
        # Start automatic snapshot thread if interval > 0
        if auto_snapshot_interval > 0:
            self._start_auto_snapshot_thread()
    
    def _start_auto_snapshot_thread(self):
        """Start background thread for automatic snapshots."""
        def auto_snapshot_worker():
            while self.auto_snapshot_running:
                current_time = time.time()
                if (current_time - self.last_auto_snapshot >= 
                    self.auto_snapshot_interval):
                    try:
                        snapshot_id = f"auto_{int(current_time)}"
                        self.create_snapshot(snapshot_id, 
                                            {"type": "automatic"})
                        self.last_auto_snapshot = current_time
                    except Exception as e:
                        logger.error(f"Auto snapshot error: {e}")
                time.sleep(10)  # Check every 10 seconds
                
        self.auto_snapshot_running = True
        thread = threading.Thread(target=auto_snapshot_worker, daemon=True)
        thread.start()
        
    def register_resource_restorer(self, 
                                  resource_type: str, 
                                  restore_func: Callable):
        """
        Register a function that can restore a resource from its state.
        
        Args:
            resource_type: Type identifier for the resource
            restore_func: Function(resource_state) -> restored_resource
        """
        self.resource_restorers[resource_type] = restore_func
        
    def create_snapshot(self, 
                       snapshot_id: str,
                       metadata: Dict[str, Any] = None) -> SystemState:
        """
        Create a new system state snapshot.
        
        Args:
            snapshot_id: Unique identifier for this snapshot
            metadata: Additional data about this snapshot
            
        Returns:
            The created SystemState object
        """
        state = SystemState(
            state_id=snapshot_id,
            timestamp=time.time(),
            metadata=metadata
        )
        
        self.snapshots[snapshot_id] = state
        
        # Save to disk
        self._save_snapshot(state)
        
        # Clean up old snapshots if needed
        self._cleanup_old_snapshots()
        
        return state
        
    def _save_snapshot(self, state: SystemState):
        """Save a snapshot to disk."""
        try:
            filename = os.path.join(
                self.snapshot_dir, 
                f"{state.state_id}.snapshot"
            )
            with open(filename, 'wb') as f:
                pickle.dump(state, f)
            logger.info(f"Saved snapshot {state.state_id} to disk")
        except Exception as e:
            logger.error(f"Failed to save snapshot {state.state_id}: {e}")
            
    def _load_snapshot(self, snapshot_id: str) -> Optional[SystemState]:
        """Load a snapshot from disk."""
        try:
            filename = os.path.join(
                self.snapshot_dir, 
                f"{snapshot_id}.snapshot"
            )
            if not os.path.exists(filename):
                return None
                
            with open(filename, 'rb') as f:
                state = pickle.load(f)
            logger.info(f"Loaded snapshot {snapshot_id} from disk")
            return state
        except Exception as e:
            logger.error(f"Failed to load snapshot {snapshot_id}: {e}")
            return None
            
    def _cleanup_old_snapshots(self):
        """Remove old snapshots to stay within max limit."""
        if len(self.snapshots) <= self.max_snapshots:
            return
            
        # Sort by timestamp (oldest first)
        sorted_ids = sorted(
            self.snapshots.keys(),
            key=lambda sid: self.snapshots[sid].timestamp
        )
        
        # Remove oldest
        to_remove = sorted_ids[:len(sorted_ids) - self.max_snapshots]
        for sid in to_remove:
            self._delete_snapshot(sid)
            
    def _delete_snapshot(self, snapshot_id: str):
        """Delete a snapshot from memory and disk."""
        if snapshot_id in self.snapshots:
            self.snapshots.pop(snapshot_id)
            
        # Remove from disk
        try:
            filename = os.path.join(
                self.snapshot_dir, 
                f"{snapshot_id}.snapshot"
            )
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as e:
            logger.error(f"Error deleting snapshot file {snapshot_id}: {e}")
            
    def add_resource_to_snapshot(self,
                               snapshot_id: str,
                               resource_id: str,
                               resource_type: str,
                               resource_state: Any,
                               dependencies: List[str] = None):
        """
        Add a resource state to an existing snapshot.
        
        Args:
            snapshot_id: Identifier of the snapshot
            resource_id: Unique identifier for this resource
            resource_type: Type of resource for proper restoration
            resource_state: Serializable state of the resource
            dependencies: IDs of resources this one depends on
        """
        if snapshot_id not in self.snapshots:
            # Try to load from disk
            state = self._load_snapshot(snapshot_id)
            if not state:
                logger.error(f"Snapshot {snapshot_id} not found")
                return False
            self.snapshots[snapshot_id] = state
            
        state = self.snapshots[snapshot_id]
        
        # Add type information to the state
        if isinstance(resource_state, dict):
            resource_state["__resource_type"] = resource_type
        else:
            resource_state = {
                "__resource_type": resource_type,
                "value": resource_state
            }
            
        state.add_resource_state(
            resource_id=resource_id,
            state=resource_state,
            dependencies=dependencies
        )
        
        # Update the snapshot on disk
        self._save_snapshot(state)
        return True
        
    def create_recovery_point(self,
                             point_id: str,
                             snapshot_id: str,
                             priority: int = 0) -> Optional[RecoveryPoint]:
        """
        Create a recovery point from an existing snapshot.
        
        Args:
            point_id: Unique identifier for this recovery point
            snapshot_id: ID of the snapshot to use for recovery
            priority: Priority of this recovery point (higher = try first)
            
        Returns:
            The created RecoveryPoint or None if snapshot not found
        """
        # Ensure snapshot exists
        if snapshot_id not in self.snapshots:
            state = self._load_snapshot(snapshot_id)
            if not state:
                logger.error(f"Cannot create recovery point: Snapshot {snapshot_id} not found")
                return None
            self.snapshots[snapshot_id] = state
            
        point = RecoveryPoint(
            point_id=point_id,
            state=self.snapshots[snapshot_id],
            priority=priority
        )
        
        self.recovery_points[point_id] = point
        return point
        
    def restore_from_point(self, 
                          point_id: str,
                          resource_filter: List[str] = None) -> Dict[str, bool]:
        """
        Attempt to restore system state from a recovery point.
        
        Args:
            point_id: ID of the recovery point to restore from
            resource_filter: Optional list of resource IDs to restore
                            (if None, all resources in the point are restored)
                            
        Returns:
            Dictionary mapping resource IDs to restoration success
        """
        if point_id not in self.recovery_points:
            logger.error(f"Recovery point {point_id} not found")
            return {}
            
        recovery_point = self.recovery_points[point_id]
        system_state = recovery_point.state
        
        # Mark the attempt
        recovery_point.mark_attempt(False)  # Will be updated on success
        
        # Determine restoration order
        restore_order = system_state.get_restore_order()
        
        # Filter if needed
        if resource_filter:
            restore_order = [rid for rid in restore_order if rid in resource_filter]
            
        # Start restoration
        results = {}
        success_count = 0
        
        for resource_id in restore_order:
            resource_state = system_state.resource_states.get(resource_id)
            if not resource_state:
                logger.warning(f"Resource {resource_id} not found in state")
                results[resource_id] = False
                continue
                
            # Get the resource type
            if isinstance(resource_state, dict) and "__resource_type" in resource_state:
                resource_type = resource_state["__resource_type"]
                
                # Clean state if needed
                if "value" in resource_state and len(resource_state) == 2:
                    # This is a simple resource with just type and value
                    resource_state = resource_state["value"]
            else:
                logger.warning(f"Resource {resource_id} has no type information")
                results[resource_id] = False
                continue
                
            # Find the appropriate restorer
            restorer = self.resource_restorers.get(resource_type)
            if not restorer:
                logger.warning(f"No restorer found for resource type {resource_type}")
                results[resource_id] = False
                continue
                
            # Attempt restoration
            try:
                restorer(resource_id, resource_state)
                results[resource_id] = True
                success_count += 1
                logger.info(f"Successfully restored resource {resource_id}")
            except Exception as e:
                logger.error(f"Failed to restore resource {resource_id}: {e}")
                results[resource_id] = False
                
        # Force garbage collection
        gc.collect()
        
        # Update recovery point status
        all_success = success_count == len(restore_order) and success_count > 0
        recovery_point.mark_attempt(all_success)
        
        return results
        
    def find_best_recovery_point(self) -> Optional[str]:
        """
        Find the best recovery point to attempt restoration from.
        Considers priority and previous attempt success.
        
        Returns:
            ID of the best recovery point or None if no points available
        """
        if not self.recovery_points:
            return None
            
        # First try points that have succeeded before
        successful_points = [
            (pid, point) for pid, point in self.recovery_points.items()
            if point.success
        ]
        
        if successful_points:
            # Sort by priority (higher first)
            successful_points.sort(key=lambda x: x[1].priority, reverse=True)
            return successful_points[0][0]
            
        # If no successful points, use all points
        all_points = list(self.recovery_points.items())
        
        # Sort by priority (higher first) and attempts (fewer first)
        all_points.sort(
            key=lambda x: (x[1].priority, -x[1].restoration_attempts), 
            reverse=True
        )
        
        return all_points[0][0] if all_points else None
        
    def auto_restore(self) -> Tuple[bool, Dict[str, bool]]:
        """
        Automatically choose the best recovery point and attempt restoration.
        
        Returns:
            Tuple of (overall_success, resource_results)
        """
        point_id = self.find_best_recovery_point()
        if not point_id:
            logger.warning("No recovery points available for auto-restore")
            return False, {}
            
        logger.info(f"Auto-restoring from point {point_id}")
        results = self.restore_from_point(point_id)
        
        # Check if all resources were restored successfully
        overall_success = all(results.values()) and results
        
        return overall_success, results 