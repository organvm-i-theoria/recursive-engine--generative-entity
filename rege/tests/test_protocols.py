"""
Tests for protocols.
"""

import pytest
from datetime import datetime, timedelta

from rege.protocols.fuse01 import FusionProtocol
from rege.protocols.recovery import SystemRecoveryProtocol
from rege.protocols.enforcement import LawEnforcer
from rege.core.models import Fragment, FusionMode, FusionType, RecoveryTrigger
from rege.core.exceptions import FusionNotEligible, CheckpointNotFound


class TestFusionProtocol:
    """Tests for FUSE01 Protocol."""

    def setup_method(self):
        """Set up test fixtures."""
        self.protocol = FusionProtocol()

    def test_check_eligibility_needs_two_fragments(self):
        """Test that fusion needs at least 2 fragments."""
        fragment = Fragment(id="F1", name="Test", charge=80, tags=["TEST+"])

        is_eligible, reason = self.protocol.check_eligibility([fragment])

        assert not is_eligible
        assert "at least 2" in reason

    def test_check_eligibility_charge_threshold(self):
        """Test charge threshold for auto fusion."""
        frag1 = Fragment(id="F1", name="Test1", charge=50, tags=["TAG+"])
        frag2 = Fragment(id="F2", name="Test2", charge=50, tags=["TAG+"])

        is_eligible, reason = self.protocol.check_eligibility([frag1, frag2])

        assert not is_eligible
        assert "below threshold" in reason

    def test_forced_mode_bypasses_checks(self):
        """Test that forced mode bypasses eligibility checks."""
        frag1 = Fragment(id="F1", name="Test1", charge=30, tags=[])
        frag2 = Fragment(id="F2", name="Test2", charge=30, tags=[])

        is_eligible, reason = self.protocol.check_eligibility(
            [frag1, frag2], mode=FusionMode.FORCED
        )

        assert is_eligible
        assert "bypasses" in reason

    def test_execute_fusion(self):
        """Test successful fusion execution."""
        frag1 = Fragment(id="F1", name="Jessica", charge=80, tags=["CHAR+", "MIR+"])
        frag2 = Fragment(id="F2", name="Doubt", charge=75, tags=["SHDW+", "MIR+"])

        fused = self.protocol.execute_fusion(
            [frag1, frag2],
            mode=FusionMode.INVOKED,
            output_route="BLOOM_ENGINE",
        )

        assert fused is not None
        assert fused.charge == 80  # INHERITED_MAX
        assert "FUSE+" in fused.tags
        assert frag1.status == "fused"
        assert frag2.status == "fused"

    def test_rollback_within_window(self):
        """Test successful rollback within window."""
        frag1 = Fragment(id="F1", name="Test1", charge=80, tags=["TAG+"])
        frag2 = Fragment(id="F2", name="Test2", charge=75, tags=["TAG+"])

        fused = self.protocol.execute_fusion(
            [frag1, frag2], mode=FusionMode.INVOKED
        )

        result = self.protocol.rollback(fused.fused_id, "Test rollback")

        assert result["status"] == "rolled_back"
        assert frag1.status == "active"
        assert frag2.status == "active"

    def test_infer_fusion_type_version_merge(self):
        """Test fusion type inference for version merge."""
        frag1 = Fragment(id="F1", name="Test", charge=80, tags=[], version="1.0")
        frag2 = Fragment(id="F2", name="Test", charge=80, tags=[], version="2.0")

        fusion_type = self.protocol._infer_fusion_type([frag1, frag2])

        assert fusion_type == FusionType.VERSION_MERGE


