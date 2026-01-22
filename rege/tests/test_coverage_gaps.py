"""
Tests for coverage gaps in core modules.

Targets:
- constants.py (62% → 85%)
- exceptions.py (57% → 80%)
- bloom_engine.py (57% → 80%)
"""

import pytest
from datetime import datetime


class TestConstants:
    """Tests for constants.py coverage gaps."""

    def test_get_tier_enum_latent(self):
        """Test get_tier_enum for LATENT tier."""
        from rege.core.constants import get_tier_enum, ChargeTier

        assert get_tier_enum(0) == ChargeTier.LATENT
        assert get_tier_enum(15) == ChargeTier.LATENT
        assert get_tier_enum(25) == ChargeTier.LATENT

    def test_get_tier_enum_processing(self):
        """Test get_tier_enum for PROCESSING tier."""
        from rege.core.constants import get_tier_enum, ChargeTier

        assert get_tier_enum(26) == ChargeTier.PROCESSING
        assert get_tier_enum(40) == ChargeTier.PROCESSING
        assert get_tier_enum(50) == ChargeTier.PROCESSING

    def test_get_tier_enum_active(self):
        """Test get_tier_enum for ACTIVE tier."""
        from rege.core.constants import get_tier_enum, ChargeTier

        assert get_tier_enum(51) == ChargeTier.ACTIVE
        assert get_tier_enum(60) == ChargeTier.ACTIVE
        assert get_tier_enum(70) == ChargeTier.ACTIVE

    def test_get_tier_enum_intense(self):
        """Test get_tier_enum for INTENSE tier."""
        from rege.core.constants import get_tier_enum, ChargeTier

        assert get_tier_enum(71) == ChargeTier.INTENSE
        assert get_tier_enum(80) == ChargeTier.INTENSE
        assert get_tier_enum(85) == ChargeTier.INTENSE

    def test_get_tier_enum_critical(self):
        """Test get_tier_enum for CRITICAL tier."""
        from rege.core.constants import get_tier_enum, ChargeTier

        assert get_tier_enum(86) == ChargeTier.CRITICAL
        assert get_tier_enum(95) == ChargeTier.CRITICAL
        assert get_tier_enum(100) == ChargeTier.CRITICAL

    def test_get_priority_with_law_loop_flag(self):
        """Test get_priority with LAW_LOOP+ flag."""
        from rege.core.constants import get_priority, Priority

        # LAW_LOOP+ flag elevates to HIGH priority
        assert get_priority(30, ["LAW_LOOP+"]) == Priority.HIGH
        assert get_priority(50, ["LAW_LOOP+"]) == Priority.HIGH

    def test_get_priority_with_emergency_flag(self):
        """Test get_priority with EMERGENCY+ flag."""
        from rege.core.constants import get_priority, Priority

        # EMERGENCY+ flag elevates to CRITICAL
        assert get_priority(30, ["EMERGENCY+"]) == Priority.CRITICAL
        assert get_priority(50, ["EMERGENCY+"]) == Priority.CRITICAL

    def test_get_priority_combined_flags(self):
        """Test get_priority with multiple flags."""
        from rege.core.constants import get_priority, Priority

        # EMERGENCY+ takes precedence
        assert get_priority(30, ["LAW_LOOP+", "EMERGENCY+"]) == Priority.CRITICAL

    def test_is_canonization_eligible_boundary(self):
        """Test is_canonization_eligible at boundary (71)."""
        from rege.core.constants import is_canonization_eligible

        assert not is_canonization_eligible(70)
        assert is_canonization_eligible(71)
        assert is_canonization_eligible(72)

    def test_is_critical_emergency_boundary(self):
        """Test is_critical_emergency at boundary (86)."""
        from rege.core.constants import is_critical_emergency

        assert not is_critical_emergency(85)
        assert is_critical_emergency(86)
        assert is_critical_emergency(87)

    def test_validate_charge_edge_cases(self):
        """Test validate_charge with edge cases."""
        from rege.core.constants import validate_charge

        # Valid boundaries
        assert validate_charge(0)
        assert validate_charge(100)
        assert validate_charge(50)

        # Invalid values
        assert not validate_charge(-1)
        assert not validate_charge(101)
        assert not validate_charge(-100)

    def test_get_tier_unknown(self):
        """Test get_tier returns UNKNOWN for out-of-range values."""
        from rege.core.constants import get_tier

        assert get_tier(-10) == "UNKNOWN"
        assert get_tier(150) == "UNKNOWN"

    def test_get_depth_limit_standard(self):
        """Test get_depth_limit returns standard limit."""
        from rege.core.constants import get_depth_limit, DepthLimits

        assert get_depth_limit([]) == DepthLimits.STANDARD
        assert get_depth_limit(["CANON+"]) == DepthLimits.STANDARD

    def test_get_depth_limit_extended(self):
        """Test get_depth_limit returns extended limit with LAW_LOOP+."""
        from rege.core.constants import get_depth_limit, DepthLimits

        assert get_depth_limit(["LAW_LOOP+"]) == DepthLimits.EXTENDED
        assert get_depth_limit(["CANON+", "LAW_LOOP+"]) == DepthLimits.EXTENDED

    def test_get_depth_limit_emergency(self):
        """Test get_depth_limit returns emergency limit with EMERGENCY+."""
        from rege.core.constants import get_depth_limit, DepthLimits

        assert get_depth_limit(["EMERGENCY+"]) == DepthLimits.EMERGENCY
        # EMERGENCY+ takes precedence over LAW_LOOP+
        assert get_depth_limit(["LAW_LOOP+", "EMERGENCY+"]) == DepthLimits.EMERGENCY

    def test_validate_tag(self):
        """Test validate_tag for valid and invalid tags."""
        from rege.core.constants import validate_tag

        # Valid tags
        assert validate_tag("ECHO+")
        assert validate_tag("FUSE+")
        assert validate_tag("CANON+")
        assert validate_tag("LAW_LOOP+")

        # Invalid tags
        assert not validate_tag("INVALID+")
        assert not validate_tag("random")
        assert not validate_tag("")

    def test_is_fusion_eligible(self):
        """Test is_fusion_eligible conditions."""
        from rege.core.constants import is_fusion_eligible

        # Needs both charge >= 70 AND overlap_count >= 2
        assert not is_fusion_eligible(69, 2)
        assert not is_fusion_eligible(70, 1)
        assert is_fusion_eligible(70, 2)
        assert is_fusion_eligible(85, 3)

    def test_is_auto_fusion_trigger(self):
        """Test is_auto_fusion_trigger at boundary (90)."""
        from rege.core.constants import is_auto_fusion_trigger

        assert not is_auto_fusion_trigger(89)
        assert is_auto_fusion_trigger(90)
        assert is_auto_fusion_trigger(100)

    def test_get_tier_level_all_tiers(self):
        """Test get_tier_level for all tiers."""
        from rege.core.constants import get_tier_level

        assert get_tier_level(0) == 1
        assert get_tier_level(25) == 1
        assert get_tier_level(26) == 2
        assert get_tier_level(50) == 2
        assert get_tier_level(51) == 3
        assert get_tier_level(70) == 3
        assert get_tier_level(71) == 4
        assert get_tier_level(85) == 4
        assert get_tier_level(86) == 5
        assert get_tier_level(100) == 5

    def test_charge_tier_enum_values(self):
        """Test ChargeTier enum values."""
        from rege.core.constants import ChargeTier

        assert ChargeTier.LATENT.value == 1
        assert ChargeTier.PROCESSING.value == 2
        assert ChargeTier.ACTIVE.value == 3
        assert ChargeTier.INTENSE.value == 4
        assert ChargeTier.CRITICAL.value == 5

    def test_priority_enum_ordering(self):
        """Test Priority enum ordering (lower = higher priority)."""
        from rege.core.constants import Priority

        assert Priority.CRITICAL < Priority.HIGH
        assert Priority.HIGH < Priority.STANDARD
        assert Priority.STANDARD < Priority.BACKGROUND


