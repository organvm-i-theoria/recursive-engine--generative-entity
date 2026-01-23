"""
Extended coverage tests for Soul Patchbay.

Targets untested paths:
- QueueOverflow exception
- Maintenance mode blocking
- Transitive deadlock detection
- Make room failure
- Junction node with multiple patches
- Complete route for non-existent route
- Queue state edge cases
- Clear method verification
"""

import pytest
from datetime import datetime

from rege.routing.patchbay import PatchQueue, get_patchbay_queue
from rege.core.models import Patch
from rege.core.constants import Priority
from rege.core.exceptions import QueueOverflow, DeadlockDetected


@pytest.fixture
def queue():
    """Create a fresh PatchQueue instance."""
    return PatchQueue(max_size=10)


@pytest.fixture
def small_queue():
    """Create a small queue for overflow testing."""
    return PatchQueue(max_size=3)


def make_patch(
    input_node="INPUT",
    output_node="OUTPUT",
    priority=Priority.STANDARD,
    charge=50,
    tags=None,
):
    """Helper to create test patches."""
    patch = Patch(
        input_node=input_node,
        output_node=output_node,
        tags=tags or [],
        charge=charge,
    )
    patch.priority = priority
    return patch


class TestQueueOverflow:
    """Test queue overflow scenarios."""

    def test_overflow_rejects_background(self, small_queue):
        """BACKGROUND patches rejected when queue full."""
        # Fill queue
        for i in range(3):
            p = make_patch(f"IN_{i}", f"OUT_{i}", Priority.STANDARD)
            small_queue.enqueue(p)

        # Try to add BACKGROUND - should be rejected
        bg = make_patch("BG_IN", "BG_OUT", Priority.BACKGROUND)
        result = small_queue.enqueue(bg)

        assert result is False

    def test_overflow_raises_for_critical(self, small_queue):
        """QueueOverflow raised when queue full of CRITICAL patches."""
        # Fill queue with CRITICAL patches
        for i in range(3):
            p = make_patch(f"CRIT_{i}", f"OUT_{i}", Priority.CRITICAL)
            small_queue.enqueue(p)

        # Try to add another CRITICAL - should raise
        crit = make_patch("NEW_CRIT", "NEW_OUT", Priority.CRITICAL)
        with pytest.raises(QueueOverflow):
            small_queue.enqueue(crit)

    def test_overflow_makes_room_for_higher_priority(self, small_queue):
        """Higher priority can evict lower priority when full."""
        # Fill queue with BACKGROUND patches
        for i in range(3):
            p = make_patch(f"BG_{i}", f"OUT_{i}", Priority.BACKGROUND)
            small_queue.enqueue(p)

        assert small_queue.size() == 3

        # Add CRITICAL - should evict a BACKGROUND
        crit = make_patch("CRIT", "CRIT_OUT", Priority.CRITICAL)
        result = small_queue.enqueue(crit)

        assert result is True
        assert small_queue.size() == 3  # Still at capacity


class TestMaintenanceMode:
    """Test maintenance mode behavior."""

    def test_enqueue_rejected_during_maintenance(self, queue):
        """Enqueue returns False during maintenance."""
        queue.enter_maintenance_mode()

        p = make_patch("TEST", "TEST_OUT", Priority.CRITICAL)
        result = queue.enqueue(p)

        assert result is False
        assert queue.is_in_maintenance() is True

    def test_dequeue_returns_none_during_maintenance(self, queue):
        """Dequeue returns None during maintenance."""
        # Add a patch first
        p = make_patch("TEST", "TEST_OUT")
        queue.enqueue(p)

        # Enter maintenance
        queue.enter_maintenance_mode()

        result = queue.dequeue()
        assert result is None

    def test_exit_maintenance_resumes_operations(self, queue):
        """Operations resume after exiting maintenance."""
        queue.enter_maintenance_mode()
        queue.exit_maintenance_mode()

        p = make_patch("TEST", "TEST_OUT")
        result = queue.enqueue(p)

        assert result is True
        assert queue.is_in_maintenance() is False


class TestTransitiveDeadlockDetection:
    """Test deadlock detection for transitive cycles."""

    def test_simple_cycle_detected(self, queue):
        """Simple A->B, B->A cycle detected."""
        p1 = make_patch("A", "B")
        p2 = make_patch("B", "A")

        is_deadlock = queue.detect_deadlock([p1, p2])
        assert is_deadlock is True
        assert queue.deadlock_count >= 1

    def test_transitive_cycle_detected(self, queue):
        """Transitive A->B->C->A cycle detected."""
        p1 = make_patch("A", "B")
        p2 = make_patch("B", "C")
        p3 = make_patch("C", "A")  # Back to A

        is_deadlock = queue.detect_deadlock([p1, p2, p3])
        assert is_deadlock is True

    def test_no_deadlock_linear_chain(self, queue):
        """Linear chain A->B->C->D has no deadlock."""
        p1 = make_patch("A", "B")
        p2 = make_patch("B", "C")
        p3 = make_patch("C", "D")

        is_deadlock = queue.detect_deadlock([p1, p2, p3])
        assert is_deadlock is False

    def test_deadlock_or_raise_raises(self, queue):
        """detect_deadlock_or_raise raises DeadlockDetected."""
        p1 = make_patch("A", "B")
        p2 = make_patch("B", "A")

        with pytest.raises(DeadlockDetected):
            queue.detect_deadlock_or_raise([p1, p2])


