"""
RE:GE Orchestration - Built-in Ritual Chains.

Pre-defined ritual chains for common workflows.
"""

from rege.orchestration.phase import (
    Phase,
    Branch,
    charge_condition,
    tag_condition,
    verdict_condition,
    status_condition,
    combined_condition,
)
from rege.orchestration.chain import RitualChain
from rege.orchestration.registry import get_chain_registry


def create_canonization_ceremony() -> RitualChain:
    """
    Create the Canonization Ceremony chain.

    Phases: HEART_OF_CANON -> RITUAL_COURT -> FUSE01 -> ARCHIVE_ORDER

    Branches:
    - If charge >= 71: proceed to RITUAL_COURT
    - If verdict is "canonize": proceed to FUSE01
    - If verdict is "reject": skip to ARCHIVE_ORDER
    """
    chain = RitualChain(
        name="canonization_ceremony",
        description="Ceremony for canonizing high-charge fragments",
        tags=["ceremony", "canon", "ritual"],
    )

    # Phase 1: Heart of Canon - Initial assessment
    chain.add_phase(Phase(
        name="canon_assessment",
        organ="HEART_OF_CANON",
        mode="assess_candidate",
        description="Assess fragment for canon worthiness",
    ))

    # Phase 2: Ritual Court - Deliberation
    chain.add_phase(Phase(
        name="court_deliberation",
        organ="RITUAL_COURT",
        mode="deliberate",
        description="Court deliberates on canonization",
        condition=charge_condition(min_charge=71),
    ))

    # Phase 3: FUSE01 - Fusion (if approved)
    chain.add_phase(Phase(
        name="fusion_merge",
        organ="FUSE01",
        mode="merge",
        description="Merge fragment into canon",
        condition=verdict_condition("canonize"),
    ))

    # Phase 4: Archive Order - Record event
    chain.add_phase(Phase(
        name="archive_record",
        organ="ARCHIVE_ORDER",
        mode="record",
        description="Archive the canonization event",
    ))

    # Add branches
    chain.add_branch(
        "court_deliberation",
        Branch(
            name="approved_for_fusion",
            condition=verdict_condition("canonize"),
            target_phase="fusion_merge",
            priority=10,
            description="Canon approved, proceed to fusion",
        ),
    )

    chain.add_branch(
        "court_deliberation",
        Branch(
            name="rejected_archive_only",
            condition=verdict_condition("reject"),
            target_phase="archive_record",
            priority=5,
            description="Canon rejected, archive only",
        ),
    )

    return chain


def create_contradiction_resolution() -> RitualChain:
    """
    Create the Contradiction Resolution chain.

    Phases: HEART_OF_CANON -> RITUAL_COURT -> (BLOOM_ENGINE or FUSE01)

    Handles contradictions between fragments or canon events.
    """
    chain = RitualChain(
        name="contradiction_resolution",
        description="Resolution workflow for contradictions",
        tags=["resolution", "contradiction", "ritual"],
    )

    # Phase 1: Heart of Canon - Identify contradiction
    chain.add_phase(Phase(
        name="identify_contradiction",
        organ="HEART_OF_CANON",
        mode="detect_conflict",
        description="Identify the nature of the contradiction",
    ))

    # Phase 2: Ritual Court - Judge contradiction
    chain.add_phase(Phase(
        name="judge_contradiction",
        organ="RITUAL_COURT",
        mode="judge_conflict",
        description="Court judges the contradiction",
    ))

    # Phase 3a: Bloom Engine - Generate synthesis
    chain.add_phase(Phase(
        name="bloom_synthesis",
        organ="BLOOM_ENGINE",
        mode="synthesize",
        description="Generate synthesis of contradictory elements",
        condition=verdict_condition("synthesize"),
    ))

    # Phase 3b: FUSE01 - Merge resolution
    chain.add_phase(Phase(
        name="fuse_resolution",
        organ="FUSE01",
        mode="resolve_conflict",
        description="Merge fragments to resolve contradiction",
        condition=verdict_condition("merge"),
    ))

    # Phase 4: Archive - Record resolution
    chain.add_phase(Phase(
        name="archive_resolution",
        organ="ARCHIVE_ORDER",
        mode="record_resolution",
        description="Archive the resolution",
    ))

    # Branches from court judgment
    chain.add_branch(
        "judge_contradiction",
        Branch(
            name="route_to_bloom",
            condition=verdict_condition("synthesize"),
            target_phase="bloom_synthesis",
            priority=10,
        ),
    )

    chain.add_branch(
        "judge_contradiction",
        Branch(
            name="route_to_fuse",
            condition=verdict_condition("merge"),
            target_phase="fuse_resolution",
            priority=10,
        ),
    )

    return chain


