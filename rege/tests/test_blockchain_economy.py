"""
Tests for Blockchain Economy organ.
"""

import pytest
from rege.organs.blockchain_economy import (
    BlockchainEconomy,
    MythBlock,
    RitualContract,
    GENESIS_HASH,
)
from rege.core.models import Invocation, Patch, DepthLevel
from datetime import datetime


class TestMythBlock:
    """Tests for MythBlock data class."""

    def test_myth_block_creation(self):
        """Test creating a MythBlock."""
        block = MythBlock(
            block_id="TEST_BLOCK",
            previous_hash="abc123",
            timestamp=datetime.now(),
            contributor="TESTER",
            charge=75,
            ritual_data={"type": "test"},
        )

        assert block.contributor == "TESTER"
        assert block.charge == 75
        assert len(block.hash) == 64  # SHA256 hex

    def test_myth_block_auto_id(self):
        """Test auto-generated block ID."""
        block = MythBlock(
            block_id="",
            previous_hash="prev",
            timestamp=datetime.now(),
            contributor="AUTO",
            charge=50,
            ritual_data={},
        )

        assert block.block_id.startswith("BLOCK_")

    def test_myth_block_hash_calculation(self):
        """Test hash is calculated consistently."""
        block = MythBlock(
            block_id="CONSISTENT",
            previous_hash="same_prev",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            contributor="HASH_TEST",
            charge=60,
            ritual_data={"key": "value"},
        )

        # Recalculate should match
        recalculated = block._calculate_hash()
        assert block.hash == recalculated

    def test_myth_block_to_dict(self):
        """Test serializing block."""
        block = MythBlock(
            block_id="SERIALIZE",
            previous_hash="prev_hash",
            timestamp=datetime.now(),
            contributor="SERIALIZER",
            charge=80,
            ritual_data={"test": "data"},
        )

        data = block.to_dict()

        assert data["block_id"] == "SERIALIZE"
        assert data["contributor"] == "SERIALIZER"
        assert "hash" in data


class TestRitualContract:
    """Tests for RitualContract data class."""

    def test_ritual_contract_creation(self):
        """Test creating a RitualContract."""
        contract = RitualContract(
            contract_id="TEST_CONTRACT",
            creator="PROMISER",
            promise="I will deliver",
            delivery_condition="Output must exist",
            charge_requirement=70,
            created_at=datetime.now(),
        )

        assert contract.creator == "PROMISER"
        assert contract.status == "pending"
        assert contract.charge_requirement == 70

    def test_ritual_contract_auto_id(self):
        """Test auto-generated contract ID."""
        contract = RitualContract(
            contract_id="",
            creator="AUTO",
            promise="Promise",
            delivery_condition="Condition",
            charge_requirement=50,
            created_at=datetime.now(),
        )

        assert contract.contract_id.startswith("CONTRACT_")

    def test_ritual_contract_to_dict(self):
        """Test serializing contract."""
        contract = RitualContract(
            contract_id="SERIALIZE",
            creator="CREATOR",
            promise="My promise",
            delivery_condition="My condition",
            charge_requirement=60,
            created_at=datetime.now(),
            witnesses=["WITNESS1", "WITNESS2"],
        )

        data = contract.to_dict()

        assert data["contract_id"] == "SERIALIZE"
        assert len(data["witnesses"]) == 2