class TestSystemRecoveryProtocol:
    """Tests for System Recovery Protocol."""

    def setup_method(self):
        """Set up test fixtures."""
        self.protocol = SystemRecoveryProtocol()

    def test_capture_snapshot(self):
        """Test snapshot capture."""
        system_state = {
            "metrics": {"active_patches": 10},
            "organs": {"HEART_OF_CANON": "active"},
            "pending": [],
            "errors": [],
        }

        snapshot = self.protocol.capture_snapshot(
            RecoveryTrigger.MANUAL, system_state
        )

        assert snapshot.snapshot_id is not None
        assert snapshot.trigger == RecoveryTrigger.MANUAL
        assert "active_patches" in snapshot.system_state

    def test_full_rollback_requires_confirmation(self):
        """Test full rollback requires confirmation."""
        # First create a checkpoint
        system_state = {"metrics": {}, "organs": {}, "pending": [], "errors": []}
        snapshot = self.protocol.capture_snapshot(RecoveryTrigger.MANUAL, system_state)

        result = self.protocol.full_rollback(snapshot.snapshot_id, confirm=False)

        assert result["status"] == "confirmation_required"

    def test_full_rollback_with_confirmation(self):
        """Test full rollback with confirmation."""
        system_state = {
            "metrics": {},
            "organs": {"HEART_OF_CANON": "active"},
            "pending": [],
            "errors": [],
        }
        snapshot = self.protocol.capture_snapshot(RecoveryTrigger.MANUAL, system_state)

        result = self.protocol.full_rollback(snapshot.snapshot_id, confirm=True)

        assert result["status"] == "success"
        assert "HEART_OF_CANON" in result["organs_restored"]

    def test_partial_recovery(self):
        """Test partial recovery of specific organs."""
        system_state = {
            "metrics": {},
            "organs": {
                "HEART_OF_CANON": "active",
                "MIRROR_CABINET": "active",
                "SOUL_PATCHBAY": "degraded",
            },
            "pending": [],
            "errors": [],
        }
        snapshot = self.protocol.capture_snapshot(RecoveryTrigger.MANUAL, system_state)

        result = self.protocol.partial_recovery(
            ["SOUL_PATCHBAY"], snapshot.snapshot_id
        )

        assert result["status"] == "success"
        assert "SOUL_PATCHBAY" in result["organs_restored"]
        assert "HEART_OF_CANON" in result["organs_unchanged"]

    def test_emergency_stop(self):
        """Test emergency stop."""
        result = self.protocol.emergency_stop("Test emergency")

        assert result["status"] == "halted"
        assert self.protocol.is_halted()
        assert result["panic_snapshot"] is not None

    def test_resume_from_halt(self):
        """Test resuming from halt."""
        self.protocol.emergency_stop("Test")

        result = self.protocol.resume_from_halt(confirm=True)

        assert result["status"] == "resumed"
        assert not self.protocol.is_halted()


class TestLawEnforcer:
    """Tests for Law Enforcer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.enforcer = LawEnforcer()

    def test_core_laws_initialized(self):
        """Test that core laws are initialized."""
        laws = self.enforcer.get_all_laws()

        assert len(laws) > 0
        assert self.enforcer.get_law("LAW_01") is not None
        assert self.enforcer.get_law("LAW_81") is not None

    def test_detect_isolation_violation(self):
        """Test detection of isolation violation (LAW_01)."""
        context = {"isolated": True}

        violation = self.enforcer.detect_violation("create_fragment", context)

        assert violation is not None
        assert any(v["law_id"] == "LAW_01" for v in violation["violations"])

    def test_detect_stagnation_violation(self):
        """Test detection of stagnation violation (LAW_04)."""
        context = {"stagnant_days": 45}

        violation = self.enforcer.detect_violation("check_entity", context)

        assert violation is not None
        assert any(v["law_id"] == "LAW_04" for v in violation["violations"])

    def test_detect_destructive_fusion_violation(self):
        """Test detection of destructive fusion violation (LAW_81)."""
        context = {"delete_sources": True}

        violation = self.enforcer.detect_violation("fusion", context)

        assert violation is not None
        assert any(v["law_id"] == "LAW_81" for v in violation["violations"])

    def test_no_violation_returns_none(self):
        """Test that no violation returns None."""
        context = {"isolated": False, "stagnant_days": 5}

        violation = self.enforcer.detect_violation("normal_action", context)

        assert violation is None

    def test_apply_consequence(self):
        """Test applying consequences."""
        violation = {
            "action": "test",
            "violations": [
                {"law_id": "LAW_01", "consequence": "reconnect"},
            ],
        }

        result = self.enforcer.apply_consequence(violation)

        assert "consequence_id" in result
        assert len(result["actions_taken"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
