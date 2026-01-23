"""
RE:GE Depth Tracker - Recursion depth management.

Based on: RE-GE_ORG_BODY_08_SOUL_PATCHBAY.md

Maximum Depth Levels:
| Depth Type   | Max Level | When Used              | Exhaustion Behavior               |
|--------------|-----------|------------------------|-----------------------------------|
| STANDARD     | 7         | Normal routing         | Warning, escalate to RITUAL_COURT |
| EXTENDED     | 12        | LAW_LOOP+ flag present | Force termination, INCOMPLETE+    |
| EMERGENCY    | 21        | RITUAL_COURT override  | Force termination, system alert   |
| ABSOLUTE     | 33        | System hard limit      | Panic stop, full state snapshot   |
"""

from typing import Tuple, List, Optional, Dict, Any
from datetime import datetime
from rege.core.constants import DepthLimits
from rege.core.models import Patch
from rege.core.exceptions import DepthLimitExceeded, PanicStop


class DepthAction:
    """Actions to take when depth limits are reached."""
    CONTINUE = "CONTINUE"
    ESCALATE_TO_RITUAL_COURT = "ESCALATE_TO_RITUAL_COURT"
    FORCE_TERMINATE_INCOMPLETE = "FORCE_TERMINATE_INCOMPLETE"
    FORCE_TERMINATE_ALERT = "FORCE_TERMINATE_ALERT"
    PANIC_STOP = "PANIC_STOP"


