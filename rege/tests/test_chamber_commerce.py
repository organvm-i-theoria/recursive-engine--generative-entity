"""
Tests for Chamber of Commerce organ.
"""

import pytest
from rege.organs.chamber_commerce import (
    ChamberOfCommerce,
    SymbolicCurrency,
    TradeRecord,
    MintRecord,
    VALUATION_CONFIG,
)
from rege.core.models import Invocation, Patch, DepthLevel
from datetime import datetime


class TestSymbolicCurrency:
    """Tests for SymbolicCurrency enum."""

    def test_all_currencies_defined(self):
        """Test all three currencies are defined."""
        currencies = [c.value for c in SymbolicCurrency]

        assert "dreampoints" in currencies
        assert "looptokens" in currencies
        assert "mirrorcredits" in currencies


class TestTradeRecord:
    """Tests for TradeRecord data class."""

    def test_trade_record_creation(self):
        """Test creating a TradeRecord."""
        trade = TradeRecord(
            trade_id="TEST_TRADE",
            from_entity="SELF",
            to_entity="ARCHIVE",
            currency=SymbolicCurrency.LOOPTOKENS,
            amount=10,
            charge_at_trade=60,
            timestamp=datetime.now(),
            reason="Test trade",
        )

        assert trade.from_entity == "SELF"
        assert trade.to_entity == "ARCHIVE"
        assert trade.amount == 10
        assert trade.status == "completed"

    def test_trade_record_auto_id(self):
        """Test auto-generated trade ID."""
        trade = TradeRecord(
            trade_id="",
            from_entity="A",
            to_entity="B",
            currency=SymbolicCurrency.DREAMPOINTS,
            amount=5,
            charge_at_trade=50,
            timestamp=datetime.now(),
        )

        assert trade.trade_id.startswith("TRADE_")

    def test_trade_record_to_dict(self):
        """Test serializing trade record."""
        trade = TradeRecord(
            trade_id="TRADE_TEST",
            from_entity="SELF",
            to_entity="OTHER",
            currency=SymbolicCurrency.MIRRORCREDITS,
            amount=20,
            charge_at_trade=70,
            timestamp=datetime.now(),
        )

        data = trade.to_dict()

        assert data["from_entity"] == "SELF"
        assert data["currency"] == "mirrorcredits"
        assert data["amount"] == 20


class TestMintRecord:
    """Tests for MintRecord data class."""

    def test_mint_record_creation(self):
        """Test creating a MintRecord."""
        mint = MintRecord(
            mint_id="TEST_MINT",
            currency=SymbolicCurrency.DREAMPOINTS,
            amount=15,
            recipient="SELF",
            source_ritual="test_ritual",
            charge_at_mint=75,
            timestamp=datetime.now(),
        )

        assert mint.amount == 15
        assert mint.recipient == "SELF"

    def test_mint_record_auto_id(self):
        """Test auto-generated mint ID."""
        mint = MintRecord(
            mint_id="",
            currency=SymbolicCurrency.LOOPTOKENS,
            amount=5,
            recipient="TEST",
            source_ritual="auto",
            charge_at_mint=60,
            timestamp=datetime.now(),
        )

        assert mint.mint_id.startswith("MINT_")


