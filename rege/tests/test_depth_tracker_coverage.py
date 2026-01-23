"""
Extended coverage tests for Depth Tracker.

Targets untested paths:
- ABSOLUTE limit (33) - PANIC_STOP
- EMERGENCY limit (21) - FORCE_TERMINATE_ALERT
- check_depth_or_raise exception paths
- Tag precedence (EMERGENCY+ vs LAW_LOOP+)
- Increment/reset depth mutations
- Depth status at_risk boundary
- Limit type name resolution
- Large depth log
"""

import pytest

from rege.routing.depth_tracker import DepthTracker, DepthAction, get_depth_tracker
from rege.core.models import Patch
from rege.core.constants import DepthLimits
from rege.core.exceptions import DepthLimitExceeded, PanicStop


@pytest.fixture
def tracker():
    """Create a fresh DepthTracker instance."""
    return DepthTracker()


def make_patch(depth=0, tags=None):
    """Helper to create test patches."""
    return Patch(
        input_node="TEST",
        output_node="OUTPUT",
        tags=tags or [],
        depth=depth,
    )


class TestAbsoluteLimit:
    """Test ABSOLUTE depth limit (33)."""

    def test_depth_33_triggers_panic_stop(self, tracker):
        """Depth >= 33 should trigger PANIC_STOP."""
        patch = make_patch(depth=33)
        can_continue, action = tracker.check_depth(patch)

        assert can_continue is False
        assert action == DepthAction.PANIC_STOP

    def test_depth_34_triggers_panic_stop(self, tracker):
        """Depth > 33 should also trigger PANIC_STOP."""
        patch = make_patch(depth=34)
        can_continue, action = tracker.check_depth(patch)

        assert can_continue is False
        assert action == DepthAction.PANIC_STOP

    def test_panic_stop_logs_exhaustion(self, tracker):
        """PANIC_STOP should log exhaustion event."""
        patch = make_patch(depth=33)
        tracker.check_depth(patch)

        log = tracker.get_depth_log()
        assert len(log) >= 1
        assert log[-1]["action"] == DepthAction.PANIC_STOP


class TestEmergencyLimit:
    """Test EMERGENCY depth limit (21)."""

    def test_depth_21_triggers_force_terminate_alert(self, tracker):
        """Depth >= 21 (but < 33) should trigger FORCE_TERMINATE_ALERT."""
        patch = make_patch(depth=21)
        can_continue, action = tracker.check_depth(patch)

        assert can_continue is False
        assert action == DepthAction.FORCE_TERMINATE_ALERT

    def test_depth_25_triggers_force_terminate_alert(self, tracker):
        """Depth between 21 and 33 should trigger FORCE_TERMINATE_ALERT."""
        patch = make_patch(depth=25)
        can_continue, action = tracker.check_depth(patch)

        assert can_continue is False
        assert action == DepthAction.FORCE_TERMINATE_ALERT


class TestCheckDepthOrRaise:
    """Test check_depth_or_raise exception paths."""

    def test_panic_stop_exception(self, tracker):
        """Depth at ABSOLUTE limit should raise PanicStop."""
        patch = make_patch(depth=33)

        with pytest.raises(PanicStop) as exc_info:
            tracker.check_depth_or_raise(patch)

        assert "33" in str(exc_info.value)

    def test_depth_limit_exceeded_standard(self, tracker):
        """Depth at STANDARD limit should raise DepthLimitExceeded."""
        patch = make_patch(depth=7)

        with pytest.raises(DepthLimitExceeded) as exc_info:
            tracker.check_depth_or_raise(patch)

        assert exc_info.value.depth == 7
        assert exc_info.value.limit == DepthLimits.STANDARD

    def test_depth_limit_exceeded_extended(self, tracker):
        """Depth at EXTENDED limit with LAW_LOOP+ should raise DepthLimitExceeded."""
        patch = make_patch(depth=12, tags=["LAW_LOOP+"])

        with pytest.raises(DepthLimitExceeded) as exc_info:
            tracker.check_depth_or_raise(patch)

        assert exc_info.value.limit == DepthLimits.EXTENDED

    def test_no_exception_below_limit(self, tracker):
        """Depth below limit should not raise."""
        patch = make_patch(depth=5)

        # Should not raise
        tracker.check_depth_or_raise(patch)