class TestJunctionNode:
    """Test junction node creation."""

    def test_junction_from_empty_raises(self, queue):
        """Creating junction from empty list raises ValueError."""
        with pytest.raises(ValueError):
            queue.create_junction_node([])

    def test_junction_two_patches(self, queue):
        """Junction merges two patches correctly."""
        p1 = make_patch("A", "TARGET", charge=60, tags=["TAG1+"])
        p2 = make_patch("B", "TARGET", charge=80, tags=["TAG2+"])

        junction = queue.create_junction_node([p1, p2])

        assert "JUNCTION" in junction.input_node
        assert "A" in junction.input_node
        assert "B" in junction.input_node
        assert junction.output_node == "TARGET"
        assert junction.charge == 80  # Max charge
        assert "JUNCTION+" in junction.tags

    def test_junction_three_patches(self, queue):
        """Junction merges three patches correctly."""
        p1 = make_patch("A", "TARGET", charge=50, tags=["T1+"])
        p2 = make_patch("B", "TARGET", charge=70, tags=["T2+"])
        p3 = make_patch("C", "TARGET", charge=90, tags=["T3+"])

        junction = queue.create_junction_node([p1, p2, p3])

        assert "A" in junction.input_node
        assert "B" in junction.input_node
        assert "C" in junction.input_node
        assert junction.charge == 90
        assert len(junction.metadata["source_patches"]) == 3


class TestCompleteRoute:
    """Test route completion tracking."""

    def test_complete_route_removes_active(self, queue):
        """complete_route removes route from active tracking."""
        p = make_patch("IN", "OUT")
        queue.enqueue(p)
        dequeued = queue.dequeue()

        # Route should be active
        assert ("IN", "OUT") in queue._active_routes

        # Complete it
        queue.complete_route(dequeued)

        # Route should be removed
        assert ("IN", "OUT") not in queue._active_routes

    def test_complete_route_nonexistent(self, queue):
        """complete_route handles non-existent route gracefully."""
        p = make_patch("NEVER", "EXISTED")

        # Should not raise
        queue.complete_route(p)


class TestCollisionDetection:
    """Test collision detection and handling."""

    def test_detect_collision_same_output(self, queue):
        """Collision detected when patches target same output."""
        p1 = make_patch("A", "SHARED")
        p2 = make_patch("B", "SHARED")

        is_collision = queue.detect_collision(p1, p2)
        assert is_collision is True
        assert queue.collision_count >= 1

    def test_detect_collision_different_output(self, queue):
        """No collision when patches target different outputs."""
        p1 = make_patch("A", "OUT1")
        p2 = make_patch("B", "OUT2")

        is_collision = queue.detect_collision(p1, p2)
        assert is_collision is False

    def test_enqueue_with_collision(self, queue):
        """Enqueue detects and records collision."""
        p1 = make_patch("A", "SHARED")
        queue.enqueue(p1)

        p2 = make_patch("B", "SHARED")
        queue.enqueue(p2)

        assert queue.collision_count >= 1
        assert p2.metadata.get("collision_detected") is True


class TestQueueState:
    """Test queue state retrieval."""

    def test_queue_state_all_critical(self, queue):
        """Queue state correctly counts all CRITICAL."""
        for i in range(3):
            p = make_patch(f"CRIT_{i}", f"OUT_{i}", Priority.CRITICAL)
            queue.enqueue(p)

        state = queue.get_queue_state()

        assert state["by_priority"]["CRITICAL"] == 3
        assert state["by_priority"]["STANDARD"] == 0

    def test_queue_state_all_background(self, queue):
        """Queue state correctly counts all BACKGROUND."""
        for i in range(3):
            p = make_patch(f"BG_{i}", f"OUT_{i}", Priority.BACKGROUND)
            queue.enqueue(p)

        state = queue.get_queue_state()

        assert state["by_priority"]["BACKGROUND"] == 3
        assert state["by_priority"]["CRITICAL"] == 0

    def test_queue_state_mixed(self, queue):
        """Queue state correctly counts mixed priorities."""
        p1 = make_patch("CRIT", "OUT1", Priority.CRITICAL)
        p2 = make_patch("HIGH", "OUT2", Priority.HIGH)
        p3 = make_patch("STD", "OUT3", Priority.STANDARD)
        p4 = make_patch("BG", "OUT4", Priority.BACKGROUND)

        queue.enqueue(p1)
        queue.enqueue(p2)
        queue.enqueue(p3)
        queue.enqueue(p4)

        state = queue.get_queue_state()

        assert state["by_priority"]["CRITICAL"] == 1
        assert state["by_priority"]["HIGH"] == 1
        assert state["by_priority"]["STANDARD"] == 1
        assert state["by_priority"]["BACKGROUND"] == 1

    def test_queue_state_maintenance_flag(self, queue):
        """Queue state reports maintenance mode."""
        queue.enter_maintenance_mode()
        state = queue.get_queue_state()

        assert state["maintenance_mode"] is True


