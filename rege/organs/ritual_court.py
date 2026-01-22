"""
RE:GE Ritual Court - Ceremonial logic and contradiction resolution.

Based on: RE-GE_ORG_BODY_05_RITUAL_COURT.md

The Ritual Court governs:
- Contradiction trials
- Grief rituals
- Fusion verdicts
- Emergency sessions
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from rege.organs.base import OrganHandler
from rege.core.models import Invocation, Patch
from rege.core.constants import get_tier, is_critical_emergency


class Verdict:
    """A verdict from the Ritual Court."""

    def __init__(
        self,
        verdict_type: str,
        ruling: str,
        charge: int,
        consequences: List[str],
    ):
        self.verdict_id = f"VERDICT_{uuid.uuid4().hex[:8].upper()}"
        self.verdict_type = verdict_type
        self.ruling = ruling
        self.charge = charge
        self.consequences = consequences
        self.delivered_at = datetime.now()
        self.appealed = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict_id": self.verdict_id,
            "verdict_type": self.verdict_type,
            "ruling": self.ruling,
            "charge": self.charge,
            "consequences": self.consequences,
            "delivered_at": self.delivered_at.isoformat(),
            "appealed": self.appealed,
        }


class RitualCourt(OrganHandler):
    """
    The Ritual Court - Ceremonial logic and contradiction resolution.

    Modes:
    - contradiction_trial: Resolve contradicting beliefs/memories
    - grief_ritual: Process grief through ritual
    - fusion_verdict: Rule on fusion requests
    - emergency_session: Emergency processing
    - default: Standard court session
    """

    @property
    def name(self) -> str:
        return "RITUAL_COURT"

    @property
    def description(self) -> str:
        return "Ceremonial logic engine for contradiction resolution and verdicts"

    def __init__(self):
        super().__init__()
        self._verdicts: Dict[str, Verdict] = {}
        self._pending_cases: List[Dict] = []
        self._session_count = 0

    def invoke(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process invocation through Ritual Court."""
        mode = invocation.mode.lower()

        if mode == "contradiction_trial":
            return self._contradiction_trial(invocation, patch)
        elif mode == "grief_ritual":
            return self._grief_ritual(invocation, patch)
        elif mode == "fusion_verdict":
            return self._fusion_verdict(invocation, patch)
        elif mode == "emergency_session":
            return self._emergency_session(invocation, patch)
        else:
            return self._default_session(invocation, patch)

    def _contradiction_trial(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Resolve contradicting beliefs/memories."""
        self._session_count += 1

        # Analyze contradiction
        analysis = self._analyze_contradiction(invocation.symbol)

        # Determine verdict
        if invocation.charge >= 86:
            # CRITICAL - requires Symbolic Fusion
            verdict = self._deliver_verdict(
                verdict_type="Symbolic Fusion",
                ruling="Fragments must be unified through FUSE01 protocol",
                charge=invocation.charge,
                consequences=["Trigger FUSE01", "Route to BLOOM_ENGINE"],
            )
        elif invocation.charge >= 71:
            # INTENSE - can be resolved through ritual
            verdict = self._deliver_verdict(
                verdict_type="Ritual Resolution",
                ruling="Contradiction can be integrated through ritual practice",
                charge=invocation.charge,
                consequences=["Create integration ritual", "Monitor for 7 days"],
            )
        else:
            # Lower charge - simple acknowledgment
            verdict = self._deliver_verdict(
                verdict_type="Acknowledgment",
                ruling="Contradiction noted, no immediate action required",
                charge=invocation.charge,
                consequences=["Archive for observation"],
            )

        return {
            "session_id": f"SESSION_{self._session_count:04d}",
            "analysis": analysis,
            "verdict": verdict.to_dict(),
            "closure_achieved": invocation.charge < 71,
        }

    def _grief_ritual(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process grief through ritual."""
        self._session_count += 1

        ritual_steps = self._design_grief_ritual(invocation.symbol, invocation.charge)

        verdict = self._deliver_verdict(
            verdict_type="Grief Ritual Prescribed",
            ruling="A ritual of witnessing and release is prescribed",
            charge=invocation.charge,
            consequences=["Complete ritual steps", "Return for closure session"],
        )

        return {
            "session_id": f"GRIEF_{self._session_count:04d}",
            "ritual_steps": ritual_steps,
            "verdict": verdict.to_dict(),
            "glyph_archive": self._generate_grief_glyph(invocation.symbol),
        }

    def _fusion_verdict(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Rule on fusion requests."""
        self._session_count += 1

        # Check if fusion is authorized
        authorized = invocation.charge >= 70 or "FUSE+" in invocation.flags

        if authorized:
            verdict = self._deliver_verdict(
                verdict_type="Symbolic Fusion Authorized",
                ruling="Fusion may proceed",
                charge=invocation.charge,
                consequences=["Execute FUSE01 protocol", "Log to FUSION_REGISTRY"],
            )
        else:
            verdict = self._deliver_verdict(
                verdict_type="Fusion Denied",
                ruling="Charge or authorization insufficient for fusion",
                charge=invocation.charge,
                consequences=["Increase charge through ritual", "Re-submit request"],
            )

        return {
            "session_id": f"FUSION_{self._session_count:04d}",
            "authorization": authorized,
            "verdict": verdict.to_dict(),
        }

    def _emergency_session(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Emergency processing."""
        self._session_count += 1

        if not is_critical_emergency(invocation.charge):
            return {
                "session_id": f"EMERG_{self._session_count:04d}",
                "status": "rejected",
                "reason": f"Charge {invocation.charge} below CRITICAL threshold (86)",
                "recommendation": "Use standard session for non-emergency matters",
            }

        verdict = self._deliver_verdict(
            verdict_type="Emergency Intervention",
            ruling="Emergency protocol activated - immediate processing required",
            charge=invocation.charge,
            consequences=[
                "All related organs notified",
                "Priority queue bypass enabled",
                "State snapshot captured",
            ],
        )

        return {
            "session_id": f"EMERG_{self._session_count:04d}",
            "emergency_level": "CRITICAL",
            "verdict": verdict.to_dict(),
            "notifications_sent": ["HEART_OF_CANON", "MIRROR_CABINET", "SOUL_PATCHBAY"],
        }

    def _default_session(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Standard court session."""
        self._session_count += 1

        return {
            "session_id": f"SESSION_{self._session_count:04d}",
            "matter": invocation.symbol,
            "charge": invocation.charge,
            "tier": get_tier(invocation.charge),
            "recommendation": self._generate_recommendation(invocation.charge),
            "status": "heard",
        }

    def perform_ritual(self, ritual_type: str, symbol: str, charge: int) -> Dict[str, Any]:
        """
        Perform a ritual.

        Args:
            ritual_type: Type of ritual
            symbol: Symbol/content to process
            charge: Emotional charge

        Returns:
            Ritual result
        """
        self._session_count += 1

        return {
            "ritual_id": f"RITUAL_{self._session_count:04d}",
            "type": ritual_type,
            "symbol_processed": symbol,
            "charge_before": charge,
            "charge_after": max(0, charge - 10),  # Rituals reduce charge
            "completion_status": "performed",
            "effects": ["Charge reduced", "Pattern acknowledged"],
        }

    def _deliver_verdict(
        self,
        verdict_type: str,
        ruling: str,
        charge: int,
        consequences: List[str],
    ) -> Verdict:
        """Create and store a verdict."""
        verdict = Verdict(verdict_type, ruling, charge, consequences)
        self._verdicts[verdict.verdict_id] = verdict
        return verdict

    def _analyze_contradiction(self, symbol: str) -> Dict[str, Any]:
        """Analyze a contradiction."""
        return {
            "parties": self._extract_parties(symbol),
            "nature": "belief_conflict" if "believe" in symbol.lower() else "memory_conflict",
            "severity": "high" if len(symbol) > 100 else "moderate",
        }

    def _extract_parties(self, symbol: str) -> List[str]:
        """Extract parties from contradiction."""
        # Simple extraction - look for 'and', 'vs', 'but'
        if " and " in symbol.lower():
            return symbol.split(" and ")[:2]
        elif " but " in symbol.lower():
            return symbol.split(" but ")[:2]
        return ["Party A", "Party B"]

    def _design_grief_ritual(self, symbol: str, charge: int) -> List[str]:
        """Design grief ritual steps."""
        base_steps = [
            "1. Name the loss aloud",
            "2. Allow the emotion without resistance",
            "3. Witness the feeling for 3 breaths",
        ]

        if charge >= 71:
            base_steps.extend([
                "4. Write what you wish you had said",
                "5. Create a symbolic offering",
                "6. Speak a word of release",
            ])

        if charge >= 86:
            base_steps.extend([
                "7. Burn or bury the written words",
                "8. Return in 7 days for closure session",
            ])

        return base_steps

    def _generate_grief_glyph(self, symbol: str) -> Dict[str, Any]:
        """Generate a grief glyph for archival."""
        return {
            "glyph_id": f"GLYPH_{uuid.uuid4().hex[:8].upper()}",
            "type": "grief_sigil",
            "elements": ["water", "salt", "time"],
            "meaning": "What was held is released",
        }

    def _generate_recommendation(self, charge: int) -> str:
        """Generate recommendation based on charge."""
        if charge >= 86:
            return "Emergency session recommended"
        elif charge >= 71:
            return "Full ritual processing recommended"
        elif charge >= 51:
            return "Standard processing sufficient"
        else:
            return "Archive and observe"

    def get_valid_modes(self) -> List[str]:
        return ["contradiction_trial", "grief_ritual", "fusion_verdict", "emergency_session", "default"]

    def get_output_types(self) -> List[str]:
        return ["closure", "law", "verdict", "glyph_archive", "authorization_verdict"]

    def get_verdict(self, verdict_id: str) -> Optional[Verdict]:
        """Get a verdict by ID."""
        return self._verdicts.get(verdict_id)

    def get_all_verdicts(self) -> List[Verdict]:
        """Get all verdicts."""
        return list(self._verdicts.values())