class TestChamberOfCommerce:
    """Tests for ChamberOfCommerce organ."""

    def setup_method(self):
        """Set up test fixtures."""
        self.organ = ChamberOfCommerce()

    def test_organ_properties(self):
        """Test organ name and description."""
        assert self.organ.name == "CHAMBER_OF_COMMERCE"
        assert "economy" in self.organ.description.lower()

    def test_valid_modes(self):
        """Test valid modes list."""
        modes = self.organ.get_valid_modes()

        assert "value" in modes
        assert "trade" in modes
        assert "mint" in modes
        assert "ledger" in modes
        assert "balance" in modes
        assert "default" in modes

    def test_assess_value_basic(self):
        """Test basic value assessment."""
        invocation = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="test fragment",
            mode="value",
            depth=DepthLevel.STANDARD,
            expect="valuation",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "valued"
        assert "value" in result
        assert "tier" in result
        assert "components" in result

    def test_assess_value_with_flags(self):
        """Test value assessment with value-boosting flags."""
        invocation = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="canon fragment",
            mode="value",
            depth=DepthLevel.STANDARD,
            expect="valuation",
            charge=70,
            flags=["CANON+", "RITUAL+"],
        )
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=70)

        result = self.organ.invoke(invocation, patch)

        assert result["components"]["flag_bonus"] == 10  # 5 per flag

    def test_assess_value_legendary_tier(self):
        """Test legendary tier valuation."""
        invocation = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="legendary item",
            mode="value",
            depth=DepthLevel.FULL_SPIRAL,  # Higher depth
            expect="valuation",
            charge=95,
            flags=["CANON+", "RITUAL+", "FUSE+", "ARCHIVE+"],
        )
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=95)
        patch.depth = 10  # High recursion depth

        result = self.organ.invoke(invocation, patch)

        assert result["tier"] == "legendary"
        assert result["value"] >= 80

    def test_assess_value_trivial_tier(self):
        """Test trivial tier valuation."""
        invocation = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="trivial",
            mode="value",
            depth=DepthLevel.LIGHT,
            expect="valuation",
            charge=10,
        )
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=10)

        result = self.organ.invoke(invocation, patch)

        assert result["tier"] == "trivial"
        assert not result["tradeable"]

    def test_assess_value_suggests_dreampoints(self):
        """Test value assessment suggests dreampoints for DREAM+ flag."""
        invocation = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="dream fragment",
            mode="value",
            depth=DepthLevel.STANDARD,
            expect="valuation",
            charge=60,
            flags=["DREAM+"],
        )
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert result["suggested_currency"] == "dreampoints"

    def test_assess_value_suggests_looptokens(self):
        """Test value assessment suggests looptokens for ECHO+ flag."""
        invocation = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="echo fragment",
            mode="value",
            depth=DepthLevel.STANDARD,
            expect="valuation",
            charge=60,
            flags=["ECHO+"],
        )
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert result["suggested_currency"] == "looptokens"

    def test_trade_invalid_format(self):
        """Test trade with invalid format."""
        invocation = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="invalid trade",
            mode="trade",
            depth=DepthLevel.STANDARD,
            expect="trade_record",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "failed"
        assert "Invalid trade format" in result["error"]

    def test_trade_invalid_currency(self):
        """Test trade with invalid currency."""
        invocation = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="SELF:OTHER:fakecoin:10",
            mode="trade",
            depth=DepthLevel.STANDARD,
            expect="trade_record",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "failed"
        assert "Invalid currency" in result["error"]

    def test_trade_invalid_amount(self):
        """Test trade with invalid amount."""
        invocation = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="SELF:OTHER:looptokens:abc",
            mode="trade",
            depth=DepthLevel.STANDARD,
            expect="trade_record",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "failed"
        assert "Invalid amount" in result["error"]

    def test_trade_negative_amount(self):
        """Test trade with negative amount."""
        invocation = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="SELF:OTHER:looptokens:-5",
            mode="trade",
            depth=DepthLevel.STANDARD,
            expect="trade_record",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "failed"
        assert "positive" in result["error"].lower()

    def test_trade_insufficient_balance(self):
        """Test trade with insufficient balance."""
        invocation = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="SELF:OTHER:looptokens:100",
            mode="trade",
            depth=DepthLevel.STANDARD,
            expect="trade_record",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "failed"
        assert "Insufficient balance" in result["error"]

    def test_trade_successful(self):
        """Test successful trade."""
        # First grant balance
        self.organ.grant_balance("SELF", SymbolicCurrency.LOOPTOKENS, 50)

        invocation = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="SELF:ARCHIVE:looptokens:20",
            mode="trade",
            depth=DepthLevel.STANDARD,
            expect="trade_record",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "completed"
        assert result["from_balance"] == 30  # 50 - 20
        assert result["to_balance"] == 20

    def test_mint_charge_too_low(self):
        """Test minting with charge below threshold."""
        invocation = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="SELF",
            mode="mint",
            depth=DepthLevel.STANDARD,
            expect="mint_record",
            charge=40,  # Below threshold
        )
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=40)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "failed"
        assert "Charge too low" in result["error"]

    def test_mint_successful(self):
        """Test successful minting."""
        invocation = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="SELF",
            mode="mint",
            depth=DepthLevel.STANDARD,
            expect="mint_record",
            charge=70,
        )
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=70)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "minted"
        assert result["mint"]["amount"] > 0
        assert result["new_balance"] > 0

    def test_mint_dreampoints_with_flag(self):
        """Test minting dreampoints with DREAM+ flag."""
        invocation = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="SELF",
            mode="mint",
            depth=DepthLevel.STANDARD,
            expect="mint_record",
            charge=60,
            flags=["DREAM+"],
        )
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "minted"
        assert result["mint"]["currency"] == "dreampoints"

    def test_mint_looptokens_with_flag(self):
        """Test minting looptokens with ECHO+ flag."""
        invocation = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="SELF",
            mode="mint",
            depth=DepthLevel.STANDARD,
            expect="mint_record",
            charge=60,
            flags=["ECHO+"],
        )
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert result["mint"]["currency"] == "looptokens"

    def test_mint_higher_charge_more_currency(self):
        """Test higher charge mints more currency."""
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=90)

        inv_low = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="LOW",
            mode="mint",
            depth=DepthLevel.STANDARD,
            expect="mint_record",
            charge=55,
        )
        result_low = self.organ.invoke(inv_low, patch)

        inv_high = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="HIGH",
            mode="mint",
            depth=DepthLevel.STANDARD,
            expect="mint_record",
            charge=95,
        )
        result_high = self.organ.invoke(inv_high, patch)

        assert result_high["mint"]["amount"] > result_low["mint"]["amount"]

    def test_query_ledger_all(self):
        """Test querying all ledger entries."""
        # Create some trades
        self.organ.grant_balance("SELF", SymbolicCurrency.LOOPTOKENS, 100)

        trade_inv = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="SELF:OTHER:looptokens:10",
            mode="trade",
            depth=DepthLevel.STANDARD,
            expect="trade_record",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=60)
        self.organ.invoke(trade_inv, patch)

        # Query ledger
        ledger_inv = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="",
            mode="ledger",
            depth=DepthLevel.STANDARD,
            expect="ledger",
            charge=50,
        )
        result = self.organ.invoke(ledger_inv, patch)

        assert result["status"] == "ledger_retrieved"
        assert len(result["trades"]) >= 1

    def test_query_ledger_filtered(self):
        """Test querying ledger with entity filter."""
        # Create trades
        self.organ.grant_balance("SELF", SymbolicCurrency.LOOPTOKENS, 100)
        self.organ.grant_balance("OTHER", SymbolicCurrency.LOOPTOKENS, 100)

        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=60)

        trade1 = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="SELF:ARCHIVE:looptokens:10",
            mode="trade",
            depth=DepthLevel.STANDARD,
            expect="trade_record",
            charge=60,
        )
        self.organ.invoke(trade1, patch)

        trade2 = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="OTHER:THIRD:looptokens:10",
            mode="trade",
            depth=DepthLevel.STANDARD,
            expect="trade_record",
            charge=60,
        )
        self.organ.invoke(trade2, patch)

        # Query filtered by SELF
        ledger_inv = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="SELF",
            mode="ledger",
            depth=DepthLevel.STANDARD,
            expect="ledger",
            charge=50,
        )
        result = self.organ.invoke(ledger_inv, patch)

        # Should only have trades involving SELF
        for trade in result["trades"]:
            assert trade["from_entity"] == "SELF" or trade["to_entity"] == "SELF"

    def test_check_balance(self):
        """Test checking balance."""
        self.organ.grant_balance("TEST_ENTITY", SymbolicCurrency.DREAMPOINTS, 50)
        self.organ.grant_balance("TEST_ENTITY", SymbolicCurrency.LOOPTOKENS, 30)

        invocation = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="TEST_ENTITY",
            mode="balance",
            depth=DepthLevel.STANDARD,
            expect="balance",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "balance_retrieved"
        assert result["balances"]["dreampoints"] == 50
        assert result["balances"]["looptokens"] == 30
        assert result["total_value"] == 80

    def test_default_economy_status(self):
        """Test default mode returns economy status."""
        invocation = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="economy_status",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "economy_status"
        assert "total_trades" in result
        assert "currency_in_circulation" in result

    def test_grant_balance_direct(self):
        """Test granting balance directly."""
        result = self.organ.grant_balance("ADMIN", SymbolicCurrency.MIRRORCREDITS, 1000)

        assert result["status"] == "granted"
        assert result["new_balance"] == 1000

    def test_state_checkpoint_and_restore(self):
        """Test checkpointing and restoring state."""
        # Create some state
        self.organ.grant_balance("CHECKPOINTED", SymbolicCurrency.DREAMPOINTS, 100)

        # Checkpoint
        state = self.organ.get_state()
        assert state["state"]["balances"]["CHECKPOINTED"]["dreampoints"] == 100

        # Reset
        self.organ.reset()
        assert self.organ._get_balance("CHECKPOINTED", SymbolicCurrency.DREAMPOINTS) == 0

        # Restore
        self.organ.restore_state(state)
        assert self.organ._balances["CHECKPOINTED"]["dreampoints"] == 100

    def test_reset_organ(self):
        """Test resetting organ to initial state."""
        # Create state
        self.organ.grant_balance("RESET_TEST", SymbolicCurrency.LOOPTOKENS, 50)

        # Reset
        self.organ.reset()

        assert len(self.organ._balances) == 0
        assert len(self.organ._trade_ledger) == 0