class TestExceptions:
    """Tests for exceptions.py coverage gaps."""

    def test_rege_error_base(self):
        """Test RegeError base exception."""
        from rege.core.exceptions import RegeError

        error = RegeError("Test error")
        assert str(error) == "Test error"

    def test_invocation_error(self):
        """Test InvocationError exception."""
        from rege.core.exceptions import InvocationError

        error = InvocationError("Invalid invocation")
        assert "Invalid invocation" in str(error)

    def test_routing_error(self):
        """Test RoutingError exception."""
        from rege.core.exceptions import RoutingError

        error = RoutingError("Routing failed")
        assert "Routing failed" in str(error)

    def test_depth_limit_exceeded(self):
        """Test DepthLimitExceeded exception."""
        from rege.core.exceptions import DepthLimitExceeded

        error = DepthLimitExceeded(depth=10, limit=7, action="route")

        assert error.depth == 10
        assert error.limit == 7
        assert error.action == "route"
        assert "10" in str(error)
        assert "7" in str(error)

    def test_depth_limit_exceeded_custom_message(self):
        """Test DepthLimitExceeded with custom message."""
        from rege.core.exceptions import DepthLimitExceeded

        error = DepthLimitExceeded(
            depth=15, limit=12, action="deep_route",
            message="Custom depth error"
        )
        assert str(error) == "Custom depth error"

    def test_deadlock_detected(self):
        """Test DeadlockDetected exception."""
        from rege.core.exceptions import DeadlockDetected

        route_chain = ["A", "B", "C", "A"]
        error = DeadlockDetected(route_chain=route_chain)

        assert error.route_chain == route_chain
        assert "A" in str(error)
        assert "deadlock" in str(error).lower()

    def test_deadlock_detected_custom_message(self):
        """Test DeadlockDetected with custom message."""
        from rege.core.exceptions import DeadlockDetected

        error = DeadlockDetected(route_chain=["X", "Y"], message="Loop detected")
        assert str(error) == "Loop detected"

    def test_queue_overflow(self):
        """Test QueueOverflow exception."""
        from rege.core.exceptions import QueueOverflow

        error = QueueOverflow(current_size=150, max_size=100)

        assert error.current_size == 150
        assert error.max_size == 100
        assert "150" in str(error)
        assert "100" in str(error)

    def test_queue_overflow_custom_message(self):
        """Test QueueOverflow with custom message."""
        from rege.core.exceptions import QueueOverflow

        error = QueueOverflow(
            current_size=200, max_size=100,
            message="Queue is full"
        )
        assert str(error) == "Queue is full"

    def test_fusion_error(self):
        """Test FusionError exception."""
        from rege.core.exceptions import FusionError

        error = FusionError("Fusion failed")
        assert "Fusion failed" in str(error)

    def test_fusion_not_eligible(self):
        """Test FusionNotEligible exception."""
        from rege.core.exceptions import FusionNotEligible

        error = FusionNotEligible(
            reason="Charge too low",
            fragments=["frag1", "frag2"]
        )

        assert error.reason == "Charge too low"
        assert error.fragments == ["frag1", "frag2"]
        assert "Charge too low" in str(error)

    def test_fusion_not_eligible_no_fragments(self):
        """Test FusionNotEligible without fragments list."""
        from rege.core.exceptions import FusionNotEligible

        error = FusionNotEligible(reason="No overlap")
        assert error.fragments == []

    def test_fusion_rollback_failed(self):
        """Test FusionRollbackFailed exception."""
        from rege.core.exceptions import FusionRollbackFailed

        error = FusionRollbackFailed(
            fused_id="FUSED_123",
            reason="Deadline passed"
        )

        assert error.fused_id == "FUSED_123"
        assert error.reason == "Deadline passed"
        assert "FUSED_123" in str(error)

    def test_recovery_error(self):
        """Test RecoveryError exception."""
        from rege.core.exceptions import RecoveryError

        error = RecoveryError("Recovery failed")
        assert "Recovery failed" in str(error)

    def test_checkpoint_not_found(self):
        """Test CheckpointNotFound exception."""
        from rege.core.exceptions import CheckpointNotFound

        error = CheckpointNotFound(checkpoint_id="CP_20240101")

        assert error.checkpoint_id == "CP_20240101"
        assert "CP_20240101" in str(error)

    def test_recovery_authorization_required(self):
        """Test RecoveryAuthorizationRequired exception."""
        from rege.core.exceptions import RecoveryAuthorizationRequired

        error = RecoveryAuthorizationRequired(
            operation="full_rollback",
            reason="Destructive operation"
        )

        assert error.operation == "full_rollback"
        assert error.reason == "Destructive operation"
        assert "full_rollback" in str(error)

    def test_organ_not_found_error(self):
        """Test OrganNotFoundError exception."""
        from rege.core.exceptions import OrganNotFoundError

        error = OrganNotFoundError(
            organ_name="FAKE_ORGAN",
            available_organs=["HEART_OF_CANON", "MIRROR_CABINET"]
        )

        assert error.organ_name == "FAKE_ORGAN"
        assert "HEART_OF_CANON" in error.available_organs
        assert "FAKE_ORGAN" in str(error)
        assert "HEART_OF_CANON" in str(error)

    def test_organ_not_found_error_no_list(self):
        """Test OrganNotFoundError without available organs list."""
        from rege.core.exceptions import OrganNotFoundError

        error = OrganNotFoundError(organ_name="MISSING")
        assert error.available_organs == []

    def test_organ_execution_error(self):
        """Test OrganExecutionError exception."""
        from rege.core.exceptions import OrganExecutionError

        original = ValueError("Original error")
        error = OrganExecutionError(
            organ_name="BLOOM_ENGINE",
            error=original
        )

        assert error.organ_name == "BLOOM_ENGINE"
        assert error.original_error == original
        assert "BLOOM_ENGINE" in str(error)

    def test_validation_error(self):
        """Test ValidationError exception."""
        from rege.core.exceptions import ValidationError

        errors = ["Invalid field A", "Invalid field B"]
        error = ValidationError(errors=errors)

        assert error.errors == errors
        assert "Invalid field A" in str(error)

    def test_invalid_mode_error(self):
        """Test InvalidModeError exception."""
        from rege.core.exceptions import InvalidModeError

        error = InvalidModeError(
            organ="HEART_OF_CANON",
            mode="invalid_mode",
            valid_modes=["mythic", "recursive", "default"]
        )

        assert error.organ == "HEART_OF_CANON"
        assert error.mode == "invalid_mode"
        assert "mythic" in error.valid_modes
        assert "invalid_mode" in str(error)

    def test_invalid_depth_error(self):
        """Test InvalidDepthError exception."""
        from rege.core.exceptions import InvalidDepthError

        error = InvalidDepthError(
            depth="super_deep",
            valid_depths=["light", "standard", "full spiral"]
        )

        assert error.depth == "super_deep"
        assert "light" in error.valid_depths
        assert "super_deep" in str(error)

    def test_persistence_error(self):
        """Test PersistenceError exception."""
        from rege.core.exceptions import PersistenceError

        error = PersistenceError("File write failed")
        assert "File write failed" in str(error)

    def test_archive_corrupted(self):
        """Test ArchiveCorrupted exception."""
        from rege.core.exceptions import ArchiveCorrupted

        error = ArchiveCorrupted(
            file_path="/path/to/archive.json",
            reason="Invalid JSON"
        )

        assert error.file_path == "/path/to/archive.json"
        assert error.reason == "Invalid JSON"
        assert "/path/to/archive.json" in str(error)

    def test_law_violation_error(self):
        """Test LawViolationError exception."""
        from rege.core.exceptions import LawViolationError

        error = LawViolationError(
            law_id="LAW_01",
            law_name="Recursive Primacy",
            violation_description="Non-recursive call detected"
        )

        assert error.law_id == "LAW_01"
        assert error.law_name == "Recursive Primacy"
        assert "LAW_01" in str(error)
        assert "Recursive Primacy" in str(error)

    def test_panic_stop(self):
        """Test PanicStop exception."""
        from rege.core.exceptions import PanicStop

        error = PanicStop(
            reason="Critical depth exceeded",
            snapshot_id="SNAP_001"
        )

        assert error.reason == "Critical depth exceeded"
        assert error.snapshot_id == "SNAP_001"
        assert "PANIC STOP" in str(error)
        assert "SNAP_001" in str(error)

    def test_panic_stop_no_snapshot(self):
        """Test PanicStop without snapshot."""
        from rege.core.exceptions import PanicStop

        error = PanicStop(reason="System halt")
        assert error.snapshot_id is None
        assert "none" in str(error).lower()