class TestBlockchainEconomy:
    """Tests for BlockchainEconomy organ."""

    def setup_method(self):
        """Set up test fixtures."""
        self.organ = BlockchainEconomy()

    def test_organ_properties(self):
        """Test organ name and description."""
        assert self.organ.name == "BLOCKCHAIN_ECONOMY"
        assert "Immutable" in self.organ.description

    def test_valid_modes(self):
        """Test valid modes list."""
        modes = self.organ.get_valid_modes()

        assert "mint" in modes
        assert "verify" in modes
        assert "contract" in modes
        assert "history" in modes
        assert "contributors" in modes
        assert "default" in modes

    def test_genesis_block_exists(self):
        """Test genesis block is created on initialization."""
        assert self.organ.get_chain_length() == 1

        genesis = self.organ.get_block(0)
        assert genesis is not None
        assert genesis.block_id == "GENESIS"
        assert genesis.previous_hash == GENESIS_HASH
        assert genesis.contributor == "SYSTEM"

    def test_mint_block(self):
        """Test minting a new block."""
        invocation = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="MINTER",
            mode="mint",
            depth=DepthLevel.STANDARD,
            expect="block",
            charge=70,
        )
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=70)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "minted"
        assert result["chain_length"] == 2
        assert result["block"]["contributor"] == "MINTER"

    def test_mint_block_default_contributor(self):
        """Test minting with default SELF contributor."""
        invocation = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="",
            mode="mint",
            depth=DepthLevel.STANDARD,
            expect="block",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["block"]["contributor"] == "SELF"

    def test_mint_block_links_to_previous(self):
        """Test new block links to previous block."""
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=60)

        # Get genesis hash
        genesis = self.organ.get_block(0)
        genesis_hash = genesis.hash

        # Mint new block
        invocation = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="LINKER",
            mode="mint",
            depth=DepthLevel.STANDARD,
            expect="block",
            charge=60,
        )
        result = self.organ.invoke(invocation, patch)

        assert result["block"]["previous_hash"] == genesis_hash

    def test_verify_chain_valid(self):
        """Test verifying a valid chain."""
        # Mint a few blocks
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=60)
        for i in range(3):
            invocation = Invocation(
                organ="BLOCKCHAIN_ECONOMY",
                symbol=f"VERIFIER_{i}",
                mode="mint",
                depth=DepthLevel.STANDARD,
                expect="block",
                charge=60,
            )
            self.organ.invoke(invocation, patch)

        # Verify
        verify_inv = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="",
            mode="verify",
            depth=DepthLevel.STANDARD,
            expect="verification_result",
            charge=50,
        )
        result = self.organ.invoke(verify_inv, patch)

        assert result["status"] == "verified"
        assert result["is_valid"]
        assert result["blocks_verified"] == 3  # 3 blocks after genesis

    def test_verify_chain_detects_tampering(self):
        """Test verification detects tampered blocks."""
        # Mint a block
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=60)
        mint_inv = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="TAMPER_TEST",
            mode="mint",
            depth=DepthLevel.STANDARD,
            expect="block",
            charge=60,
        )
        self.organ.invoke(mint_inv, patch)

        # Tamper with a block (directly modify chain for testing)
        self.organ._chain[1].ritual_data["tampered"] = True
        # Note: hash won't match after tampering

        # Verify
        verify_inv = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="",
            mode="verify",
            depth=DepthLevel.STANDARD,
            expect="verification_result",
            charge=50,
        )
        result = self.organ.invoke(verify_inv, patch)

        assert not result["is_valid"]
        assert len(result["errors"]) > 0

    def test_create_contract(self):
        """Test creating a ritual contract."""
        invocation = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="I promise to deliver|Output exists|70",
            mode="contract",
            depth=DepthLevel.STANDARD,
            expect="contract",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "contract_created"
        assert result["contract"]["promise"] == "I promise to deliver"
        assert result["contract"]["charge_requirement"] == 70

    def test_create_contract_invalid_format(self):
        """Test creating contract with invalid format."""
        invocation = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="just a promise without condition",
            mode="contract",
            depth=DepthLevel.STANDARD,
            expect="contract",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "failed"
        assert "Invalid contract format" in result["error"]

    def test_create_contract_default_charge(self):
        """Test creating contract with default charge requirement."""
        invocation = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="Promise|Condition",  # No charge specified
            mode="contract",
            depth=DepthLevel.STANDARD,
            expect="contract",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert result["contract"]["charge_requirement"] == 51  # Default

    def test_fulfill_contract_success(self):
        """Test successfully fulfilling a contract."""
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=80)

        # Create contract
        create_inv = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="Promise|Condition|60",
            mode="contract",
            depth=DepthLevel.STANDARD,
            expect="contract",
            charge=60,
        )
        create_result = self.organ.invoke(create_inv, patch)
        contract_id = create_result["contract"]["contract_id"]

        # Fulfill contract
        fulfill_inv = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol=contract_id,
            mode="contract",
            depth=DepthLevel.STANDARD,
            expect="contract",
            charge=80,  # Above requirement
            flags=["FULFILL+"],
        )
        result = self.organ.invoke(fulfill_inv, patch)

        assert result["status"] == "contract_fulfilled"
        assert result["contract"]["status"] == "fulfilled"

    def test_fulfill_contract_charge_too_low(self):
        """Test fulfillment fails with low charge."""
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=50)

        # Create contract with high requirement
        create_inv = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="Promise|Condition|80",
            mode="contract",
            depth=DepthLevel.STANDARD,
            expect="contract",
            charge=60,
        )
        create_result = self.organ.invoke(create_inv, patch)
        contract_id = create_result["contract"]["contract_id"]

        # Try to fulfill with low charge
        fulfill_inv = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol=contract_id,
            mode="contract",
            depth=DepthLevel.STANDARD,
            expect="contract",
            charge=50,  # Below requirement
            flags=["FULFILL+"],
        )
        result = self.organ.invoke(fulfill_inv, patch)

        assert result["status"] == "failed"
        assert "Charge below requirement" in result["error"]

    def test_fulfill_contract_not_found(self):
        """Test fulfillment of non-existent contract."""
        invocation = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="NONEXISTENT_CONTRACT",
            mode="contract",
            depth=DepthLevel.STANDARD,
            expect="contract",
            charge=80,
            flags=["FULFILL+"],
        )
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=80)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "failed"
        assert "not found" in result["error"]

    def test_fulfill_contract_already_fulfilled(self):
        """Test can't fulfill already fulfilled contract."""
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=80)

        # Create and fulfill contract
        create_inv = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="Promise|Condition|50",
            mode="contract",
            depth=DepthLevel.STANDARD,
            expect="contract",
            charge=60,
        )
        create_result = self.organ.invoke(create_inv, patch)
        contract_id = create_result["contract"]["contract_id"]

        fulfill_inv = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol=contract_id,
            mode="contract",
            depth=DepthLevel.STANDARD,
            expect="contract",
            charge=80,
            flags=["FULFILL+"],
        )
        self.organ.invoke(fulfill_inv, patch)

        # Try to fulfill again
        result = self.organ.invoke(fulfill_inv, patch)

        assert result["status"] == "failed"
        assert "already" in result["error"]

    def test_evaluate_contract(self):
        """Test evaluating a contract."""
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=60)

        # Create contract
        create_inv = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="Promise|Condition|70",
            mode="contract",
            depth=DepthLevel.STANDARD,
            expect="contract",
            charge=60,
        )
        create_result = self.organ.invoke(create_inv, patch)
        contract_id = create_result["contract"]["contract_id"]

        # Evaluate with charge below requirement
        eval_inv = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol=contract_id,
            mode="contract",
            depth=DepthLevel.STANDARD,
            expect="contract",
            charge=60,
            flags=["EVALUATE+"],
        )
        result = self.organ.invoke(eval_inv, patch)

        assert result["status"] == "evaluated"
        assert not result["would_satisfy"]
        assert result["charge_gap"] == 10

    def test_query_history_all(self):
        """Test querying all history."""
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=60)

        # Mint some blocks
        for i in range(3):
            invocation = Invocation(
                organ="BLOCKCHAIN_ECONOMY",
                symbol=f"HISTORIAN_{i}",
                mode="mint",
                depth=DepthLevel.STANDARD,
                expect="block",
                charge=60,
            )
            self.organ.invoke(invocation, patch)

        # Query history
        history_inv = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="",
            mode="history",
            depth=DepthLevel.STANDARD,
            expect="history",
            charge=50,
        )
        result = self.organ.invoke(history_inv, patch)

        assert result["status"] == "history_retrieved"
        assert result["total_chain_length"] == 4  # genesis + 3

    def test_query_history_filtered(self):
        """Test querying history filtered by contributor."""
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=60)

        # Mint blocks from different contributors
        for contributor in ["ALICE", "BOB", "ALICE"]:
            invocation = Invocation(
                organ="BLOCKCHAIN_ECONOMY",
                symbol=contributor,
                mode="mint",
                depth=DepthLevel.STANDARD,
                expect="block",
                charge=60,
            )
            self.organ.invoke(invocation, patch)

        # Query ALICE's history
        history_inv = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="ALICE",
            mode="history",
            depth=DepthLevel.STANDARD,
            expect="history",
            charge=50,
        )
        result = self.organ.invoke(history_inv, patch)

        assert result["status"] == "history_retrieved"
        assert result["returned_count"] == 2  # ALICE has 2 blocks

    def test_get_contributors_all(self):
        """Test getting all contributor stats."""
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=60)

        # Mint blocks from different contributors
        for contributor in ["ALICE", "BOB"]:
            invocation = Invocation(
                organ="BLOCKCHAIN_ECONOMY",
                symbol=contributor,
                mode="mint",
                depth=DepthLevel.STANDARD,
                expect="block",
                charge=60,
            )
            self.organ.invoke(invocation, patch)

        # Get all contributors
        contrib_inv = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="",
            mode="contributors",
            depth=DepthLevel.STANDARD,
            expect="contributor_stats",
            charge=50,
        )
        result = self.organ.invoke(contrib_inv, patch)

        assert result["status"] == "all_contributors"
        assert result["total_contributors"] == 3  # SYSTEM, ALICE, BOB

    def test_get_contributors_specific(self):
        """Test getting specific contributor stats."""
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=70)

        # Mint multiple blocks from same contributor
        for _ in range(3):
            invocation = Invocation(
                organ="BLOCKCHAIN_ECONOMY",
                symbol="CHARLIE",
                mode="mint",
                depth=DepthLevel.STANDARD,
                expect="block",
                charge=70,
            )
            self.organ.invoke(invocation, patch)

        # Get CHARLIE's stats
        contrib_inv = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="CHARLIE",
            mode="contributors",
            depth=DepthLevel.STANDARD,
            expect="contributor_stats",
            charge=50,
        )
        result = self.organ.invoke(contrib_inv, patch)

        assert result["status"] == "contributor_stats"
        assert result["stats"]["block_count"] == 3
        assert result["stats"]["average_charge"] == 70

    def test_get_contributors_not_found(self):
        """Test getting non-existent contributor."""
        invocation = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="UNKNOWN",
            mode="contributors",
            depth=DepthLevel.STANDARD,
            expect="contributor_stats",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "not_found"

    def test_default_chain_status(self):
        """Test default mode returns chain status."""
        invocation = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="chain_status",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "chain_status"
        assert "chain_length" in result
        assert "latest_block_hash" in result

    def test_get_block_by_index(self):
        """Test getting block by index."""
        genesis = self.organ.get_block(0)
        assert genesis is not None
        assert genesis.block_id == "GENESIS"

        # Invalid index
        invalid = self.organ.get_block(999)
        assert invalid is None

    def test_get_contract_by_id(self):
        """Test getting contract by ID."""
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=60)

        # Create contract
        create_inv = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="Promise|Condition|60",
            mode="contract",
            depth=DepthLevel.STANDARD,
            expect="contract",
            charge=60,
        )
        create_result = self.organ.invoke(create_inv, patch)
        contract_id = create_result["contract"]["contract_id"]

        # Get by ID
        contract = self.organ.get_contract(contract_id)
        assert contract is not None
        assert contract.promise == "Promise"

        # Non-existent
        assert self.organ.get_contract("FAKE") is None

    def test_reset_reinitializes_genesis(self):
        """Test reset creates new genesis block."""
        # Mint some blocks
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=60)
        invocation = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="RESETTER",
            mode="mint",
            depth=DepthLevel.STANDARD,
            expect="block",
            charge=60,
        )
        self.organ.invoke(invocation, patch)

        assert self.organ.get_chain_length() == 2

        # Reset
        self.organ.reset()

        assert self.organ.get_chain_length() == 1
        assert self.organ.get_block(0).block_id == "GENESIS"


