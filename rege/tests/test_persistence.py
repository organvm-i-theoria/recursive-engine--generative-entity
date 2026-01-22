"""
Tests for persistence module: ArchiveManager, CheckpointManager, and schemas.
"""

import pytest
import json
from datetime import datetime
from pathlib import Path

from rege.persistence.archive import ArchiveManager, get_archive_manager
from rege.persistence.checkpoint import CheckpointManager
from rege.persistence.schemas import validate_data, get_schema, SCHEMAS
from rege.core.models import RecoveryTrigger
from rege.core.exceptions import ArchiveCorrupted, PersistenceError


class TestArchiveManager:
    """Tests for ArchiveManager."""

    def test_init_creates_directories(self, tmp_path):
        """Test that initialization creates directory hierarchy."""
        archive_dir = tmp_path / "test_archive"
        manager = ArchiveManager(str(archive_dir))

        assert archive_dir.exists()
        assert (archive_dir / "patches").exists()
        assert (archive_dir / "fusions").exists()
        assert (archive_dir / "canon").exists()
        assert (archive_dir / "queue").exists()
        assert (archive_dir / "logs").exists()
        assert (archive_dir / "checkpoints").exists()

    def test_save_and_load_json(self, tmp_path):
        """Test basic roundtrip save and load."""
        manager = ArchiveManager(str(tmp_path / "archive"))
        test_data = {"key": "value", "number": 42, "list": [1, 2, 3]}

        manager.save("patches", "test.json", test_data)
        loaded = manager.load("patches", "test.json")

        assert loaded == test_data

    def test_load_missing_file_returns_none(self, tmp_path):
        """Test that loading a missing file returns None."""
        manager = ArchiveManager(str(tmp_path / "archive"))

        result = manager.load("patches", "nonexistent.json")

        assert result is None

    def test_append_to_empty_file(self, tmp_path):
        """Test appending to a file that doesn't exist creates an array."""
        manager = ArchiveManager(str(tmp_path / "archive"))
        entry = {"id": "1", "data": "test"}

        manager.append("logs", "test_log.json", entry)
        loaded = manager.load("logs", "test_log.json")

        assert loaded == [entry]

    def test_append_to_existing_array(self, tmp_path):
        """Test appending to an existing array extends it."""
        manager = ArchiveManager(str(tmp_path / "archive"))
        entry1 = {"id": "1", "data": "first"}
        entry2 = {"id": "2", "data": "second"}

        manager.append("logs", "test_log.json", entry1)
        manager.append("logs", "test_log.json", entry2)
        loaded = manager.load("logs", "test_log.json")

        assert len(loaded) == 2
        assert loaded[0] == entry1
        assert loaded[1] == entry2

    def test_save_with_datetime_objects(self, tmp_path):
        """Test that datetime objects are serialized via default=str."""
        manager = ArchiveManager(str(tmp_path / "archive"))
        test_data = {"timestamp": datetime.now(), "name": "test"}

        path = manager.save("patches", "datetime_test.json", test_data)
        loaded = manager.load("patches", "datetime_test.json")

        assert "timestamp" in loaded
        assert isinstance(loaded["timestamp"], str)

    def test_exists_returns_correct_boolean(self, tmp_path):
        """Test file existence check."""
        manager = ArchiveManager(str(tmp_path / "archive"))

        assert not manager.exists("patches", "test.json")

        manager.save("patches", "test.json", {"test": True})

        assert manager.exists("patches", "test.json")

    def test_get_archive_stats(self, tmp_path):
        """Test archive statistics introspection."""
        manager = ArchiveManager(str(tmp_path / "archive"))
        manager.save("patches", "test1.json", {"data": 1})
        manager.save("patches", "test2.json", {"data": 2})

        stats = manager.get_archive_stats()

        assert stats["exists"]
        assert "patches" in stats["files"]
        assert stats["files"]["patches"]["count"] == 2

    def test_clear_all_requires_confirmation(self, tmp_path):
        """Test that clear_all requires confirm=True."""
        manager = ArchiveManager(str(tmp_path / "archive"))
        manager.save("patches", "test.json", {"data": 1})

        result = manager.clear_all(confirm=False)

        assert result is False
        assert manager.exists("patches", "test.json")

    def test_clear_all_with_confirmation(self, tmp_path):
        """Test that clear_all with confirm=True clears everything."""
        manager = ArchiveManager(str(tmp_path / "archive"))
        manager.save("patches", "test.json", {"data": 1})

        result = manager.clear_all(confirm=True)

        assert result is True
        assert not manager.exists("patches", "test.json")

    def test_save_patch_records(self, tmp_path):
        """Test saving patch records."""
        manager = ArchiveManager(str(tmp_path / "archive"))
        patches = [
            {"patch_id": "PATCH_001", "status": "completed"},
            {"patch_id": "PATCH_002", "status": "pending"},
        ]

        path = manager.save_patch_records(patches)
        loaded = manager.load_patch_records()

        assert len(loaded) == 2
        assert loaded[0]["patch_id"] == "PATCH_001"

    def test_load_patch_records_empty(self, tmp_path):
        """Test loading patch records when file doesn't exist."""
        manager = ArchiveManager(str(tmp_path / "archive"))

        loaded = manager.load_patch_records()

        assert loaded == []

    def test_save_fusion_registry(self, tmp_path):
        """Test saving fusion registry."""
        manager = ArchiveManager(str(tmp_path / "archive"))
        fusions = [{"fused_id": "FUSED_001", "type": "blend"}]

        manager.save_fusion_registry(fusions)
        loaded = manager.load_fusion_registry()

        assert len(loaded) == 1
        assert loaded[0]["fused_id"] == "FUSED_001"

    def test_save_canon_events(self, tmp_path):
        """Test saving canon events."""
        manager = ArchiveManager(str(tmp_path / "archive"))
        events = [{"event_id": "CANON_001", "content": "test event"}]

        manager.save_canon_events(events)
        loaded = manager.load_canon_events()

        assert len(loaded) == 1
        assert loaded[0]["event_id"] == "CANON_001"

    def test_save_and_load_queue_state(self, tmp_path):
        """Test saving and loading queue state."""
        manager = ArchiveManager(str(tmp_path / "archive"))
        state = {"total_size": 10, "max_size": 100}

        manager.save_queue_state(state)
        loaded = manager.load_queue_state()

        assert loaded["total_size"] == 10
        assert "captured_at" in loaded

    def test_append_invocation_log(self, tmp_path):
        """Test appending to invocation log."""
        manager = ArchiveManager(str(tmp_path / "archive"))
        entry1 = {"invocation_id": "INV_001", "organ": "HEART_OF_CANON"}
        entry2 = {"invocation_id": "INV_002", "organ": "MIRROR_CABINET"}

        manager.append_invocation_log(entry1)
        manager.append_invocation_log(entry2)
        loaded = manager.load_invocation_log()

        assert len(loaded) == 2

    def test_append_violation_log(self, tmp_path):
        """Test appending to violation log."""
        manager = ArchiveManager(str(tmp_path / "archive"))
        violation = {"action": "test", "violations": ["rule1"]}

        manager.append_violation_log(violation)
        loaded = manager.load_violation_log()

        assert len(loaded) == 1

    def test_save_checkpoint_registry(self, tmp_path):
        """Test saving checkpoint registry."""
        manager = ArchiveManager(str(tmp_path / "archive"))
        checkpoints = [{"snapshot_id": "SNAP_001", "name": "test"}]

        manager.save_checkpoint_registry(checkpoints)
        loaded = manager.load_checkpoint_registry()

        assert len(loaded) == 1

    def test_load_corrupted_json_raises_archive_corrupted(self, tmp_path):
        """Test that loading corrupted JSON raises ArchiveCorrupted."""
        manager = ArchiveManager(str(tmp_path / "archive"))
        file_path = tmp_path / "archive" / "patches" / "corrupted.json"
        file_path.write_text("{ invalid json")

        with pytest.raises(ArchiveCorrupted):
            manager.load("patches", "corrupted.json")


