import logging
import pickle
import time
import os
from typing import Dict, Any, List, Optional
import tempfile

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RecoveryManager")

class RecoveryManager:
    """
    RecoveryManager manages state restoration after circuit-breaking events.
    It provides checkpoint creation and restoration mechanisms to recover
    from memory-related issues.
    """
    
    def __init__(self, 
                 checkpoint_dir: Optional[str] = None,
                 max_checkpoints: int = 5,
                 compression_level: int = 5):
        """
        Initialize the RecoveryManager.
        
        Args:
            checkpoint_dir: Directory to store checkpoints. If None, a temp dir is used.
            max_checkpoints: Maximum number of checkpoints to keep
            compression_level: Compression level for pickle (0-9)
        """
        if checkpoint_dir:
            os.makedirs(checkpoint_dir, exist_ok=True)
            self.checkpoint_dir = checkpoint_dir
        else:
            self.checkpoint_dir = tempfile.mkdtemp(prefix="visionai_recovery_")
            
        self.max_checkpoints = max_checkpoints
        self.compression_level = compression_level
        self.checkpoints: List[Dict[str, Any]] = []
        
        logger.info(f"RecoveryManager initialized. Checkpoint dir: {self.checkpoint_dir}")
    
    def create_checkpoint(self) -> Dict[str, Any]:
        """
        Create a checkpoint of the current application state.
        
        Returns:
            Dict with checkpoint metadata
        """
        checkpoint_id = int(time.time() * 1000)
        checkpoint_path = os.path.join(self.checkpoint_dir, f"checkpoint_{checkpoint_id}.pkl")
        
        checkpoint_meta = {
            "id": checkpoint_id,
            "timestamp": time.time(),
            "path": checkpoint_path,
            "data": None  # Will be filled by function-specific state
        }
        
        # Add to checkpoints list and maintain max size
        self.checkpoints.append(checkpoint_meta)
        if len(self.checkpoints) > self.max_checkpoints:
            oldest = self.checkpoints.pop(0)
            if os.path.exists(oldest["path"]):
                try:
                    os.remove(oldest["path"])
                    logger.debug(f"Removed old checkpoint: {oldest['path']}")
                except Exception as e:
                    logger.warning(f"Failed to remove old checkpoint {oldest['path']}: {e}")
        
        logger.debug(f"Created checkpoint: {checkpoint_id}")
        return checkpoint_meta
    
    def save_state(self, checkpoint_meta: Dict[str, Any], state: Any) -> None:
        """
        Save application state to a checkpoint file.
        
        Args:
            checkpoint_meta: Checkpoint metadata from create_checkpoint
            state: Application state to save
        """
        try:
            checkpoint_path = checkpoint_meta["path"]
            with open(checkpoint_path, 'wb') as f:
                pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            checkpoint_meta["data"] = {
                "size": os.path.getsize(checkpoint_path),
                "saved_at": time.time()
            }
            logger.info(f"Saved state to checkpoint: {checkpoint_path}")
        except Exception as e:
            logger.error(f"Failed to save state to checkpoint: {e}")
    
    def restore_from_checkpoint(self, checkpoint_meta: Dict[str, Any]) -> Any:
        """
        Restore application state from a checkpoint.
        
        Args:
            checkpoint_meta: Checkpoint metadata
            
        Returns:
            Restored application state
        """
        checkpoint_path = checkpoint_meta["path"]
        
        if not os.path.exists(checkpoint_path):
            logger.warning(f"Checkpoint file not found: {checkpoint_path}")
            return None
        
        try:
            with open(checkpoint_path, 'rb') as f:
                state = pickle.load(f)
            
            logger.info(f"Restored state from checkpoint: {checkpoint_path}")
            return state
        except Exception as e:
            logger.error(f"Failed to restore from checkpoint: {e}")
            return None
    
    def get_latest_checkpoint(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest checkpoint metadata.
        
        Returns:
            Latest checkpoint metadata or None if no checkpoints
        """
        if not self.checkpoints:
            return None
        return self.checkpoints[-1]
    
    def cleanup(self) -> None:
        """
        Remove all checkpoint files.
        """
        for checkpoint in self.checkpoints:
            if os.path.exists(checkpoint["path"]):
                try:
                    os.remove(checkpoint["path"])
                except Exception as e:
                    logger.warning(f"Failed to remove checkpoint {checkpoint['path']}: {e}")
        
        self.checkpoints = []
        logger.info("All checkpoints cleaned up") 