class TestBlockchainEconomyIntegration:
    """Integration tests for Blockchain Economy."""

    def test_full_contract_lifecycle(self):
        """Test complete contract lifecycle: create, evaluate, fulfill."""
        organ = BlockchainEconomy()
        patch = Patch(input_node="test", output_node="BLOCKCHAIN_ECONOMY", tags=[], charge=80)

        # 1. Create contract
        create_inv = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol="Deliver artifact|Artifact verified|70",
            mode="contract",
            depth=DepthLevel.STANDARD,
            expect="contract",
            charge=60,
        )
        create_result = organ.invoke(create_inv, patch)
        contract_id = create_result["contract"]["contract_id"]
        initial_chain_length = organ.get_chain_length()

        # 2. Evaluate (not ready)
        eval_inv = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol=contract_id,
            mode="contract",
            depth=DepthLevel.STANDARD,
            expect="contract",
            charge=50,
            flags=["EVALUATE+"],
        )
        eval_result = organ.invoke(eval_inv, patch)
        assert not eval_result["would_satisfy"]

        # 3. Fulfill
        fulfill_inv = Invocation(
            organ="BLOCKCHAIN_ECONOMY",
            symbol=contract_id,
            mode="contract",
            depth=DepthLevel.STANDARD,
            expect="contract",
            charge=80,
            flags=["FULFILL+"],
        )
        fulfill_result = organ.invoke(fulfill_inv, patch)
        assert fulfill_result["status"] == "contract_fulfilled"

        # 4. Verify chain grew (contract create + fulfill = 2 new blocks)
        final_chain_length = organ.get_chain_length()
        assert final_chain_length == initial_chain_length + 1  # Fulfill adds 1 more


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