def create_grief_processing() -> RitualChain:
    """
    Create the Grief Processing chain.

    Phases: RITUAL_COURT (grief_ritual) -> iterative steps -> closure

    Multi-step ritual for processing grief.
    """
    chain = RitualChain(
        name="grief_processing",
        description="Multi-step ritual for grief processing",
        tags=["grief", "ritual", "healing"],
    )

    # Phase 1: Grief Invocation
    chain.add_phase(Phase(
        name="grief_invocation",
        organ="RITUAL_COURT",
        mode="grief_ritual",
        description="Invoke the grief ritual",
    ))

    # Phase 2: Mirror Reflection
    chain.add_phase(Phase(
        name="mirror_reflection",
        organ="MIRROR_CABINET",
        mode="reflect_grief",
        description="Reflect on the source of grief",
    ))

    # Phase 3: Dream Council - Process collectively
    chain.add_phase(Phase(
        name="dream_council",
        organ="DREAM_COUNCIL",
        mode="collective_process",
        description="Process grief through collective dreaming",
    ))

    # Phase 4: Grief Glyph Creation
    chain.add_phase(Phase(
        name="create_glyph",
        organ="CODE_FORGE",
        mode="create_glyph",
        description="Create a grief glyph symbol",
    ))

    # Phase 5: Archive the glyph
    chain.add_phase(Phase(
        name="archive_glyph",
        organ="ARCHIVE_ORDER",
        mode="store_glyph",
        description="Archive the grief glyph",
    ))

    # Phase 6: Closure ritual
    chain.add_phase(Phase(
        name="closure_ritual",
        organ="RITUAL_COURT",
        mode="closure",
        description="Perform closure ritual",
    ))

    # Compensation for interrupted grief processing
    chain.set_compensation(
        "grief_invocation",
        Phase(
            name="grief_shelter",
            organ="RITUAL_COURT",
            mode="shelter",
            description="Provide shelter if grief processing interrupted",
        ),
    )

    return chain


def create_emergency_recovery() -> RitualChain:
    """
    Create the Emergency Recovery chain.

    Phases: RITUAL_COURT (emergency) -> FUSE01 (forced) -> RECOVERY

    Triggered on depth limit exceeded or system crisis.
    """
    chain = RitualChain(
        name="emergency_recovery",
        description="Emergency recovery sequence",
        tags=["emergency", "recovery", "critical"],
    )

    # Phase 1: Emergency declaration
    chain.add_phase(Phase(
        name="declare_emergency",
        organ="RITUAL_COURT",
        mode="emergency_declaration",
        description="Declare system emergency",
    ))

    # Phase 2: Capture panic snapshot
    chain.add_phase(Phase(
        name="panic_snapshot",
        organ="ARCHIVE_ORDER",
        mode="panic_capture",
        description="Capture panic snapshot of system state",
    ))

    # Phase 3: Forced fusion of critical fragments
    chain.add_phase(Phase(
        name="forced_fusion",
        organ="FUSE01",
        mode="emergency_fuse",
        description="Force fusion of critical fragments",
        condition=lambda ctx: ctx.get("fusion_required", False),
    ))

    # Phase 4: Recovery execution
    chain.add_phase(Phase(
        name="execute_recovery",
        organ="RECOVERY",
        mode="execute",
        description="Execute recovery protocol",
    ))

    # Phase 5: Verify system state
    chain.add_phase(Phase(
        name="verify_state",
        organ="ARCHIVE_ORDER",
        mode="verify",
        description="Verify system state after recovery",
    ))

    return chain


