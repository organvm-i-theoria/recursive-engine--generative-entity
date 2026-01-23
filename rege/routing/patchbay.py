"""
RE:GE Soul Patchbay - Priority queue and routing management.

Based on: RE-GE_ORG_BODY_08_SOUL_PATCHBAY.md

Priority Levels:
| Priority | Name       | Conditions                          | Queue Behavior                    |
|----------|------------|-------------------------------------|-----------------------------------|
| P0       | CRITICAL   | charge >= 86 OR emergency flag      | Immediate processing, may bypass  |
| P1       | HIGH       | LAW_LOOP+ tag OR charge >= 71       | Front of queue after CRITICAL     |
| P2       | STANDARD   | Default priority, charge 51-70      | Normal FIFO processing            |
| P3       | BACKGROUND | ECHO+ only OR charge <= 50          | Processed when queue clear        |

Conflict Resolution:
1. Same priority, same timestamp: FIFO
2. Cross-organ collision: Create junction node
3. Deadlock detection: Circular routing triggers RITUAL_COURT escalation
4. Resource exhaustion: Defer BACKGROUND, process CRITICAL only
"""

import heapq
from datetime import datetime
from typing import List, Optional, Dict, Any, Set, Tuple
from rege.core.models import Patch
from rege.core.constants import Priority
from rege.core.exceptions import QueueOverflow, DeadlockDetected