class TestCheckpointManager:
    """Tests for CheckpointManager."""

    def test_create_checkpoint_saves_snapshot(self, tmp_path):
        """Test that creating a checkpoint saves a snapshot file."""
        archive = ArchiveManager(str(tmp_path / "archive"))
        manager = CheckpointManager(archive)
        system_state = {
            "metrics": {"total_size": 10},
            "organs": {"HEART_OF_CANON": "active"},
            "pending": [],
            "errors": [],
        }

        snapshot = manager.create_checkpoint("test_checkpoint", system_state)

        assert snapshot.snapshot_id.startswith("SNAP_")
        snapshot_path = manager._snapshots_dir / f"{snapshot.snapshot_id}.json"
        assert snapshot_path.exists()

    def test_create_checkpoint_updates_registry(self, tmp_path):
        """Test that creating a checkpoint updates the registry."""
        archive = ArchiveManager(str(tmp_path / "archive"))
        manager = CheckpointManager(archive)
        system_state = {"metrics": {}, "organs": {}, "pending": [], "errors": []}

        manager.create_checkpoint("test", system_state)
        registry = manager.list_checkpoints()

        assert len(registry) == 1
        assert registry[0]["name"] == "test"

    def test_load_checkpoint_deserializes(self, tmp_path):
        """Test loading a checkpoint deserializes correctly."""
        archive = ArchiveManager(str(tmp_path / "archive"))
        manager = CheckpointManager(archive)
        system_state = {
            "metrics": {"test_metric": 42},
            "organs": {"TEST_ORGAN": "active"},
            "pending": [],
            "errors": [],
        }

        created = manager.create_checkpoint("roundtrip", system_state)
        loaded = manager.load_checkpoint(created.snapshot_id)

        assert loaded.snapshot_id == created.snapshot_id
        assert loaded.system_state.get("checkpoint_name") == "roundtrip"

    def test_load_checkpoint_not_found(self, tmp_path):
        """Test loading a non-existent checkpoint raises error."""
        from rege.core.exceptions import CheckpointNotFound

        archive = ArchiveManager(str(tmp_path / "archive"))
        manager = CheckpointManager(archive)

        with pytest.raises(CheckpointNotFound):
            manager.load_checkpoint("SNAP_NONEXISTENT")

    def test_list_checkpoints(self, tmp_path):
        """Test listing all checkpoints."""
        archive = ArchiveManager(str(tmp_path / "archive"))
        manager = CheckpointManager(archive)
        system_state = {"metrics": {}, "organs": {}, "pending": [], "errors": []}

        manager.create_checkpoint("first", system_state)
        manager.create_checkpoint("second", system_state)
        checkpoints = manager.list_checkpoints()

        assert len(checkpoints) == 2

    def test_get_latest_checkpoint(self, tmp_path):
        """Test getting the most recent checkpoint."""
        archive = ArchiveManager(str(tmp_path / "archive"))
        manager = CheckpointManager(archive)
        system_state = {"metrics": {}, "organs": {}, "pending": [], "errors": []}

        manager.create_checkpoint("first", system_state)
        manager.create_checkpoint("latest", system_state)
        latest = manager.get_latest_checkpoint()

        assert latest.system_state.get("checkpoint_name") == "latest"

    def test_get_latest_checkpoint_empty(self, tmp_path):
        """Test getting latest checkpoint when none exist."""
        archive = ArchiveManager(str(tmp_path / "archive"))
        manager = CheckpointManager(archive)

        result = manager.get_latest_checkpoint()

        assert result is None

    def test_get_checkpoint_by_name(self, tmp_path):
        """Test finding a checkpoint by name."""
        archive = ArchiveManager(str(tmp_path / "archive"))
        manager = CheckpointManager(archive)
        system_state = {"metrics": {}, "organs": {}, "pending": [], "errors": []}

        manager.create_checkpoint("findme", system_state)
        found = manager.get_checkpoint_by_name("findme")

        assert found is not None
        assert found.system_state.get("checkpoint_name") == "findme"

    def test_get_checkpoint_by_name_not_found(self, tmp_path):
        """Test finding a non-existent checkpoint by name."""
        archive = ArchiveManager(str(tmp_path / "archive"))
        manager = CheckpointManager(archive)

        result = manager.get_checkpoint_by_name("nonexistent")

        assert result is None

    def test_delete_checkpoint(self, tmp_path):
        """Test deleting a checkpoint removes file and registry entry."""
        archive = ArchiveManager(str(tmp_path / "archive"))
        manager = CheckpointManager(archive)
        system_state = {"metrics": {}, "organs": {}, "pending": [], "errors": []}

        snapshot = manager.create_checkpoint("deleteme", system_state)
        result = manager.delete_checkpoint(snapshot.snapshot_id)

        assert result is True
        assert len(manager.list_checkpoints()) == 0

    def test_delete_checkpoint_not_found(self, tmp_path):
        """Test deleting a non-existent checkpoint returns False."""
        archive = ArchiveManager(str(tmp_path / "archive"))
        manager = CheckpointManager(archive)

        result = manager.delete_checkpoint("SNAP_NONEXISTENT")

        assert result is False

    def test_prune_old_checkpoints(self, tmp_path):
        """Test pruning keeps only the most recent checkpoints."""
        import time
        archive = ArchiveManager(str(tmp_path / "archive"))
        manager = CheckpointManager(archive)
        system_state = {"metrics": {}, "organs": {}, "pending": [], "errors": []}

        # Create checkpoints with slight delay to ensure different timestamps
        for i in range(5):
            manager.create_checkpoint(f"checkpoint_{i}", system_state)
            time.sleep(0.01)  # Small delay for timestamp differentiation

        initial_count = len(manager.list_checkpoints())
        assert initial_count == 5

        deleted_count = manager.prune_old_checkpoints(keep_count=2)

        # Should delete some checkpoints and keep 2
        assert deleted_count >= 1
        assert len(manager.list_checkpoints()) <= 2

    def test_prune_old_checkpoints_nothing_to_delete(self, tmp_path):
        """Test pruning when count is below threshold."""
        archive = ArchiveManager(str(tmp_path / "archive"))
        manager = CheckpointManager(archive)
        system_state = {"metrics": {}, "organs": {}, "pending": [], "errors": []}

        manager.create_checkpoint("single", system_state)
        deleted_count = manager.prune_old_checkpoints(keep_count=5)

        assert deleted_count == 0

    def test_export_checkpoint(self, tmp_path):
        """Test exporting a checkpoint to dictionary."""
        archive = ArchiveManager(str(tmp_path / "archive"))
        manager = CheckpointManager(archive)
        system_state = {"metrics": {}, "organs": {}, "pending": [], "errors": []}

        snapshot = manager.create_checkpoint("export_test", system_state)
        exported = manager.export_checkpoint(snapshot.snapshot_id)

        assert "snapshot_id" in exported
        assert "timestamp" in exported

    def test_import_checkpoint(self, tmp_path):
        """Test importing a checkpoint from dictionary."""
        archive = ArchiveManager(str(tmp_path / "archive"))
        manager = CheckpointManager(archive)

        data = {
            "snapshot_id": "SNAP_IMPORTED",
            "timestamp": datetime.now().isoformat(),
            "trigger": "manual",
            "system_state": {"checkpoint_name": "imported"},
            "organ_states": {},
            "pending_operations": [],
            "error_log": [],
        }

        imported = manager.import_checkpoint(data)

        assert imported.snapshot_id == "SNAP_IMPORTED"
        loaded = manager.load_checkpoint("SNAP_IMPORTED")
        assert loaded is not None

    def test_create_checkpoint_with_trigger(self, tmp_path):
        """Test creating checkpoint with specific trigger."""
        archive = ArchiveManager(str(tmp_path / "archive"))
        manager = CheckpointManager(archive)
        system_state = {"metrics": {}, "organs": {}, "pending": [], "errors": []}

        snapshot = manager.create_checkpoint(
            "triggered",
            system_state,
            trigger=RecoveryTrigger.CORRUPTION
        )

        assert snapshot.trigger == RecoveryTrigger.CORRUPTION


