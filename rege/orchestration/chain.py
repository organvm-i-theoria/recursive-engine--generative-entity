"""
RE:GE Orchestration - RitualChain and ChainExecution.

RitualChain defines a multi-step workflow.
ChainExecution tracks execution history and results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from rege.orchestration.phase import Phase, PhaseResult, PhaseStatus, Branch


class ChainStatus(Enum):
    """Status of a chain execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    COMPENSATING = "compensating"


@dataclass
class ChainExecution:
    """
    Tracks execution of a ritual chain.

    Records all phase results, branches taken, and timing.
    """

    execution_id: str = ""
    chain_name: str = ""
    status: ChainStatus = ChainStatus.PENDING
    started_at: str = ""
    completed_at: Optional[str] = None
    phase_results: List[PhaseResult] = field(default_factory=list)
    current_phase: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    escalations: List[str] = field(default_factory=list)
    compensations_executed: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def __post_init__(self):
        """Initialize execution tracking."""
        if not self.execution_id:
            self.execution_id = f"exec_{uuid.uuid4().hex[:12]}"
        if not self.started_at:
            self.started_at = datetime.now().isoformat()

    def add_phase_result(self, result: PhaseResult) -> None:
        """Add a phase result to the execution."""
        self.phase_results.append(result)

    def mark_running(self, phase_name: str) -> None:
        """Mark execution as running with current phase."""
        self.status = ChainStatus.RUNNING
        self.current_phase = phase_name

    def mark_completed(self) -> None:
        """Mark execution as completed."""
        self.status = ChainStatus.COMPLETED
        self.completed_at = datetime.now().isoformat()
        self.current_phase = None

    def mark_failed(self, error: str) -> None:
        """Mark execution as failed."""
        self.status = ChainStatus.FAILED
        self.completed_at = datetime.now().isoformat()
        self.error = error

    def mark_paused(self) -> None:
        """Mark execution as paused."""
        self.status = ChainStatus.PAUSED

    def mark_compensating(self) -> None:
        """Mark execution as compensating."""
        self.status = ChainStatus.COMPENSATING

    def add_escalation(self, escalation_type: str) -> None:
        """Record an escalation event."""
        self.escalations.append(escalation_type)

    def add_compensation(self, phase_name: str) -> None:
        """Record a compensation execution."""
        self.compensations_executed.append(phase_name)

    def get_duration_ms(self) -> int:
        """Get total execution duration in milliseconds."""
        start = datetime.fromisoformat(self.started_at)
        end = datetime.fromisoformat(self.completed_at) if self.completed_at else datetime.now()
        return int((end - start).total_seconds() * 1000)

    def get_phase_count(self) -> Dict[str, int]:
        """Get count of phases by status."""
        counts = {status.value: 0 for status in PhaseStatus}
        for result in self.phase_results:
            counts[result.status.value] += 1
        return counts

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "execution_id": self.execution_id,
            "chain_name": self.chain_name,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "phase_results": [r.to_dict() for r in self.phase_results],
            "current_phase": self.current_phase,
            "context": self.context,
            "escalations": self.escalations,
            "compensations_executed": self.compensations_executed,
            "error": self.error,
            "duration_ms": self.get_duration_ms(),
            "phase_counts": self.get_phase_count(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChainExecution":
        """Create from dictionary."""
        execution = cls(
            execution_id=data["execution_id"],
            chain_name=data["chain_name"],
            status=ChainStatus(data["status"]),
            started_at=data["started_at"],
            completed_at=data.get("completed_at"),
            current_phase=data.get("current_phase"),
            context=data.get("context", {}),
            escalations=data.get("escalations", []),
            compensations_executed=data.get("compensations_executed", []),
            error=data.get("error"),
        )

        for result_data in data.get("phase_results", []):
            execution.phase_results.append(PhaseResult.from_dict(result_data))

        return execution


@dataclass
class RitualChain:
    """
    A multi-step ritual workflow.

    Chains define a sequence of phases with optional branching and compensation.
    """

    name: str
    description: str = ""
    phases: List[Phase] = field(default_factory=list)
    entry_phase: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate chain configuration."""
        if not self.name:
            raise ValueError("Chain name is required")

    def add_phase(self, phase: Phase) -> "RitualChain":
        """Add a phase to the chain."""
        # Check for duplicate names
        if any(p.name == phase.name for p in self.phases):
            raise ValueError(f"Phase '{phase.name}' already exists in chain")

        self.phases.append(phase)

        # Set entry phase if first
        if len(self.phases) == 1 and not self.entry_phase:
            self.entry_phase = phase.name

        return self

    def remove_phase(self, phase_name: str) -> bool:
        """Remove a phase from the chain."""
        for i, phase in enumerate(self.phases):
            if phase.name == phase_name:
                self.phases.pop(i)
                # Clear entry phase if removed
                if self.entry_phase == phase_name:
                    self.entry_phase = self.phases[0].name if self.phases else None
                return True
        return False

    def get_phase(self, name: str) -> Optional[Phase]:
        """Get a phase by name."""
        for phase in self.phases:
            if phase.name == name:
                return phase
        return None

    def get_entry_phase(self) -> Optional[Phase]:
        """Get the entry phase of the chain."""
        if self.entry_phase:
            return self.get_phase(self.entry_phase)
        return self.phases[0] if self.phases else None

    def get_next_phase(self, current_phase_name: str) -> Optional[Phase]:
        """Get the next phase in sequence (if no branch taken)."""
        for i, phase in enumerate(self.phases):
            if phase.name == current_phase_name:
                if i + 1 < len(self.phases):
                    return self.phases[i + 1]
                return None
        return None

    def add_branch(
        self,
        from_phase: str,
        branch: Branch,
    ) -> "RitualChain":
        """Add a branch to a phase."""
        phase = self.get_phase(from_phase)
        if not phase:
            raise ValueError(f"Phase '{from_phase}' not found")

        # Validate target phase exists
        if not self.get_phase(branch.target_phase):
            raise ValueError(f"Target phase '{branch.target_phase}' not found")

        phase.branches.append(branch)
        return self

    def set_compensation(
        self,
        phase_name: str,
        compensation: Phase,
    ) -> "RitualChain":
        """Set compensation for a phase."""
        phase = self.get_phase(phase_name)
        if not phase:
            raise ValueError(f"Phase '{phase_name}' not found")

        phase.compensation = compensation
        return self

    def validate(self) -> Dict[str, Any]:
        """Validate the chain configuration."""
        errors = []
        warnings = []

        # Check for phases
        if not self.phases:
            errors.append("Chain has no phases")

        # Check entry phase
        if self.entry_phase and not self.get_phase(self.entry_phase):
            errors.append(f"Entry phase '{self.entry_phase}' not found")

        # Check branch targets
        for phase in self.phases:
            for branch in phase.branches:
                if not self.get_phase(branch.target_phase):
                    errors.append(
                        f"Branch '{branch.name}' in phase '{phase.name}' "
                        f"targets non-existent phase '{branch.target_phase}'"
                    )

        # Check for unreachable phases
        reachable = self._find_reachable_phases()
        for phase in self.phases:
            if phase.name not in reachable:
                warnings.append(f"Phase '{phase.name}' may be unreachable")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def _find_reachable_phases(self) -> set:
        """Find all phases reachable from entry point."""
        if not self.phases:
            return set()

        reachable = set()
        entry = self.entry_phase or self.phases[0].name
        to_visit = [entry]

        while to_visit:
            current = to_visit.pop(0)
            if current in reachable:
                continue

            reachable.add(current)
            phase = self.get_phase(current)
            if phase:
                # Add branch targets
                for branch in phase.branches:
                    if branch.target_phase not in reachable:
                        to_visit.append(branch.target_phase)

                # Add next sequential phase
                next_phase = self.get_next_phase(current)
                if next_phase and next_phase.name not in reachable:
                    to_visit.append(next_phase.name)

        return reachable

    def get_phase_graph(self) -> Dict[str, List[str]]:
        """Get a graph representation of phase connections."""
        graph = {}
        for phase in self.phases:
            targets = []

            # Branch targets
            for branch in phase.branches:
                targets.append(branch.target_phase)

            # Next sequential phase
            next_phase = self.get_next_phase(phase.name)
            if next_phase:
                targets.append(next_phase.name)

            graph[phase.name] = list(set(targets))

        return graph

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "phases": [p.to_dict() for p in self.phases],
            "entry_phase": self.entry_phase,
            "created_at": self.created_at,
            "version": self.version,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RitualChain":
        """Create from dictionary."""
        chain = cls(
            name=data["name"],
            description=data.get("description", ""),
            entry_phase=data.get("entry_phase"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            version=data.get("version", "1.0"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )

        for phase_data in data.get("phases", []):
            chain.phases.append(Phase.from_dict(phase_data))

        return chain
