"""
RE:GE Mask Engine - Identity layers and persona assembly.

Based on: RE-GE_ORG_BODY_11_MASK_ENGINE.md

The Mask Engine governs:
- Persona assembly and management
- Identity layering
- Mask inheritance
- Role shifting
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from rege.organs.base import OrganHandler
from rege.core.models import Invocation, Patch
from rege.core.constants import get_tier


class Mask:
    """A persona/mask that can be worn."""

    def __init__(
        self,
        name: str,
        archetype: str,
        charge: int,
        traits: List[str],
        inherited_from: Optional[str] = None,
    ):
        self.mask_id = f"MASK_{uuid.uuid4().hex[:8].upper()}"
        self.name = name
        self.archetype = archetype
        self.charge = charge
        self.traits = traits
        self.inherited_from = inherited_from
        self.created_at = datetime.now()
        self.wear_count = 0
        self.last_worn = None
        self.active = False
        self.identity_layers: List[str] = []

    def wear(self) -> Dict[str, Any]:
        """Wear this mask."""
        self.wear_count += 1
        self.last_worn = datetime.now()
        self.active = True

        return {
            "mask_id": self.mask_id,
            "name": self.name,
            "status": "worn",
            "wear_count": self.wear_count,
        }

    def remove(self) -> Dict[str, Any]:
        """Remove this mask."""
        self.active = False

        return {
            "mask_id": self.mask_id,
            "name": self.name,
            "status": "removed",
        }

    def add_layer(self, layer_name: str) -> None:
        """Add an identity layer to the mask."""
        if layer_name not in self.identity_layers:
            self.identity_layers.append(layer_name)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mask_id": self.mask_id,
            "name": self.name,
            "archetype": self.archetype,
            "charge": self.charge,
            "traits": self.traits,
            "inherited_from": self.inherited_from,
            "created_at": self.created_at.isoformat(),
            "wear_count": self.wear_count,
            "last_worn": self.last_worn.isoformat() if self.last_worn else None,
            "active": self.active,
            "identity_layers": self.identity_layers,
            "tier": get_tier(self.charge),
        }


class MaskEngine(OrganHandler):
    """
    The Mask Engine - Identity layers and persona assembly.

    Modes:
    - assembly: Construct new personas
    - inheritance: Derive masks from existing ones
    - shift: Transition between personas
    - default: Standard mask operations
    """

    @property
    def name(self) -> str:
        return "MASK_ENGINE"

    @property
    def description(self) -> str:
        return "Identity layers and persona assembly engine"

    def __init__(self):
        super().__init__()
        self._masks: Dict[str, Mask] = {}
        self._active_mask: Optional[str] = None
        self._lineage: Dict[str, List[str]] = {}  # mask_id -> child_ids
        self._archetypes = self._init_archetypes()

    def invoke(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process invocation through Mask Engine."""
        mode = invocation.mode.lower()

        if mode == "assembly":
            return self._assembly(invocation, patch)
        elif mode == "inheritance":
            return self._inheritance(invocation, patch)
        elif mode == "shift":
            return self._shift(invocation, patch)
        else:
            return self._default_process(invocation, patch)

    def _assembly(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Construct a new persona."""
        # Extract mask properties from symbol
        name = self._extract_mask_name(invocation.symbol)
        archetype = self._identify_archetype(invocation.symbol)
        traits = self._extract_traits(invocation.symbol)

        mask = Mask(
            name=name,
            archetype=archetype,
            charge=invocation.charge,
            traits=traits,
        )

        self._masks[mask.mask_id] = mask

        return {
            "mask": mask.to_dict(),
            "status": "assembled",
            "archetype_properties": self._archetypes.get(archetype, {}),
            "ready_to_wear": invocation.charge >= 51,
        }

    def _inheritance(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Derive a mask from an existing one."""
        # Find parent mask
        parent_id = self._find_mask_by_content(invocation.symbol)

        if not parent_id or parent_id not in self._masks:
            return {
                "status": "parent_not_found",
                "searched_for": invocation.symbol,
                "suggestion": "Create a mask first using assembly mode",
            }

        parent = self._masks[parent_id]

        # Create child mask
        child = Mask(
            name=f"{parent.name}_Heir",
            archetype=parent.archetype,
            charge=min(100, parent.charge + 5),  # Inherited masks gain slight charge
            traits=parent.traits.copy(),
            inherited_from=parent.mask_id,
        )

        # Track lineage
        if parent.mask_id not in self._lineage:
            self._lineage[parent.mask_id] = []
        self._lineage[parent.mask_id].append(child.mask_id)

        self._masks[child.mask_id] = child

        return {
            "child_mask": child.to_dict(),
            "parent_mask": parent.to_dict(),
            "inheritance_chain": self._get_lineage_chain(child.mask_id),
            "status": "inherited",
        }

    def _shift(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Transition between personas."""
        target_id = self._find_mask_by_content(invocation.symbol)

        result = {"shift_requested": True}

        # Remove current mask if any
        if self._active_mask:
            current = self._masks.get(self._active_mask)
            if current:
                result["removed"] = current.remove()

        # Wear new mask if found
        if target_id and target_id in self._masks:
            new_mask = self._masks[target_id]
            result["worn"] = new_mask.wear()
            self._active_mask = target_id
            result["status"] = "shifted"
        else:
            self._active_mask = None
            result["status"] = "bare" if target_id else "target_not_found"

        return result

    def _default_process(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Standard mask operations."""
        active = self._masks.get(self._active_mask) if self._active_mask else None

        return {
            "active_mask": active.to_dict() if active else None,
            "total_masks": len(self._masks),
            "available_archetypes": list(self._archetypes.keys()),
            "status": "worn" if active else "bare",
        }

    def _init_archetypes(self) -> Dict[str, Dict[str, Any]]:
        """Initialize archetype definitions."""
        return {
            "Hero": {
                "core_trait": "courage",
                "shadow": "hubris",
                "function": "overcoming obstacles",
            },
            "Sage": {
                "core_trait": "wisdom",
                "shadow": "detachment",
                "function": "seeking truth",
            },
            "Rebel": {
                "core_trait": "liberation",
                "shadow": "destruction",
                "function": "breaking rules",
            },
            "Lover": {
                "core_trait": "passion",
                "shadow": "obsession",
                "function": "connection and intimacy",
            },
            "Creator": {
                "core_trait": "imagination",
                "shadow": "perfectionism",
                "function": "making new things",
            },
            "Caregiver": {
                "core_trait": "compassion",
                "shadow": "martyrdom",
                "function": "nurturing others",
            },
            "Ruler": {
                "core_trait": "control",
                "shadow": "tyranny",
                "function": "ordering and leading",
            },
            "Magician": {
                "core_trait": "transformation",
                "shadow": "manipulation",
                "function": "changing reality",
            },
            "Jester": {
                "core_trait": "joy",
                "shadow": "irresponsibility",
                "function": "living fully",
            },
            "Orphan": {
                "core_trait": "resilience",
                "shadow": "victimhood",
                "function": "surviving",
            },
            "Shadow": {
                "core_trait": "hidden power",
                "shadow": "self-destruction",
                "function": "revealing denied aspects",
            },
            "Witness": {
                "core_trait": "presence",
                "shadow": "dissociation",
                "function": "observing without judgment",
            },
        }

    def _extract_mask_name(self, symbol: str) -> str:
        """Extract mask name from symbol."""
        words = symbol.split()[:3]
        return "_".join(w.capitalize() for w in words) or "Unnamed_Mask"

    def _identify_archetype(self, symbol: str) -> str:
        """Identify archetype from symbol content."""
        symbol_lower = symbol.lower()

        archetype_keywords = {
            "Hero": ["hero", "brave", "fight", "overcome"],
            "Sage": ["wise", "knowledge", "truth", "learn"],
            "Rebel": ["rebel", "break", "rule", "against"],
            "Lover": ["love", "passion", "connect", "heart"],
            "Creator": ["create", "make", "art", "build"],
            "Caregiver": ["care", "help", "nurture", "support"],
            "Ruler": ["lead", "control", "order", "power"],
            "Magician": ["transform", "change", "magic", "alchemy"],
            "Jester": ["joy", "play", "fun", "laugh"],
            "Shadow": ["shadow", "dark", "hidden", "deny"],
            "Witness": ["observe", "watch", "witness", "see"],
        }

        for archetype, keywords in archetype_keywords.items():
            if any(kw in symbol_lower for kw in keywords):
                return archetype

        return "Orphan"  # Default archetype

    def _extract_traits(self, symbol: str) -> List[str]:
        """Extract traits from symbol."""
        trait_keywords = [
            "strong", "weak", "kind", "cruel", "wise", "foolish",
            "brave", "fearful", "loving", "cold", "creative", "rigid",
        ]

        symbol_lower = symbol.lower()
        found = [t for t in trait_keywords if t in symbol_lower]

        return found or ["undefined"]

    def _find_mask_by_content(self, content: str) -> Optional[str]:
        """Find a mask by content/name similarity."""
        content_lower = content.lower()

        # Check for direct ID reference
        for mask_id in self._masks.keys():
            if mask_id.lower() in content_lower:
                return mask_id

        # Check for name match
        for mask_id, mask in self._masks.items():
            if mask.name.lower() in content_lower:
                return mask_id

        return None

    def _get_lineage_chain(self, mask_id: str) -> List[str]:
        """Get the inheritance chain for a mask."""
        chain = []
        current = self._masks.get(mask_id)

        while current and current.inherited_from:
            chain.insert(0, current.inherited_from)
            current = self._masks.get(current.inherited_from)

        chain.append(mask_id)
        return chain

    def get_valid_modes(self) -> List[str]:
        return ["assembly", "inheritance", "shift", "default"]

    def get_output_types(self) -> List[str]:
        return ["persona", "mask_record", "identity_layer"]

    def get_mask(self, mask_id: str) -> Optional[Mask]:
        """Get a mask by ID."""
        return self._masks.get(mask_id)

    def get_all_masks(self) -> List[Mask]:
        """Get all masks."""
        return list(self._masks.values())

    def get_active_mask(self) -> Optional[Mask]:
        """Get the currently active mask."""
        if self._active_mask:
            return self._masks.get(self._active_mask)
        return None