class TestTagPrecedence:
    """Test tag precedence for limit determination."""

    def test_emergency_tag_uses_emergency_limit(self, tracker):
        """EMERGENCY+ tag should use EMERGENCY limit (21)."""
        patch = make_patch(depth=0, tags=["EMERGENCY+"])
        limit = tracker.get_limit(patch)

        assert limit == DepthLimits.EMERGENCY

    def test_law_loop_tag_uses_extended_limit(self, tracker):
        """LAW_LOOP+ tag should use EXTENDED limit (12)."""
        patch = make_patch(depth=0, tags=["LAW_LOOP+"])
        limit = tracker.get_limit(patch)

        assert limit == DepthLimits.EXTENDED

    def test_no_tags_uses_standard_limit(self, tracker):
        """No special tags should use STANDARD limit (7)."""
        patch = make_patch(depth=0, tags=[])
        limit = tracker.get_limit(patch)

        assert limit == DepthLimits.STANDARD

    def test_emergency_takes_precedence(self, tracker):
        """EMERGENCY+ takes precedence over LAW_LOOP+."""
        patch = make_patch(depth=0, tags=["EMERGENCY+", "LAW_LOOP+"])
        limit = tracker.get_limit(patch)

        assert limit == DepthLimits.EMERGENCY


class TestIncrementResetDepth:
    """Test depth increment and reset mutations."""

    def test_increment_depth(self, tracker):
        """increment_depth should increase patch.depth by 1."""
        patch = make_patch(depth=5)
        new_depth = tracker.increment_depth(patch)

        assert new_depth == 6
        assert patch.depth == 6

    def test_reset_depth(self, tracker):
        """reset_depth should set patch.depth to 0."""
        patch = make_patch(depth=10)
        tracker.reset_depth(patch)

        assert patch.depth == 0


class TestDepthStatus:
    """Test get_depth_status output."""

    def test_depth_status_basic(self, tracker):
        """Test basic depth status structure."""
        patch = make_patch(depth=3)
        status = tracker.get_depth_status(patch)

        assert status["current_depth"] == 3
        assert status["limit"] == 7  # STANDARD
        assert status["remaining"] == 4
        assert status["at_risk"] is False

    def test_depth_status_at_risk_remaining_2(self, tracker):
        """remaining <= 2 should set at_risk True."""
        patch = make_patch(depth=5)  # 7 - 5 = 2 remaining
        status = tracker.get_depth_status(patch)

        assert status["remaining"] == 2
        assert status["at_risk"] is True

    def test_depth_status_at_risk_remaining_1(self, tracker):
        """remaining = 1 should set at_risk True."""
        patch = make_patch(depth=6)  # 7 - 6 = 1 remaining
        status = tracker.get_depth_status(patch)

        assert status["remaining"] == 1
        assert status["at_risk"] is True

    def test_depth_status_not_at_risk_remaining_3(self, tracker):
        """remaining = 3 should set at_risk False."""
        patch = make_patch(depth=4)  # 7 - 4 = 3 remaining
        status = tracker.get_depth_status(patch)

        assert status["remaining"] == 3
        assert status["at_risk"] is False

    def test_depth_status_percentage(self, tracker):
        """Test percentage calculation."""
        patch = make_patch(depth=7)  # 100% of limit 7
        status = tracker.get_depth_status(patch)

        assert status["percentage_used"] == 100

    def test_depth_status_zero_depth(self, tracker):
        """Test percentage at depth 0."""
        patch = make_patch(depth=0)
        status = tracker.get_depth_status(patch)

        assert status["percentage_used"] == 0
        assert status["remaining"] == 7

    def test_depth_status_tags_affecting_limit(self, tracker):
        """Test tags_affecting_limit field."""
        patch = make_patch(depth=0, tags=["EMERGENCY+", "OTHER+"])
        status = tracker.get_depth_status(patch)

        assert "EMERGENCY+" in status["tags_affecting_limit"]
        assert "OTHER+" not in status["tags_affecting_limit"]


