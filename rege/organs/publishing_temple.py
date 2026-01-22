"""
RE:GE Publishing Temple - Final gate for releasing outputs.

Based on: RE-GE_ORG_BODY_22_PUBLISHING_TEMPLE.md

The Publishing Temple governs:
- Publication gating and risk assessment
- Metadata sealing (date, law refs, origin loop)
- Scarcity settings for releases
- Distribution tracking
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid

from rege.organs.base import OrganHandler
from rege.core.models import Invocation, Patch


class PublicationFormat(Enum):
    """Export formats for publications."""
    DIGITAL = "digital"        # Standard digital release
    PRINT = "print"            # Physical print
    NFT = "nft"                # Blockchain token
    ARCHIVE = "archive"        # Archival preservation
    RITUAL = "ritual"          # Live ritual release


class ScarcityLevel(Enum):
    """Scarcity levels for publications."""
    UNLIMITED = "unlimited"    # No limit
    LIMITED = "limited"        # Fixed quantity
    UNIQUE = "unique"          # One-of-one
    TIMED = "timed"            # Available for limited time


@dataclass
class RitualExport:
    """
    A publication export ready for release.

    Tracks the final form of output including metadata,
    scarcity settings, and distribution information.
    """
    export_id: str
    source_id: str  # Product or fragment ID
    format: PublicationFormat
    scarcity: ScarcityLevel
    scarcity_count: Optional[int]  # For LIMITED scarcity
    metadata: Dict[str, Any]
    sealed_at: Optional[datetime]
    published_at: Optional[datetime]
    risk_score: int  # 0-100
    status: str = "pending"  # pending, sanctified, published, withdrawn
    distributed_count: int = 0
    law_references: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.export_id:
            self.export_id = f"EXPORT_{uuid.uuid4().hex[:8].upper()}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize export to dictionary."""
        return {
            "export_id": self.export_id,
            "source_id": self.source_id,
            "format": self.format.value,
            "scarcity": self.scarcity.value,
            "scarcity_count": self.scarcity_count,
            "metadata": self.metadata,
            "sealed_at": self.sealed_at.isoformat() if self.sealed_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "risk_score": self.risk_score,
            "status": self.status,
            "distributed_count": self.distributed_count,
            "law_references": self.law_references,
        }


# Publication gating configuration
PUBLICATION_CONFIG = {
    "max_risk_score": 75,      # Risk must be <= this to publish
    "min_charge_for_nft": 86,  # CRITICAL tier for NFT
    "min_charge_for_print": 71,  # INTENSE tier for print
    "default_scarcity": "unlimited",
}


