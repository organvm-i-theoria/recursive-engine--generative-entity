"""
RE:GE Process→Product Converter - Converts lived process into sharable forms.

Based on: RE-GE_ORG_BODY_19_PROCESS_PRODUCT.md

The Process→Product Converter governs:
- Readiness evaluation for conversion
- Format transformation (scroll, pdf, app, maxpatch, drop)
- Visibility tier assignment (sacred, public, paid, collectible)
- Compression loss tracking
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid

from rege.organs.base import OrganHandler
from rege.core.models import Invocation, Patch


class ProductFormat(Enum):
    """Output formats for converted products."""
    SCROLL = "scroll"          # Long-form text/narrative
    PDF = "pdf"                # Static document
    APP = "app"                # Interactive application
    MAXPATCH = "maxpatch"      # Max/MSP patch
    DROP = "drop"              # Minimal release/artifact
    GLYPH = "glyph"            # Symbolic image/token
    RITUAL_CODE = "ritual_code"  # Executable ritual


class VisibilityTier(Enum):
    """Visibility tiers for products."""
    SACRED = "sacred"          # Private, personal only
    PUBLIC = "public"          # Open to all
    PAID = "paid"              # Requires transaction
    COLLECTIBLE = "collectible"  # Limited, tradeable


@dataclass
class RitualProduct:
    """
    A product converted from lived process.

    Tracks the transformation from process to shareable form,
    including format, tier, and information loss.
    """
    product_id: str
    source_symbol: str
    format: ProductFormat
    tier: VisibilityTier
    charge_at_conversion: int
    depth_at_conversion: int
    compression_loss: float  # 0.0 - 1.0, information lost in conversion
    created_at: datetime
    resolved: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.product_id:
            self.product_id = f"PRODUCT_{uuid.uuid4().hex[:8].upper()}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize product to dictionary."""
        return {
            "product_id": self.product_id,
            "source_symbol": self.source_symbol,
            "format": self.format.value,
            "tier": self.tier.value,
            "charge_at_conversion": self.charge_at_conversion,
            "depth_at_conversion": self.depth_at_conversion,
            "compression_loss": self.compression_loss,
            "created_at": self.created_at.isoformat(),
            "resolved": self.resolved,
            "metadata": self.metadata,
        }


# Readiness thresholds
READINESS_CONFIG = {
    "min_charge": 71,        # INTENSE tier minimum
    "min_depth": 5,          # Sufficient processing depth
    "requires_resolution": True,
}

# Format recommendations by charge range
FORMAT_RECOMMENDATIONS = {
    (86, 100): [ProductFormat.APP, ProductFormat.MAXPATCH, ProductFormat.RITUAL_CODE],
    (71, 85): [ProductFormat.SCROLL, ProductFormat.PDF, ProductFormat.GLYPH],
    (51, 70): [ProductFormat.DROP, ProductFormat.GLYPH],
    (0, 50): [ProductFormat.DROP],
}

# Compression loss by format (how much is lost in translation)
COMPRESSION_LOSS = {
    ProductFormat.SCROLL: 0.1,
    ProductFormat.PDF: 0.2,
    ProductFormat.APP: 0.05,
    ProductFormat.MAXPATCH: 0.15,
    ProductFormat.DROP: 0.4,
    ProductFormat.GLYPH: 0.3,
    ProductFormat.RITUAL_CODE: 0.08,
}


