"""
RE:GE - Recursive Engine: Generative Entity

A symbolic operating system for myth, identity, ritual, and recursive systems.
"""

__version__ = "1.0.0"
__author__ = "RE:GE System"

from rege.core.models import (
    Fragment,
    Patch,
    Invocation,
    FusedFragment,
    CanonEvent,
    StateSnapshot,
)
from rege.core.constants import (
    ChargeTier,
    Priority,
    DepthLimits,
    get_tier,
    get_tier_level,
    get_priority,
    is_canonization_eligible,
    is_fusion_eligible,
    is_critical_emergency,
)
from rege.parser.invocation_parser import InvocationParser
from rege.routing.patchbay import PatchQueue
from rege.routing.dispatcher import Dispatcher

__all__ = [
    # Models
    "Fragment",
    "Patch",
    "Invocation",
    "FusedFragment",
    "CanonEvent",
    "StateSnapshot",
    # Constants
    "ChargeTier",
    "Priority",
    "DepthLimits",
    "get_tier",
    "get_tier_level",
    "get_priority",
    "is_canonization_eligible",
    "is_fusion_eligible",
    "is_critical_emergency",
    # Parser
    "InvocationParser",
    # Routing
    "PatchQueue",
    "Dispatcher",
]
