"""
RE:GE Data Models - Core data classes for the symbolic operating system.

Based on specifications:
- RE-GE_CONSTANTS_CHARGE_THRESHOLDS.md
- RE-GE_ORG_BODY_08_SOUL_PATCHBAY.md
- RE-GE_OS_INTERFACE_01_RITUAL_ACCESS_CO.md
- RE-GE_PROTOCOL_FUSE01.md
- RE-GE_PROTOCOL_SYSTEM_RECOVERY.md
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid


# =============================================================================
# Enumerations
# =============================================================================

class DepthLevel(Enum):
    """Invocation depth levels."""
    LIGHT = "light"
    STANDARD = "standard"
    FULL_SPIRAL = "full spiral"


class FusionMode(Enum):
    """FUSE01 protocol operating modes."""
    AUTO = "auto"           # Passive synthesis, logged silently
    INVOKED = "invoked"     # Explicit ritual call, confirmation required
    FORCED = "forced"       # Emergency merge, bypasses thresholds


class FusionType(Enum):
    """Types of fragment fusion."""
    CHARACTER_EMOTION_BLEND = "character_emotion_blend"
    MEMORY_CONSOLIDATION = "memory_consolidation"
    VERSION_MERGE = "version_merge"


class ChargeCalculation(Enum):
    """Methods for calculating fused fragment charge."""
    INHERITED_MAX = "inherited_max"    # max(source_charges)
    AVERAGED = "averaged"              # sum(source_charges) / count
    SUMMED_CAPPED = "summed_capped"    # min(sum(source_charges), 100)


class RecoveryMode(Enum):
    """System recovery protocol modes."""
    FULL_ROLLBACK = "full_rollback"
    PARTIAL = "partial"
    RECONSTRUCT = "reconstruct"
    EMERGENCY_STOP = "emergency_stop"


class RecoveryTrigger(Enum):
    """Triggers for system recovery."""
    CORRUPTION = "corruption"
    DEADLOCK = "deadlock"
    DATA_LOSS = "data_loss"
    DEPTH_PANIC = "depth_panic"
    MANUAL = "manual"


class FragmentStatus(Enum):
    """Status states for fragments."""
    ACTIVE = "active"
    FUSED = "fused"
    ARCHIVED = "archived"
    DECAYED = "decayed"
    PENDING = "pending"


class PatchStatus(Enum):
    """Status states for patches."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


# =============================================================================
# Core Data Classes
# =============================================================================