def create_seasonal_bloom() -> RitualChain:
    """
    Create the Seasonal Bloom chain.

    Phases: BLOOM_ENGINE -> ARCHIVE_ORDER -> schedule next

    Time-based trigger for seasonal mutations.
    """
    chain = RitualChain(
        name="seasonal_bloom",
        description="Seasonal bloom cycle for mutations",
        tags=["bloom", "seasonal", "mutation"],
    )

    # Phase 1: Bloom calculation
    chain.add_phase(Phase(
        name="calculate_bloom",
        organ="BLOOM_ENGINE",
        mode="calculate_season",
        description="Calculate current bloom phase",
    ))

    # Phase 2: Apply mutations
    chain.add_phase(Phase(
        name="apply_mutations",
        organ="BLOOM_ENGINE",
        mode="mutate",
        description="Apply seasonal mutations",
    ))

    # Phase 3: Version consolidation check
    chain.add_phase(Phase(
        name="check_consolidation",
        organ="ARCHIVE_ORDER",
        mode="check_versions",
        description="Check if version consolidation needed",
    ))

    # Phase 4: Execute consolidation if needed
    chain.add_phase(Phase(
        name="consolidate_versions",
        organ="FUSE01",
        mode="consolidate",
        description="Consolidate versions if threshold reached",
        condition=status_condition("consolidation_needed"),
    ))

    # Phase 5: Archive bloom event
    chain.add_phase(Phase(
        name="archive_bloom",
        organ="ARCHIVE_ORDER",
        mode="record_bloom",
        description="Archive the bloom event",
    ))

    # Branch for consolidation
    chain.add_branch(
        "check_consolidation",
        Branch(
            name="needs_consolidation",
            condition=status_condition("consolidation_needed"),
            target_phase="consolidate_versions",
            priority=10,
        ),
    )

    chain.add_branch(
        "check_consolidation",
        Branch(
            name="skip_consolidation",
            condition=lambda ctx: ctx.get("status") != "consolidation_needed",
            target_phase="archive_bloom",
            priority=5,
        ),
    )

    return chain


def create_fragment_lifecycle() -> RitualChain:
    """
    Create the Fragment Lifecycle chain.

    Complete lifecycle management for fragments.
    """
    chain = RitualChain(
        name="fragment_lifecycle",
        description="Complete fragment lifecycle management",
        tags=["fragment", "lifecycle", "management"],
    )

    # Phase 1: Creation
    chain.add_phase(Phase(
        name="create_fragment",
        organ="HEART_OF_CANON",
        mode="create",
        description="Create new fragment",
    ))

    # Phase 2: Initial charge assignment
    chain.add_phase(Phase(
        name="assign_charge",
        organ="BLOOM_ENGINE",
        mode="calculate_charge",
        description="Calculate and assign initial charge",
    ))

    # Phase 3: Tag assignment
    chain.add_phase(Phase(
        name="assign_tags",
        organ="ARCHIVE_ORDER",
        mode="auto_tag",
        description="Automatically assign tags",
    ))

    # Phase 4: Store in archive
    chain.add_phase(Phase(
        name="store_fragment",
        organ="ARCHIVE_ORDER",
        mode="store",
        description="Store fragment in archive",
    ))

    # Phase 5: Schedule decay
    chain.add_phase(Phase(
        name="schedule_decay",
        organ="BLOOM_ENGINE",
        mode="schedule_decay",
        description="Schedule decay processing",
    ))

    return chain


def register_builtin_chains() -> int:
    """
    Register all built-in chains with the global registry.

    Returns:
        Number of chains registered
    """
    registry = get_chain_registry()

    chains = [
        create_canonization_ceremony(),
        create_contradiction_resolution(),
        create_grief_processing(),
        create_emergency_recovery(),
        create_seasonal_bloom(),
        create_fragment_lifecycle(),
    ]

    registered = 0
    for chain in chains:
        if registry.register(chain):
            registered += 1

    return registered


def get_builtin_chain_names() -> list:
    """Get list of built-in chain names."""
    return [
        "canonization_ceremony",
        "contradiction_resolution",
        "grief_processing",
        "emergency_recovery",
        "seasonal_bloom",
        "fragment_lifecycle",
    ]
