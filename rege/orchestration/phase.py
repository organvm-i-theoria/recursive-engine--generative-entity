"""
RE:GE Orchestration - Phase and Branch definitions.

Phases represent individual steps in a ritual chain.
Branches enable conditional flow between phases.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
import uuid


class PhaseStatus(Enum):
    """Status of a phase execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    COMPENSATED = "compensated"


@dataclass
class PhaseResult:
    """Result of a phase execution."""

    phase_name: str
    status: PhaseStatus
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: int = 0
    executed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    branch_taken: Optional[str] = None
    compensation_triggered: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "phase_name": self.phase_name,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "executed_at": self.executed_at,
            "branch_taken": self.branch_taken,
            "compensation_triggered": self.compensation_triggered,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PhaseResult":
        """Create from dictionary."""
        return cls(
            phase_name=data["phase_name"],
            status=PhaseStatus(data["status"]),
            output=data.get("output"),
            error=data.get("error"),
            duration_ms=data.get("duration_ms", 0),
            executed_at=data.get("executed_at", datetime.now().isoformat()),
            branch_taken=data.get("branch_taken"),
            compensation_triggered=data.get("compensation_triggered", False),
        )


@dataclass
class Branch:
    """
    Conditional branch in a ritual chain.

    Branches enable conditional routing based on phase results.
    """

    name: str
    condition: Callable[[Dict[str, Any]], bool]
    target_phase: str
    priority: int = 0
    description: str = ""

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate if this branch should be taken."""
        try:
            return self.condition(context)
        except Exception:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (without callable)."""
        return {
            "name": self.name,
            "target_phase": self.target_phase,
            "priority": self.priority,
            "description": self.description,
        }


@dataclass
class Phase:
    """
    A single phase in a ritual chain.

    Phases represent individual steps that invoke organs with specific modes.
    """

    name: str
    organ: str
    mode: str
    description: str = ""
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    branches: List[Branch] = field(default_factory=list)
    compensation: Optional["Phase"] = None
    timeout_ms: int = 30000
    required: bool = True
    input_mapping: Optional[Dict[str, str]] = None
    output_mapping: Optional[Dict[str, str]] = None

    def __post_init__(self):
        """Validate phase configuration."""
        if not self.name:
            raise ValueError("Phase name is required")
        if not self.organ:
            raise ValueError("Phase organ is required")
        if not self.mode:
            raise ValueError("Phase mode is required")

    def should_execute(self, context: Dict[str, Any]) -> bool:
        """Check if this phase should execute given the context."""
        if self.condition is None:
            return True
        try:
            return self.condition(context)
        except Exception:
            return False

    def select_branch(self, context: Dict[str, Any]) -> Optional[Branch]:
        """Select the first matching branch based on context."""
        # Sort branches by priority (higher first)
        sorted_branches = sorted(self.branches, key=lambda b: b.priority, reverse=True)

        for branch in sorted_branches:
            if branch.evaluate(context):
                return branch

        return None

    def get_input(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get input for this phase from context using input_mapping."""
        if not self.input_mapping:
            return context.copy()

        mapped_input = {}
        for phase_key, context_key in self.input_mapping.items():
            if context_key in context:
                mapped_input[phase_key] = context[context_key]

        return mapped_input

    def map_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Map phase output to context keys using output_mapping."""
        if not self.output_mapping:
            return output

        mapped_output = {}
        for output_key, context_key in self.output_mapping.items():
            if output_key in output:
                mapped_output[context_key] = output[output_key]

        return mapped_output

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "organ": self.organ,
            "mode": self.mode,
            "description": self.description,
            "branches": [b.to_dict() for b in self.branches],
            "compensation": self.compensation.to_dict() if self.compensation else None,
            "timeout_ms": self.timeout_ms,
            "required": self.required,
            "input_mapping": self.input_mapping,
            "output_mapping": self.output_mapping,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Phase":
        """Create from dictionary (note: callables not restored)."""
        compensation = None
        if data.get("compensation"):
            compensation = cls.from_dict(data["compensation"])

        return cls(
            name=data["name"],
            organ=data["organ"],
            mode=data["mode"],
            description=data.get("description", ""),
            branches=[],  # Branches with callables cannot be restored
            compensation=compensation,
            timeout_ms=data.get("timeout_ms", 30000),
            required=data.get("required", True),
            input_mapping=data.get("input_mapping"),
            output_mapping=data.get("output_mapping"),
        )


# Common condition helpers
def charge_condition(min_charge: int = 0, max_charge: int = 100) -> Callable:
    """Create a condition that checks charge is within range."""

    def condition(context: Dict[str, Any]) -> bool:
        charge = context.get("charge", 50)
        return min_charge <= charge <= max_charge

    return condition


def tag_condition(required_tag: str) -> Callable:
    """Create a condition that checks for a required tag."""

    def condition(context: Dict[str, Any]) -> bool:
        tags = context.get("tags", [])
        return required_tag in tags

    return condition


def verdict_condition(expected_ruling: str) -> Callable:
    """Create a condition that checks verdict ruling."""

    def condition(context: Dict[str, Any]) -> bool:
        verdict = context.get("verdict", {})
        return verdict.get("ruling") == expected_ruling

    return condition


def status_condition(expected_status: str) -> Callable:
    """Create a condition that checks status."""

    def condition(context: Dict[str, Any]) -> bool:
        return context.get("status") == expected_status

    return condition


def has_key_condition(key: str) -> Callable:
    """Create a condition that checks for a key in context."""

    def condition(context: Dict[str, Any]) -> bool:
        return key in context

    return condition


def combined_condition(*conditions: Callable, mode: str = "and") -> Callable:
    """Combine multiple conditions with AND or OR logic."""

    def condition(context: Dict[str, Any]) -> bool:
        results = [c(context) for c in conditions]
        if mode == "and":
            return all(results)
        elif mode == "or":
            return any(results)
        return False

    return condition
