"""
RE:GE Orchestration Module - Workflow orchestration for ritual chains.

Based on: RE-GE Enhancement Suite Plan - Phase 5

Provides:
- Phase and Branch definitions for workflow steps
- RitualChain for multi-step workflow orchestration
- ChainExecution tracking for execution history
- Built-in ritual chains (canonization, contradiction resolution, etc.)
"""

from rege.orchestration.phase import Phase, Branch, PhaseResult
from rege.orchestration.chain import RitualChain, ChainExecution
from rege.orchestration.registry import ChainRegistry, get_chain_registry
from rege.orchestration.orchestrator import RitualChainOrchestrator

__all__ = [
    "Phase",
    "Branch",
    "PhaseResult",
    "RitualChain",
    "ChainExecution",
    "ChainRegistry",
    "get_chain_registry",
    "RitualChainOrchestrator",
]
