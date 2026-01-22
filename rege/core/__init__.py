"""
RE:GE Core - Foundational models, constants, and exceptions.
"""

from rege.core.constants import (
    ChargeTier,
    Priority,
    DepthLimits,
    CHARGE_TIERS,
    get_tier,
    get_tier_level,
    get_priority,
    is_canonization_eligible,
    is_fusion_eligible,
    is_critical_emergency,
)
from rege.core.models import (
    Fragment,
    Patch,
    Invocation,
    FusedFragment,
    CanonEvent,
    StateSnapshot,
    DepthLevel,
    FusionMode,
    FusionType,
    ChargeCalculation,
    RecoveryMode,
    RecoveryTrigger,
)
from rege.core.exceptions import (
    RegeError,
    InvocationError,
    RoutingError,
    DepthLimitExceeded,
    FusionError,
    RecoveryError,
    OrganNotFoundError,
    ValidationError,
)

__all__ = [
    # Constants
    "ChargeTier",
    "Priority",
    "DepthLimits",
    "CHARGE_TIERS",
    "get_tier",
    "get_tier_level",
    "get_priority",
    "is_canonization_eligible",
    "is_fusion_eligible",
    "is_critical_emergency",
    # Models
    "Fragment",
    "Patch",
    "Invocation",
    "FusedFragment",
    "CanonEvent",
    "StateSnapshot",
    "DepthLevel",
    "FusionMode",
    "FusionType",
    "ChargeCalculation",
    "RecoveryMode",
    "RecoveryTrigger",
    # Exceptions
    "RegeError",
    "InvocationError",
    "RoutingError",
    "DepthLimitExceeded",
    "FusionError",
    "RecoveryError",
    "OrganNotFoundError",
    "ValidationError",
]