class TestLimitTypeNames:
    """Test _get_limit_type name resolution."""

    def test_limit_type_standard(self, tracker):
        """STANDARD limit returns 'STANDARD'."""
        result = tracker._get_limit_type(DepthLimits.STANDARD)
        assert result == "STANDARD"

    def test_limit_type_extended(self, tracker):
        """EXTENDED limit returns 'EXTENDED'."""
        result = tracker._get_limit_type(DepthLimits.EXTENDED)
        assert result == "EXTENDED"

    def test_limit_type_emergency(self, tracker):
        """EMERGENCY limit returns 'EMERGENCY'."""
        result = tracker._get_limit_type(DepthLimits.EMERGENCY)
        assert result == "EMERGENCY"

    def test_limit_type_unknown(self, tracker):
        """Unknown limit returns 'ABSOLUTE'."""
        result = tracker._get_limit_type(999)
        assert result == "ABSOLUTE"


class TestDepthLog:
    """Test depth log functionality."""

    def test_get_depth_log_empty(self, tracker):
        """Empty log returns empty list."""
        log = tracker.get_depth_log()
        assert log == []

    def test_get_depth_log_after_exhaustion(self, tracker):
        """Log populated after exhaustion."""
        patch = make_patch(depth=7)
        tracker.check_depth(patch)

        log = tracker.get_depth_log()
        assert len(log) == 1
        assert log[0]["depth"] == 7

    def test_get_depth_log_limit(self, tracker):
        """Log respects limit parameter."""
        # Create 10 exhaustion events
        for i in range(10):
            patch = make_patch(depth=7)
            tracker.check_depth(patch)

        log = tracker.get_depth_log(limit=5)
        assert len(log) == 5

    def test_clear_log(self, tracker):
        """clear_log empties the log."""
        patch = make_patch(depth=7)
        tracker.check_depth(patch)

        tracker.clear_log()

        assert tracker.get_depth_log() == []


class TestExhaustionCount:
    """Test exhaustion counting."""

    def test_exhaustion_count_increments(self, tracker):
        """Exhaustion count increments on each exhaustion."""
        assert tracker.get_exhaustion_count() == 0

        patch = make_patch(depth=7)
        tracker.check_depth(patch)

        assert tracker.get_exhaustion_count() == 1

        tracker.check_depth(patch)

        assert tracker.get_exhaustion_count() == 2


class TestContinueAction:
    """Test CONTINUE action for normal depths."""

    def test_depth_below_limit_continues(self, tracker):
        """Depth below limit returns CONTINUE."""
        patch = make_patch(depth=5)
        can_continue, action = tracker.check_depth(patch)

        assert can_continue is True
        assert action == DepthAction.CONTINUE


class TestEscalateToRitualCourt:
    """Test ESCALATE_TO_RITUAL_COURT for STANDARD limit."""

    def test_standard_limit_escalates(self, tracker):
        """STANDARD limit (7) with depth=7 escalates to ritual court."""
        patch = make_patch(depth=7)
        can_continue, action = tracker.check_depth(patch)

        assert can_continue is False
        assert action == DepthAction.ESCALATE_TO_RITUAL_COURT


class TestForceTerminateIncomplete:
    """Test FORCE_TERMINATE_INCOMPLETE for EXTENDED limit."""

    def test_extended_limit_force_terminates(self, tracker):
        """EXTENDED limit (12) with depth=12 force terminates."""
        patch = make_patch(depth=12, tags=["LAW_LOOP+"])
        can_continue, action = tracker.check_depth(patch)

        assert can_continue is False
        assert action == DepthAction.FORCE_TERMINATE_INCOMPLETE


class TestGlobalTracker:
    """Test global depth tracker singleton."""

    def test_get_depth_tracker_singleton(self):
        """get_depth_tracker returns same instance."""
        t1 = get_depth_tracker()
        t2 = get_depth_tracker()

        assert t1 is t2


class TestSnapshotId:
    """Test snapshot ID generation."""

    def test_snapshot_id_format(self, tracker):
        """Snapshot ID has PANIC_ prefix."""
        snapshot_id = tracker._generate_snapshot_id()

        assert snapshot_id.startswith("PANIC_")
        assert len(snapshot_id) > 6