@dataclass
class Fragment:
    """
    A symbolic fragment - the basic unit of meaning in RE:GE.

    Fragments are memories, emotions, character aspects, or versioned selves
    that can be processed, routed, fused, and archived.
    """
    id: str
    name: str
    charge: int
    tags: List[str]
    version: str = "1.0"
    status: str = "active"
    fused_into: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = f"FRAG_{uuid.uuid4().hex[:8].upper()}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize fragment to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "charge": self.charge,
            "tags": self.tags,
            "version": self.version,
            "status": self.status,
            "fused_into": self.fused_into,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Fragment":
        """Deserialize fragment from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            charge=data["charge"],
            tags=data["tags"],
            version=data.get("version", "1.0"),
            status=data.get("status", "active"),
            fused_into=data.get("fused_into"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Patch:
    """
    A routing request between symbolic nodes.

    Patches flow through the SOUL_PATCHBAY queue for processing.
    Based on: RE-GE_ORG_BODY_08_SOUL_PATCHBAY.md
    """
    input_node: str
    output_node: str
    tags: List[str]
    charge: int = 50
    status: str = "pending"
    priority: int = 2  # Priority.STANDARD
    enqueued_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    depth: int = 0
    patch_id: str = field(default_factory=lambda: f"PATCH_{uuid.uuid4().hex[:8].upper()}")
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate priority from charge and tags."""
        from rege.core.constants import get_priority
        self.priority = get_priority(self.charge, self.tags)

    def activate(self) -> str:
        """Activate the patch for processing."""
        self.status = "active"
        return f"Routing {self.input_node} -> {self.output_node} | tags: {', '.join(self.tags)}"

    def complete(self) -> None:
        """Mark patch as completed."""
        self.status = "completed"
        self.processed_at = datetime.now()

    def fail(self, reason: str) -> None:
        """Mark patch as failed."""
        self.status = "failed"
        self.processed_at = datetime.now()
        self.metadata["failure_reason"] = reason

    def __lt__(self, other: "Patch") -> bool:
        """Enable heap comparison by priority then timestamp."""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.enqueued_at < other.enqueued_at

    def to_dict(self) -> Dict[str, Any]:
        """Serialize patch to dictionary."""
        return {
            "patch_id": self.patch_id,
            "input_node": self.input_node,
            "output_node": self.output_node,
            "tags": self.tags,
            "charge": self.charge,
            "status": self.status,
            "priority": self.priority,
            "enqueued_at": self.enqueued_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "depth": self.depth,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Patch":
        """Deserialize patch from dictionary."""
        patch = cls(
            input_node=data["input_node"],
            output_node=data["output_node"],
            tags=data["tags"],
            charge=data.get("charge", 50),
            status=data.get("status", "pending"),
            depth=data.get("depth", 0),
            metadata=data.get("metadata", {}),
        )
        patch.patch_id = data.get("patch_id", patch.patch_id)
        if data.get("enqueued_at"):
            patch.enqueued_at = datetime.fromisoformat(data["enqueued_at"])
        if data.get("processed_at"):
            patch.processed_at = datetime.fromisoformat(data["processed_at"])
        return patch


@dataclass
class Invocation:
    """
    A parsed invocation request.

    Based on: RE-GE_OS_INTERFACE_01_RITUAL_ACCESS_CO.md
    """
    organ: str
    symbol: str
    mode: str
    depth: DepthLevel
    expect: str
    flags: List[str] = field(default_factory=list)
    raw_text: str = ""
    parsed_at: datetime = field(default_factory=datetime.now)
    invocation_id: Optional[str] = None
    charge: int = 50  # Default charge, may be overridden

    def __post_init__(self):
        if not self.invocation_id:
            self.invocation_id = f"INV_{uuid.uuid4().hex[:8].upper()}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize invocation to dictionary."""
        return {
            "invocation_id": self.invocation_id,
            "organ": self.organ,
            "symbol": self.symbol,
            "mode": self.mode,
            "depth": self.depth.value,
            "expect": self.expect,
            "flags": self.flags,
            "charge": self.charge,
            "parsed_at": self.parsed_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Invocation":
        """Deserialize invocation from dictionary."""
        depth_str = data.get("depth", "standard")
        if depth_str == "light":
            depth = DepthLevel.LIGHT
        elif depth_str == "full spiral":
            depth = DepthLevel.FULL_SPIRAL
        else:
            depth = DepthLevel.STANDARD

        return cls(
            organ=data["organ"],
            symbol=data["symbol"],
            mode=data["mode"],
            depth=depth,
            expect=data["expect"],
            flags=data.get("flags", []),
            raw_text=data.get("raw_text", ""),
            invocation_id=data.get("invocation_id"),
            charge=data.get("charge", 50),
        )


@dataclass
class FusedFragment:
    """
    Result of FUSE01 protocol execution.

    Based on: RE-GE_PROTOCOL_FUSE01.md
    """
    fused_id: str
    source_fragments: List[Fragment]
    fusion_type: FusionType
    charge: int
    output_route: str
    timestamp: datetime
    tags: List[str]
    status: str = "active"
    rollback_available: bool = True
    rollback_deadline: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=7))
    charge_calculation: ChargeCalculation = ChargeCalculation.INHERITED_MAX

    def to_dict(self) -> Dict[str, Any]:
        """Serialize fused fragment to dictionary."""
        return {
            "fused_id": self.fused_id,
            "source_fragments": [
                {"id": f.id, "name": f.name, "charge_at_fusion": f.charge}
                for f in self.source_fragments
            ],
            "fusion_type": self.fusion_type.value,
            "charge": self.charge,
            "charge_calculation": self.charge_calculation.value,
            "output_route": self.output_route,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "status": self.status,
            "rollback_available": self.rollback_available,
            "rollback_deadline": self.rollback_deadline.isoformat(),
        }


