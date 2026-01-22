"""
RE:GE Organ Base - Abstract base class for organ handlers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from rege.core.models import Invocation, Patch, InvocationResult


class OrganHandler(ABC):
    """
    Abstract base class for RE:GE organ handlers.

    Each organ handler must implement:
    - invoke(): Main invocation entry point
    - get_valid_modes(): List of valid processing modes
    - get_output_types(): List of possible output types

    Organ handlers process symbolic invocations and produce results
    that can be routed to other organs or archived.
    """

    def __init__(self):
        """Initialize the organ handler."""
        self._invocation_count = 0
        self._last_invocation: Optional[datetime] = None
        self._state: Dict[str, Any] = {}

    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of this organ."""
        pass

    @property
    def description(self) -> str:
        """Human-readable description of the organ."""
        return "No description available"

    @abstractmethod
    def invoke(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """
        Process an invocation through this organ.

        Args:
            invocation: The parsed invocation request
            patch: The routing patch for this invocation

        Returns:
            Dictionary containing the organ's output
        """
        pass

    @abstractmethod
    def get_valid_modes(self) -> List[str]:
        """
        Get list of valid processing modes for this organ.

        Returns:
            List of mode names
        """
        pass

    @abstractmethod
    def get_output_types(self) -> List[str]:
        """
        Get list of possible output types this organ can produce.

        Returns:
            List of output type names
        """
        pass

    def before_invoke(self, invocation: Invocation, patch: Patch) -> None:
        """
        Hook called before invoke(). Override for pre-processing.

        Args:
            invocation: The invocation to be processed
            patch: The routing patch
        """
        self._invocation_count += 1
        self._last_invocation = datetime.now()

    def after_invoke(
        self,
        invocation: Invocation,
        patch: Patch,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Hook called after invoke(). Override for post-processing.

        Args:
            invocation: The processed invocation
            patch: The routing patch
            result: The result from invoke()

        Returns:
            Potentially modified result dictionary
        """
        return result

    def get_state(self) -> Dict[str, Any]:
        """
        Get current organ state for checkpointing.

        Returns:
            Dictionary of state data
        """
        return {
            "name": self.name,
            "invocation_count": self._invocation_count,
            "last_invocation": self._last_invocation.isoformat() if self._last_invocation else None,
            "state": self._state.copy(),
        }

    def restore_state(self, state: Dict[str, Any]) -> None:
        """
        Restore organ state from checkpoint.

        Args:
            state: State dictionary to restore
        """
        self._invocation_count = state.get("invocation_count", 0)
        if state.get("last_invocation"):
            self._last_invocation = datetime.fromisoformat(state["last_invocation"])
        self._state = state.get("state", {})

    def reset(self) -> None:
        """Reset organ to initial state."""
        self._invocation_count = 0
        self._last_invocation = None
        self._state = {}

    def __call__(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """
        Make the organ callable directly.

        Calls before_invoke, invoke, and after_invoke in sequence.

        Args:
            invocation: The invocation to process
            patch: The routing patch

        Returns:
            Result dictionary
        """
        self.before_invoke(invocation, patch)
        result = self.invoke(invocation, patch)
        return self.after_invoke(invocation, patch, result)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"
