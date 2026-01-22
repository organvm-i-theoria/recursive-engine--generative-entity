"""
RE:GE Mythic Senate - Law governance and symbolic debate.

Based on: RE-GE_ORG_BODY_03_MYTHIC_SENATE.md

The Mythic Senate governs:
- Law creation and voting
- Symbolic debate resolution
- Voting weight by charge tier
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from rege.organs.base import OrganHandler
from rege.core.models import Invocation, Patch, LawProposal
from rege.core.constants import get_tier, is_canonization_eligible


class MythicSenate(OrganHandler):
    """
    The Mythic Senate - Law governance and symbolic debate engine.

    Modes:
    - legislative: Create new law proposals
    - debate: Debate existing proposals
    - vote: Cast votes on proposals
    - default: Standard processing
    """

    @property
    def name(self) -> str:
        return "MYTHIC_SENATE"

    @property
    def description(self) -> str:
        return "Law governance, symbolic debate, and voting on mythic laws"

    def __init__(self):
        super().__init__()
        self._laws: Dict[str, LawProposal] = {}
        self._vote_history: List[Dict] = []
        self._law_counter = 0

    def invoke(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process invocation through Mythic Senate."""
        mode = invocation.mode.lower()

        if mode == "legislative":
            return self._legislative_process(invocation, patch)
        elif mode == "debate":
            return self._debate_process(invocation, patch)
        elif mode == "vote":
            return self._vote_process(invocation, patch)
        else:
            return self._default_process(invocation, patch)

    def _legislative_process(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Create a new law proposal."""
        law = self.create_law(
            name=self._extract_law_name(invocation.symbol),
            description=invocation.symbol,
            proposed_by=invocation.organ,
            charge=invocation.charge,
            tags=invocation.flags,
        )

        return {
            "law_proposal": law.to_dict(),
            "status": "proposed",
            "voting_weight_info": self._calculate_voting_weight_info(law.charge),
            "next_steps": ["debate", "vote"],
        }

    def _debate_process(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process debate on proposals."""
        # Find relevant law to debate
        law_id = self._find_law_by_content(invocation.symbol)

        if law_id and law_id in self._laws:
            law = self._laws[law_id]
            return {
                "debating_law": law.to_dict(),
                "arguments": self._generate_debate_arguments(law, invocation.symbol),
                "debate_weight": self._calculate_voting_weight(invocation.charge),
            }

        return {
            "status": "no_law_found",
            "searched_for": invocation.symbol,
            "suggestion": "Create a law proposal first using legislative mode",
        }

    def _vote_process(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Cast a vote on a proposal."""
        # Determine vote direction from symbol content
        vote_for = "yes" in invocation.symbol.lower() or "approve" in invocation.symbol.lower()
        law_id = self._find_law_by_content(invocation.symbol)

        if not law_id or law_id not in self._laws:
            return {
                "status": "vote_failed",
                "reason": "Law not found",
            }

        result = self.ritual_vote(law_id, vote_for, invocation.charge)
        return result

    def _default_process(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Standard processing - list laws or provide status."""
        pending = [l.to_dict() for l in self._laws.values() if l.vote_status == "pending"]
        approved = [l.to_dict() for l in self._laws.values() if l.vote_status == "approved"]

        return {
            "total_laws": len(self._laws),
            "pending_count": len(pending),
            "approved_count": len(approved),
            "pending_laws": pending[:5],  # First 5
            "recent_approved": approved[-3:] if approved else [],
        }

    def create_law(
        self,
        name: str,
        description: str,
        proposed_by: str,
        charge: int,
        tags: List[str] = None,
    ) -> LawProposal:
        """
        Create a new law proposal.

        Args:
            name: Law name
            description: Law description
            proposed_by: Origin organ/entity
            charge: Emotional charge
            tags: Associated tags

        Returns:
            The created LawProposal
        """
        self._law_counter += 1
        law_id = f"LAW_{self._law_counter:02d}"

        law = LawProposal(
            law_id=law_id,
            name=name,
            description=description,
            proposed_by=proposed_by,
            charge=charge,
            tags=tags or [],
        )

        self._laws[law_id] = law
        return law

    def ritual_vote(self, law_id: str, vote_for: bool, charge: int) -> Dict[str, Any]:
        """
        Cast a ritual vote on a law.

        Voting weight is determined by charge tier:
        - INTENSE+ (71+): Full weight (1.0)
        - PROCESSING (26-50): Reduced weight (0.5)
        - LATENT (0-25): Minimal weight (0.25)

        Args:
            law_id: ID of law to vote on
            vote_for: True for approval, False against
            charge: Voter's charge level

        Returns:
            Vote result
        """
        if law_id not in self._laws:
            return {"status": "failed", "reason": "Law not found"}

        law = self._laws[law_id]
        weight = self._calculate_voting_weight(charge)

        if vote_for:
            law.votes_for += weight
        else:
            law.votes_against += weight

        # Record vote
        self._vote_history.append({
            "timestamp": datetime.now().isoformat(),
            "law_id": law_id,
            "vote": "for" if vote_for else "against",
            "weight": weight,
            "charge": charge,
        })

        # Check if law passes (simple majority)
        total_votes = law.votes_for + law.votes_against
        if total_votes >= 3:  # Minimum votes needed
            if law.votes_for > law.votes_against:
                law.vote_status = "approved"
                law.enacted_at = datetime.now()
            elif law.votes_against > law.votes_for:
                law.vote_status = "rejected"

        return {
            "status": "voted",
            "law_id": law_id,
            "vote": "for" if vote_for else "against",
            "weight": weight,
            "current_tally": {
                "for": law.votes_for,
                "against": law.votes_against,
            },
            "law_status": law.vote_status,
        }

    def _calculate_voting_weight(self, charge: int) -> float:
        """Calculate voting weight based on charge."""
        if charge >= 71:  # INTENSE tier
            return 1.0
        elif charge >= 51:  # ACTIVE tier
            return 0.75
        elif charge >= 26:  # PROCESSING tier
            return 0.5
        else:  # LATENT tier
            return 0.25

    def _calculate_voting_weight_info(self, charge: int) -> Dict[str, Any]:
        """Get detailed voting weight information."""
        weight = self._calculate_voting_weight(charge)
        tier = get_tier(charge)

        return {
            "charge": charge,
            "tier": tier,
            "weight": weight,
            "weight_explanation": f"Tier {tier} grants {weight} voting weight",
        }

    def _extract_law_name(self, symbol: str) -> str:
        """Extract a law name from symbol content."""
        # Take first phrase up to punctuation or limit
        words = symbol.split()[:5]
        name = " ".join(words)
        return name.title()

    def _find_law_by_content(self, content: str) -> Optional[str]:
        """Find a law ID by searching content."""
        content_lower = content.lower()

        # Check for direct law ID reference
        for law_id in self._laws.keys():
            if law_id.lower() in content_lower:
                return law_id

        # Check for name match
        for law_id, law in self._laws.items():
            if law.name.lower() in content_lower:
                return law_id

        return None

    def _generate_debate_arguments(self, law: LawProposal, context: str) -> Dict[str, Any]:
        """Generate debate arguments for a law."""
        return {
            "for": [
                f"This law addresses recurring pattern with charge {law.charge}",
                "Pattern recognition supports codification",
            ],
            "against": [
                "May be premature to codify",
                "Consider more observation before law",
            ],
            "context_provided": context,
        }

    def get_valid_modes(self) -> List[str]:
        return ["legislative", "debate", "vote", "default"]

    def get_output_types(self) -> List[str]:
        return ["law_proposal", "vote_result", "echo_record"]

    def get_all_laws(self) -> List[LawProposal]:
        """Get all laws."""
        return list(self._laws.values())

    def get_law(self, law_id: str) -> Optional[LawProposal]:
        """Get a specific law by ID."""
        return self._laws.get(law_id)
