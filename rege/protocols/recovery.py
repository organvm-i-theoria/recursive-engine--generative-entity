"""
RE:GE System Recovery Protocol - System recovery and rollback.

Based on: RE-GE_PROTOCOL_SYSTEM_RECOVERY.md

The System Recovery Protocol governs:
- State snapshots and checkpoints
- Full and partial rollback
- Data reconstruction
- Emergency stop
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from rege.core.models import StateSnapshot, RecoveryMode, RecoveryTrigger
from rege.core.exceptions import (
    RecoveryError,
    CheckpointNotFound,
    RecoveryAuthorizationRequired,
    PanicStop,
)


class SystemRecoveryProtocol:
    """
    RE:GE System Recovery Protocol implementation.

    Recovery triggers:
    - CORRUPTION: Data integrity failure
    - DEADLOCK: Circular routing unresolved
    - DATA_LOSS: Archive records missing
    - DEPTH_PANIC: Absolute recursion limit reached
    - MANUAL: User-initiated recovery

    Recovery modes:
    - full_rollback: Restore to checkpoint
    - partial: Restore specific organs
    - reconstruct: Rebuild from echoes/archives
    - emergency_stop: Halt all operations
    """

    AUTHORIZATION_THRESHOLD_HOURS = 24

    def __init__(self):
        self.checkpoints: Dict[str, StateSnapshot] = {}
        self.recovery_log: List[Dict] = []
        self._snapshot_counter = 0
        self._halted = False

    def capture_snapshot(
        self,
        trigger: RecoveryTrigger,
        system_state: Dict[str, Any],
    ) -> StateSnapshot:
        """
        Capture current system state.

        Args:
            trigger: What triggered the snapshot
            system_state: Current state data

        Returns:
            The created StateSnapshot
        """
        self._snapshot_counter += 1
        now = datetime.now()

        snapshot = StateSnapshot(
            snapshot_id=f"SNAP_{now.strftime('%Y%m%d_%H%M%S')}_{self._snapshot_counter:03d}",
            timestamp=now,
            trigger=trigger,
            system_state=system_state.get("metrics", {}),
            organ_states=system_state.get("organs", {}),
            pending_operations=system_state.get("pending", []),
            error_log=system_state.get("errors", []),
            recovery_point=self._find_last_stable_checkpoint(),
        )

        self.checkpoints[snapshot.snapshot_id] = snapshot
        return snapshot

    def full_rollback(
        self,
        checkpoint_id: str,
        confirm: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute full system rollback to checkpoint.

        Args:
            checkpoint_id: ID of checkpoint to restore
            confirm: Must be True to execute

        Returns:
            Rollback result

        Raises:
            CheckpointNotFound: If checkpoint doesn't exist
            RecoveryAuthorizationRequired: If requires court authorization
        """
        if not confirm:
            return {
                "status": "confirmation_required",
                "message": "Set confirm=True to execute full rollback",
            }

        if checkpoint_id not in self.checkpoints:
            raise CheckpointNotFound(checkpoint_id)

        checkpoint = self.checkpoints[checkpoint_id]

        # Check if requires authorization
        if self.requires_ritual_court(RecoveryMode.FULL_ROLLBACK, checkpoint_id):
            raise RecoveryAuthorizationRequired(
                "full_rollback",
                f"Rollback older than {self.AUTHORIZATION_THRESHOLD_HOURS} hours"
            )

        result = {
            "status": "success",
            "mode": "full_rollback",
            "checkpoint": checkpoint_id,
            "restored_at": datetime.now().isoformat(),
            "organs_restored": list(checkpoint.organ_states.keys()),
            "data_age": str(datetime.now() - checkpoint.timestamp),
        }

        self._log_recovery(result)
        return result

    def partial_recovery(
        self,
        organs: List[str],
        checkpoint_id: str,
    ) -> Dict[str, Any]:
        """
        Execute partial organ recovery.

        Args:
            organs: List of organ names to restore
            checkpoint_id: ID of checkpoint to use

        Returns:
            Recovery result

        Raises:
            CheckpointNotFound: If checkpoint doesn't exist
        """
        if checkpoint_id not in self.checkpoints:
            raise CheckpointNotFound(checkpoint_id)

        checkpoint = self.checkpoints[checkpoint_id]

        # Filter to requested organs
        restored_organs = {
            organ: state
            for organ, state in checkpoint.organ_states.items()
            if organ in organs
        }

        not_found = [o for o in organs if o not in checkpoint.organ_states]

        result = {
            "status": "success",
            "mode": "partial",
            "checkpoint": checkpoint_id,
            "restored_at": datetime.now().isoformat(),
            "organs_restored": list(restored_organs.keys()),
            "organs_not_found": not_found,
            "organs_unchanged": [
                o for o in checkpoint.organ_states
                if o not in organs
            ],
        }

        self._log_recovery(result)
        return result

    def reconstruct_data(
        self,
        target: str,
        sources: List[str],
    ) -> Dict[str, Any]:
        """
        Attempt data reconstruction from available sources.

        Args:
            target: What to reconstruct (fragment ID, data type, etc.)
            sources: Where to look (ECHO_SHELL, ARCHIVE_ORDER, etc.)

        Returns:
            Reconstruction result
        """
        # Simulate reconstruction
        result = {
            "status": "attempted",
            "mode": "reconstruct",
            "target": target,
            "sources_searched": sources,
            "reconstructed_at": datetime.now().isoformat(),
            "recovery_quality": "partial",  # full, partial, failed
            "tags_applied": ["RECOVERED+", "RECONSTRUCTED+"],
            "warnings": [
                "Reconstructed data may be incomplete",
                "Original metadata may be lost",
            ],
        }

        self._log_recovery(result)
        return result

    def emergency_stop(self, reason: str) -> Dict[str, Any]:
        """
        Execute emergency system halt.

        Args:
            reason: Reason for emergency stop

        Returns:
            Stop result
        """
        self._halted = True

        # Capture panic snapshot
        panic_snapshot = self.capture_snapshot(
            RecoveryTrigger.MANUAL,
            {
                "metrics": {"emergency": True, "halted": True},
                "organs": {},
                "pending": [],
                "errors": [reason],
            }
        )

        result = {
            "status": "halted",
            "mode": "emergency_stop",
            "reason": reason,
            "halted_at": datetime.now().isoformat(),
            "panic_snapshot": panic_snapshot.snapshot_id,
            "requires_manual_intervention": True,
        }

        self._log_recovery(result)
        return result

    def resume_from_halt(self, confirm: bool = False) -> Dict[str, Any]:
        """
        Resume from emergency halt.

        Args:
            confirm: Must be True to resume

        Returns:
            Resume result
        """
        if not self._halted:
            return {"status": "not_halted", "message": "System is not halted"}

        if not confirm:
            return {
                "status": "confirmation_required",
                "message": "Set confirm=True to resume from halt",
            }

        self._halted = False

        return {
            "status": "resumed",
            "resumed_at": datetime.now().isoformat(),
            "recommendation": "Run partial_recovery to restore organ states",
        }

    def requires_ritual_court(
        self,
        mode: RecoveryMode,
        checkpoint_id: Optional[str] = None,
    ) -> bool:
        """
        Check if recovery requires RITUAL_COURT authorization.

        Args:
            mode: Recovery mode
            checkpoint_id: Optional checkpoint for age check

        Returns:
            True if authorization required
        """
        if mode == RecoveryMode.FULL_ROLLBACK and checkpoint_id:
            checkpoint = self.checkpoints.get(checkpoint_id)
            if checkpoint:
                age = datetime.now() - checkpoint.timestamp
                return age > timedelta(hours=self.AUTHORIZATION_THRESHOLD_HOURS)

        return False

    def _find_last_stable_checkpoint(self) -> Optional[str]:
        """Find most recent stable (manual) checkpoint."""
        stable = [
            (id, snap) for id, snap in self.checkpoints.items()
            if snap.trigger == RecoveryTrigger.MANUAL
        ]
        if stable:
            return max(stable, key=lambda x: x[1].timestamp)[0]
        return None

    def _log_recovery(self, result: Dict[str, Any]) -> None:
        """Log recovery operation."""
        self.recovery_log.append({
            **result,
            "logged_at": datetime.now().isoformat(),
        })

    def is_halted(self) -> bool:
        """Check if system is halted."""
        return self._halted

    def get_checkpoint(self, checkpoint_id: str) -> Optional[StateSnapshot]:
        """Get a checkpoint by ID."""
        return self.checkpoints.get(checkpoint_id)

    def get_all_checkpoints(self) -> List[StateSnapshot]:
        """Get all checkpoints."""
        return list(self.checkpoints.values())

    def get_recovery_log(self, limit: int = 50) -> List[Dict]:
        """Get recent recovery log entries."""
        return self.recovery_log[-limit:]

    def create_manual_checkpoint(
        self,
        name: str,
        system_state: Dict[str, Any],
    ) -> StateSnapshot:
        """
        Create a manual checkpoint with a custom name.

        Args:
            name: Descriptive name for checkpoint
            system_state: Current state data

        Returns:
            The created checkpoint
        """
        snapshot = self.capture_snapshot(RecoveryTrigger.MANUAL, system_state)

        # Add name to metadata
        snapshot.system_state["checkpoint_name"] = name

        return snapshot


# Global recovery protocol instance
_recovery_protocol: Optional[SystemRecoveryProtocol] = None


def get_recovery_protocol() -> SystemRecoveryProtocol:
    """Get or create global recovery protocol instance."""
    global _recovery_protocol
    if _recovery_protocol is None:
        _recovery_protocol = SystemRecoveryProtocol()
    return _recovery_protocol
