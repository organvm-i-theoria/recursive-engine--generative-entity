"""
RE:GE Blockchain Economy - Immutable record system for ritual tracking.

Based on: RE-GE_ORG_BODY_13_BLOCKCHAIN_ECONOMY.md

The Blockchain Economy governs:
- Immutable block creation with hash linking
- Smart ritual contracts (promise/delivery validation)
- Contributor tracking and attribution
- Chain integrity verification
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import uuid
import hashlib
import json

from rege.organs.base import OrganHandler
from rege.core.models import Invocation, Patch


@dataclass
class MythBlock:
    """
    A block in the mythic blockchain.

    Each block contains ritual data and is cryptographically
    linked to the previous block.
    """
    block_id: str
    previous_hash: str
    timestamp: datetime
    contributor: str
    charge: int
    ritual_data: Dict[str, Any]
    hash: str = ""
    nonce: int = 0

    def __post_init__(self):
        if not self.block_id:
            self.block_id = f"BLOCK_{uuid.uuid4().hex[:8].upper()}"
        if not self.hash:
            self.hash = self._calculate_hash()

    def _calculate_hash(self) -> str:
        """Calculate the block's hash."""
        block_string = json.dumps({
            "block_id": self.block_id,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp.isoformat(),
            "contributor": self.contributor,
            "charge": self.charge,
            "ritual_data": self.ritual_data,
            "nonce": self.nonce,
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize block to dictionary."""
        return {
            "block_id": self.block_id,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp.isoformat(),
            "contributor": self.contributor,
            "charge": self.charge,
            "ritual_data": self.ritual_data,
            "hash": self.hash,
            "nonce": self.nonce,
        }


@dataclass
class RitualContract:
    """
    A smart ritual contract with promise and delivery conditions.

    Contracts track promises made and their fulfillment status.
    """
    contract_id: str
    creator: str
    promise: str
    delivery_condition: str
    charge_requirement: int
    created_at: datetime
    fulfilled_at: Optional[datetime] = None
    status: str = "pending"  # pending, fulfilled, expired, violated
    witnesses: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.contract_id:
            self.contract_id = f"CONTRACT_{uuid.uuid4().hex[:8].upper()}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize contract to dictionary."""
        return {
            "contract_id": self.contract_id,
            "creator": self.creator,
            "promise": self.promise,
            "delivery_condition": self.delivery_condition,
            "charge_requirement": self.charge_requirement,
            "created_at": self.created_at.isoformat(),
            "fulfilled_at": self.fulfilled_at.isoformat() if self.fulfilled_at else None,
            "status": self.status,
            "witnesses": self.witnesses,
            "metadata": self.metadata,
        }


# Genesis block configuration
GENESIS_HASH = "0" * 64


class BlockchainEconomy(OrganHandler):
    """
    Blockchain Economy - Immutable record system for ritual tracking.

    Modes:
    - mint: Create new block
    - verify: Verify chain integrity
    - contract: Create/evaluate ritual contract
    - history: Query block history
    - contributors: Get contributor stats
    - default: Chain status
    """

    @property
    def name(self) -> str:
        return "BLOCKCHAIN_ECONOMY"

    @property
    def description(self) -> str:
        return "Immutable record system for ritual tracking"

    def __init__(self):
        super().__init__()
        self._chain: List[MythBlock] = []
        self._contracts: Dict[str, RitualContract] = {}
        self._contributors: Dict[str, Dict[str, Any]] = {}
        self._initialize_genesis()

    def _initialize_genesis(self) -> None:
        """Initialize the chain with genesis block."""
        genesis = MythBlock(
            block_id="GENESIS",
            previous_hash=GENESIS_HASH,
            timestamp=datetime.now(),
            contributor="SYSTEM",
            charge=100,
            ritual_data={"type": "genesis", "message": "In the beginning was the loop"},
        )
        self._chain.append(genesis)
        self._update_contributor_stats("SYSTEM", genesis)

    def invoke(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process invocation through Blockchain Economy."""
        mode = invocation.mode.lower()

        if mode == "mint":
            return self._mint_block(invocation, patch)
        elif mode == "verify":
            return self._verify_chain(invocation, patch)
        elif mode == "contract":
            return self._handle_contract(invocation, patch)
        elif mode == "history":
            return self._query_history(invocation, patch)
        elif mode == "contributors":
            return self._get_contributors(invocation, patch)
        else:
            return self._default_chain(invocation, patch)

    def _mint_block(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Mint a new block on the chain."""
        # Get previous block
        previous_block = self._chain[-1]

        # Parse contributor from symbol or default to SELF
        contributor = invocation.symbol.strip().upper() if invocation.symbol else "SELF"

        # Build ritual data
        ritual_data = {
            "type": "ritual_record",
            "invocation_id": invocation.invocation_id,
            "depth": patch.depth,
            "flags": invocation.flags,
            "timestamp": datetime.now().isoformat(),
        }

        # Create new block
        new_block = MythBlock(
            block_id="",
            previous_hash=previous_block.hash,
            timestamp=datetime.now(),
            contributor=contributor,
            charge=invocation.charge,
            ritual_data=ritual_data,
        )

        # Add to chain
        self._chain.append(new_block)

        # Update contributor stats
        self._update_contributor_stats(contributor, new_block)

        return {
            "status": "minted",
            "block": new_block.to_dict(),
            "chain_length": len(self._chain),
            "contributor_total_blocks": self._contributors[contributor]["block_count"],
        }

    def _verify_chain(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Verify the integrity of the blockchain."""
        is_valid = True
        errors = []
        blocks_verified = 0

        for i in range(1, len(self._chain)):
            current = self._chain[i]
            previous = self._chain[i - 1]

            # Verify hash linkage
            if current.previous_hash != previous.hash:
                is_valid = False
                errors.append(f"Block {i} hash mismatch: expected {previous.hash[:16]}...")

            # Verify current block's hash
            recalculated = current._calculate_hash()
            if current.hash != recalculated:
                is_valid = False
                errors.append(f"Block {i} integrity violated")

            blocks_verified += 1

        return {
            "status": "verified" if is_valid else "corrupted",
            "is_valid": is_valid,
            "blocks_verified": blocks_verified,
            "chain_length": len(self._chain),
            "errors": errors,
            "genesis_hash": self._chain[0].hash[:16] + "...",
            "latest_hash": self._chain[-1].hash[:16] + "...",
        }

    def _handle_contract(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Create or evaluate a ritual contract."""
        # Parse action from flags
        if "FULFILL+" in invocation.flags:
            return self._fulfill_contract(invocation)
        elif "EVALUATE+" in invocation.flags:
            return self._evaluate_contract(invocation)
        else:
            return self._create_contract(invocation)

    def _create_contract(self, invocation: Invocation) -> Dict[str, Any]:
        """Create a new ritual contract."""
        # Parse contract from symbol: "PROMISE|CONDITION|CHARGE"
        parts = invocation.symbol.split("|")
        if len(parts) < 2:
            return {
                "status": "failed",
                "error": "Invalid contract format. Use PROMISE|CONDITION|CHARGE_REQUIREMENT",
                "example": "I will create|Deliver output|70",
            }

        promise = parts[0].strip()
        condition = parts[1].strip()
        charge_requirement = int(parts[2].strip()) if len(parts) > 2 else 51

        contract = RitualContract(
            contract_id="",
            creator="SELF",
            promise=promise,
            delivery_condition=condition,
            charge_requirement=charge_requirement,
            created_at=datetime.now(),
        )

        self._contracts[contract.contract_id] = contract

        # Record contract creation on chain
        self._mint_contract_block(contract, "created")

        return {
            "status": "contract_created",
            "contract": contract.to_dict(),
            "evaluation_criteria": {
                "charge_must_exceed": charge_requirement,
                "condition": condition,
            },
        }

    def _fulfill_contract(self, invocation: Invocation) -> Dict[str, Any]:
        """Attempt to fulfill a contract."""
        contract_id = invocation.symbol.strip().upper()

        if contract_id not in self._contracts:
            return {
                "status": "failed",
                "error": f"Contract not found: {contract_id}",
            }

        contract = self._contracts[contract_id]

        if contract.status != "pending":
            return {
                "status": "failed",
                "error": f"Contract already {contract.status}",
            }

        # Check charge requirement
        if invocation.charge < contract.charge_requirement:
            return {
                "status": "failed",
                "error": "Charge below requirement",
                "required": contract.charge_requirement,
                "provided": invocation.charge,
            }

        # Mark as fulfilled
        contract.status = "fulfilled"
        contract.fulfilled_at = datetime.now()

        # Record fulfillment on chain
        self._mint_contract_block(contract, "fulfilled")

        return {
            "status": "contract_fulfilled",
            "contract": contract.to_dict(),
            "fulfillment_charge": invocation.charge,
        }

    def _evaluate_contract(self, invocation: Invocation) -> Dict[str, Any]:
        """Evaluate contract status."""
        contract_id = invocation.symbol.strip().upper()

        if contract_id not in self._contracts:
            return {
                "status": "failed",
                "error": f"Contract not found: {contract_id}",
            }

        contract = self._contracts[contract_id]

        # Check if current charge would satisfy
        would_satisfy = invocation.charge >= contract.charge_requirement

        return {
            "status": "evaluated",
            "contract": contract.to_dict(),
            "current_charge": invocation.charge,
            "would_satisfy": would_satisfy,
            "charge_gap": max(0, contract.charge_requirement - invocation.charge),
        }

    def _mint_contract_block(self, contract: RitualContract, action: str) -> None:
        """Mint a block recording contract action."""
        previous_block = self._chain[-1]

        ritual_data = {
            "type": "contract_record",
            "contract_id": contract.contract_id,
            "action": action,
            "promise": contract.promise[:50],
            "timestamp": datetime.now().isoformat(),
        }

        block = MythBlock(
            block_id="",
            previous_hash=previous_block.hash,
            timestamp=datetime.now(),
            contributor=contract.creator,
            charge=contract.charge_requirement,
            ritual_data=ritual_data,
        )

        self._chain.append(block)
        self._update_contributor_stats(contract.creator, block)

    def _query_history(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Query block history."""
        # Parse filter from symbol
        filter_by = invocation.symbol.strip().upper() if invocation.symbol else None
        limit = 20

        # Get blocks based on filter
        if filter_by:
            blocks = [
                b.to_dict() for b in self._chain
                if b.contributor == filter_by or filter_by in str(b.ritual_data)
            ]
        else:
            blocks = [b.to_dict() for b in self._chain[-limit:]]

        return {
            "status": "history_retrieved",
            "filter": filter_by,
            "blocks": blocks,
            "total_chain_length": len(self._chain),
            "returned_count": len(blocks),
        }

    def _get_contributors(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Get contributor statistics."""
        specific_contributor = invocation.symbol.strip().upper() if invocation.symbol else None

        if specific_contributor:
            if specific_contributor not in self._contributors:
                return {
                    "status": "not_found",
                    "contributor": specific_contributor,
                }
            return {
                "status": "contributor_stats",
                "contributor": specific_contributor,
                "stats": self._contributors[specific_contributor],
            }

        # Return all contributors
        return {
            "status": "all_contributors",
            "contributors": self._contributors,
            "total_contributors": len(self._contributors),
        }

    def _default_chain(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Return chain status."""
        return {
            "status": "chain_status",
            "chain_length": len(self._chain),
            "active_contracts": len([c for c in self._contracts.values() if c.status == "pending"]),
            "total_contracts": len(self._contracts),
            "total_contributors": len(self._contributors),
            "latest_block_hash": self._chain[-1].hash[:16] + "...",
            "genesis_timestamp": self._chain[0].timestamp.isoformat(),
        }

    def _update_contributor_stats(self, contributor: str, block: MythBlock) -> None:
        """Update statistics for a contributor."""
        if contributor not in self._contributors:
            self._contributors[contributor] = {
                "block_count": 0,
                "total_charge": 0,
                "first_contribution": block.timestamp.isoformat(),
                "last_contribution": block.timestamp.isoformat(),
            }

        stats = self._contributors[contributor]
        stats["block_count"] += 1
        stats["total_charge"] += block.charge
        stats["last_contribution"] = block.timestamp.isoformat()
        stats["average_charge"] = stats["total_charge"] / stats["block_count"]

    def get_chain_length(self) -> int:
        """Get current chain length."""
        return len(self._chain)

    def get_block(self, index: int) -> Optional[MythBlock]:
        """Get block by index."""
        if 0 <= index < len(self._chain):
            return self._chain[index]
        return None

    def get_contract(self, contract_id: str) -> Optional[RitualContract]:
        """Get contract by ID."""
        return self._contracts.get(contract_id)

    def get_valid_modes(self) -> List[str]:
        return ["mint", "verify", "contract", "history", "contributors", "default"]

    def get_output_types(self) -> List[str]:
        return ["block", "verification_result", "contract", "history", "contributor_stats", "chain_status"]

    def get_state(self) -> Dict[str, Any]:
        """Get current organ state for checkpointing."""
        state = super().get_state()
        state["state"].update({
            "chain": [b.to_dict() for b in self._chain],
            "contracts": {k: v.to_dict() for k, v in self._contracts.items()},
            "contributors": self._contributors,
        })
        return state

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore organ state from checkpoint."""
        super().restore_state(state)
        inner_state = state.get("state", {})
        self._contributors = inner_state.get("contributors", {})
        # Note: chain and contracts restoration would require deserialization

    def reset(self) -> None:
        """Reset organ to initial state."""
        super().reset()
        self._chain = []
        self._contracts = {}
        self._contributors = {}
        self._initialize_genesis()
