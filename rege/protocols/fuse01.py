"""
RE:GE FUSE01 Protocol - Fragment fusion engine.

Based on: RE-GE_PROTOCOL_FUSE01.md

The FUSE01 Protocol governs:
- Fragment eligibility checking
- Fusion execution
- Rollback handling
- Output routing
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

from rege.core.models import (
    Fragment,
    FusedFragment,
    FusionMode,
    FusionType,
    ChargeCalculation,
)
from rege.core.constants import TIER_BOUNDARIES, is_fusion_eligible
from rege.core.exceptions import FusionError, FusionNotEligible, FusionRollbackFailed


class FusionProtocol:
    """
    FUSE01 Protocol: Fragment Fusion Engine

    Activation conditions:
    1. charge >= 70 AND overlap_count >= 2
    2. RITUAL_COURT verdict == "Symbolic Fusion"
    3. Archive versions >= 3 (auto-consolidation)
    4. Explicit invocation with ::CALL_PROTOCOL FUSE01

    Operating modes:
    - auto: Passive synthesis, logged silently
    - invoked: Explicit ritual call, confirmation required
    - forced: Emergency merge, bypasses thresholds
    """

    FUSION_CHARGE_THRESHOLD = 70  # ACTIVE/INTENSE boundary
    OVERLAP_THRESHOLD = 2
    FORCED_CHARGE_THRESHOLD = 86  # CRITICAL tier
    ROLLBACK_WINDOW_DAYS = 7

    def __init__(self):
        self.fusion_registry: Dict[str, FusedFragment] = {}
        self._sequence_counter = 0
        self._rollback_log: List[Dict] = []

    def check_eligibility(
        self,
        fragments: List[Fragment],
        mode: FusionMode = FusionMode.AUTO,
    ) -> Tuple[bool, str]:
        """
        Check if fragments are eligible for fusion.

        Args:
            fragments: List of fragments to potentially fuse
            mode: Fusion mode (auto, invoked, forced)

        Returns:
            Tuple of (is_eligible, reason)
        """
        if len(fragments) < 2:
            return False, "Fusion requires at least 2 fragments"

        if mode == FusionMode.FORCED:
            return True, "Forced mode bypasses eligibility checks"

        # Check charge threshold
        max_charge = max(f.charge for f in fragments)
        if max_charge < self.FUSION_CHARGE_THRESHOLD:
            return False, f"Maximum charge {max_charge} below threshold {self.FUSION_CHARGE_THRESHOLD}"

        # Check overlap (simplified: same tags indicate overlap)
        tag_sets = [set(f.tags) for f in fragments]
        common_tags = set.intersection(*tag_sets)
        if len(common_tags) < 1 and mode == FusionMode.AUTO:
            return False, "Insufficient overlap for auto fusion"

        return True, "Eligible for fusion"

    def execute_fusion(
        self,
        fragments: List[Fragment],
        mode: FusionMode,
        output_route: str = "BLOOM_ENGINE",
        fusion_type: Optional[FusionType] = None,
        charge_calc: ChargeCalculation = ChargeCalculation.INHERITED_MAX,
    ) -> Optional[FusedFragment]:
        """
        Execute fusion protocol on fragments.

        Args:
            fragments: Fragments to fuse
            mode: Fusion mode
            output_route: Where to route the fused fragment
            fusion_type: Type of fusion (auto-detected if None)
            charge_calc: Charge calculation method

        Returns:
            FusedFragment if successful, None if rejected

        Raises:
            FusionNotEligible: If fragments don't meet eligibility
        """
        # Check eligibility
        is_eligible, reason = self.check_eligibility(fragments, mode)
        if not is_eligible:
            raise FusionNotEligible(reason, fragments)

        # Generate fused ID
        fused_id = self._generate_fused_id(fragments)

        # Calculate charge
        charge = self._calculate_charge(fragments, charge_calc)

        # Determine fusion type if not specified
        if fusion_type is None:
            fusion_type = self._infer_fusion_type(fragments)

        # Merge tags
        merged_tags = list(set(tag for f in fragments for tag in f.tags))
        merged_tags.append("FUSE+")

        # Create fused fragment
        fused = FusedFragment(
            fused_id=fused_id,
            source_fragments=fragments,
            fusion_type=fusion_type,
            charge=charge,
            output_route=output_route,
            timestamp=datetime.now(),
            tags=merged_tags,
            charge_calculation=charge_calc,
        )

        # Mark source fragments as fused
        for fragment in fragments:
            fragment.status = "fused"
            fragment.fused_into = fused_id

        # Register fusion
        self.fusion_registry[fused_id] = fused

        return fused

    def rollback(self, fused_id: str, reason: str = "Manual rollback") -> Dict[str, Any]:
        """
        Rollback a fusion if within the rollback window.

        Args:
            fused_id: ID of the fused fragment
            reason: Reason for rollback (default: "Manual rollback")

        Returns:
            Rollback result dictionary with status, fused_id, restored_count
        """
        if fused_id not in self.fusion_registry:
            return {
                "status": "failed",
                "reason": "Fusion not found",
                "fused_id": fused_id,
            }

        fused = self.fusion_registry[fused_id]

        if not fused.rollback_available:
            return {
                "status": "failed",
                "reason": "Rollback not available",
                "fused_id": fused_id,
            }

        if datetime.now() > fused.rollback_deadline:
            return {
                "status": "failed",
                "reason": "Rollback window expired",
                "fused_id": fused_id,
            }

        # Check if fused fragment has been further processed
        if "CANON+" in fused.tags:
            return {
                "status": "failed",
                "reason": "Cannot rollback canonized fusion",
                "fused_id": fused_id,
            }

        # Restore source fragments
        for fragment in fused.source_fragments:
            fragment.status = "active"
            fragment.fused_into = None

        # Mark fused as rolled back
        fused.status = "rolled_back"
        fused.rollback_available = False

        # Log rollback
        rollback_entry = {
            "fused_id": fused_id,
            "reason": reason,
            "rolled_back_at": datetime.now().isoformat(),
            "source_fragments_restored": len(fused.source_fragments),
        }
        self._rollback_log.append(rollback_entry)

        return {
            "status": "rolled_back",
            "fused_id": fused_id,
            "restored_count": len(fused.source_fragments),
            "fragments_restored": [f.id for f in fused.source_fragments],
            "reason": reason,
        }

    def route_output(self, fused: FusedFragment) -> Dict[str, Any]:
        """
        Route fused fragment to destination.

        Args:
            fused: The fused fragment to route

        Returns:
            Routing instructions
        """
        return {
            "action": "route",
            "destination": fused.output_route,
            "payload": fused.to_dict(),
            "notifications": [
                {"target": "SOUL_PATCHBAY", "action": "update_routes"},
                {"target": "ARCHIVE_ORDER", "action": "log_fusion"},
            ],
        }

    def _generate_fused_id(self, fragments: List[Fragment]) -> str:
        """Generate unique fused fragment ID."""
        self._sequence_counter += 1
        names = "_".join(f.name.lower().replace(" ", "_")[:10] for f in fragments[:3])
        return f"FUSE_{self._sequence_counter:03d}_{names}"

    def _calculate_charge(
        self,
        fragments: List[Fragment],
        method: ChargeCalculation,
    ) -> int:
        """Calculate fused fragment charge."""
        charges = [f.charge for f in fragments]

        if method == ChargeCalculation.INHERITED_MAX:
            return max(charges)
        elif method == ChargeCalculation.AVERAGED:
            return sum(charges) // len(charges)
        elif method == ChargeCalculation.SUMMED_CAPPED:
            return min(sum(charges), 100)

        return max(charges)

    def _infer_fusion_type(self, fragments: List[Fragment]) -> FusionType:
        """Infer fusion type from fragment characteristics."""
        # Check for version patterns
        versions = [f.version for f in fragments]
        if len(set(versions)) > 1:
            return FusionType.VERSION_MERGE

        # Check for emotion-related tags
        emotion_tags = {"SHDW+", "GRIEF+", "FEAR+", "SHAME+", "DOUBT+"}
        has_emotion = any(tag in emotion_tags for f in fragments for tag in f.tags)
        has_char = any("CHAR+" in f.tags for f in fragments)

        if has_emotion and has_char:
            return FusionType.CHARACTER_EMOTION_BLEND

        return FusionType.MEMORY_CONSOLIDATION

    def get_fusion(self, fused_id: str) -> Optional[FusedFragment]:
        """Get a fused fragment by ID."""
        return self.fusion_registry.get(fused_id)

    def get_all_fusions(self) -> List[FusedFragment]:
        """Get all fusions."""
        return list(self.fusion_registry.values())

    def get_active_fusions(self) -> List[FusedFragment]:
        """Get all active (non-rolled-back) fusions."""
        return [f for f in self.fusion_registry.values() if f.status == "active"]

    def get_rollback_log(self) -> List[Dict]:
        """Get rollback history."""
        return self._rollback_log.copy()

    def get_eligible_fragments(self) -> List[Fragment]:
        """
        Get fragments that are eligible for fusion.

        Returns fragments from source_fragments of active fusions that meet
        the eligibility criteria (charge >= 70).
        """
        # Note: In a real system, this would query the fragment store
        # For now, return fragments from existing fusions that could be re-fused
        eligible = []

        for fused in self.fusion_registry.values():
            if fused.status == "rolled_back":
                # Rolled-back source fragments might be eligible again
                for fragment in fused.source_fragments:
                    if fragment.charge >= self.FUSION_CHARGE_THRESHOLD:
                        eligible.append(fragment)

        return eligible


# Global fusion protocol instance
_fusion_protocol: Optional[FusionProtocol] = None


def get_fusion_protocol() -> FusionProtocol:
    """Get or create global fusion protocol instance."""
    global _fusion_protocol
    if _fusion_protocol is None:
        _fusion_protocol = FusionProtocol()
    return _fusion_protocol