class TestChamberOfCommerceIntegration:
    """Integration tests for Chamber of Commerce."""

    def test_full_economic_cycle(self):
        """Test a full economic cycle: mint, value, trade."""
        organ = ChamberOfCommerce()
        patch = Patch(input_node="test", output_node="CHAMBER_OF_COMMERCE", tags=[], charge=80)

        # 1. Mint some currency
        mint_inv = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="PRODUCER",
            mode="mint",
            depth=DepthLevel.STANDARD,
            expect="mint_record",
            charge=80,
        )
        mint_result = organ.invoke(mint_inv, patch)
        assert mint_result["status"] == "minted"
        initial_balance = mint_result["new_balance"]

        # 2. Value a fragment
        value_inv = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="valuable fragment",
            mode="value",
            depth=DepthLevel.STANDARD,
            expect="valuation",
            charge=75,
            flags=["CANON+"],
        )
        value_result = organ.invoke(value_inv, patch)
        assert value_result["tradeable"]

        # 3. Trade
        trade_amount = min(5, initial_balance)
        trade_inv = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol=f"PRODUCER:CONSUMER:mirrorcredits:{trade_amount}",
            mode="trade",
            depth=DepthLevel.STANDARD,
            expect="trade_record",
            charge=60,
        )
        trade_result = organ.invoke(trade_inv, patch)
        assert trade_result["status"] == "completed"

        # 4. Check balances
        producer_balance = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="PRODUCER",
            mode="balance",
            depth=DepthLevel.STANDARD,
            expect="balance",
            charge=50,
        )
        producer_result = organ.invoke(producer_balance, patch)
        assert producer_result["balances"]["mirrorcredits"] == initial_balance - trade_amount

        consumer_balance = Invocation(
            organ="CHAMBER_OF_COMMERCE",
            symbol="CONSUMER",
            mode="balance",
            depth=DepthLevel.STANDARD,
            expect="balance",
            charge=50,
        )
        consumer_result = organ.invoke(consumer_balance, patch)
        assert consumer_result["balances"]["mirrorcredits"] == trade_amount


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
