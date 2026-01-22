"""
RE:GE Exceptions - Custom exception classes for the symbolic operating system.
"""


class RegeError(Exception):
    """Base exception for all RE:GE errors."""
    pass


class InvocationError(RegeError):
    """Error during invocation parsing or execution."""
    pass


class RoutingError(RegeError):
    """Error during patch routing through Soul Patchbay."""
    pass


class DepthLimitExceeded(RoutingError):
    """Recursion depth limit exceeded during routing."""

    def __init__(self, depth: int, limit: int, action: str, message: str = None):
        self.depth = depth
        self.limit = limit
        self.action = action
        super().__init__(
            message or f"Depth limit exceeded: {depth} >= {limit}. Action: {action}"
        )


class DeadlockDetected(RoutingError):
    """Circular routing detected causing deadlock."""

    def __init__(self, route_chain: list, message: str = None):
        self.route_chain = route_chain
        super().__init__(
            message or f"Deadlock detected in routing chain: {route_chain}"
        )


class QueueOverflow(RoutingError):
    """Patch queue has exceeded maximum capacity."""

    def __init__(self, current_size: int, max_size: int, message: str = None):
        self.current_size = current_size
        self.max_size = max_size
        super().__init__(
            message or f"Queue overflow: {current_size} >= {max_size}"
        )


class FusionError(RegeError):
    """Error during FUSE01 protocol execution."""
    pass


class FusionNotEligible(FusionError):
    """Fragments not eligible for fusion."""

    def __init__(self, reason: str, fragments: list = None):
        self.reason = reason
        self.fragments = fragments or []
        super().__init__(f"Fusion not eligible: {reason}")


class FusionRollbackFailed(FusionError):
    """Fusion rollback operation failed."""

    def __init__(self, fused_id: str, reason: str):
        self.fused_id = fused_id
        self.reason = reason
        super().__init__(f"Rollback failed for {fused_id}: {reason}")


class RecoveryError(RegeError):
    """Error during system recovery protocol."""
    pass


class CheckpointNotFound(RecoveryError):
    """Requested checkpoint does not exist."""

    def __init__(self, checkpoint_id: str):
        self.checkpoint_id = checkpoint_id
        super().__init__(f"Checkpoint not found: {checkpoint_id}")


class RecoveryAuthorizationRequired(RecoveryError):
    """Recovery operation requires RITUAL_COURT authorization."""

    def __init__(self, operation: str, reason: str):
        self.operation = operation
        self.reason = reason
        super().__init__(f"Authorization required for {operation}: {reason}")


class OrganNotFoundError(RegeError):
    """Requested organ does not exist in the registry."""

    def __init__(self, organ_name: str, available_organs: list = None):
        self.organ_name = organ_name
        self.available_organs = available_organs or []
        super().__init__(
            f"Organ not found: {organ_name}. "
            f"Available: {', '.join(self.available_organs)}"
        )


class OrganExecutionError(RegeError):
    """Error during organ handler execution."""

    def __init__(self, organ_name: str, error: Exception):
        self.organ_name = organ_name
        self.original_error = error
        super().__init__(f"Error in {organ_name}: {error}")


class ValidationError(RegeError):
    """Validation error for invocations, fragments, or other entities."""

    def __init__(self, errors: list):
        self.errors = errors
        super().__init__(f"Validation failed: {'; '.join(errors)}")


class InvalidModeError(ValidationError):
    """Invalid mode specified for organ."""

    def __init__(self, organ: str, mode: str, valid_modes: list):
        self.organ = organ
        self.mode = mode
        self.valid_modes = valid_modes
        super().__init__([
            f"Invalid mode '{mode}' for organ {organ}. "
            f"Valid modes: {', '.join(valid_modes)}"
        ])


class InvalidDepthError(ValidationError):
    """Invalid depth level specified."""

    def __init__(self, depth: str, valid_depths: list):
        self.depth = depth
        self.valid_depths = valid_depths
        super().__init__([
            f"Invalid depth '{depth}'. Valid depths: {', '.join(valid_depths)}"
        ])


class PersistenceError(RegeError):
    """Error during file persistence operations."""
    pass


class ArchiveCorrupted(PersistenceError):
    """Archive file is corrupted or malformed."""

    def __init__(self, file_path: str, reason: str):
        self.file_path = file_path
        self.reason = reason
        super().__init__(f"Archive corrupted: {file_path} - {reason}")


class LawViolationError(RegeError):
    """A system law has been violated."""

    def __init__(self, law_id: str, law_name: str, violation_description: str):
        self.law_id = law_id
        self.law_name = law_name
        self.violation_description = violation_description
        super().__init__(
            f"Law violation - {law_id} ({law_name}): {violation_description}"
        )


class PanicStop(RegeError):
    """System panic stop triggered - requires manual intervention."""

    def __init__(self, reason: str, snapshot_id: str = None):
        self.reason = reason
        self.snapshot_id = snapshot_id
        super().__init__(
            f"PANIC STOP: {reason}. "
            f"Snapshot: {snapshot_id or 'none'}. "
            "Manual intervention required."
        )