class PatchQueue:
    """
    Priority queue for managing patch routing requests.

    The Soul Patchbay queue handles:
    - Priority-based ordering (CRITICAL > HIGH > STANDARD > BACKGROUND)
    - Collision detection and junction node creation
    - Deadlock detection for circular routing
    - Queue state metrics and monitoring
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize the patch queue.

        Args:
            max_size: Maximum queue capacity before overflow handling
        """
        self._heap: List[Patch] = []
        self._counter = 0
        self._processed_count = 0
        self.max_size = max_size
        self.collision_count = 0
        self.deadlock_count = 0
        self._active_routes: Set[Tuple[str, str]] = set()
        self._pending_by_output: Dict[str, List[Patch]] = {}
        self._maintenance_mode = False

    def enqueue(self, patch: Patch) -> bool:
        """
        Add patch to queue with priority ordering.

        Args:
            patch: The patch to enqueue

        Returns:
            True if patch was enqueued, False if rejected

        Raises:
            QueueOverflow: If queue is at capacity and cannot accept more CRITICAL items
        """
        if self._maintenance_mode:
            return False

        # Check for overflow
        if len(self._heap) >= self.max_size:
            # Overflow: reject BACKGROUND, attempt to make room for others
            if patch.priority == Priority.BACKGROUND:
                return False

            # Try to remove lowest priority item
            if not self._make_room_for(patch):
                raise QueueOverflow(len(self._heap), self.max_size)

        # Check for collision
        collisions = self._check_collision(patch)
        if collisions:
            # Handle collision by creating junction if needed
            self._handle_collision(patch, collisions)

        # Enqueue
        heapq.heappush(self._heap, patch)
        self._counter += 1

        # Track by output node
        if patch.output_node not in self._pending_by_output:
            self._pending_by_output[patch.output_node] = []
        self._pending_by_output[patch.output_node].append(patch)

        return True

    def dequeue(self) -> Optional[Patch]:
        """
        Remove and return highest priority patch.

        Returns:
            The next patch to process, or None if queue is empty
        """
        if not self._heap or self._maintenance_mode:
            return None

        patch = heapq.heappop(self._heap)
        patch.processed_at = datetime.now()
        self._processed_count += 1

        # Track active route
        route = (patch.input_node, patch.output_node)
        self._active_routes.add(route)

        # Remove from output tracking
        if patch.output_node in self._pending_by_output:
            try:
                self._pending_by_output[patch.output_node].remove(patch)
            except ValueError:
                pass

        return patch

    def peek_next(self) -> Optional[Patch]:
        """
        View next patch without removing.

        Returns:
            The next patch to be processed, or None if empty
        """
        return self._heap[0] if self._heap else None

    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self._heap) == 0

    def size(self) -> int:
        """Get current queue size."""
        return len(self._heap)

    def complete_route(self, patch: Patch) -> None:
        """
        Mark a route as completed, removing from active tracking.

        Args:
            patch: The completed patch
        """
        route = (patch.input_node, patch.output_node)
        self._active_routes.discard(route)

    def _make_room_for(self, patch: Patch) -> bool:
        """
        Attempt to make room for a higher-priority patch.

        Returns:
            True if room was made, False otherwise
        """
        # Sort heap to find lowest priority
        self._heap.sort()

        # Find items with lower priority than the incoming patch
        for i in range(len(self._heap) - 1, -1, -1):
            if self._heap[i].priority > patch.priority:
                removed = self._heap.pop(i)
                # Clean up tracking
                if removed.output_node in self._pending_by_output:
                    try:
                        self._pending_by_output[removed.output_node].remove(removed)
                    except ValueError:
                        pass
                # Re-heapify
                heapq.heapify(self._heap)
                return True

        return False

    def _check_collision(self, patch: Patch) -> List[Patch]:
        """
        Check if patch collides with existing patches.

        A collision occurs when multiple patches target the same output node.

        Returns:
            List of colliding patches
        """
        if patch.output_node in self._pending_by_output:
            return self._pending_by_output[patch.output_node].copy()
        return []

    def _handle_collision(self, patch: Patch, collisions: List[Patch]) -> None:
        """Handle collision by recording and potentially creating junction."""
        self.collision_count += 1
        patch.metadata["collision_detected"] = True
        patch.metadata["collision_count"] = len(collisions)

    def detect_collision(self, patch1: Patch, patch2: Patch) -> bool:
        """
        Check if two patches target the same output.

        Args:
            patch1: First patch
            patch2: Second patch

        Returns:
            True if patches collide
        """
        if patch1.output_node == patch2.output_node:
            self.collision_count += 1
            return True
        return False

    def detect_deadlock(self, patch_chain: List[Patch]) -> bool:
        """
        Detect circular routing in patch chain.

        A deadlock occurs when routes form a cycle:
        A -> B -> C -> A

        Args:
            patch_chain: List of patches in a routing chain

        Returns:
            True if deadlock detected
        """
        visited: Set[Tuple[str, str]] = set()

        for patch in patch_chain:
            route = (patch.input_node, patch.output_node)
            if route in visited:
                self.deadlock_count += 1
                return True
            visited.add(route)

        # Also check for transitive cycles
        nodes_visited: Set[str] = set()
        for patch in patch_chain:
            if patch.output_node in nodes_visited:
                # Potential cycle - check if we're routing back to an earlier node
                self.deadlock_count += 1
                return True
            nodes_visited.add(patch.input_node)

        return False

    def detect_deadlock_or_raise(self, patch_chain: List[Patch]) -> None:
        """
        Detect deadlock and raise exception if found.

        Args:
            patch_chain: List of patches to check

        Raises:
            DeadlockDetected: If circular routing is detected
        """
        if self.detect_deadlock(patch_chain):
            routes = [(p.input_node, p.output_node) for p in patch_chain]
            raise DeadlockDetected(routes)

    def create_junction_node(self, patches: List[Patch]) -> Patch:
        """
        Merge colliding patches into a junction node.

        Junction nodes combine multiple input sources into a single routing point.

        Args:
            patches: List of patches to merge

        Returns:
            New junction patch combining all inputs
        """
        if not patches:
            raise ValueError("Cannot create junction from empty patch list")

        # Merge tags from all patches
        merged_tags = list(set(tag for p in patches for tag in p.tags))
        merged_tags.append("JUNCTION+")

        # Use maximum charge
        max_charge = max(p.charge for p in patches)

        # Combine input nodes
        inputs = [p.input_node for p in patches]
        junction_input = f"JUNCTION[{'+'.join(inputs)}]"

        # Create junction patch
        junction = Patch(
            input_node=junction_input,
            output_node=patches[0].output_node,
            tags=merged_tags,
            charge=max_charge,
        )

        junction.metadata["source_patches"] = [p.patch_id for p in patches]
        junction.metadata["junction_type"] = "collision_merge"

        return junction

    def enter_maintenance_mode(self) -> None:
        """
        Enter maintenance mode - pauses all queue operations.

        Used during system recovery procedures.
        """
        self._maintenance_mode = True

    def exit_maintenance_mode(self) -> None:
        """Exit maintenance mode - resumes queue operations."""
        self._maintenance_mode = False

    def is_in_maintenance(self) -> bool:
        """Check if queue is in maintenance mode."""
        return self._maintenance_mode

    def get_queue_state(self) -> Dict[str, Any]:
        """
        Return current queue metrics.

        Returns:
            Dictionary with queue state information
        """
        by_priority = {
            "CRITICAL": 0,
            "HIGH": 0,
            "STANDARD": 0,
            "BACKGROUND": 0,
        }

        for patch in self._heap:
            if patch.priority == Priority.CRITICAL:
                by_priority["CRITICAL"] += 1
            elif patch.priority == Priority.HIGH:
                by_priority["HIGH"] += 1
            elif patch.priority == Priority.STANDARD:
                by_priority["STANDARD"] += 1
            else:
                by_priority["BACKGROUND"] += 1

        return {
            "total_size": len(self._heap),
            "max_size": self.max_size,
            "by_priority": by_priority,
            "priority_distribution": by_priority,  # Alias for CLI compatibility
            "collision_count": self.collision_count,
            "deadlock_count": self.deadlock_count,
            "total_enqueued": self._counter,
            "total_processed": self._processed_count,
            "active_routes": len(self._active_routes),
            "maintenance_mode": self._maintenance_mode,
        }

    def get_patches_by_priority(self, priority: Priority) -> List[Patch]:
        """Get all patches with a specific priority."""
        return [p for p in self._heap if p.priority == priority]

    def get_patches_by_output(self, output_node: str) -> List[Patch]:
        """Get all patches targeting a specific output node."""
        return self._pending_by_output.get(output_node, []).copy()

    def clear(self) -> int:
        """
        Clear the entire queue.

        Returns:
            Number of patches removed
        """
        count = len(self._heap)
        self._heap = []
        self._pending_by_output = {}
        self._active_routes = set()
        return count

    def peek_all(self) -> List[Patch]:
        """
        Get all patches in the queue without removing them.

        Returns:
            List of all patches, sorted by priority
        """
        return sorted(self._heap)

    def to_list(self) -> List[Dict]:
        """Export queue contents as list of dictionaries."""
        return [patch.to_dict() for patch in sorted(self._heap)]


# Global patchbay queue instance
_patchbay_queue: Optional[PatchQueue] = None


def get_patchbay_queue() -> PatchQueue:
    """Get or create global patchbay queue instance."""
    global _patchbay_queue
    if _patchbay_queue is None:
        _patchbay_queue = PatchQueue()
    return _patchbay_queue
