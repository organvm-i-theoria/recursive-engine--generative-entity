"""
RE:GE Law Enforcement - Mythic law detection and enforcement.

The Law Enforcer governs:
- Law violation detection
- Consequence application
- Violation logging
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from rege.core.exceptions import LawViolationError


class Law:
    """A mythic law in the RE:GE system."""

    def __init__(
        self,
        law_id: str,
        name: str,
        description: str,
        consequence: str,
        charge_threshold: int = 0,
    ):
        self.law_id = law_id
        self.name = name
        self.description = description
        self.consequence = consequence
        self.charge_threshold = charge_threshold
        self.active = True
        self.violations_count = 0

    def check(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Check if this law is violated in the given context.

        Returns violation description if violated, None otherwise.
        """
        # Override in subclasses for specific law logic
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "law_id": self.law_id,
            "name": self.name,
            "description": self.description,
            "consequence": self.consequence,
            "charge_threshold": self.charge_threshold,
            "active": self.active,
            "violations_count": self.violations_count,
        }


class LawEnforcer:
    """
    Law enforcement engine for the RE:GE system.

    Detects violations and applies consequences based on the mythic lawbook.
    """

    def __init__(self):
        self._laws: Dict[str, Law] = {}
        self._violation_log: List[Dict] = []
        self._init_core_laws()

    def _init_core_laws(self) -> None:
        """Initialize core system laws."""
        core_laws = [
            Law(
                "LAW_01", "Recursive Primacy",
                "All symbols exist within recursion; nothing is isolated",
                "Isolation triggers reconnection ritual",
            ),
            Law(
                "LAW_04", "Right to Transform",
                "All entities have the right to mutate and evolve",
                "Stagnation triggers BLOOM_ENGINE intervention",
            ),
            Law(
                "LAW_06", "Symbol-to-Code Equivalence",
                "Every symbol can be translated to executable form",
                "Untranslatable symbols routed to CODE_FORGE for resolution",
            ),
            Law(
                "LAW_78", "Charge Determines Fate",
                "A symbol's charge tier governs its processing path and ritual weight",
                "Incorrect routing triggers SOUL_PATCHBAY correction",
            ),
            Law(
                "LAW_79", "Tier Boundaries Are Sacred",
                "Crossing a tier boundary triggers specific system behaviors",
                "Threshold violations logged and corrected",
            ),
            Law(
                "LAW_80", "No Charge Is Final",
                "All charges may increase or decay over time",
                "Static charges trigger decay evaluation",
            ),
            Law(
                "LAW_81", "Fusion Preserves Source",
                "No fusion may delete source fragments; all origins remain retrievable",
                "Destructive fusion triggers rollback",
            ),
        ]

        for law in core_laws:
            self._laws[law.law_id] = law

    def register_law(self, law: Law) -> None:
        """Register a new law."""
        self._laws[law.law_id] = law

    def detect_violation(
        self,
        action: str,
        context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if an action violates any laws.

        Args:
            action: Description of the action
            context: Context data for checking

        Returns:
            Violation details if detected, None otherwise
        """
        violations = []

        for law in self._laws.values():
            if not law.active:
                continue

            violation_desc = law.check(context)
            if violation_desc:
                violations.append({
                    "law_id": law.law_id,
                    "law_name": law.name,
                    "violation": violation_desc,
                    "consequence": law.consequence,
                })
                law.violations_count += 1

        # Check specific violation patterns
        violations.extend(self._check_specific_violations(action, context))

        if violations:
            return {
                "action": action,
                "violations": violations,
                "timestamp": datetime.now().isoformat(),
            }

        return None

    def _check_specific_violations(
        self,
        action: str,
        context: Dict[str, Any],
    ) -> List[Dict]:
        """Check for specific violation patterns."""
        violations = []

        # Check for isolation violations (LAW_01)
        if context.get("isolated", False):
            violations.append({
                "law_id": "LAW_01",
                "law_name": "Recursive Primacy",
                "violation": "Entity exists in isolation",
                "consequence": "Isolation triggers reconnection ritual",
            })

        # Check for stagnation (LAW_04)
        if context.get("stagnant_days", 0) > 30:
            violations.append({
                "law_id": "LAW_04",
                "law_name": "Right to Transform",
                "violation": f"Entity stagnant for {context.get('stagnant_days')} days",
                "consequence": "Stagnation triggers BLOOM_ENGINE intervention",
            })

        # Check for destructive fusion (LAW_81)
        if action == "fusion" and context.get("delete_sources", False):
            violations.append({
                "law_id": "LAW_81",
                "law_name": "Fusion Preserves Source",
                "violation": "Fusion attempted with source deletion",
                "consequence": "Destructive fusion triggers rollback",
            })

        # Check for tier boundary violations (LAW_79)
        if "charge_change" in context:
            old_tier = self._get_tier(context.get("old_charge", 50))
            new_tier = self._get_tier(context.get("new_charge", 50))
            if old_tier != new_tier:
                # Not a violation, but should trigger specific behaviors
                pass

        return violations

    def apply_consequence(self, violation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply consequence for a violation.

        Args:
            violation: Violation details

        Returns:
            Consequence application result
        """
        consequence_id = f"CONSEQ_{uuid.uuid4().hex[:8].upper()}"

        result = {
            "consequence_id": consequence_id,
            "violation": violation,
            "applied_at": datetime.now().isoformat(),
            "actions_taken": [],
        }

        for v in violation.get("violations", []):
            action = self._determine_action(v)
            result["actions_taken"].append({
                "law_id": v["law_id"],
                "action": action,
            })

        # Log violation
        self._violation_log.append({
            **violation,
            "consequence_id": consequence_id,
            "logged_at": datetime.now().isoformat(),
        })

        return result

    def _determine_action(self, violation: Dict[str, Any]) -> str:
        """Determine corrective action for a violation."""
        law_id = violation.get("law_id", "")

        actions = {
            "LAW_01": "route_to_SOUL_PATCHBAY_for_reconnection",
            "LAW_04": "invoke_BLOOM_ENGINE_mutation",
            "LAW_06": "route_to_CODE_FORGE",
            "LAW_78": "recalculate_routing_priority",
            "LAW_79": "trigger_tier_transition_behaviors",
            "LAW_80": "schedule_decay_evaluation",
            "LAW_81": "initiate_fusion_rollback",
        }

        return actions.get(law_id, "log_and_monitor")

    def _get_tier(self, charge: int) -> str:
        """Get tier name for charge value."""
        if charge <= 25:
            return "LATENT"
        elif charge <= 50:
            return "PROCESSING"
        elif charge <= 70:
            return "ACTIVE"
        elif charge <= 85:
            return "INTENSE"
        else:
            return "CRITICAL"

    def get_law(self, law_id: str) -> Optional[Law]:
        """Get a law by ID."""
        return self._laws.get(law_id)

    def get_all_laws(self) -> List[Law]:
        """Get all laws."""
        return list(self._laws.values())

    def get_active_laws(self) -> List[Law]:
        """Get all active laws."""
        return [law for law in self._laws.values() if law.active]

    def get_violation_log(self, limit: int = 50) -> List[Dict]:
        """Get recent violation log entries."""
        return self._violation_log[-limit:]

    def deactivate_law(self, law_id: str) -> bool:
        """Deactivate a law."""
        if law_id in self._laws:
            self._laws[law_id].active = False
            return True
        return False

    def activate_law(self, law_id: str) -> bool:
        """Activate a law."""
        if law_id in self._laws:
            self._laws[law_id].active = True
            return True
        return False


# Global law enforcer instance
_law_enforcer: Optional[LawEnforcer] = None


def get_law_enforcer() -> LawEnforcer:
    """Get or create global law enforcer instance."""
    global _law_enforcer
    if _law_enforcer is None:
        _law_enforcer = LawEnforcer()
    return _law_enforcer
