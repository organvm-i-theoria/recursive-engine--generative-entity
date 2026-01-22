"""
Tests for the routing system.
"""

import pytest
from rege.routing.patchbay import PatchQueue
from rege.routing.depth_tracker import DepthTracker, DepthAction
from rege.core.models import Patch
from rege.core.constants import Priority, DepthLimits


class TestPatchQueue:
    """Tests for PatchQueue."""

    def setup_method(self):
        """Set up test fixtures."""
        self.queue = PatchQueue(max_size=100)

    def test_enqueue_dequeue(self):
        """Test basic enqueue and dequeue."""
        patch = Patch(
            input_node="TEST",
            output_node="MIRROR_CABINET",
            tags=["TEST+"],
            charge=50,
        )

        assert self.queue.enqueue(patch)
        assert self.queue.size() == 1

        result = self.queue.dequeue()
        assert result == patch
        assert self.queue.size() == 0

    def test_priority_ordering(self):
        """Test that higher priority items are dequeued first."""
        low = Patch(input_node="A", output_node="B", tags=[], charge=30)  # BACKGROUND
        high = Patch(input_node="C", output_node="D", tags=[], charge=80)  # HIGH
        critical = Patch(input_node="E", output_node="F", tags=["EMERGENCY+"], charge=90)  # CRITICAL

        self.queue.enqueue(low)
        self.queue.enqueue(high)
        self.queue.enqueue(critical)

        # Should come out in priority order
        assert self.queue.dequeue().priority == Priority.CRITICAL
        assert self.queue.dequeue().priority == Priority.HIGH
        assert self.queue.dequeue().priority == Priority.BACKGROUND

    def test_peek_does_not_remove(self):
        """Test that peek doesn't remove item."""
        patch = Patch(input_node="A", output_node="B", tags=[], charge=50)
        self.queue.enqueue(patch)

        peeked = self.queue.peek_next()
        assert peeked == patch
        assert self.queue.size() == 1

    def test_collision_detection(self):
        """Test collision detection between patches."""
        patch1 = Patch(input_node="A", output_node="TARGET", tags=[], charge=50)
        patch2 = Patch(input_node="B", output_node="TARGET", tags=[], charge=50)

        assert self.queue.detect_collision(patch1, patch2)
        assert self.queue.collision_count == 1

    def test_deadlock_detection(self):
        """Test deadlock detection in patch chain."""
        patches = [
            Patch(input_node="A", output_node="B", tags=[], charge=50),
            Patch(input_node="B", output_node="C", tags=[], charge=50),
            Patch(input_node="C", output_node="A", tags=[], charge=50),  # Creates cycle
        ]

        assert self.queue.detect_deadlock(patches)
        assert self.queue.deadlock_count == 1

    def test_create_junction_node(self):
        """Test junction node creation."""
        patch1 = Patch(input_node="A", output_node="TARGET", tags=["TAG1+"], charge=50)
        patch2 = Patch(input_node="B", output_node="TARGET", tags=["TAG2+"], charge=70)

        junction = self.queue.create_junction_node([patch1, patch2])

        assert "JUNCTION[A+B]" in junction.input_node
        assert junction.output_node == "TARGET"
        assert "JUNCTION+" in junction.tags
        assert junction.charge == 70  # Max of sources

    def test_queue_state(self):
        """Test getting queue state."""
        patch = Patch(input_node="A", output_node="B", tags=[], charge=50)
        self.queue.enqueue(patch)

        state = self.queue.get_queue_state()

        assert state["total_size"] == 1
        assert state["max_size"] == 100
        assert "by_priority" in state

    def test_maintenance_mode(self):
        """Test maintenance mode blocks operations."""
        self.queue.enter_maintenance_mode()

        patch = Patch(input_node="A", output_node="B", tags=[], charge=50)
        assert not self.queue.enqueue(patch)
        assert self.queue.dequeue() is None

        self.queue.exit_maintenance_mode()
        assert self.queue.enqueue(patch)


class TestDepthTracker:
    """Tests for DepthTracker."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tracker = DepthTracker()

    def test_standard_depth_limit(self):
        """Test standard depth limit."""
        patch = Patch(input_node="A", output_node="B", tags=[], charge=50, depth=6)

        can_continue, action = self.tracker.check_depth(patch)
        assert can_continue
        assert action == DepthAction.CONTINUE

        # At limit
        patch.depth = 7
        can_continue, action = self.tracker.check_depth(patch)
        assert not can_continue
        assert action == DepthAction.ESCALATE_TO_RITUAL_COURT

    def test_extended_depth_limit_with_law_loop(self):
        """Test extended limit with LAW_LOOP+ tag."""
        patch = Patch(
            input_node="A",
            output_node="B",
            tags=["LAW_LOOP+"],
            charge=50,
            depth=10,
        )

        can_continue, action = self.tracker.check_depth(patch)
        assert can_continue

        patch.depth = 12
        can_continue, action = self.tracker.check_depth(patch)
        assert not can_continue
        assert action == DepthAction.FORCE_TERMINATE_INCOMPLETE

    def test_absolute_limit_triggers_panic(self):
        """Test absolute limit triggers panic stop."""
        patch = Patch(input_node="A", output_node="B", tags=[], charge=50, depth=33)

        can_continue, action = self.tracker.check_depth(patch)
        assert not can_continue
        assert action == DepthAction.PANIC_STOP

    def test_increment_depth(self):
        """Test depth increment."""
        patch = Patch(input_node="A", output_node="B", tags=[], charge=50, depth=0)

        new_depth = self.tracker.increment_depth(patch)
        assert new_depth == 1
        assert patch.depth == 1

    def test_get_depth_status(self):
        """Test depth status report."""
        patch = Patch(input_node="A", output_node="B", tags=[], charge=50, depth=5)

        status = self.tracker.get_depth_status(patch)

        assert status["current_depth"] == 5
        assert status["limit"] == DepthLimits.STANDARD
        assert status["remaining"] == 2
        assert status["at_risk"]  # remaining <= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