class TestSchemas:
    """Tests for persistence schemas."""

    def test_validate_data_checks_required_fields(self):
        """Test that validation checks required fields."""
        valid_fragment = {
            "id": "FRAG_001",
            "name": "test",
            "charge": 50,
            "tags": ["TEST+"],
        }

        result = validate_data(valid_fragment, "fragment")

        assert result is True

    def test_validate_data_returns_false_for_missing_fields(self):
        """Test that validation returns False for missing required fields."""
        invalid_fragment = {
            "id": "FRAG_001",
            # missing: name, charge, tags
        }

        result = validate_data(invalid_fragment, "fragment")

        assert result is False

    def test_validate_data_unknown_schema(self):
        """Test that validation returns False for unknown schema."""
        result = validate_data({}, "unknown_schema")

        assert result is False

    def test_get_schema_returns_schema(self):
        """Test getting a schema by name."""
        schema = get_schema("fragment")

        assert "type" in schema
        assert "required" in schema
        assert "properties" in schema

    def test_get_schema_unknown(self):
        """Test getting unknown schema returns empty dict."""
        schema = get_schema("nonexistent")

        assert schema == {}

    def test_validate_patch_schema(self):
        """Test validating a patch."""
        valid_patch = {
            "patch_id": "PATCH_001",
            "input_node": "SELF",
            "output_node": "HEART_OF_CANON",
            "tags": ["TEST+"],
        }

        result = validate_data(valid_patch, "patch")

        assert result is True

    def test_validate_canon_event_schema(self):
        """Test validating a canon event."""
        valid_event = {
            "event_id": "CANON_001",
            "content": "test event",
            "charge": 75,
            "status": "canonized",
        }

        result = validate_data(valid_event, "canon_event")

        assert result is True

    def test_validate_state_snapshot_schema(self):
        """Test validating a state snapshot."""
        valid_snapshot = {
            "snapshot_id": "SNAP_001",
            "timestamp": datetime.now().isoformat(),
            "trigger": "manual",
        }

        result = validate_data(valid_snapshot, "state_snapshot")

        assert result is True

    def test_all_schemas_exist(self):
        """Test that all expected schemas are defined."""
        expected_schemas = [
            "fragment",
            "patch",
            "fused_fragment",
            "canon_event",
            "state_snapshot",
            "invocation_log",
            "violation_log",
            "queue_state",
        ]

        for schema_name in expected_schemas:
            assert schema_name in SCHEMAS, f"Missing schema: {schema_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
