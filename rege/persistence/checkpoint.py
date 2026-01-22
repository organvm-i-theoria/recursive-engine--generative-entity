"""
RE:GE Checkpoint Manager - State snapshot persistence.

Manages:
- Creating checkpoints
- Restoring from checkpoints
- Checkpoint registry
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

from rege.core.models import StateSnapshot, RecoveryTrigger
from rege.core.exceptions import CheckpointNotFound, PersistenceError
from rege.persistence.archive import ArchiveManager, get_archive_manager


class CheckpointManager:
    """
    Manages state checkpoints for system recovery.

    Checkpoint structure:
    checkpoints/
    ├── CHECKPOINT_REGISTRY.json
    └── snapshots/
        ├── SNAP_20250420_033300_001.json
        └── ...
    """

    def __init__(self, archive_manager: Optional[ArchiveManager] = None):
        """
        Initialize checkpoint manager.

        Args:
            archive_manager: Archive manager for persistence
        """
        self.archive = archive_manager or get_archive_manager()
        self._snapshots_dir = self.archive.archive_dir / "checkpoints" / "snapshots"
        self._snapshots_dir.mkdir(parents=True, exist_ok=True)

    def create_checkpoint(
        self,
        name: str,
        system_state: Dict[str, Any],
        trigger: RecoveryTrigger = RecoveryTrigger.MANUAL,
    ) -> StateSnapshot:
        """
        Create a new checkpoint.

        Args:
            name: Descriptive name for the checkpoint
            system_state: Current system state data
            trigger: What triggered this checkpoint

        Returns:
            The created StateSnapshot
        """
        now = datetime.now()
        snapshot_id = f"SNAP_{now.strftime('%Y%m%d_%H%M%S')}"

        snapshot = StateSnapshot(
            snapshot_id=snapshot_id,
            timestamp=now,
            trigger=trigger,
            system_state=system_state.get("metrics", {}),
            organ_states=system_state.get("organs", {}),
            pending_operations=system_state.get("pending", []),
            error_log=system_state.get("errors", []),
        )

        # Add name to system state
        snapshot.system_state["checkpoint_name"] = name

        # Save snapshot
        self._save_snapshot(snapshot)

        # Update registry
        self._update_registry(snapshot)

        return snapshot

    def _save_snapshot(self, snapshot: StateSnapshot) -> str:
        """Save a snapshot to file."""
        file_path = self._snapshots_dir / f"{snapshot.snapshot_id}.json"

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(snapshot.to_dict(), f, indent=2, default=str)
        except Exception as e:
            raise PersistenceError(f"Failed to save snapshot: {e}")

        return str(file_path)

    def _update_registry(self, snapshot: StateSnapshot) -> None:
        """Update the checkpoint registry."""
        registry = self.archive.load_checkpoint_registry()

        entry = {
            "snapshot_id": snapshot.snapshot_id,
            "name": snapshot.system_state.get("checkpoint_name", "unnamed"),
            "timestamp": snapshot.timestamp.isoformat(),
            "trigger": snapshot.trigger.value,
        }

        registry.append(entry)
        self.archive.save_checkpoint_registry(registry)

    def load_checkpoint(self, snapshot_id: str) -> StateSnapshot:
        """
        Load a checkpoint by ID.

        Args:
            snapshot_id: ID of the snapshot

        Returns:
            The loaded StateSnapshot

        Raises:
            CheckpointNotFound: If checkpoint doesn't exist
        """
        file_path = self._snapshots_dir / f"{snapshot_id}.json"

        if not file_path.exists():
            raise CheckpointNotFound(snapshot_id)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            raise PersistenceError(f"Failed to load snapshot: {e}")

        return StateSnapshot.from_dict(data)

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """List all checkpoints in registry."""
        return self.archive.load_checkpoint_registry()

    def get_latest_checkpoint(self) -> Optional[StateSnapshot]:
        """Get the most recent checkpoint."""
        registry = self.list_checkpoints()
        if not registry:
            return None

        # Sort by timestamp and get latest
        sorted_registry = sorted(registry, key=lambda x: x["timestamp"], reverse=True)
        return self.load_checkpoint(sorted_registry[0]["snapshot_id"])

    def get_checkpoint_by_name(self, name: str) -> Optional[StateSnapshot]:
        """Find a checkpoint by name."""
        registry = self.list_checkpoints()

        for entry in registry:
            if entry.get("name") == name:
                return self.load_checkpoint(entry["snapshot_id"])

        return None

    def delete_checkpoint(self, snapshot_id: str) -> bool:
        """
        Delete a checkpoint.

        Args:
            snapshot_id: ID of the snapshot to delete

        Returns:
            True if deleted
        """
        file_path = self._snapshots_dir / f"{snapshot_id}.json"

        if not file_path.exists():
            return False

        file_path.unlink()

        # Update registry
        registry = self.archive.load_checkpoint_registry()
        registry = [e for e in registry if e["snapshot_id"] != snapshot_id]
        self.archive.save_checkpoint_registry(registry)

        return True

    def prune_old_checkpoints(self, keep_count: int = 10) -> int:
        """
        Remove old checkpoints, keeping only the most recent.

        Args:
            keep_count: Number of checkpoints to keep

        Returns:
            Number of checkpoints deleted
        """
        registry = self.list_checkpoints()

        if len(registry) <= keep_count:
            return 0

        # Sort by timestamp
        sorted_registry = sorted(registry, key=lambda x: x["timestamp"], reverse=True)

        # Delete old ones
        to_delete = sorted_registry[keep_count:]
        deleted = 0

        for entry in to_delete:
            if self.delete_checkpoint(entry["snapshot_id"]):
                deleted += 1

        return deleted

    def export_checkpoint(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Export a checkpoint for external use.

        Args:
            snapshot_id: ID of the snapshot

        Returns:
            Full snapshot data as dictionary
        """
        snapshot = self.load_checkpoint(snapshot_id)
        return snapshot.to_dict()

    def import_checkpoint(self, data: Dict[str, Any]) -> StateSnapshot:
        """
        Import a checkpoint from external data.

        Args:
            data: Snapshot data dictionary

        Returns:
            The imported StateSnapshot
        """
        snapshot = StateSnapshot.from_dict(data)

        # Save it
        self._save_snapshot(snapshot)
        self._update_registry(snapshot)

        return snapshot


# Global checkpoint manager instance
_checkpoint_manager: Optional[CheckpointManager] = None


def get_checkpoint_manager() -> CheckpointManager:
    """Get or create global checkpoint manager instance."""
    global _checkpoint_manager
    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager()
    return _checkpoint_manager
