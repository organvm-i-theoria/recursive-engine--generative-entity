"""
RE:GE Dream Council - Collective processing and prophecy.

Based on: RE-GE_ORG_BODY_10_DREAM_COUNCIL.md

The Dream Council governs:
- Dream interpretation
- Prophetic lawmaking
- Glyph decoding
- Oneiric review queue
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from rege.organs.base import OrganHandler
from rege.core.models import Invocation, Patch, LawProposal
from rege.core.constants import get_tier


class Dream:
    """A dream record."""

    def __init__(self, content: str, charge: int, dreamer: str = "SELF"):
        self.dream_id = f"DREAM_{uuid.uuid4().hex[:8].upper()}"
        self.content = content
        self.charge = charge
        self.dreamer = dreamer
        self.recorded_at = datetime.now()
        self.symbols: List[str] = []
        self.interpretation: Optional[str] = None
        self.prophecy_weight = charge / 100
        self.status = "recorded"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dream_id": self.dream_id,
            "content": self.content,
            "charge": self.charge,
            "dreamer": self.dreamer,
            "recorded_at": self.recorded_at.isoformat(),
            "symbols": self.symbols,
            "interpretation": self.interpretation,
            "prophecy_weight": self.prophecy_weight,
            "status": self.status,
            "tier": get_tier(self.charge),
        }


class DreamCouncil(OrganHandler):
    """
    The Dream Council - Collective processing and prophecy.

    Modes:
    - prophetic_lawmaking: Derive laws from dreams
    - glyph_decode: Decode dream symbols
    - interpretation: Full dream interpretation
    - default: Standard dream processing
    """

    @property
    def name(self) -> str:
        return "DREAM_COUNCIL"

    @property
    def description(self) -> str:
        return "Collective processing and prophecy from dreams"

    def __init__(self):
        super().__init__()
        self._dreams: Dict[str, Dream] = {}
        self._review_queue: List[str] = []  # Dream IDs pending review
        self._symbol_dictionary: Dict[str, str] = self._init_symbol_dictionary()
        self._proposed_laws: List[Dict] = []

    def invoke(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process invocation through Dream Council."""
        mode = invocation.mode.lower()

        if mode == "prophetic_lawmaking":
            return self._prophetic_lawmaking(invocation, patch)
        elif mode == "glyph_decode":
            return self._glyph_decode(invocation, patch)
        elif mode == "interpretation":
            return self._interpretation(invocation, patch)
        else:
            return self._default_process(invocation, patch)

    def _prophetic_lawmaking(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Derive laws from dreams."""
        dream = self._create_dream(invocation)

        # Extract symbols for law basis
        dream.symbols = self._extract_symbols(invocation.symbol)

        # Generate law proposal if charge is high enough
        law_proposal = None
        if invocation.charge >= 71:  # INTENSE+
            law_proposal = self._propose_law_from_dream(dream)

        # Archive the dream
        archive_symbol = self._generate_archive_symbol(dream)

        return {
            "dream": dream.to_dict(),
            "symbols_extracted": dream.symbols,
            "law_proposal": law_proposal,
            "archive_symbol": archive_symbol,
            "prophecy_strength": dream.prophecy_weight,
        }

    def _glyph_decode(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Decode dream symbols/glyphs."""
        symbols = self._extract_symbols(invocation.symbol)
        decodings = {}

        for symbol in symbols:
            decodings[symbol] = self._decode_symbol(symbol)

        return {
            "input": invocation.symbol,
            "symbols_found": symbols,
            "decodings": decodings,
            "synthesis": self._synthesize_meanings(decodings),
        }

    def _interpretation(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Full dream interpretation."""
        dream = self._create_dream(invocation)

        # Full analysis
        dream.symbols = self._extract_symbols(invocation.symbol)
        dream.interpretation = self._generate_interpretation(dream)
        dream.status = "interpreted"

        return {
            "dream": dream.to_dict(),
            "dream_map": self._generate_dream_map(dream),
            "emotional_layer": self._analyze_emotional_layer(dream),
            "recommended_ritual": self._recommend_ritual(dream),
        }

    def _default_process(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Standard dream processing."""
        dream = self._create_dream(invocation)
        self._review_queue.append(dream.dream_id)

        return {
            "dream": dream.to_dict(),
            "queued_for_review": True,
            "queue_position": len(self._review_queue),
        }

    def _create_dream(self, invocation: Invocation) -> Dream:
        """Create a dream from invocation."""
        dream = Dream(
            content=invocation.symbol,
            charge=invocation.charge,
            dreamer=invocation.organ,
        )

        self._dreams[dream.dream_id] = dream
        return dream

    def _init_symbol_dictionary(self) -> Dict[str, str]:
        """Initialize dream symbol dictionary."""
        return {
            "water": "emotion, unconscious, memory flow",
            "glass": "fragility, transparency, reflection barrier",
            "hallway": "transition, choice, passage through time",
            "door": "opportunity, threshold, change",
            "mirror": "self-reflection, shadow work, identity",
            "fire": "transformation, passion, destruction/renewal",
            "falling": "loss of control, letting go, fear",
            "flying": "freedom, transcendence, escape",
            "teeth": "power, aging, fear of loss",
            "house": "self, psyche, internal architecture",
            "snake": "transformation, hidden knowledge, fear",
            "death": "ending, transformation, new beginning",
            "chase": "avoidance, fear, unresolved issue",
            "child": "innocence, potential, inner child",
            "animal": "instinct, nature, shadow aspect",
        }

    def _extract_symbols(self, content: str) -> List[str]:
        """Extract known symbols from content."""
        content_lower = content.lower()
        found = []

        for symbol in self._symbol_dictionary.keys():
            if symbol in content_lower:
                found.append(symbol)

        return found or ["unknown_glyph"]

    def _decode_symbol(self, symbol: str) -> str:
        """Decode a single symbol."""
        return self._symbol_dictionary.get(
            symbol.lower(),
            "Symbol meaning requires deeper analysis"
        )

    def _synthesize_meanings(self, decodings: Dict[str, str]) -> str:
        """Synthesize multiple symbol meanings."""
        if not decodings:
            return "No symbols decoded"

        meanings = list(decodings.values())
        if len(meanings) == 1:
            return meanings[0]

        return f"Combined meaning: {' + '.join(meanings[:3])}"

    def _generate_interpretation(self, dream: Dream) -> str:
        """Generate full dream interpretation."""
        symbols_meaning = [self._decode_symbol(s) for s in dream.symbols]

        base = f"Dream analysis (charge {dream.charge}, {get_tier(dream.charge)} tier): "

        if dream.charge >= 86:
            base += "This dream carries critical urgency. "
        elif dream.charge >= 71:
            base += "This dream demands attention. "
        else:
            base += "This dream offers gentle guidance. "

        if symbols_meaning:
            base += f"Key themes: {', '.join(symbols_meaning[:3])}."

        return base

    def _generate_dream_map(self, dream: Dream) -> Dict[str, Any]:
        """Generate a dream map structure."""
        return {
            "dream_id": dream.dream_id,
            "core_symbols": dream.symbols,
            "emotional_charge": dream.charge,
            "connections": [
                {"to": "MIRROR_CABINET", "reason": "self-reflection elements"},
                {"to": "ECHO_SHELL", "reason": "recurring pattern potential"},
            ],
            "temporal_layer": "present_processing",
        }

    def _analyze_emotional_layer(self, dream: Dream) -> Dict[str, Any]:
        """Analyze the emotional layer of the dream."""
        content_lower = dream.content.lower()

        emotions = {
            "fear": any(w in content_lower for w in ["afraid", "scared", "fear", "terror"]),
            "grief": any(w in content_lower for w in ["sad", "loss", "grief", "gone"]),
            "joy": any(w in content_lower for w in ["happy", "joy", "light", "peace"]),
            "anger": any(w in content_lower for w in ["angry", "rage", "furious"]),
            "love": any(w in content_lower for w in ["love", "heart", "embrace"]),
        }

        detected = [e for e, present in emotions.items() if present]

        return {
            "detected_emotions": detected or ["complex/undefined"],
            "primary_emotion": detected[0] if detected else "undefined",
            "charge_supports": get_tier(dream.charge),
        }

    def _recommend_ritual(self, dream: Dream) -> Dict[str, Any]:
        """Recommend a ritual based on dream content."""
        if dream.charge >= 86:
            return {
                "type": "emergency_processing",
                "steps": ["Record immediately", "Seek RITUAL_COURT session", "Do not suppress"],
            }
        elif dream.charge >= 71:
            return {
                "type": "active_integration",
                "steps": ["Journal the dream fully", "Identify recurrence patterns", "Create symbol art"],
            }
        else:
            return {
                "type": "gentle_observation",
                "steps": ["Note key symbols", "Allow natural processing", "Check for recurrence"],
            }

    def _propose_law_from_dream(self, dream: Dream) -> Dict[str, Any]:
        """Propose a law based on dream content."""
        if not dream.symbols:
            return None

        primary_symbol = dream.symbols[0]

        proposal = {
            "law_id": f"LAW_DREAM_{len(self._proposed_laws) + 1:02d}",
            "name": f"{primary_symbol.title()} Speaks",
            "description": f"Pattern observed in dream: {dream.content[:50]}...",
            "source": dream.dream_id,
            "prophecy_weight": dream.prophecy_weight,
        }

        self._proposed_laws.append(proposal)
        return proposal

    def _generate_archive_symbol(self, dream: Dream) -> str:
        """Generate an archive symbol for the dream."""
        tier = get_tier(dream.charge)
        primary = dream.symbols[0] if dream.symbols else "void"

        return f"DREAM_{tier}_{primary.upper()}"

    def get_valid_modes(self) -> List[str]:
        return ["prophetic_lawmaking", "glyph_decode", "interpretation", "default"]

    def get_output_types(self) -> List[str]:
        return ["law_proposal", "archive_symbol", "dream_map"]

    def get_dream(self, dream_id: str) -> Optional[Dream]:
        """Get a dream by ID."""
        return self._dreams.get(dream_id)

    def get_review_queue(self) -> List[Dream]:
        """Get dreams pending review."""
        return [self._dreams[did] for did in self._review_queue if did in self._dreams]
