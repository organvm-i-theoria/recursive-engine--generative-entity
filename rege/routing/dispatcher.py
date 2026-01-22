"""
RE:GE Dispatcher - Routes invocations through the system.

The Dispatcher coordinates:
- Parsing invocations
- Validating against organ registry
- Creating patches and enqueueing
- Invoking organ handlers
- Formatting and logging results
"""

import time
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

from rege.core.models import Invocation, Patch, InvocationResult, DepthLevel
from rege.core.constants import Priority, get_priority
from rege.core.exceptions import (
    InvocationError,
    RoutingError,
    OrganNotFoundError,
    OrganExecutionError,
    DepthLimitExceeded,
)
from rege.parser.invocation_parser import InvocationParser
from rege.parser.validator import InvocationValidator, InvocationLogger
from rege.routing.patchbay import PatchQueue, get_patchbay_queue
from rege.routing.depth_tracker import DepthTracker, get_depth_tracker, DepthAction


class Dispatcher:
    """
    Central dispatcher for RE:GE invocations.

    Lifecycle:
    INPUT -> PARSE -> VALIDATE -> QUEUE -> EXECUTE -> FORMAT -> LOG
    """

    def __init__(
        self,
        queue: Optional[PatchQueue] = None,
        depth_tracker: Optional[DepthTracker] = None,
    ):
        """
        Initialize the dispatcher.

        Args:
            queue: Optional custom queue, defaults to global patchbay
            depth_tracker: Optional custom depth tracker
        """
        self.parser = InvocationParser()
        self.validator = InvocationValidator()
        self.logger = InvocationLogger()
        self.queue = queue or get_patchbay_queue()
        self.depth_tracker = depth_tracker or get_depth_tracker()

        # Organ handler registry
        self._handlers: Dict[str, Callable] = {}

        # Execution log
        self._execution_log: List[Dict] = []

    def register_handler(self, organ_name: str, handler: Callable) -> None:
        """
        Register a handler function for an organ.

        Args:
            organ_name: Name of the organ
            handler: Callable that takes (Invocation, Patch) and returns result
        """
        self._handlers[organ_name.upper()] = handler

    def dispatch(self, text: str) -> InvocationResult:
        """
        Dispatch a single invocation from raw text.

        Args:
            text: Raw invocation text with ritual syntax

        Returns:
            InvocationResult with execution outcome

        Raises:
            InvocationError: If parsing or validation fails
        """
        start_time = time.time()

        # 1. PARSE
        invocation = self.parser.parse(text)
        if not invocation:
            raise InvocationError(f"Failed to parse invocation: {text[:100]}...")

        # 2. VALIDATE
        self.validator.validate_or_raise(invocation)

        # 3. QUEUE
        patch = self._create_patch(invocation)
        self.queue.enqueue(patch)

        # 4. EXECUTE
        try:
            result = self._execute(invocation, patch)
        except Exception as e:
            result = self._create_error_result(invocation, e, start_time)

        # 5. FORMAT (handled by result object)

        # 6. LOG
        execution_time_ms = int((time.time() - start_time) * 1000)
        self.logger.log(invocation, result.output, execution_time_ms, result.status)

        return result

    def dispatch_chain(self, text: str) -> List[InvocationResult]:
        """
        Dispatch multiple chained invocations.

        Args:
            text: Text containing one or more invocations

        Returns:
            List of InvocationResults
        """
        invocations = self.parser.parse_chain(text)
        results = []

        for invocation in invocations:
            try:
                # Validate
                self.validator.validate_or_raise(invocation)

                # Create and enqueue patch
                patch = self._create_patch(invocation)
                self.queue.enqueue(patch)

                # Execute
                start_time = time.time()
                result = self._execute(invocation, patch)
                results.append(result)

            except Exception as e:
                start_time = time.time()
                results.append(self._create_error_result(invocation, e, start_time))

        return results

    def process_queue(self, max_items: int = 10) -> List[InvocationResult]:
        """
        Process items from the queue.

        Args:
            max_items: Maximum number of items to process

        Returns:
            List of results from processed items
        """
        results = []

        for _ in range(max_items):
            patch = self.queue.dequeue()
            if not patch:
                break

            # Reconstruct invocation from patch
            invocation = self._patch_to_invocation(patch)

            try:
                start_time = time.time()
                result = self._execute(invocation, patch)
                results.append(result)
            except Exception as e:
                start_time = time.time()
                results.append(self._create_error_result(invocation, e, start_time))

        return results

    def _create_patch(self, invocation: Invocation) -> Patch:
        """Create a Patch from an Invocation."""
        return Patch(
            input_node=invocation.symbol or "SELF",
            output_node=invocation.organ,
            tags=invocation.flags,
            charge=invocation.charge,
            metadata={
                "invocation_id": invocation.invocation_id,
                "mode": invocation.mode,
                "depth": invocation.depth.value,
                "expect": invocation.expect,
            }
        )

    def _patch_to_invocation(self, patch: Patch) -> Invocation:
        """Reconstruct an Invocation from a Patch."""
        metadata = patch.metadata
        depth_str = metadata.get("depth", "standard")

        if depth_str == "light":
            depth = DepthLevel.LIGHT
        elif depth_str == "full spiral":
            depth = DepthLevel.FULL_SPIRAL
        else:
            depth = DepthLevel.STANDARD

        return Invocation(
            organ=patch.output_node,
            symbol=patch.input_node,
            mode=metadata.get("mode", "default"),
            depth=depth,
            expect=metadata.get("expect", "default_output"),
            flags=patch.tags,
            charge=patch.charge,
            invocation_id=metadata.get("invocation_id"),
        )

    def _execute(self, invocation: Invocation, patch: Patch) -> InvocationResult:
        """
        Execute an invocation through its organ handler.

        Args:
            invocation: The parsed invocation
            patch: The routing patch

        Returns:
            InvocationResult with execution outcome
        """
        start_time = time.time()
        organ_name = invocation.organ.upper()

        # Check depth limits
        can_continue, action = self.depth_tracker.check_depth(patch)
        if not can_continue:
            return self._handle_depth_limit(invocation, patch, action, start_time)

        # Increment depth for this execution
        self.depth_tracker.increment_depth(patch)

        # Find handler
        handler = self._handlers.get(organ_name)

        if handler:
            try:
                output = handler(invocation, patch)
                status = "success"
                errors = []
            except Exception as e:
                output = None
                status = "failed"
                errors = [str(e)]
        else:
            # No handler registered - return default response
            output = self._default_handler(invocation, patch)
            status = "success"
            errors = []

        # Mark route complete
        self.queue.complete_route(patch)

        execution_time_ms = int((time.time() - start_time) * 1000)

        return InvocationResult(
            invocation_id=invocation.invocation_id,
            organ=organ_name,
            status=status,
            output=output,
            output_type=invocation.expect,
            execution_time_ms=execution_time_ms,
            errors=errors,
        )

    def _default_handler(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Default handler when no specific handler is registered."""
        return {
            "message": f"Invocation received by {invocation.organ}",
            "symbol": invocation.symbol,
            "mode": invocation.mode,
            "depth": invocation.depth.value,
            "expect": invocation.expect,
            "charge": invocation.charge,
            "flags": invocation.flags,
            "status": "processed",
            "note": "No specific handler registered for this organ",
        }

    def _handle_depth_limit(
        self,
        invocation: Invocation,
        patch: Patch,
        action: str,
        start_time: float
    ) -> InvocationResult:
        """Handle depth limit exceeded."""
        execution_time_ms = int((time.time() - start_time) * 1000)

        side_effects = []
        if action == DepthAction.ESCALATE_TO_RITUAL_COURT:
            status = "escalated"
            side_effects.append({
                "type": "escalation",
                "target": "RITUAL_COURT",
                "reason": "depth_limit_exceeded",
            })
        elif action == DepthAction.FORCE_TERMINATE_INCOMPLETE:
            status = "incomplete"
            side_effects.append({
                "type": "fragment_created",
                "tag": "INCOMPLETE+",
                "target": "ECHO_SHELL",
            })
        elif action == DepthAction.PANIC_STOP:
            status = "panic"
            side_effects.append({
                "type": "system_halt",
                "reason": "absolute_depth_limit",
            })
        else:
            status = "terminated"

        return InvocationResult(
            invocation_id=invocation.invocation_id,
            organ=invocation.organ,
            status=status,
            output={"action": action, "depth": patch.depth},
            output_type="depth_limit_response",
            execution_time_ms=execution_time_ms,
            errors=[f"Depth limit action: {action}"],
            side_effects=side_effects,
        )

    def _create_error_result(
        self,
        invocation: Invocation,
        error: Exception,
        start_time: float
    ) -> InvocationResult:
        """Create an error result for failed executions."""
        execution_time_ms = int((time.time() - start_time) * 1000)

        return InvocationResult(
            invocation_id=invocation.invocation_id if invocation else "UNKNOWN",
            organ=invocation.organ if invocation else "UNKNOWN",
            status="failed",
            output=None,
            output_type="error",
            execution_time_ms=execution_time_ms,
            errors=[str(error)],
        )

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        return self.queue.get_queue_state()

    def get_execution_log(self, limit: int = 50) -> List[Dict]:
        """Get recent execution log entries."""
        return self.logger.get_recent(limit)

    def get_handler_names(self) -> List[str]:
        """Get list of registered handler names."""
        return list(self._handlers.keys())


# Global dispatcher instance
_dispatcher: Optional[Dispatcher] = None


def get_dispatcher() -> Dispatcher:
    """Get or create global dispatcher instance."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = Dispatcher()
    return _dispatcher


def invoke(text: str) -> InvocationResult:
    """
    Quick invocation dispatch.

    Args:
        text: Raw invocation text

    Returns:
        InvocationResult
    """
    return get_dispatcher().dispatch(text)