class DepthTracker:
    """
    Tracks and enforces recursion depth limits for routing operations.

    Limits:
    - STANDARD (7): Normal routing operations
    - EXTENDED (12): When LAW_LOOP+ flag is present
    - EMERGENCY (21): RITUAL_COURT override
    - ABSOLUTE (33): System hard limit - triggers panic stop
    """

    def __init__(self):
        self.depth_log: List[Dict[str, Any]] = []
        self._exhaustion_count = 0
        self._current_depth = 0
        self._max_depth_reached = 0

    @property
    def current_depth(self) -> int:
        """Get the current recursion depth."""
        return self._current_depth

    @property
    def max_depth_reached(self) -> int:
        """Get the maximum depth reached in this session."""
        return self._max_depth_reached

    @property
    def depth_exhaustions(self) -> int:
        """Get the number of depth exhaustion events."""
        return self._exhaustion_count

    def get_limit(self, patch: Patch) -> int:
        """
        Determine depth limit based on patch properties.

        Args:
            patch: The patch to check

        Returns:
            Maximum allowed depth for this patch
        """
        if "EMERGENCY+" in patch.tags:
            return DepthLimits.EMERGENCY
        elif "LAW_LOOP+" in patch.tags:
            return DepthLimits.EXTENDED
        return DepthLimits.STANDARD

    def check_depth(self, patch: Patch) -> Tuple[bool, str]:
        """
        Check if patch exceeds depth limit.

        Args:
            patch: The patch to check

        Returns:
            Tuple of (can_continue: bool, action: str)
        """
        limit = self.get_limit(patch)

        # Absolute limit takes precedence
        if patch.depth >= DepthLimits.ABSOLUTE:
            self._log_exhaustion(patch, DepthLimits.ABSOLUTE, DepthAction.PANIC_STOP)
            return False, DepthAction.PANIC_STOP

        # Emergency limit
        if patch.depth >= DepthLimits.EMERGENCY:
            self._log_exhaustion(patch, DepthLimits.EMERGENCY, DepthAction.FORCE_TERMINATE_ALERT)
            return False, DepthAction.FORCE_TERMINATE_ALERT

        # Dynamic limit based on patch properties
        if patch.depth >= limit:
            if limit == DepthLimits.STANDARD:
                self._log_exhaustion(patch, limit, DepthAction.ESCALATE_TO_RITUAL_COURT)
                return False, DepthAction.ESCALATE_TO_RITUAL_COURT
            else:
                self._log_exhaustion(patch, limit, DepthAction.FORCE_TERMINATE_INCOMPLETE)
                return False, DepthAction.FORCE_TERMINATE_INCOMPLETE

        return True, DepthAction.CONTINUE

    def check_depth_or_raise(self, patch: Patch) -> None:
        """
        Check depth and raise exception if limit exceeded.

        Args:
            patch: The patch to check

        Raises:
            PanicStop: If absolute limit reached
            DepthLimitExceeded: If any depth limit exceeded
        """
        can_continue, action = self.check_depth(patch)

        if not can_continue:
            limit = self.get_limit(patch)

            if action == DepthAction.PANIC_STOP:
                raise PanicStop(
                    f"Absolute depth limit ({DepthLimits.ABSOLUTE}) exceeded",
                    snapshot_id=self._generate_snapshot_id()
                )

            raise DepthLimitExceeded(
                depth=patch.depth,
                limit=limit,
                action=action
            )

    def increment_depth(self, patch: Patch) -> int:
        """
        Increment patch depth counter.

        Args:
            patch: The patch to increment

        Returns:
            New depth value
        """
        patch.depth += 1
        self._current_depth = patch.depth
        if patch.depth > self._max_depth_reached:
            self._max_depth_reached = patch.depth
        return patch.depth

    def reset_depth(self, patch: Patch) -> None:
        """
        Reset patch depth to zero.

        Args:
            patch: The patch to reset
        """
        patch.depth = 0

    def _log_exhaustion(self, patch: Patch, limit: int, action: str) -> None:
        """Log a depth exhaustion event."""
        self._exhaustion_count += 1
        self.depth_log.append({
            "timestamp": datetime.now().isoformat(),
            "patch_id": patch.patch_id,
            "input_node": patch.input_node,
            "output_node": patch.output_node,
            "depth": patch.depth,
            "limit": limit,
            "action": action,
            "tags": patch.tags,
        })

    def _generate_snapshot_id(self) -> str:
        """Generate a snapshot ID for panic situations."""
        return f"PANIC_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def get_exhaustion_count(self) -> int:
        """Get total number of depth exhaustion events."""
        return self._exhaustion_count

    def get_depth_log(self, limit: int = 100) -> List[Dict]:
        """Get recent depth exhaustion log entries."""
        return self.depth_log[-limit:]

    def get_exhaustion_log(self, limit: int = 100) -> List[Dict]:
        """Get recent depth exhaustion log entries (alias for get_depth_log)."""
        return self.depth_log[-limit:]

    def clear_log(self) -> None:
        """Clear the depth log."""
        self.depth_log = []

    def clear_exhaustion_log(self) -> None:
        """Clear the depth exhaustion log (alias for clear_log)."""
        self.depth_log = []
        self._exhaustion_count = 0

    def get_depth_status(self, patch: Patch) -> Dict[str, Any]:
        """
        Get detailed depth status for a patch.

        Args:
            patch: The patch to analyze

        Returns:
            Dictionary with depth status information
        """
        limit = self.get_limit(patch)
        remaining = limit - patch.depth

        return {
            "current_depth": patch.depth,
            "limit": limit,
            "limit_type": self._get_limit_type(limit),
            "remaining": max(0, remaining),
            "percentage_used": min(100, (patch.depth / limit) * 100),
            "at_risk": remaining <= 2,
            "tags_affecting_limit": [t for t in patch.tags if t in ("EMERGENCY+", "LAW_LOOP+")],
        }

    def _get_limit_type(self, limit: int) -> str:
        """Get human-readable limit type name."""
        if limit == DepthLimits.STANDARD:
            return "STANDARD"
        elif limit == DepthLimits.EXTENDED:
            return "EXTENDED"
        elif limit == DepthLimits.EMERGENCY:
            return "EMERGENCY"
        else:
            return "ABSOLUTE"


# Global depth tracker instance
_depth_tracker: Optional[DepthTracker] = None


def get_depth_tracker() -> DepthTracker:
    """Get or create global depth tracker instance."""
    global _depth_tracker
    if _depth_tracker is None:
        _depth_tracker = DepthTracker()
    return _depth_tracker
