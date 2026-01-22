"""
RE:GE Organs - Symbolic processing organs of the system.

Each organ implements specific mythic functions:
- HEART_OF_CANON: Canon events and mythic truth
- MIRROR_CABINET: Emotional processing and contradiction
- MYTHIC_SENATE: Law governance and voting
- ARCHIVE_ORDER: Storage and retrieval
- RITUAL_COURT: Ceremonial logic and verdicts
- CODE_FORGE: Symbol-to-code translation
- BLOOM_ENGINE: Generative growth and mutation
- SOUL_PATCHBAY: Routing hub (handled by routing module)
- ECHO_SHELL: Decay and whispered loops
- DREAM_COUNCIL: Prophecy and dream processing
- MASK_ENGINE: Identity and persona assembly
"""

from rege.organs.base import OrganHandler
from rege.organs.registry import OrganRegistry, get_organ_registry
from rege.organs.heart_of_canon import HeartOfCanon
from rege.organs.mirror_cabinet import MirrorCabinet
from rege.organs.mythic_senate import MythicSenate
from rege.organs.archive_order import ArchiveOrder
from rege.organs.ritual_court import RitualCourt
from rege.organs.code_forge import CodeForge
from rege.organs.bloom_engine import BloomEngine
from rege.organs.echo_shell import EchoShell
from rege.organs.dream_council import DreamCouncil
from rege.organs.mask_engine import MaskEngine

__all__ = [
    # Base
    "OrganHandler",
    "OrganRegistry",
    "get_organ_registry",
    # Organs
    "HeartOfCanon",
    "MirrorCabinet",
    "MythicSenate",
    "ArchiveOrder",
    "RitualCourt",
    "CodeForge",
    "BloomEngine",
    "EchoShell",
    "DreamCouncil",
    "MaskEngine",
]
