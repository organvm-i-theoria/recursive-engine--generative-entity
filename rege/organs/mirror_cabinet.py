"""
RE:GE Mirror Cabinet - Emotional processing and contradiction engine.

Based on: RE-GE_ORG_BODY_02_MIRROR_CABINET.md

The Mirror Cabinet governs:
- Contradiction and belief fracture
- Shame-based recursion
- Shadow integration
- Self-fragment parsing
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from rege.organs.base import OrganHandler
from rege.core.models import Invocation, Patch, Fragment
from rege.core.constants import get_tier, is_fusion_eligible


class SelfFragment:
    """A fragment of self identified by the Mirror Cabinet."""

    def __init__(self, name: str, charge: int, loop_phrase: str):
        self.id = f"FRAG_{uuid.uuid4().hex[:8].upper()}"
        self.name = name
        self.charge = charge
        self.loop_phrase = loop_phrase
        self.resolved = False
        self.created_at = datetime.now()

    def mirror_response(self) -> str:
        """Generate the fragment's mirror response."""
        return f"{self.name} echoes: '{self.loop_phrase}'"

    def attempt_resolution(self) -> str:
        """
        Attempt to resolve the fragment.

        Uses unified charge tier system:
        - Below ACTIVE tier (51): Can be self-resolved
        - ACTIVE+ (51+): Requires Ritual Court
        """
        if self.charge <= 50:  # PROCESSING tier or below
            self.resolved = True
            return "Fragment accepted and integrated."
        return "Fragment requires ritual court."

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "charge": self.charge,
            "loop_phrase": self.loop_phrase,
            "resolved": self.resolved,
            "created_at": self.created_at.isoformat(),
        }


