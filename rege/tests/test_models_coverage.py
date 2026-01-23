"""
Tests for models module coverage improvements (85% → 95%).

Targets:
- Fragment dataclass edge cases
- Patch dataclass comparison and serialization
- Invocation dataclass serialization
- FusedFragment dataclass
- CanonEvent dataclass
- StateSnapshot dataclass
"""

import pytest
from datetime import datetime, timedelta
import uuid

from rege.core.models import (
    Fragment,
    Patch,
    Invocation,
    FusedFragment,
    CanonEvent,
    StateSnapshot,
    InvocationResult,
    LawProposal,
    DepthLevel,
    FusionType,
    FusionMode,
    ChargeCalculation,
    RecoveryTrigger,
    RecoveryMode,
    FragmentStatus,
    PatchStatus,
)


class TestFragmentDataclass:
    """Tests for Fragment dataclass edge cases."""

    def test_post_init_empty_id_generates_uuid(self):
        """Test __post_init__ with empty ID generates UUID."""
        fragment = Fragment(
            id="",
            name="Test Fragment",
            charge=50,
            tags=["CANON+"],
        )
        assert fragment.id.startswith("FRAG_")
        assert len(fragment.id) == 13  # FRAG_ + 8 hex chars

    def test_post_init_provided_id_preserved(self):
        """Test __post_init__ with provided ID preserves it."""
        fragment = Fragment(
            id="CUSTOM_ID_001",
            name="Custom Fragment",
            charge=60,
            tags=[],
        )
        assert fragment.id == "CUSTOM_ID_001"

    def test_from_dict_missing_optional_fields(self):
        """Test from_dict with missing optional fields."""
        data = {
            "id": "FRAG_001",
            "name": "Minimal Fragment",
            "charge": 50,
            "tags": ["ECHO+"],
        }
        fragment = Fragment.from_dict(data)

        assert fragment.id == "FRAG_001"
        assert fragment.version == "1.0"  # Default
        assert fragment.status == "active"  # Default
        assert fragment.fused_into is None
        assert fragment.metadata == {}

    def test_from_dict_with_datetime_strings(self):
        """Test from_dict parses datetime strings correctly."""
        now = datetime.now()
        data = {
            "id": "FRAG_002",
            "name": "Dated Fragment",
            "charge": 70,
            "tags": [],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        fragment = Fragment.from_dict(data)

        assert fragment.created_at.date() == now.date()
        assert fragment.updated_at.date() == now.date()

    def test_from_dict_missing_datetime_uses_now(self):
        """Test from_dict uses datetime.now() when missing datetimes."""
        data = {
            "id": "FRAG_003",
            "name": "No Dates Fragment",
            "charge": 40,
            "tags": [],
        }
        before = datetime.now()
        fragment = Fragment.from_dict(data)
        after = datetime.now()

        assert before <= fragment.created_at <= after
        assert before <= fragment.updated_at <= after

    def test_to_dict_round_trip(self):
        """Test to_dict and from_dict round-trip serialization."""
        original = Fragment(
            id="FRAG_ROUND",
            name="Round Trip",
            charge=75,
            tags=["CANON+", "MIRROR+"],
            version="2.0",
            status="active",
            fused_into=None,
            metadata={"key": "value", "number": 42},
        )

        serialized = original.to_dict()
        restored = Fragment.from_dict(serialized)

        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.charge == original.charge
        assert restored.tags == original.tags
        assert restored.version == original.version
        assert restored.metadata == original.metadata

    def test_metadata_with_complex_nested_objects(self):
        """Test metadata with complex nested objects."""
        fragment = Fragment(
            id="",
            name="Complex Metadata",
            charge=50,
            tags=[],
            metadata={
                "nested": {"deep": {"value": 123}},
                "list": [1, 2, {"inner": "data"}],
                "mixed": {"array": [1, 2, 3], "string": "test"},
            },
        )

        assert fragment.metadata["nested"]["deep"]["value"] == 123
        assert fragment.metadata["list"][2]["inner"] == "data"


class TestPatchDataclass:
    """Tests for Patch dataclass edge cases."""

    def test_lt_comparison_different_priorities(self):
        """Test __lt__ comparison with different priorities."""
        high_priority = Patch(
            input_node="A",
            output_node="B",
            tags=["EMERGENCY+"],
            charge=90,
        )
        low_priority = Patch(
            input_node="C",
            output_node="D",
            tags=[],
            charge=30,
        )

        # Lower priority value = higher priority (for heap)
        assert high_priority < low_priority

    def test_lt_comparison_equal_priorities_different_timestamps(self):
        """Test __lt__ comparison with equal priorities, different timestamps."""
        patch1 = Patch(
            input_node="A",
            output_node="B",
            tags=[],
            charge=60,
        )
        # Manually set earlier timestamp
        patch1.enqueued_at = datetime(2025, 1, 1, 12, 0, 0)

        patch2 = Patch(
            input_node="C",
            output_node="D",
            tags=[],
            charge=60,
        )
        patch2.enqueued_at = datetime(2025, 1, 1, 12, 0, 1)

        # Equal priority, earlier timestamp wins
        assert patch1 < patch2

    def test_lt_comparison_equal_priority_and_timestamp(self):
        """Test __lt__ comparison with equal priorities AND timestamps."""
        fixed_time = datetime(2025, 1, 1, 12, 0, 0)

        patch1 = Patch(
            input_node="A",
            output_node="B",
            tags=[],
            charge=60,
        )
        patch1.enqueued_at = fixed_time

        patch2 = Patch(
            input_node="C",
            output_node="D",
            tags=[],
            charge=60,
        )
        patch2.enqueued_at = fixed_time

        # With identical times, comparison is False (not strictly less than)
        assert not (patch1 < patch2)
        assert not (patch2 < patch1)

    def test_post_init_priority_calculation(self):
        """Test __post_init__ priority calculation from charge and tags."""
        from rege.core.constants import Priority

        # CRITICAL tier
        critical_patch = Patch(input_node="A", output_node="B", tags=[], charge=90)
        assert critical_patch.priority == Priority.CRITICAL

        # HIGH tier (INTENSE)
        high_patch = Patch(input_node="A", output_node="B", tags=[], charge=75)
        assert high_patch.priority == Priority.HIGH

        # STANDARD tier (ACTIVE)
        standard_patch = Patch(input_node="A", output_node="B", tags=[], charge=60)
        assert standard_patch.priority == Priority.STANDARD

        # BACKGROUND tier
        background_patch = Patch(input_node="A", output_node="B", tags=[], charge=30)
        assert background_patch.priority == Priority.BACKGROUND

    def test_from_dict_with_invalid_status(self):
        """Test from_dict with various status values."""
        data = {
            "input_node": "A",
            "output_node": "B",
            "tags": [],
            "charge": 50,
            "status": "completed",  # Valid status
        }
        patch = Patch.from_dict(data)
        assert patch.status == "completed"

    def test_from_dict_missing_priority_recalculation(self):
        """Test from_dict without priority triggers recalculation."""
        data = {
            "input_node": "A",
            "output_node": "B",
            "tags": ["EMERGENCY+"],
            "charge": 90,
        }
        patch = Patch.from_dict(data)
        # Priority should be calculated in __post_init__
        from rege.core.constants import Priority
        assert patch.priority == Priority.CRITICAL

    def test_comparison_for_heap_ordering(self):
        """Test comparison works correctly for heap ordering."""
        patches = [
            Patch(input_node="A", output_node="B", tags=[], charge=30),
            Patch(input_node="C", output_node="D", tags=["EMERGENCY+"], charge=95),
            Patch(input_node="E", output_node="F", tags=[], charge=60),
            Patch(input_node="G", output_node="H", tags=[], charge=75),
        ]

        sorted_patches = sorted(patches)

        # Should be sorted by priority (lower value first)
        assert sorted_patches[0].charge == 95  # CRITICAL
        assert sorted_patches[1].charge == 75  # HIGH
        assert sorted_patches[2].charge == 60  # STANDARD
        assert sorted_patches[3].charge == 30  # BACKGROUND

    def test_activate_method(self):
        """Test activate() method updates status and returns message."""
        patch = Patch(input_node="SOURCE", output_node="DEST", tags=["CANON+"], charge=70)

        message = patch.activate()

        assert patch.status == "active"
        assert "SOURCE" in message
        assert "DEST" in message
        assert "CANON+" in message

    def test_complete_method(self):
        """Test complete() method updates status and timestamp."""
        patch = Patch(input_node="A", output_node="B", tags=[], charge=50)
        assert patch.processed_at is None

        patch.complete()

        assert patch.status == "completed"
        assert patch.processed_at is not None

    def test_fail_method(self):
        """Test fail() method updates status and records reason."""
        patch = Patch(input_node="A", output_node="B", tags=[], charge=50)

        patch.fail("Connection timeout")

        assert patch.status == "failed"
        assert patch.metadata["failure_reason"] == "Connection timeout"
        assert patch.processed_at is not None


class TestInvocationDataclass:
    """Tests for Invocation dataclass edge cases."""

    def test_from_dict_with_light_depth(self):
        """Test from_dict with 'light' depth level."""
        data = {
            "organ": "MIRROR_CABINET",
            "symbol": "test",
            "mode": "emotional_reflection",
            "depth": "light",
            "expect": "fragment_map",
        }
        invocation = Invocation.from_dict(data)
        assert invocation.depth == DepthLevel.LIGHT

    def test_from_dict_with_full_spiral_depth(self):
        """Test from_dict with 'full spiral' depth level."""
        data = {
            "organ": "ECHO_SHELL",
            "symbol": "recursive test",
            "mode": "recursive",
            "depth": "full spiral",
            "expect": "echo_log",
        }
        invocation = Invocation.from_dict(data)
        assert invocation.depth == DepthLevel.FULL_SPIRAL

    def test_from_dict_missing_depth_defaults_standard(self):
        """Test from_dict with missing depth defaults to STANDARD."""
        data = {
            "organ": "HEART_OF_CANON",
            "symbol": "test",
            "mode": "mythic",
            "expect": "pulse_check",
        }
        invocation = Invocation.from_dict(data)
        assert invocation.depth == DepthLevel.STANDARD

    def test_to_dict_with_all_depth_levels(self):
        """Test to_dict with all DepthLevel enum values."""
        for depth in DepthLevel:
            invocation = Invocation(
                organ="TEST",
                symbol="test",
                mode="default",
                depth=depth,
                expect="output",
            )
            data = invocation.to_dict()
            assert data["depth"] == depth.value

    def test_invocation_id_auto_generation(self):
        """Test invocation_id auto-generation in __post_init__."""
        invocation = Invocation(
            organ="BLOOM_ENGINE",
            symbol="growth test",
            mode="growth",
            depth=DepthLevel.STANDARD,
            expect="mutated_fragment",
        )
        assert invocation.invocation_id.startswith("INV_")
        assert len(invocation.invocation_id) == 12  # INV_ + 8 hex chars

    def test_invocation_id_preserved_if_provided(self):
        """Test invocation_id preserved if provided."""
        invocation = Invocation(
            organ="BLOOM_ENGINE",
            symbol="test",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="output",
            invocation_id="CUSTOM_INV_001",
        )
        assert invocation.invocation_id == "CUSTOM_INV_001"

    def test_flags_list_serialization(self):
        """Test flags list serialization."""
        invocation = Invocation(
            organ="RITUAL_COURT",
            symbol="contradiction test",
            mode="ruling",
            depth=DepthLevel.FULL_SPIRAL,
            expect="verdict",
            flags=["CANON+", "ECHO+", "MIRROR+"],
        )
        data = invocation.to_dict()
        assert data["flags"] == ["CANON+", "ECHO+", "MIRROR+"]


class TestFusedFragmentDataclass:
    """Tests for FusedFragment dataclass edge cases."""

    def test_to_dict_with_source_fragments(self):
        """Test to_dict with source fragments."""
        frag1 = Fragment(id="FRAG_001", name="Source 1", charge=70, tags=["CHAR+"])
        frag2 = Fragment(id="FRAG_002", name="Source 2", charge=80, tags=["SHDW+"])

        fused = FusedFragment(
            fused_id="FUSED_001",
            source_fragments=[frag1, frag2],
            fusion_type=FusionType.CHARACTER_EMOTION_BLEND,
            charge=80,
            output_route="ARCHIVE_ORDER",
            timestamp=datetime.now(),
            tags=["FUSE+"],
        )

        data = fused.to_dict()
        assert len(data["source_fragments"]) == 2
        assert data["source_fragments"][0]["id"] == "FRAG_001"
        assert data["source_fragments"][0]["charge_at_fusion"] == 70
        assert data["fusion_type"] == "character_emotion_blend"

    def test_to_dict_with_empty_source_fragments(self):
        """Test to_dict with empty source_fragments list."""
        fused = FusedFragment(
            fused_id="FUSED_EMPTY",
            source_fragments=[],
            fusion_type=FusionType.VERSION_MERGE,
            charge=50,
            output_route="BLOOM_ENGINE",
            timestamp=datetime.now(),
            tags=["FUSE+"],
        )

        data = fused.to_dict()
        assert data["source_fragments"] == []

    def test_rollback_deadline_default(self):
        """Test rollback_deadline default is 7 days in future."""
        before = datetime.now()
        fused = FusedFragment(
            fused_id="FUSED_DEADLINE",
            source_fragments=[],
            fusion_type=FusionType.MEMORY_CONSOLIDATION,
            charge=60,
            output_route="ARCHIVE_ORDER",
            timestamp=datetime.now(),
            tags=["FUSE+"],
        )
        after = datetime.now()

        # Deadline should be approximately 7 days from now
        assert fused.rollback_deadline > before + timedelta(days=6)
        assert fused.rollback_deadline < after + timedelta(days=8)

    def test_charge_calculation_methods(self):
        """Test different charge calculation methods."""
        fused_max = FusedFragment(
            fused_id="FUSED_MAX",
            source_fragments=[],
            fusion_type=FusionType.CHARACTER_EMOTION_BLEND,
            charge=80,
            output_route="ARCHIVE_ORDER",
            timestamp=datetime.now(),
            tags=["FUSE+"],
            charge_calculation=ChargeCalculation.INHERITED_MAX,
        )
        assert fused_max.charge_calculation == ChargeCalculation.INHERITED_MAX

        fused_avg = FusedFragment(
            fused_id="FUSED_AVG",
            source_fragments=[],
            fusion_type=FusionType.MEMORY_CONSOLIDATION,
            charge=65,
            output_route="ARCHIVE_ORDER",
            timestamp=datetime.now(),
            tags=["FUSE+"],
            charge_calculation=ChargeCalculation.AVERAGED,
        )
        assert fused_avg.charge_calculation == ChargeCalculation.AVERAGED


class TestCanonEventDataclass:
    """Tests for CanonEvent dataclass edge cases."""

    def test_post_init_empty_event_id_generates(self):
        """Test __post_init__ with empty event_id generates UUID."""
        event = CanonEvent(
            event_id="",
            content="Test event",
            charge=75,
            status="glowing",
            linked_nodes=["NODE_001"],
        )
        assert event.event_id.startswith("CANON_")
        assert len(event.event_id) == 14  # CANON_ + 8 hex chars

    def test_post_init_provided_event_id_preserved(self):
        """Test __post_init__ with provided event_id preserves it."""
        event = CanonEvent(
            event_id="CUSTOM_EVENT",
            content="Custom event",
            charge=80,
            status="emergent_canon",
            linked_nodes=[],
        )
        assert event.event_id == "CUSTOM_EVENT"

    def test_to_dict_with_canonized_at_none(self):
        """Test to_dict with canonized_at None."""
        event = CanonEvent(
            event_id="EVT_001",
            content="Not yet canonized",
            charge=70,
            status="canon_candidate",
            linked_nodes=["NODE_A", "NODE_B"],
            canonized_at=None,
        )
        data = event.to_dict()
        assert data["canonized_at"] is None

    def test_to_dict_with_canonized_at_set(self):
        """Test to_dict with canonized_at set."""
        now = datetime.now()
        event = CanonEvent(
            event_id="EVT_002",
            content="Canonized event",
            charge=85,
            status="canonized",
            linked_nodes=["NODE_X"],
            canonized_at=now,
        )
        data = event.to_dict()
        assert data["canonized_at"] == now.isoformat()

    def test_linked_nodes_serialization(self):
        """Test linked_nodes serialization."""
        event = CanonEvent(
            event_id="",
            content="Multi-linked event",
            charge=75,
            status="glowing",
            linked_nodes=["NODE_1", "NODE_2", "NODE_3", "NODE_4"],
        )
        data = event.to_dict()
        assert data["linked_nodes"] == ["NODE_1", "NODE_2", "NODE_3", "NODE_4"]


class TestStateSnapshotDataclass:
    """Tests for StateSnapshot dataclass edge cases."""

    def test_from_dict_with_valid_recovery_trigger(self):
        """Test from_dict with valid RecoveryTrigger value."""
        data = {
            "snapshot_id": "SNAP_001",
            "timestamp": datetime.now().isoformat(),
            "trigger": "corruption",
            "system_state": {"key": "value"},
            "organ_states": {"HEART_OF_CANON": "active"},
            "pending_operations": [],
            "error_log": [],
        }
        snapshot = StateSnapshot.from_dict(data)
        assert snapshot.trigger == RecoveryTrigger.CORRUPTION

    def test_from_dict_all_recovery_triggers(self):
        """Test from_dict with all RecoveryTrigger values."""
        for trigger in RecoveryTrigger:
            data = {
                "snapshot_id": f"SNAP_{trigger.value}",
                "timestamp": datetime.now().isoformat(),
                "trigger": trigger.value,
                "system_state": {},
                "organ_states": {},
                "pending_operations": [],
                "error_log": [],
            }
            snapshot = StateSnapshot.from_dict(data)
            assert snapshot.trigger == trigger

    def test_from_dict_missing_optional_fields(self):
        """Test from_dict with missing optional fields."""
        data = {
            "snapshot_id": "SNAP_MIN",
            "timestamp": datetime.now().isoformat(),
            "trigger": "manual",
            "system_state": {},
            "organ_states": {},
            "pending_operations": [],
            "error_log": [],
        }
        snapshot = StateSnapshot.from_dict(data)
        assert snapshot.recovery_point is None

    def test_snapshot_id_auto_generation(self):
        """Test snapshot_id auto-generation from timestamp."""
        timestamp = datetime(2025, 1, 22, 14, 30, 45)
        snapshot = StateSnapshot(
            snapshot_id="",
            timestamp=timestamp,
            trigger=RecoveryTrigger.MANUAL,
            system_state={},
            organ_states={},
            pending_operations=[],
            error_log=[],
        )
        # Should generate from timestamp
        assert snapshot.snapshot_id == "SNAP_20250122_143045"

    def test_organ_states_serialization(self):
        """Test organ_states serialization."""
        snapshot = StateSnapshot(
            snapshot_id="",
            timestamp=datetime.now(),
            trigger=RecoveryTrigger.DEADLOCK,
            system_state={"queue_size": 50},
            organ_states={
                "HEART_OF_CANON": "active",
                "MIRROR_CABINET": "halted",
                "BLOOM_ENGINE": "processing",
            },
            pending_operations=[{"op": "patch", "id": "P001"}],
            error_log=["Error 1", "Error 2"],
        )
        data = snapshot.to_dict()
        assert len(data["organ_states"]) == 3
        assert data["organ_states"]["MIRROR_CABINET"] == "halted"


class TestInvocationResultDataclass:
    """Tests for InvocationResult dataclass."""

    def test_to_dict_with_dict_output(self):
        """Test to_dict with dict output."""
        result = InvocationResult(
            invocation_id="INV_001",
            organ="HEART_OF_CANON",
            status="success",
            output={"event": "created", "charge": 75},
            output_type="dict",
            execution_time_ms=150,
        )
        data = result.to_dict()
        assert data["output"] == {"event": "created", "charge": 75}

    def test_to_dict_with_non_serializable_output(self):
        """Test to_dict with non-serializable output converts to string."""
        class CustomObject:
            def __str__(self):
                return "CustomObject(test)"

        result = InvocationResult(
            invocation_id="INV_002",
            organ="BLOOM_ENGINE",
            status="success",
            output=CustomObject(),
            output_type="custom",
            execution_time_ms=100,
        )
        data = result.to_dict()
        assert data["output"] == "CustomObject(test)"

    def test_to_dict_with_errors_and_side_effects(self):
        """Test to_dict includes errors and side_effects."""
        result = InvocationResult(
            invocation_id="INV_003",
            organ="RITUAL_COURT",
            status="partial",
            output={"verdict": "deferred"},
            output_type="dict",
            execution_time_ms=200,
            errors=["Warning: low charge", "Notice: pending review"],
            side_effects=[
                {"type": "patch_created", "id": "PATCH_001"},
                {"type": "log_entry", "message": "Court convened"},
            ],
        )
        data = result.to_dict()
        assert len(data["errors"]) == 2
        assert len(data["side_effects"]) == 2


class TestLawProposalDataclass:
    """Tests for LawProposal dataclass."""

    def test_to_dict_complete(self):
        """Test to_dict with complete LawProposal."""
        now = datetime.now()
        enacted = now + timedelta(days=1)

        proposal = LawProposal(
            law_id="LAW_99",
            name="Test Law",
            description="A law for testing",
            proposed_by="MYTHIC_SENATE",
            charge=75,
            vote_status="approved",
            votes_for=10,
            votes_against=2,
            enacted_at=enacted,
            tags=["FOUNDATIONAL+", "SYSTEM+"],
        )
        data = proposal.to_dict()

        assert data["law_id"] == "LAW_99"
        assert data["vote_status"] == "approved"
        assert data["votes_for"] == 10
        assert data["enacted_at"] == enacted.isoformat()

    def test_to_dict_with_enacted_at_none(self):
        """Test to_dict with enacted_at None (pending law)."""
        proposal = LawProposal(
            law_id="LAW_100",
            name="Pending Law",
            description="Not yet enacted",
            proposed_by="HEART_OF_CANON",
            charge=60,
        )
        data = proposal.to_dict()
        assert data["enacted_at"] is None


class TestEnumerations:
    """Tests for enumeration values and behaviors."""

    def test_depth_level_values(self):
        """Test DepthLevel enum values."""
        assert DepthLevel.LIGHT.value == "light"
        assert DepthLevel.STANDARD.value == "standard"
        assert DepthLevel.FULL_SPIRAL.value == "full spiral"

    def test_fusion_mode_values(self):
        """Test FusionMode enum values."""
        assert FusionMode.AUTO.value == "auto"
        assert FusionMode.INVOKED.value == "invoked"
        assert FusionMode.FORCED.value == "forced"

    def test_fusion_type_values(self):
        """Test FusionType enum values."""
        assert FusionType.CHARACTER_EMOTION_BLEND.value == "character_emotion_blend"
        assert FusionType.MEMORY_CONSOLIDATION.value == "memory_consolidation"
        assert FusionType.VERSION_MERGE.value == "version_merge"

    def test_recovery_mode_values(self):
        """Test RecoveryMode enum values."""
        assert RecoveryMode.FULL_ROLLBACK.value == "full_rollback"
        assert RecoveryMode.PARTIAL.value == "partial"
        assert RecoveryMode.RECONSTRUCT.value == "reconstruct"
        assert RecoveryMode.EMERGENCY_STOP.value == "emergency_stop"

    def test_recovery_trigger_values(self):
        """Test RecoveryTrigger enum values."""
        assert RecoveryTrigger.CORRUPTION.value == "corruption"
        assert RecoveryTrigger.DEADLOCK.value == "deadlock"
        assert RecoveryTrigger.DATA_LOSS.value == "data_loss"
        assert RecoveryTrigger.DEPTH_PANIC.value == "depth_panic"
        assert RecoveryTrigger.MANUAL.value == "manual"

    def test_fragment_status_values(self):
        """Test FragmentStatus enum values."""
        assert FragmentStatus.ACTIVE.value == "active"
        assert FragmentStatus.FUSED.value == "fused"
        assert FragmentStatus.ARCHIVED.value == "archived"
        assert FragmentStatus.DECAYED.value == "decayed"
        assert FragmentStatus.PENDING.value == "pending"

    def test_patch_status_values(self):
        """Test PatchStatus enum values."""
        assert PatchStatus.PENDING.value == "pending"
        assert PatchStatus.ACTIVE.value == "active"
        assert PatchStatus.COMPLETED.value == "completed"
        assert PatchStatus.FAILED.value == "failed"
        assert PatchStatus.ESCALATED.value == "escalated"

    def test_charge_calculation_values(self):
        """Test ChargeCalculation enum values."""
        assert ChargeCalculation.INHERITED_MAX.value == "inherited_max"
        assert ChargeCalculation.AVERAGED.value == "averaged"
        assert ChargeCalculation.SUMMED_CAPPED.value == "summed_capped"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