class ProcessProductConverter(OrganHandler):
    """
    Process→Product Converter - Converts lived process into sharable forms.

    Modes:
    - evaluate: Check conversion readiness
    - convert: Transform process to product
    - tier: Assign visibility tier
    - formats: List available formats
    - default: Conversion status
    """

    @property
    def name(self) -> str:
        return "PROCESS_PRODUCT"

    @property
    def description(self) -> str:
        return "Converts lived process into sharable forms"

    def __init__(self):
        super().__init__()
        self._products: Dict[str, RitualProduct] = {}
        self._conversion_history: List[Dict[str, Any]] = []
        self._pending_conversions: Dict[str, Dict[str, Any]] = {}

    def invoke(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process invocation through Process→Product Converter."""
        mode = invocation.mode.lower()

        if mode == "evaluate":
            return self._evaluate_readiness(invocation, patch)
        elif mode == "convert":
            return self._convert_process(invocation, patch)
        elif mode == "tier":
            return self._assign_tier(invocation, patch)
        elif mode == "formats":
            return self._list_formats(invocation, patch)
        else:
            return self._default_status(invocation, patch)

    def _evaluate_readiness(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Evaluate if process is ready for conversion."""
        charge = invocation.charge
        depth = patch.depth

        # Check resolution status (assume resolved unless INCOMPLETE+ flag)
        resolved = "INCOMPLETE+" not in invocation.flags

        # Check all readiness criteria
        charge_ready = charge >= READINESS_CONFIG["min_charge"]
        depth_ready = depth >= READINESS_CONFIG["min_depth"]
        resolution_ready = resolved or not READINESS_CONFIG["requires_resolution"]

        is_ready = charge_ready and depth_ready and resolution_ready

        # Build readiness report
        readiness_report = {
            "charge": {
                "current": charge,
                "required": READINESS_CONFIG["min_charge"],
                "ready": charge_ready,
                "gap": max(0, READINESS_CONFIG["min_charge"] - charge),
            },
            "depth": {
                "current": depth,
                "required": READINESS_CONFIG["min_depth"],
                "ready": depth_ready,
                "gap": max(0, READINESS_CONFIG["min_depth"] - depth),
            },
            "resolution": {
                "resolved": resolved,
                "ready": resolution_ready,
            },
        }

        # Suggest formats based on current charge
        suggested_formats = self._suggest_formats(charge)

        return {
            "status": "ready" if is_ready else "not_ready",
            "is_ready": is_ready,
            "readiness_report": readiness_report,
            "suggested_formats": [f.value for f in suggested_formats],
            "symbol": invocation.symbol[:50] if invocation.symbol else "unnamed",
        }

    def _convert_process(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Convert process to product."""
        charge = invocation.charge
        depth = patch.depth
        resolved = "INCOMPLETE+" not in invocation.flags

        # Check readiness
        if charge < READINESS_CONFIG["min_charge"]:
            return {
                "status": "failed",
                "error": "Charge below conversion threshold",
                "required": READINESS_CONFIG["min_charge"],
                "current": charge,
            }

        if depth < READINESS_CONFIG["min_depth"]:
            return {
                "status": "failed",
                "error": "Depth below conversion threshold",
                "required": READINESS_CONFIG["min_depth"],
                "current": depth,
            }

        # Determine format from flags or suggest
        format_type = self._determine_format(invocation.flags, charge)

        # Determine visibility tier
        tier = self._determine_tier(invocation.flags, charge)

        # Calculate compression loss
        compression_loss = COMPRESSION_LOSS.get(format_type, 0.2)

        # Adjust for depth (deeper processing = less loss)
        depth_bonus = min(0.1, depth * 0.01)
        final_loss = max(0.0, compression_loss - depth_bonus)

        # Create product
        product = RitualProduct(
            product_id="",
            source_symbol=invocation.symbol[:100] if invocation.symbol else "unnamed",
            format=format_type,
            tier=tier,
            charge_at_conversion=charge,
            depth_at_conversion=depth,
            compression_loss=round(final_loss, 3),
            created_at=datetime.now(),
            resolved=resolved,
            metadata={
                "flags": invocation.flags,
                "invocation_id": invocation.invocation_id,
            },
        )

        self._products[product.product_id] = product

        # Record conversion
        self._conversion_history.append({
            "product_id": product.product_id,
            "timestamp": datetime.now().isoformat(),
            "charge": charge,
            "format": format_type.value,
        })

        return {
            "status": "converted",
            "product": product.to_dict(),
            "compression_loss_percent": round(final_loss * 100, 1),
            "information_preserved_percent": round((1 - final_loss) * 100, 1),
        }

    def _assign_tier(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Assign or reassign visibility tier to a product."""
        # Parse product ID and new tier from symbol: "PRODUCT_ID:TIER"
        parts = invocation.symbol.split(":")
        if len(parts) < 2:
            # Just return tier recommendation for current charge
            tier = self._determine_tier(invocation.flags, invocation.charge)
            return {
                "status": "tier_recommended",
                "recommended_tier": tier.value,
                "charge": invocation.charge,
                "tier_descriptions": {
                    "sacred": "Private, personal only",
                    "public": "Open to all",
                    "paid": "Requires transaction",
                    "collectible": "Limited, tradeable",
                },
            }

        product_id = parts[0].strip().upper()
        tier_str = parts[1].strip().lower()

        # Validate tier
        try:
            new_tier = VisibilityTier(tier_str)
        except ValueError:
            return {
                "status": "failed",
                "error": f"Invalid tier: {tier_str}",
                "valid_tiers": [t.value for t in VisibilityTier],
            }

        # Find and update product
        if product_id not in self._products:
            return {
                "status": "failed",
                "error": f"Product not found: {product_id}",
            }

        product = self._products[product_id]
        old_tier = product.tier
        product.tier = new_tier

        return {
            "status": "tier_assigned",
            "product_id": product_id,
            "old_tier": old_tier.value,
            "new_tier": new_tier.value,
        }

    def _list_formats(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """List available formats with recommendations."""
        charge = invocation.charge
        suggested = self._suggest_formats(charge)

        format_details = {}
        for fmt in ProductFormat:
            loss = COMPRESSION_LOSS.get(fmt, 0.2)
            format_details[fmt.value] = {
                "compression_loss": loss,
                "information_preserved": round(1 - loss, 2),
                "recommended_for_charge": fmt in suggested,
            }

        return {
            "status": "formats_listed",
            "current_charge": charge,
            "formats": format_details,
            "recommended": [f.value for f in suggested],
        }

    def _default_status(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Return conversion status."""
        return {
            "status": "converter_status",
            "total_products": len(self._products),
            "conversion_history_length": len(self._conversion_history),
            "pending_conversions": len(self._pending_conversions),
            "recent_conversions": self._conversion_history[-5:],
        }

    def _suggest_formats(self, charge: int) -> List[ProductFormat]:
        """Suggest formats based on charge level."""
        for (low, high), formats in FORMAT_RECOMMENDATIONS.items():
            if low <= charge <= high:
                return formats
        return [ProductFormat.DROP]

    def _determine_format(self, flags: List[str], charge: int) -> ProductFormat:
        """Determine format from flags or charge."""
        # Check for explicit format flags
        format_flags = {
            "SCROLL+": ProductFormat.SCROLL,
            "PDF+": ProductFormat.PDF,
            "APP+": ProductFormat.APP,
            "MAXPATCH+": ProductFormat.MAXPATCH,
            "DROP+": ProductFormat.DROP,
            "GLYPH+": ProductFormat.GLYPH,
            "RITUAL_CODE+": ProductFormat.RITUAL_CODE,
        }

        for flag, fmt in format_flags.items():
            if flag in flags:
                return fmt

        # Use charge-based suggestion
        suggested = self._suggest_formats(charge)
        return suggested[0] if suggested else ProductFormat.DROP

    def _determine_tier(self, flags: List[str], charge: int) -> VisibilityTier:
        """Determine visibility tier from flags or charge."""
        # Check for explicit tier flags
        if "SACRED+" in flags:
            return VisibilityTier.SACRED
        if "PUBLIC+" in flags:
            return VisibilityTier.PUBLIC
        if "PAID+" in flags:
            return VisibilityTier.PAID
        if "COLLECTIBLE+" in flags:
            return VisibilityTier.COLLECTIBLE

        # Charge-based tier
        if charge >= 86:
            return VisibilityTier.COLLECTIBLE
        elif charge >= 71:
            return VisibilityTier.PAID
        elif charge >= 51:
            return VisibilityTier.PUBLIC
        else:
            return VisibilityTier.SACRED

    def get_product(self, product_id: str) -> Optional[RitualProduct]:
        """Get product by ID."""
        return self._products.get(product_id)

    def get_products_by_tier(self, tier: VisibilityTier) -> List[RitualProduct]:
        """Get all products of a specific tier."""
        return [p for p in self._products.values() if p.tier == tier]

    def get_products_by_format(self, format_type: ProductFormat) -> List[RitualProduct]:
        """Get all products of a specific format."""
        return [p for p in self._products.values() if p.format == format_type]

    def get_valid_modes(self) -> List[str]:
        return ["evaluate", "convert", "tier", "formats", "default"]

    def get_output_types(self) -> List[str]:
        return ["readiness_report", "product", "tier_assignment", "format_list", "converter_status"]

    def get_state(self) -> Dict[str, Any]:
        """Get current organ state for checkpointing."""
        state = super().get_state()
        state["state"].update({
            "products": {k: v.to_dict() for k, v in self._products.items()},
            "conversion_history": self._conversion_history,
        })
        return state

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore organ state from checkpoint."""
        super().restore_state(state)
        inner_state = state.get("state", {})
        self._conversion_history = inner_state.get("conversion_history", [])
        # Note: products restoration would require RitualProduct deserialization

    def reset(self) -> None:
        """Reset organ to initial state."""
        super().reset()
        self._products = {}
        self._conversion_history = []
        self._pending_conversions = {}