class TestClear:
    """Test queue clearing."""

    def test_clear_empties_heap(self, queue):
        """Clear empties the heap."""
        for i in range(5):
            p = make_patch(f"IN_{i}", f"OUT_{i}")
            queue.enqueue(p)

        queue.clear()

        assert queue.size() == 0
        assert queue.is_empty() is True

    def test_clear_resets_pending_tracking(self, queue):
        """Clear resets pending_by_output tracking."""
        p = make_patch("IN", "OUT")
        queue.enqueue(p)

        queue.clear()

        assert len(queue._pending_by_output) == 0

    def test_clear_resets_active_routes(self, queue):
        """Clear resets active_routes tracking."""
        p = make_patch("IN", "OUT")
        queue.enqueue(p)
        queue.dequeue()  # Creates active route

        queue.clear()

        assert len(queue._active_routes) == 0


class TestToList:
    """Test queue export."""

    def test_to_list_empty(self, queue):
        """Empty queue exports as empty list."""
        result = queue.to_list()
        assert result == []

    def test_to_list_with_patches(self, queue):
        """Queue with patches exports correctly."""
        p1 = make_patch("A", "OUT1")
        p2 = make_patch("B", "OUT2")
        queue.enqueue(p1)
        queue.enqueue(p2)

        result = queue.to_list()

        assert len(result) == 2
        assert all("patch_id" in r for r in result)


class TestGetPatchesByPriority:
    """Test filtering patches by priority."""

    def test_get_patches_by_priority(self, queue):
        """get_patches_by_priority filters correctly."""
        p1 = make_patch("CRIT", "OUT1", Priority.CRITICAL)
        p2 = make_patch("STD1", "OUT2", Priority.STANDARD)
        p3 = make_patch("STD2", "OUT3", Priority.STANDARD)

        queue.enqueue(p1)
        queue.enqueue(p2)
        queue.enqueue(p3)

        critical = queue.get_patches_by_priority(Priority.CRITICAL)
        standard = queue.get_patches_by_priority(Priority.STANDARD)

        assert len(critical) == 1
        assert len(standard) == 2


class TestGetPatchesByOutput:
    """Test filtering patches by output node."""

    def test_get_patches_by_output(self, queue):
        """get_patches_by_output filters correctly."""
        p1 = make_patch("A", "SHARED")
        p2 = make_patch("B", "SHARED")
        p3 = make_patch("C", "OTHER")

        queue.enqueue(p1)
        queue.enqueue(p2)
        queue.enqueue(p3)

        shared = queue.get_patches_by_output("SHARED")
        other = queue.get_patches_by_output("OTHER")

        assert len(shared) == 2
        assert len(other) == 1

    def test_get_patches_by_output_nonexistent(self, queue):
        """get_patches_by_output returns empty for nonexistent output."""
        result = queue.get_patches_by_output("NONEXISTENT")
        assert result == []


class TestPeekNext:
    """Test peek functionality."""

    def test_peek_next_empty(self, queue):
        """Peek on empty queue returns None."""
        assert queue.peek_next() is None

    def test_peek_next_with_patches(self, queue):
        """Peek returns next patch without removing."""
        p = make_patch("IN", "OUT")
        queue.enqueue(p)

        peeked = queue.peek_next()

        assert peeked is not None
        assert queue.size() == 1  # Not removed


class TestMakeRoomFor:
    """Test make room logic."""

    def test_make_room_fails_when_all_higher_priority(self, small_queue):
        """_make_room_for fails when all items are higher priority."""
        # Fill with CRITICAL
        for i in range(3):
            p = make_patch(f"CRIT_{i}", f"OUT_{i}", Priority.CRITICAL)
            small_queue.enqueue(p)

        # Try to make room for STANDARD (lower than CRITICAL)
        std = make_patch("STD", "STD_OUT", Priority.STANDARD)
        result = small_queue._make_room_for(std)

        assert result is False

    def test_make_room_succeeds_evicting_lower(self, small_queue):
        """_make_room_for succeeds evicting lower priority."""
        # Fill with BACKGROUND
        for i in range(3):
            p = make_patch(f"BG_{i}", f"OUT_{i}", Priority.BACKGROUND)
            small_queue.enqueue(p)

        # Make room for CRITICAL
        crit = make_patch("CRIT", "CRIT_OUT", Priority.CRITICAL)
        result = small_queue._make_room_for(crit)

        assert result is True
        assert small_queue.size() == 2  # One evicted


class TestGlobalQueue:
    """Test global patchbay queue singleton."""

    def test_get_patchbay_queue_singleton(self):
        """get_patchbay_queue returns same instance."""
        q1 = get_patchbay_queue()
        q2 = get_patchbay_queue()

        assert q1 is q2
