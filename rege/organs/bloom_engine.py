"""
RE:GE Bloom Engine - Generative growth and mutation scheduler.

Based on: RE-GE_ORG_BODY_07_BLOOM_ENGINE.md

The Bloom Engine governs:
- Symbolic transformation over time
- Seasonal states and creative phases
- Self-versioning and mutation
- Loop expiration and ritual renewal
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

from rege.organs.base import OrganHandler
from rege.core.models import Invocation, Patch, Fragment
from rege.core.constants import DepthLimits


class BloomCycle:
    """A bloom cycle managing transformation phases."""

    MUTATION_DEPTH_LIMIT = 7  # Aligns with STANDARD depth limit
    MAX_VERSION_BRANCHES = 5  # Prevent infinite version branching

    def __init__(
        self,
        phase: str,
        trigger_event: str,
        mutation_path: str,
        duration_days: int,
    ):
        self.cycle_id = f"CYCLE_{uuid.uuid4().hex[:8].upper()}"
        self.phase = phase
        self.trigger = trigger_event
        self.mutation_path = mutation_path
        self.duration = duration_days
        self.status = "pending"
        self.mutation_depth = 0
        self.version_branches = 0
        self.created_at = datetime.now()
        self.ends_at = datetime.now() + timedelta(days=duration_days)
        self.mutations: List[Dict] = []

    def initiate(self) -> str:
        """Initiate the bloom cycle."""
        if self.mutation_depth >= self.MUTATION_DEPTH_LIMIT:
            self.status = "consolidated"
            return f"Bloom phase '{self.phase}' at depth limit - forcing consolidation"

        self.status = "active"
        self.mutation_depth += 1
        return f"Bloom phase '{self.phase}' initiated. Mutation path: {self.mutation_path}"

    def branch_version(self) -> bool:
        """Attempt to create version branch."""
        if self.version_branches >= self.MAX_VERSION_BRANCHES:
            self.force_consolidation()
            return False
        self.version_branches += 1
        return True

    def force_consolidation(self) -> Dict[str, Any]:
        """Force consolidation when limits reached."""
        self.status = "consolidated"
        return {
            "action": "FUSE01",
            "reason": "depth_limit_exceeded",
            "mutation_depth": self.mutation_depth,
            "version_branches": self.version_branches,
        }

    def add_mutation(self, mutation_type: str, description: str) -> None:
        """Record a mutation event."""
        self.mutations.append({
            "type": mutation_type,
            "description": description,
            "timestamp": datetime.now().isoformat(),
        })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "phase": self.phase,
            "trigger": self.trigger,
            "mutation_path": self.mutation_path,
            "duration": self.duration,
            "status": self.status,
            "mutation_depth": self.mutation_depth,
            "version_branches": self.version_branches,
            "created_at": self.created_at.isoformat(),
            "ends_at": self.ends_at.isoformat(),
            "mutations": self.mutations,
        }


class BloomEngine(OrganHandler):
    """
    The Bloom Engine - Generative growth and mutation scheduler.

    Modes:
    - seasonal_mutation: Process seasonal transformations
    - growth: Initiate growth cycles
    - versioning: Manage fragment versions
    - default: Standard bloom processing
    """

    @property
    def name(self) -> str:
        return "BLOOM_ENGINE"

    @property
    def description(self) -> str:
        return "Generative growth and mutation scheduler for symbolic transformation"

    def __init__(self):
        super().__init__()
        self._cycles: Dict[str, BloomCycle] = {}
        self._version_registry: Dict[str, List[str]] = {}  # base_id -> version_ids
        self._season_tracker: Dict[str, str] = {}  # entity -> current_season

    def invoke(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process invocation through Bloom Engine."""
        mode = invocation.mode.lower()

        if mode == "seasonal_mutation":
            return self._seasonal_mutation(invocation, patch)
        elif mode == "growth":
            return self._growth(invocation, patch)
        elif mode == "versioning":
            return self._versioning(invocation, patch)
        elif mode == "seasonal_growth":
            return self._seasonal_mutation(invocation, patch)
        else:
            return self._default_bloom(invocation, patch)

    def _seasonal_mutation(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process seasonal transformation."""
        cycle = self.initiate_bloom(
            phase=f"Seasonal_{self._get_current_season()}",
            trigger_event=invocation.symbol,
            mutation_path="+".join(invocation.flags) or "STANDARD",
            duration_days=self._calculate_duration(invocation.charge),
        )

        # Determine mutation type
        mutation_type = self._determine_mutation_type(invocation.charge)
        cycle.add_mutation(mutation_type, invocation.symbol[:100])

        return {
            "cycle": cycle.to_dict(),
            "mutation_type": mutation_type,
            "mutated_fragment": self._create_mutated_fragment(invocation),
            "symbolic_schedule": self._generate_schedule(cycle),
        }

    def _growth(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Initiate growth cycle."""
        cycle = self.initiate_bloom(
            phase="Growth",
            trigger_event=invocation.symbol,
            mutation_path="GROWTH+",
            duration_days=14,  # Standard growth period
        )

        initiation_result = cycle.initiate()

        return {
            "cycle": cycle.to_dict(),
            "initiation": initiation_result,
            "growth_potential": invocation.charge / 100,
            "recommended_actions": self._growth_recommendations(invocation.charge),
        }

    def _versioning(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Manage fragment versions."""
        base_id = self._extract_base_id(invocation.symbol)

        # Track version
        if base_id not in self._version_registry:
            self._version_registry[base_id] = []

        version_count = len(self._version_registry[base_id]) + 1
        new_version_id = f"{base_id}_v{version_count}.0"
        self._version_registry[base_id].append(new_version_id)

        # Check if consolidation needed
        consolidation_needed = version_count >= 3

        result = {
            "base_id": base_id,
            "new_version": new_version_id,
            "total_versions": version_count,
            "version_map": self._version_registry[base_id],
        }

        if consolidation_needed:
            result["consolidation_needed"] = True
            result["recommendation"] = "Trigger FUSE01 to consolidate versions"

        return result

    def _default_bloom(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Standard bloom processing."""
        return {
            "status": "bloom_acknowledged",
            "symbol": invocation.symbol,
            "charge": invocation.charge,
            "bloom_potential": self._calculate_bloom_potential(invocation.charge),
            "season": self._get_current_season(),
        }

    def initiate_bloom(
        self,
        phase: str,
        trigger_event: str,
        mutation_path: str,
        duration_days: int,
    ) -> BloomCycle:
        """
        Initiate a new bloom cycle.

        Args:
            phase: Name of the bloom phase
            trigger_event: Event that triggered the bloom
            mutation_path: Path of mutation (tags)
            duration_days: Duration of the cycle

        Returns:
            The created BloomCycle
        """
        cycle = BloomCycle(phase, trigger_event, mutation_path, duration_days)
        self._cycles[cycle.cycle_id] = cycle
        return cycle

    def branch_version(self, cycle_id: str) -> Dict[str, Any]:
        """
        Attempt to create a version branch.

        Args:
            cycle_id: ID of the cycle

        Returns:
            Branch result
        """
        if cycle_id not in self._cycles:
            return {"status": "failed", "reason": "Cycle not found"}

        cycle = self._cycles[cycle_id]
        success = cycle.branch_version()

        if success:
            return {
                "status": "branched",
                "cycle_id": cycle_id,
                "branch_number": cycle.version_branches,
            }
        else:
            return {
                "status": "consolidated",
                "reason": "Max branches reached",
                "consolidation": cycle.force_consolidation(),
            }

    def force_consolidation(self, cycle_id: str) -> Dict[str, Any]:
        """
        Force consolidation of a cycle.

        Args:
            cycle_id: ID of the cycle

        Returns:
            Consolidation result
        """
        if cycle_id not in self._cycles:
            return {"status": "failed", "reason": "Cycle not found"}

        cycle = self._cycles[cycle_id]
        return cycle.force_consolidation()

    def _get_current_season(self) -> str:
        """Determine current symbolic season."""
        month = datetime.now().month
        if month in [3, 4, 5]:
            return "SPRING"
        elif month in [6, 7, 8]:
            return "SUMMER"
        elif month in [9, 10, 11]:
            return "AUTUMN"
        else:
            return "WINTER"

    def _calculate_duration(self, charge: int) -> int:
        """Calculate bloom duration based on charge."""
        if charge >= 86:
            return 30  # Critical - month-long cycle
        elif charge >= 71:
            return 21  # Intense - 3 weeks
        elif charge >= 51:
            return 14  # Active - 2 weeks
        else:
            return 7   # Standard - 1 week

    def _determine_mutation_type(self, charge: int) -> str:
        """Determine mutation type based on charge."""
        if charge >= 86:
            return "metamorphosis"  # Complete transformation
        elif charge >= 71:
            return "evolution"      # Significant growth
        elif charge >= 51:
            return "adaptation"     # Moderate change
        else:
            return "drift"          # Minor variation

    def _create_mutated_fragment(self, invocation: Invocation) -> Dict[str, Any]:
        """Create a mutated fragment from invocation."""
        return {
            "fragment_id": f"MUTANT_{uuid.uuid4().hex[:8].upper()}",
            "source": invocation.symbol[:50],
            "charge": invocation.charge,
            "mutation_type": self._determine_mutation_type(invocation.charge),
            "tags": invocation.flags + ["MUTATE+"],
        }

    def _generate_schedule(self, cycle: BloomCycle) -> Dict[str, Any]:
        """Generate a symbolic schedule for the cycle."""
        return {
            "cycle_id": cycle.cycle_id,
            "start_date": cycle.created_at.isoformat(),
            "end_date": cycle.ends_at.isoformat(),
            "checkpoints": [
                {
                    "name": "Quarter Point",
                    "date": (cycle.created_at + timedelta(days=cycle.duration // 4)).isoformat(),
                },
                {
                    "name": "Midpoint",
                    "date": (cycle.created_at + timedelta(days=cycle.duration // 2)).isoformat(),
                },
                {
                    "name": "Final Quarter",
                    "date": (cycle.created_at + timedelta(days=3 * cycle.duration // 4)).isoformat(),
                },
            ],
        }

    def _growth_recommendations(self, charge: int) -> List[str]:
        """Generate growth recommendations based on charge."""
        recommendations = ["Monitor for emergent patterns"]

        if charge >= 71:
            recommendations.append("Consider version branching")
        if charge >= 86:
            recommendations.append("Prepare for metamorphosis checkpoint")

        return recommendations

    def _calculate_bloom_potential(self, charge: int) -> float:
        """Calculate bloom potential (0-1)."""
        return min(1.0, charge / 80)

    def _extract_base_id(self, symbol: str) -> str:
        """Extract base ID from symbol for versioning."""
        # Look for version pattern
        import re
        match = re.search(r'(\w+)_v[\d.]+', symbol)
        if match:
            return match.group(1)

        # Generate from content
        words = symbol.split()[:2]
        return "_".join(w.capitalize() for w in words) or "Fragment"

    def get_valid_modes(self) -> List[str]:
        return ["seasonal_mutation", "growth", "versioning", "seasonal_growth", "default"]

    def get_output_types(self) -> List[str]:
        return ["mutated_fragment", "symbolic_schedule", "version_map", "versioned_fragment"]

    def get_active_cycles(self) -> List[BloomCycle]:
        """Get all active bloom cycles."""
        return [c for c in self._cycles.values() if c.status == "active"]

    def get_cycle(self, cycle_id: str) -> Optional[BloomCycle]:
        """Get a specific cycle."""
        return self._cycles.get(cycle_id)