class PublishingTemple(OrganHandler):
    """
    Publishing Temple - Final gate for releasing outputs.

    Modes:
    - sanctify: Prepare for publication (risk check)
    - publish: Execute publication
    - seal: Finalize metadata
    - withdraw: Remove from publication
    - queue: View publication queue
    - default: Publication status
    """

    @property
    def name(self) -> str:
        return "PUBLISHING_TEMPLE"

    @property
    def description(self) -> str:
        return "Final gate for releasing outputs"

    def __init__(self):
        super().__init__()
        self._exports: Dict[str, RitualExport] = {}
        self._publication_queue: List[str] = []
        self._publication_history: List[Dict[str, Any]] = []
        self._distribution_log: List[Dict[str, Any]] = []

    def invoke(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process invocation through Publishing Temple."""
        mode = invocation.mode.lower()

        if mode == "sanctify":
            return self._sanctify_export(invocation, patch)
        elif mode == "publish":
            return self._publish_export(invocation, patch)
        elif mode == "seal":
            return self._seal_metadata(invocation, patch)
        elif mode == "withdraw":
            return self._withdraw_export(invocation, patch)
        elif mode == "queue":
            return self._view_queue(invocation, patch)
        else:
            return self._default_status(invocation, patch)

    def _sanctify_export(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Prepare export for publication with risk assessment."""
        source_id = invocation.symbol.strip() if invocation.symbol else f"SOURCE_{uuid.uuid4().hex[:8].upper()}"

        # Calculate risk score
        risk_score = self._calculate_risk(invocation, patch)

        # Determine format
        format_type = self._determine_format(invocation.flags, invocation.charge)

        # Determine scarcity
        scarcity, count = self._determine_scarcity(invocation.flags)

        # Check if risk is acceptable
        risk_acceptable = risk_score <= PUBLICATION_CONFIG["max_risk_score"]

        # Build metadata
        metadata = {
            "sanctified_by": "PUBLISHING_TEMPLE",
            "charge_at_sanctification": invocation.charge,
            "depth_at_sanctification": patch.depth,
            "flags": invocation.flags,
            "origin_loop": invocation.invocation_id,
        }

        # Create export
        export = RitualExport(
            export_id="",
            source_id=source_id,
            format=format_type,
            scarcity=scarcity,
            scarcity_count=count,
            metadata=metadata,
            sealed_at=None,
            published_at=None,
            risk_score=risk_score,
            status="sanctified" if risk_acceptable else "risk_blocked",
        )

        self._exports[export.export_id] = export

        if risk_acceptable:
            self._publication_queue.append(export.export_id)

        return {
            "status": "sanctified" if risk_acceptable else "blocked",
            "export": export.to_dict(),
            "risk_assessment": {
                "score": risk_score,
                "threshold": PUBLICATION_CONFIG["max_risk_score"],
                "acceptable": risk_acceptable,
            },
            "ready_to_publish": risk_acceptable,
            "queue_position": len(self._publication_queue) if risk_acceptable else None,
        }

    def _publish_export(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Execute publication of a sanctified export."""
        export_id = invocation.symbol.strip().upper() if invocation.symbol else None

        # If no ID provided, publish from queue
        if not export_id and self._publication_queue:
            export_id = self._publication_queue[0]

        if not export_id:
            return {
                "status": "failed",
                "error": "No export ID provided and queue is empty",
            }

        if export_id not in self._exports:
            return {
                "status": "failed",
                "error": f"Export not found: {export_id}",
            }

        export = self._exports[export_id]

        # Check if sanctified
        if export.status not in ["sanctified", "pending"]:
            return {
                "status": "failed",
                "error": f"Export not ready for publication. Status: {export.status}",
            }

        # Final risk check
        if export.risk_score > PUBLICATION_CONFIG["max_risk_score"]:
            return {
                "status": "blocked",
                "error": "Risk score exceeds threshold",
                "risk_score": export.risk_score,
                "threshold": PUBLICATION_CONFIG["max_risk_score"],
            }

        # Seal metadata if not already sealed
        if not export.sealed_at:
            export.sealed_at = datetime.now()

        # Publish
        export.published_at = datetime.now()
        export.status = "published"

        # Remove from queue
        if export_id in self._publication_queue:
            self._publication_queue.remove(export_id)

        # Record in history
        self._publication_history.append({
            "export_id": export_id,
            "published_at": export.published_at.isoformat(),
            "format": export.format.value,
            "scarcity": export.scarcity.value,
        })

        return {
            "status": "published",
            "export": export.to_dict(),
            "publication_record": {
                "published_at": export.published_at.isoformat(),
                "format": export.format.value,
                "scarcity": export.scarcity.value,
                "scarcity_count": export.scarcity_count,
            },
        }

    def _seal_metadata(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Seal metadata for an export."""
        export_id = invocation.symbol.strip().upper() if invocation.symbol else None

        if not export_id:
            return {
                "status": "failed",
                "error": "Export ID required for sealing",
            }

        if export_id not in self._exports:
            return {
                "status": "failed",
                "error": f"Export not found: {export_id}",
            }

        export = self._exports[export_id]

        if export.sealed_at:
            return {
                "status": "already_sealed",
                "export_id": export_id,
                "sealed_at": export.sealed_at.isoformat(),
            }

        # Add sealing metadata
        export.metadata["sealed_date"] = datetime.now().isoformat()
        export.metadata["seal_charge"] = invocation.charge

        # Add law references from flags
        for flag in invocation.flags:
            if flag.startswith("LAW_"):
                export.law_references.append(flag)

        export.sealed_at = datetime.now()

        return {
            "status": "sealed",
            "export": export.to_dict(),
            "seal_timestamp": export.sealed_at.isoformat(),
            "law_references": export.law_references,
        }

    def _withdraw_export(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Withdraw an export from publication."""
        export_id = invocation.symbol.strip().upper() if invocation.symbol else None

        if not export_id:
            return {
                "status": "failed",
                "error": "Export ID required for withdrawal",
            }

        if export_id not in self._exports:
            return {
                "status": "failed",
                "error": f"Export not found: {export_id}",
            }

        export = self._exports[export_id]
        previous_status = export.status

        export.status = "withdrawn"

        # Remove from queue if present
        if export_id in self._publication_queue:
            self._publication_queue.remove(export_id)

        return {
            "status": "withdrawn",
            "export_id": export_id,
            "previous_status": previous_status,
            "withdrawn_at": datetime.now().isoformat(),
        }

    def _view_queue(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """View the publication queue."""
        queue_details = []
        for export_id in self._publication_queue:
            export = self._exports.get(export_id)
            if export:
                queue_details.append({
                    "export_id": export_id,
                    "source_id": export.source_id,
                    "format": export.format.value,
                    "risk_score": export.risk_score,
                    "status": export.status,
                })

        return {
            "status": "queue_retrieved",
            "queue_length": len(self._publication_queue),
            "queue": queue_details,
            "total_exports": len(self._exports),
            "published_count": len([e for e in self._exports.values() if e.status == "published"]),
        }

    def _default_status(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Return publication status."""
        status_counts = {
            "pending": 0,
            "sanctified": 0,
            "published": 0,
            "withdrawn": 0,
            "risk_blocked": 0,
        }
        for export in self._exports.values():
            if export.status in status_counts:
                status_counts[export.status] += 1

        return {
            "status": "temple_status",
            "total_exports": len(self._exports),
            "queue_length": len(self._publication_queue),
            "status_breakdown": status_counts,
            "publication_history_length": len(self._publication_history),
            "recent_publications": self._publication_history[-5:],
        }

    def _calculate_risk(self, invocation: Invocation, patch: Patch) -> int:
        """Calculate risk score for publication."""
        risk = 50  # Base risk

        # Lower charge = higher risk
        if invocation.charge < 51:
            risk += 25
        elif invocation.charge < 71:
            risk += 10
        elif invocation.charge >= 86:
            risk -= 15

        # Certain flags reduce risk
        if "CANON+" in invocation.flags:
            risk -= 10
        if "ARCHIVE+" in invocation.flags:
            risk -= 5

        # Certain flags increase risk
        if "VOLATILE+" in invocation.flags:
            risk += 20
        if "INCOMPLETE+" in invocation.flags:
            risk += 15

        # Lower depth = higher risk
        if patch.depth < 3:
            risk += 15
        elif patch.depth >= 7:
            risk -= 10

        return max(0, min(100, risk))

    def _determine_format(self, flags: List[str], charge: int) -> PublicationFormat:
        """Determine publication format."""
        format_flags = {
            "DIGITAL+": PublicationFormat.DIGITAL,
            "PRINT+": PublicationFormat.PRINT,
            "NFT+": PublicationFormat.NFT,
            "ARCHIVE+": PublicationFormat.ARCHIVE,
            "RITUAL+": PublicationFormat.RITUAL,
        }

        for flag, fmt in format_flags.items():
            if flag in flags:
                # Validate charge requirements
                if fmt == PublicationFormat.NFT and charge < PUBLICATION_CONFIG["min_charge_for_nft"]:
                    continue
                if fmt == PublicationFormat.PRINT and charge < PUBLICATION_CONFIG["min_charge_for_print"]:
                    continue
                return fmt

        # Default based on charge
        if charge >= 86:
            return PublicationFormat.NFT
        elif charge >= 71:
            return PublicationFormat.PRINT
        else:
            return PublicationFormat.DIGITAL

    def _determine_scarcity(self, flags: List[str]) -> tuple:
        """Determine scarcity settings."""
        if "UNIQUE+" in flags:
            return ScarcityLevel.UNIQUE, 1
        if "LIMITED+" in flags:
            # Try to find count in flags
            for flag in flags:
                if flag.startswith("COUNT_"):
                    try:
                        count = int(flag.replace("COUNT_", ""))
                        return ScarcityLevel.LIMITED, count
                    except ValueError:
                        pass
            return ScarcityLevel.LIMITED, 100  # Default limited count
        if "TIMED+" in flags:
            return ScarcityLevel.TIMED, None
        return ScarcityLevel.UNLIMITED, None

    def record_distribution(self, export_id: str, recipient: str = "UNKNOWN") -> Dict[str, Any]:
        """Record a distribution event."""
        if export_id not in self._exports:
            return {"status": "failed", "error": "Export not found"}

        export = self._exports[export_id]

        if export.status != "published":
            return {"status": "failed", "error": "Export not published"}

        # Check scarcity limits
        if export.scarcity == ScarcityLevel.UNIQUE and export.distributed_count >= 1:
            return {"status": "failed", "error": "Unique item already distributed"}

        if export.scarcity == ScarcityLevel.LIMITED and export.scarcity_count:
            if export.distributed_count >= export.scarcity_count:
                return {"status": "failed", "error": "Limited quantity exhausted"}

        export.distributed_count += 1

        self._distribution_log.append({
            "export_id": export_id,
            "recipient": recipient,
            "distributed_at": datetime.now().isoformat(),
            "distribution_number": export.distributed_count,
        })

        return {
            "status": "distributed",
            "export_id": export_id,
            "distribution_number": export.distributed_count,
            "remaining": export.scarcity_count - export.distributed_count if export.scarcity_count else None,
        }

    def get_export(self, export_id: str) -> Optional[RitualExport]:
        """Get export by ID."""
        return self._exports.get(export_id)

    def get_valid_modes(self) -> List[str]:
        return ["sanctify", "publish", "seal", "withdraw", "queue", "default"]

    def get_output_types(self) -> List[str]:
        return ["sanctification", "publication", "seal_record", "withdrawal", "queue_status", "temple_status"]

    def get_state(self) -> Dict[str, Any]:
        """Get current organ state for checkpointing."""
        state = super().get_state()
        state["state"].update({
            "exports": {k: v.to_dict() for k, v in self._exports.items()},
            "publication_queue": self._publication_queue,
            "publication_history": self._publication_history,
            "distribution_log": self._distribution_log,
        })
        return state

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore organ state from checkpoint."""
        super().restore_state(state)
        inner_state = state.get("state", {})
        self._publication_queue = inner_state.get("publication_queue", [])
        self._publication_history = inner_state.get("publication_history", [])
        self._distribution_log = inner_state.get("distribution_log", [])

    def reset(self) -> None:
        """Reset organ to initial state."""
        super().reset()
        self._exports = {}
        self._publication_queue = []
        self._publication_history = []
        self._distribution_log = []
