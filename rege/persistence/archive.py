"""
RE:GE Archive Manager - JSON file persistence.

Manages persistence of:
- PATCH_RECORDS.json
- FUSION_REGISTRY.json
- CANON_EVENT_ARCHIVE.json
- QUEUE_STATE_LOG.json
- INVOCATION_LOG.json
- VIOLATION_LOG.json
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from rege.core.exceptions import PersistenceError, ArchiveCorrupted


class ArchiveManager:
    """
    Manages JSON file persistence for RE:GE system data.

    File structure:
    archive_dir/
    ├── patches/
    │   └── PATCH_RECORDS.json
    ├── fusions/
    │   └── FUSION_REGISTRY.json
    ├── canon/
    │   └── CANON_EVENT_ARCHIVE.json
    ├── queue/
    │   └── QUEUE_STATE_LOG.json
    ├── logs/
    │   ├── INVOCATION_LOG.json
    │   └── VIOLATION_LOG.json
    └── checkpoints/
        └── CHECKPOINT_REGISTRY.json
    """

    DEFAULT_ARCHIVE_DIR = ".rege_archive"

    def __init__(self, archive_dir: Optional[str] = None):
        """
        Initialize the archive manager.

        Args:
            archive_dir: Directory for archive files. Defaults to .rege_archive
        """
        self.archive_dir = Path(archive_dir or self.DEFAULT_ARCHIVE_DIR)
        self._init_directories()

    def _init_directories(self) -> None:
        """Create archive directory structure."""
        subdirs = ["patches", "fusions", "canon", "queue", "logs", "checkpoints"]
        for subdir in subdirs:
            (self.archive_dir / subdir).mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, category: str, filename: str) -> Path:
        """Get full path for a data file."""
        return self.archive_dir / category / filename

    def save(self, category: str, filename: str, data: Any) -> str:
        """
        Save data to a JSON file.

        Args:
            category: Subdirectory (patches, fusions, etc.)
            filename: File name
            data: Data to save (must be JSON serializable)

        Returns:
            Path to saved file
        """
        file_path = self._get_file_path(category, filename)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            raise PersistenceError(f"Failed to save {file_path}: {e}")

        return str(file_path)

    def load(self, category: str, filename: str) -> Any:
        """
        Load data from a JSON file.

        Args:
            category: Subdirectory
            filename: File name

        Returns:
            Loaded data

        Raises:
            ArchiveCorrupted: If file is malformed
        """
        file_path = self._get_file_path(category, filename)

        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ArchiveCorrupted(str(file_path), f"Invalid JSON: {e}")
        except Exception as e:
            raise PersistenceError(f"Failed to load {file_path}: {e}")

    def append(self, category: str, filename: str, entry: Dict) -> None:
        """
        Append an entry to a JSON array file.

        Args:
            category: Subdirectory
            filename: File name
            entry: Entry to append
        """
        existing = self.load(category, filename) or []
        if not isinstance(existing, list):
            existing = [existing]
        existing.append(entry)
        self.save(category, filename, existing)

    def exists(self, category: str, filename: str) -> bool:
        """Check if a file exists."""
        return self._get_file_path(category, filename).exists()

    # Convenience methods for specific file types

    def save_patch_records(self, patches: List[Dict]) -> str:
        """Save patch records."""
        return self.save("patches", "PATCH_RECORDS.json", {
            "patches": patches,
            "saved_at": datetime.now().isoformat(),
            "count": len(patches),
        })

    def load_patch_records(self) -> List[Dict]:
        """Load patch records."""
        data = self.load("patches", "PATCH_RECORDS.json")
        return data.get("patches", []) if data else []

    def save_fusion_registry(self, fusions: List[Dict]) -> str:
        """Save fusion registry."""
        return self.save("fusions", "FUSION_REGISTRY.json", {
            "fusions": fusions,
            "saved_at": datetime.now().isoformat(),
            "count": len(fusions),
        })

    def load_fusion_registry(self) -> List[Dict]:
        """Load fusion registry."""
        data = self.load("fusions", "FUSION_REGISTRY.json")
        return data.get("fusions", []) if data else []

    def save_canon_events(self, events: List[Dict]) -> str:
        """Save canon event archive."""
        return self.save("canon", "CANON_EVENT_ARCHIVE.json", {
            "events": events,
            "saved_at": datetime.now().isoformat(),
            "count": len(events),
        })

    def load_canon_events(self) -> List[Dict]:
        """Load canon event archive."""
        data = self.load("canon", "CANON_EVENT_ARCHIVE.json")
        return data.get("events", []) if data else []

    def save_queue_state(self, state: Dict) -> str:
        """Save queue state snapshot."""
        state["captured_at"] = datetime.now().isoformat()
        return self.save("queue", "QUEUE_STATE_LOG.json", state)

    def load_queue_state(self) -> Optional[Dict]:
        """Load queue state."""
        return self.load("queue", "QUEUE_STATE_LOG.json")

    def append_invocation_log(self, log_entry: Dict) -> None:
        """Append to invocation log."""
        self.append("logs", "INVOCATION_LOG.json", log_entry)

    def load_invocation_log(self) -> List[Dict]:
        """Load invocation log."""
        return self.load("logs", "INVOCATION_LOG.json") or []

    def append_violation_log(self, violation: Dict) -> None:
        """Append to violation log."""
        self.append("logs", "VIOLATION_LOG.json", violation)

    def load_violation_log(self) -> List[Dict]:
        """Load violation log."""
        return self.load("logs", "VIOLATION_LOG.json") or []

    def save_checkpoint_registry(self, checkpoints: List[Dict]) -> str:
        """Save checkpoint registry."""
        return self.save("checkpoints", "CHECKPOINT_REGISTRY.json", {
            "checkpoints": checkpoints,
            "saved_at": datetime.now().isoformat(),
            "count": len(checkpoints),
        })

    def load_checkpoint_registry(self) -> List[Dict]:
        """Load checkpoint registry."""
        data = self.load("checkpoints", "CHECKPOINT_REGISTRY.json")
        return data.get("checkpoints", []) if data else []

    def get_archive_stats(self) -> Dict[str, Any]:
        """Get statistics about the archive."""
        stats = {
            "archive_dir": str(self.archive_dir),
            "exists": self.archive_dir.exists(),
            "files": {},
        }

        for category in ["patches", "fusions", "canon", "queue", "logs", "checkpoints"]:
            category_path = self.archive_dir / category
            if category_path.exists():
                files = list(category_path.glob("*.json"))
                stats["files"][category] = {
                    "count": len(files),
                    "files": [f.name for f in files],
                }

        return stats

    def clear_all(self, confirm: bool = False) -> bool:
        """
        Clear all archive data.

        Args:
            confirm: Must be True to execute

        Returns:
            True if cleared
        """
        if not confirm:
            return False

        import shutil
        if self.archive_dir.exists():
            shutil.rmtree(self.archive_dir)
        self._init_directories()
        return True


# Global archive manager instance
_archive_manager: Optional[ArchiveManager] = None


def get_archive_manager(archive_dir: Optional[str] = None) -> ArchiveManager:
    """Get or create global archive manager instance."""
    global _archive_manager
    if _archive_manager is None or archive_dir is not None:
        _archive_manager = ArchiveManager(archive_dir)
    return _archive_manager