class TestBloomEngineExtended:
    """Extended tests for bloom_engine.py coverage gaps."""

    def test_growth_mode(self):
        """Test growth mode processing."""
        from rege.organs.bloom_engine import BloomEngine
        from rege.core.models import Invocation, Patch, DepthLevel

        engine = BloomEngine()
        invocation = Invocation(
            organ="BLOOM_ENGINE",
            symbol="growth test",
            mode="growth",
            depth=DepthLevel.STANDARD,
            expect="mutated_fragment",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="BLOOM_ENGINE", tags=[], charge=60)

        result = engine.invoke(invocation, patch)

        assert "cycle" in result
        assert "initiation" in result
        assert "growth_potential" in result
        assert result["growth_potential"] == 0.6  # charge / 100

    def test_default_bloom_processing(self):
        """Test default bloom processing."""
        from rege.organs.bloom_engine import BloomEngine
        from rege.core.models import Invocation, Patch, DepthLevel

        engine = BloomEngine()
        invocation = Invocation(
            organ="BLOOM_ENGINE",
            symbol="default test",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="default_output",
            charge=45,
        )
        patch = Patch(input_node="test", output_node="BLOOM_ENGINE", tags=[], charge=45)

        result = engine.invoke(invocation, patch)

        assert result["status"] == "bloom_acknowledged"
        assert result["charge"] == 45
        assert "bloom_potential" in result
        assert "season" in result

    def test_extract_base_id_with_version(self):
        """Test extracting base ID from versioned symbol."""
        from rege.organs.bloom_engine import BloomEngine

        engine = BloomEngine()

        # With version pattern
        assert engine._extract_base_id("Fragment_v1.0") == "Fragment"
        assert engine._extract_base_id("MyEntity_v2.3") == "MyEntity"

        # Without version pattern
        assert engine._extract_base_id("Simple Fragment") == "Simple_Fragment"
        assert engine._extract_base_id("one") == "One"

    def test_calculate_bloom_potential_across_range(self):
        """Test bloom potential calculation across charge range."""
        from rege.organs.bloom_engine import BloomEngine

        engine = BloomEngine()

        assert engine._calculate_bloom_potential(0) == 0.0
        assert engine._calculate_bloom_potential(40) == 0.5
        assert engine._calculate_bloom_potential(80) == 1.0
        assert engine._calculate_bloom_potential(100) == 1.0  # Capped at 1.0

    def test_bloom_cycle_initiate_at_depth_limit(self):
        """Test bloom cycle initiation at depth limit."""
        from rege.organs.bloom_engine import BloomCycle

        cycle = BloomCycle(
            phase="Deep",
            trigger_event="deep trigger",
            mutation_path="DEEP+",
            duration_days=7,
        )

        # Force to depth limit
        cycle.mutation_depth = BloomCycle.MUTATION_DEPTH_LIMIT

        result = cycle.initiate()

        assert cycle.status == "consolidated"
        assert "depth limit" in result.lower()

    def test_bloom_cycle_force_consolidation(self):
        """Test forcing consolidation returns FUSE01 action."""
        from rege.organs.bloom_engine import BloomCycle

        cycle = BloomCycle(
            phase="Test",
            trigger_event="trigger",
            mutation_path="TEST+",
            duration_days=7,
        )
        cycle.mutation_depth = 5
        cycle.version_branches = 3

        result = cycle.force_consolidation()

        assert result["action"] == "FUSE01"
        assert result["reason"] == "depth_limit_exceeded"
        assert result["mutation_depth"] == 5
        assert cycle.status == "consolidated"

    def test_bloom_cycle_add_mutation(self):
        """Test adding mutations to cycle."""
        from rege.organs.bloom_engine import BloomCycle

        cycle = BloomCycle(
            phase="Test",
            trigger_event="trigger",
            mutation_path="TEST+",
            duration_days=7,
        )

        cycle.add_mutation("adaptation", "Minor change")
        cycle.add_mutation("evolution", "Major change")

        assert len(cycle.mutations) == 2
        assert cycle.mutations[0]["type"] == "adaptation"
        assert cycle.mutations[1]["type"] == "evolution"

    def test_bloom_engine_get_active_cycles(self):
        """Test getting active cycles."""
        from rege.organs.bloom_engine import BloomEngine
        from rege.core.models import Invocation, Patch, DepthLevel

        engine = BloomEngine()
        patch = Patch(input_node="test", output_node="BLOOM_ENGINE", tags=[], charge=60)

        # Create a cycle via growth mode
        invocation = Invocation(
            organ="BLOOM_ENGINE",
            symbol="active test",
            mode="growth",
            depth=DepthLevel.STANDARD,
            expect="mutated_fragment",
            charge=60,
        )
        engine.invoke(invocation, patch)

        active = engine.get_active_cycles()
        assert len(active) == 1
        assert active[0].status == "active"

    def test_bloom_engine_get_cycle(self):
        """Test getting specific cycle by ID."""
        from rege.organs.bloom_engine import BloomEngine
        from rege.core.models import Invocation, Patch, DepthLevel

        engine = BloomEngine()
        patch = Patch(input_node="test", output_node="BLOOM_ENGINE", tags=[], charge=60)

        invocation = Invocation(
            organ="BLOOM_ENGINE",
            symbol="get cycle test",
            mode="growth",
            depth=DepthLevel.STANDARD,
            expect="mutated_fragment",
            charge=60,
        )
        result = engine.invoke(invocation, patch)
        cycle_id = result["cycle"]["cycle_id"]

        retrieved = engine.get_cycle(cycle_id)
        assert retrieved is not None
        assert retrieved.cycle_id == cycle_id

    def test_bloom_engine_branch_version_not_found(self):
        """Test branching version for non-existent cycle."""
        from rege.organs.bloom_engine import BloomEngine

        engine = BloomEngine()
        result = engine.branch_version("NON_EXISTENT_CYCLE")

        assert result["status"] == "failed"
        assert "not found" in result["reason"].lower()

    def test_bloom_engine_force_consolidation_not_found(self):
        """Test forcing consolidation for non-existent cycle."""
        from rege.organs.bloom_engine import BloomEngine

        engine = BloomEngine()
        result = engine.force_consolidation("NON_EXISTENT_CYCLE")

        assert result["status"] == "failed"
        assert "not found" in result["reason"].lower()

    def test_seasonal_growth_mode(self):
        """Test seasonal_growth mode (alias for seasonal_mutation)."""
        from rege.organs.bloom_engine import BloomEngine
        from rege.core.models import Invocation, Patch, DepthLevel

        engine = BloomEngine()
        invocation = Invocation(
            organ="BLOOM_ENGINE",
            symbol="seasonal growth",
            mode="seasonal_growth",
            depth=DepthLevel.STANDARD,
            expect="mutated_fragment",
            charge=70,
        )
        patch = Patch(input_node="test", output_node="BLOOM_ENGINE", tags=[], charge=70)

        result = engine.invoke(invocation, patch)

        assert "cycle" in result
        assert "mutation_type" in result

    def test_determine_mutation_type_all_tiers(self):
        """Test mutation type determination for all charge tiers."""
        from rege.organs.bloom_engine import BloomEngine

        engine = BloomEngine()

        assert engine._determine_mutation_type(25) == "drift"
        assert engine._determine_mutation_type(60) == "adaptation"
        assert engine._determine_mutation_type(75) == "evolution"
        assert engine._determine_mutation_type(90) == "metamorphosis"

    def test_calculate_duration_all_tiers(self):
        """Test duration calculation for all charge tiers."""
        from rege.organs.bloom_engine import BloomEngine

        engine = BloomEngine()

        assert engine._calculate_duration(30) == 7   # Standard
        assert engine._calculate_duration(60) == 14  # Active
        assert engine._calculate_duration(80) == 21  # Intense
        assert engine._calculate_duration(90) == 30  # Critical


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