@dataclass
class CanonEvent:
    """
    A canonized event in the Heart of Canon.

    Based on: RE-GE_ORG_BODY_01_HEART_OF_CANON.md
    """
    event_id: str
    content: str
    charge: int
    status: str  # "glowing", "emergent_canon", "canon_candidate", "echo", "canonized"
    linked_nodes: List[str]
    event_type: str = "emotional_rupture"
    recurrence: int = 1
    symbol: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    canonized_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.event_id:
            self.event_id = f"CANON_{uuid.uuid4().hex[:8].upper()}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize canon event to dictionary."""
        return {
            "event_id": self.event_id,
            "content": self.content,
            "charge": self.charge,
            "status": self.status,
            "linked_nodes": self.linked_nodes,
            "event_type": self.event_type,
            "recurrence": self.recurrence,
            "symbol": self.symbol,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "canonized_at": self.canonized_at.isoformat() if self.canonized_at else None,
            "metadata": self.metadata,
        }


@dataclass
class StateSnapshot:
    """
    System state snapshot for recovery.

    Based on: RE-GE_PROTOCOL_SYSTEM_RECOVERY.md
    """
    snapshot_id: str
    timestamp: datetime
    trigger: RecoveryTrigger
    system_state: Dict[str, Any]
    organ_states: Dict[str, str]
    pending_operations: List[Dict]
    error_log: List[str]
    recovery_point: Optional[str] = None

    def __post_init__(self):
        if not self.snapshot_id:
            self.snapshot_id = f"SNAP_{self.timestamp.strftime('%Y%m%d_%H%M%S')}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize snapshot to dictionary."""
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp.isoformat(),
            "trigger": self.trigger.value,
            "system_state": self.system_state,
            "organ_states": self.organ_states,
            "pending_operations": self.pending_operations,
            "error_log": self.error_log,
            "recovery_point": self.recovery_point,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateSnapshot":
        """Deserialize snapshot from dictionary."""
        return cls(
            snapshot_id=data["snapshot_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            trigger=RecoveryTrigger(data["trigger"]),
            system_state=data["system_state"],
            organ_states=data["organ_states"],
            pending_operations=data["pending_operations"],
            error_log=data["error_log"],
            recovery_point=data.get("recovery_point"),
        )


@dataclass
class InvocationResult:
    """
    Result of an organ invocation.
    """
    invocation_id: str
    organ: str
    status: str  # "success", "failed", "escalated"
    output: Any
    output_type: str
    execution_time_ms: int
    timestamp: datetime = field(default_factory=datetime.now)
    errors: List[str] = field(default_factory=list)
    side_effects: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize result to dictionary."""
        return {
            "invocation_id": self.invocation_id,
            "organ": self.organ,
            "status": self.status,
            "output": self.output if isinstance(self.output, (dict, list, str, int, float, bool, type(None))) else str(self.output),
            "output_type": self.output_type,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat(),
            "errors": self.errors,
            "side_effects": self.side_effects,
        }


@dataclass
class LawProposal:
    """
    A proposed law from the Mythic Senate.
    """
    law_id: str
    name: str
    description: str
    proposed_by: str  # organ or entity that proposed
    charge: int
    vote_status: str = "pending"  # pending, approved, rejected
    votes_for: int = 0
    votes_against: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    enacted_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize law proposal to dictionary."""
        return {
            "law_id": self.law_id,
            "name": self.name,
            "description": self.description,
            "proposed_by": self.proposed_by,
            "charge": self.charge,
            "vote_status": self.vote_status,
            "votes_for": self.votes_for,
            "votes_against": self.votes_against,
            "created_at": self.created_at.isoformat(),
            "enacted_at": self.enacted_at.isoformat() if self.enacted_at else None,
            "tags": self.tags,
        }