class MirrorCabinet(OrganHandler):
    """
    The Mirror Cabinet - Emotional processing engine for contradiction and shadow work.

    Modes:
    - emotional_reflection: Process emotional content
    - grief_mirroring: Process grief and loss
    - shadow_work: Integrate shadow aspects
    - default: Standard reflection
    """

    @property
    def name(self) -> str:
        return "MIRROR_CABINET"

    @property
    def description(self) -> str:
        return "Emotional processing engine for contradiction, shame, and shadow integration"

    def __init__(self):
        super().__init__()
        self._fragments: Dict[str, SelfFragment] = {}
        self._reflection_log: List[Dict] = []

    def invoke(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process invocation through Mirror Cabinet."""
        mode = invocation.mode.lower()

        if mode == "emotional_reflection":
            return self._emotional_reflection(invocation, patch)
        elif mode == "grief_mirroring":
            return self._grief_mirroring(invocation, patch)
        elif mode == "shadow_work":
            return self._shadow_work(invocation, patch)
        else:
            return self._default_reflection(invocation, patch)

    def _emotional_reflection(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process emotional content and generate reflection."""
        fragment = self._create_fragment(invocation)
        self._fragments[fragment.id] = fragment

        # Check resolution path
        resolution = fragment.attempt_resolution()
        requires_court = fragment.charge > 50

        # Check fusion eligibility
        overlap_count = self._count_overlapping_fragments(fragment)
        fusion_eligible = is_fusion_eligible(fragment.charge, overlap_count)

        result = {
            "fragment": fragment.to_dict(),
            "mirror_response": fragment.mirror_response(),
            "resolution_path": resolution,
            "requires_ritual_court": requires_court,
            "tier": get_tier(fragment.charge),
        }

        if fusion_eligible:
            result["fusion_eligible"] = True
            result["overlap_count"] = overlap_count
            result["recommended_action"] = "trigger_fuse01"

        # Generate law suggestion if charge is high
        if fragment.charge >= 71:
            result["law_suggestion"] = self._generate_law_suggestion(fragment)

        self._log_reflection(invocation, fragment, result)
        return result

    def _grief_mirroring(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process grief and loss."""
        fragment = self._create_fragment(invocation)
        fragment.name = f"Grief_{fragment.name}"
        self._fragments[fragment.id] = fragment

        # Grief always has elevated charge
        fragment.charge = min(100, fragment.charge + 15)

        return {
            "fragment": fragment.to_dict(),
            "mirror_response": f"The mirror sees your grief: {invocation.symbol}",
            "grief_stage": self._identify_grief_stage(invocation.symbol),
            "integration_path": "Through acknowledgment, grief becomes wisdom.",
            "requires_ritual_court": fragment.charge > 50,
            "tier": get_tier(fragment.charge),
        }

    def _shadow_work(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process shadow aspects for integration."""
        fragment = self._create_fragment(invocation)
        fragment.name = f"Shadow_{fragment.name}"
        self._fragments[fragment.id] = fragment

        # Identify shadow archetype
        archetype = self._identify_shadow_archetype(invocation.symbol)

        return {
            "fragment": fragment.to_dict(),
            "shadow_archetype": archetype,
            "mirror_response": f"The shadow speaks: {fragment.loop_phrase}",
            "integration_guidance": self._generate_integration_guidance(archetype),
            "reclamation_possible": fragment.charge < 86,
            "tier": get_tier(fragment.charge),
        }

    def _default_reflection(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Standard reflection processing."""
        fragment = self._create_fragment(invocation)
        self._fragments[fragment.id] = fragment

        return {
            "fragment": fragment.to_dict(),
            "mirror_response": fragment.mirror_response(),
            "tier": get_tier(fragment.charge),
            "status": "reflected",
        }

    def _create_fragment(self, invocation: Invocation) -> SelfFragment:
        """Create a SelfFragment from invocation."""
        # Extract name from symbol or generate
        symbol = invocation.symbol
        name = self._extract_fragment_name(symbol)
        loop_phrase = self._extract_loop_phrase(symbol)

        return SelfFragment(
            name=name,
            charge=invocation.charge,
            loop_phrase=loop_phrase,
        )

    def _extract_fragment_name(self, symbol: str) -> str:
        """Extract or generate a fragment name."""
        # Simple extraction - first few words capitalized
        words = symbol.split()[:3]
        return "_".join(w.capitalize() for w in words) + "_Fragment"

    def _extract_loop_phrase(self, symbol: str) -> str:
        """Extract the core loop phrase from symbol."""
        return symbol[:100] if len(symbol) > 100 else symbol

    def _count_overlapping_fragments(self, fragment: SelfFragment) -> int:
        """Count fragments that overlap with the given fragment."""
        count = 0
        for existing in self._fragments.values():
            if existing.id != fragment.id:
                # Simple overlap: similar charge or shared words
                if abs(existing.charge - fragment.charge) < 15:
                    count += 1
                elif any(word in existing.loop_phrase.lower() for word in fragment.loop_phrase.lower().split()):
                    count += 1
        return count

    def _generate_law_suggestion(self, fragment: SelfFragment) -> Dict[str, Any]:
        """Generate a law suggestion based on fragment."""
        return {
            "proposed_law": f"LAW_XX: {fragment.name} Recognition",
            "description": f"Pattern '{fragment.loop_phrase[:50]}...' recognized as recurring. May warrant law.",
            "charge": fragment.charge,
        }

    def _identify_grief_stage(self, symbol: str) -> str:
        """Identify grief stage from content."""
        symbol_lower = symbol.lower()
        if any(word in symbol_lower for word in ["deny", "can't be", "impossible"]):
            return "denial"
        elif any(word in symbol_lower for word in ["angry", "unfair", "why"]):
            return "anger"
        elif any(word in symbol_lower for word in ["if only", "maybe", "what if"]):
            return "bargaining"
        elif any(word in symbol_lower for word in ["sad", "empty", "hopeless"]):
            return "depression"
        else:
            return "processing"

    def _identify_shadow_archetype(self, symbol: str) -> str:
        """Identify shadow archetype from content."""
        symbol_lower = symbol.lower()
        archetypes = {
            "Saboteur": ["sabotage", "ruin", "destroy", "can't finish"],
            "Critic": ["never good", "worthless", "failure", "stupid"],
            "Victim": ["always happens", "can't help", "helpless"],
            "Villain": ["hurt", "damage", "wrong", "guilty"],
            "Ghost": ["forgotten", "invisible", "ignored", "unseen"],
        }

        for archetype, keywords in archetypes.items():
            if any(kw in symbol_lower for kw in keywords):
                return archetype

        return "Unknown Shadow"

    def _generate_integration_guidance(self, archetype: str) -> str:
        """Generate integration guidance for shadow archetype."""
        guidance = {
            "Saboteur": "The Saboteur protects through prevention. Ask what it fears.",
            "Critic": "The Critic sought perfection to earn love. Offer unconditional acceptance.",
            "Victim": "The Victim learned helplessness as survival. Restore agency gently.",
            "Villain": "The Villain carries projected shame. Separate action from identity.",
            "Ghost": "The Ghost learned invisibility was safety. Witness without demand.",
            "Unknown Shadow": "Meet this shadow with curiosity, not judgment.",
        }
        return guidance.get(archetype, guidance["Unknown Shadow"])

    def _log_reflection(self, invocation: Invocation, fragment: SelfFragment, result: Dict) -> None:
        """Log a reflection for tracking."""
        self._reflection_log.append({
            "timestamp": datetime.now().isoformat(),
            "invocation_id": invocation.invocation_id,
            "fragment_id": fragment.id,
            "charge": fragment.charge,
            "resolved": fragment.resolved,
        })

    def get_valid_modes(self) -> List[str]:
        return ["emotional_reflection", "grief_mirroring", "shadow_work", "default"]

    def get_output_types(self) -> List[str]:
        return ["fragment_map", "law_suggestion", "reflection_sentence"]

    def get_fragments(self) -> List[SelfFragment]:
        """Get all tracked fragments."""
        return list(self._fragments.values())

    def get_unresolved_fragments(self) -> List[SelfFragment]:
        """Get all unresolved fragments."""
        return [f for f in self._fragments.values() if not f.resolved]
