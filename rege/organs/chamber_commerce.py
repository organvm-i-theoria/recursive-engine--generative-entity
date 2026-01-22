"""
RE:GE Chamber of Commerce - Symbolic economy and mythic valuation engine.

Based on: RE-GE_ORG_BODY_12_CHAMBER_OF_COMMERCE.md

The Chamber of Commerce governs:
- Symbolic currency types and their creation
- Mythic valuation of fragments and processes
- Trade and exchange between symbolic entities
- Economic ledger tracking
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid

from rege.organs.base import OrganHandler
from rege.core.models import Invocation, Patch


class SymbolicCurrency(Enum):
    """Types of symbolic currency in the mythic economy."""
    DREAMPOINTS = "dreampoints"      # Earned through dream processing
    LOOPTOKENS = "looptokens"        # Earned through recurrence and patterns
    MIRRORCREDITS = "mirrorcredits"  # Earned through reflection and shadow work


@dataclass
class TradeRecord:
    """
    Record of a symbolic trade transaction.

    Trades transfer value between entities within the mythic economy.
    """
    trade_id: str
    from_entity: str
    to_entity: str
    currency: SymbolicCurrency
    amount: int
    charge_at_trade: int
    timestamp: datetime
    reason: str = ""
    status: str = "completed"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.trade_id:
            self.trade_id = f"TRADE_{uuid.uuid4().hex[:8].upper()}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize trade record to dictionary."""
        return {
            "trade_id": self.trade_id,
            "from_entity": self.from_entity,
            "to_entity": self.to_entity,
            "currency": self.currency.value,
            "amount": self.amount,
            "charge_at_trade": self.charge_at_trade,
            "timestamp": self.timestamp.isoformat(),
            "reason": self.reason,
            "status": self.status,
            "metadata": self.metadata,
        }


@dataclass
class MintRecord:
    """Record of currency minting."""
    mint_id: str
    currency: SymbolicCurrency
    amount: int
    recipient: str
    source_ritual: str
    charge_at_mint: int
    timestamp: datetime

    def __post_init__(self):
        if not self.mint_id:
            self.mint_id = f"MINT_{uuid.uuid4().hex[:8].upper()}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize mint record to dictionary."""
        return {
            "mint_id": self.mint_id,
            "currency": self.currency.value,
            "amount": self.amount,
            "recipient": self.recipient,
            "source_ritual": self.source_ritual,
            "charge_at_mint": self.charge_at_mint,
            "timestamp": self.timestamp.isoformat(),
        }


# Valuation coefficients
VALUATION_CONFIG = {
    "recursion_multiplier": 2,
    "charge_weight": 1,
    "base_cost": 10,
    "max_daily_mint": 100,
    "mint_charge_threshold": 51,  # ACTIVE tier minimum
}


class ChamberOfCommerce(OrganHandler):
    """
    Chamber of Commerce - Symbolic economy and mythic valuation engine.

    Modes:
    - value: Assess symbolic value of fragment/process
    - trade: Execute fragment exchange
    - mint: Create new currency units
    - ledger: Query trade history
    - balance: Check entity balance
    - default: Economy status
    """

    @property
    def name(self) -> str:
        return "CHAMBER_OF_COMMERCE"

    @property
    def description(self) -> str:
        return "Symbolic economy and mythic valuation engine"

    def __init__(self):
        super().__init__()
        self._balances: Dict[str, Dict[str, int]] = {}  # entity -> {currency -> amount}
        self._trade_ledger: List[TradeRecord] = []
        self._mint_ledger: List[MintRecord] = []
        self._daily_minted: Dict[str, int] = {}  # date_str -> total_minted
        self._valuation_cache: Dict[str, Dict[str, Any]] = {}

    def invoke(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process invocation through Chamber of Commerce."""
        mode = invocation.mode.lower()

        if mode == "value":
            return self._assess_value(invocation, patch)
        elif mode == "trade":
            return self._execute_trade(invocation, patch)
        elif mode == "mint":
            return self._mint_currency(invocation, patch)
        elif mode == "ledger":
            return self._query_ledger(invocation, patch)
        elif mode == "balance":
            return self._check_balance(invocation, patch)
        else:
            return self._default_economy(invocation, patch)

    def _assess_value(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Assess symbolic value of a fragment/process."""
        symbol = invocation.symbol
        charge = invocation.charge
        flags = invocation.flags

        # Calculate recursion factor from recurrence tracking
        recursion_depth = patch.depth + 1

        # Count value-boosting flags
        value_flags = ["CANON+", "RITUAL+", "FUSE+", "ARCHIVE+"]
        flag_bonus = sum(5 for f in flags if f.upper() in value_flags)

        # Calculate value: value = (recursion * 2 + charge) - cost + flag_bonus
        config = VALUATION_CONFIG
        raw_value = (recursion_depth * config["recursion_multiplier"] + charge) - config["base_cost"] + flag_bonus
        value = max(0, raw_value)

        # Determine value tier
        if value >= 80:
            tier = "legendary"
        elif value >= 60:
            tier = "rare"
        elif value >= 40:
            tier = "uncommon"
        elif value >= 20:
            tier = "common"
        else:
            tier = "trivial"

        # Suggest appropriate currency
        if "DREAM+" in flags:
            suggested_currency = SymbolicCurrency.DREAMPOINTS
        elif "ECHO+" in flags or recursion_depth > 3:
            suggested_currency = SymbolicCurrency.LOOPTOKENS
        else:
            suggested_currency = SymbolicCurrency.MIRRORCREDITS

        valuation = {
            "status": "valued",
            "symbol": symbol[:50] if symbol else "unnamed",
            "value": value,
            "tier": tier,
            "components": {
                "recursion_contribution": recursion_depth * config["recursion_multiplier"],
                "charge_contribution": charge,
                "flag_bonus": flag_bonus,
                "base_cost": config["base_cost"],
            },
            "suggested_currency": suggested_currency.value,
            "tradeable": value >= 20,
        }

        # Cache valuation
        if symbol:
            self._valuation_cache[symbol[:50]] = valuation

        return valuation

    def _execute_trade(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Execute a symbolic trade between entities."""
        # Parse trade details from symbol: "FROM:TO:CURRENCY:AMOUNT"
        parts = invocation.symbol.split(":")
        if len(parts) < 4:
            return {
                "status": "failed",
                "error": "Invalid trade format. Use FROM:TO:CURRENCY:AMOUNT",
                "example": "SELF:ARCHIVE:looptokens:10",
            }

        from_entity = parts[0].strip().upper()
        to_entity = parts[1].strip().upper()
        currency_str = parts[2].strip().lower()
        try:
            amount = int(parts[3].strip())
        except ValueError:
            return {
                "status": "failed",
                "error": f"Invalid amount: {parts[3]}",
            }

        # Validate currency
        try:
            currency = SymbolicCurrency(currency_str)
        except ValueError:
            return {
                "status": "failed",
                "error": f"Invalid currency: {currency_str}",
                "valid_currencies": [c.value for c in SymbolicCurrency],
            }

        # Validate amount
        if amount <= 0:
            return {
                "status": "failed",
                "error": "Trade amount must be positive",
            }

        # Check sender balance
        sender_balance = self._get_balance(from_entity, currency)
        if sender_balance < amount:
            return {
                "status": "failed",
                "error": "Insufficient balance",
                "available": sender_balance,
                "requested": amount,
            }

        # Execute trade
        self._debit(from_entity, currency, amount)
        self._credit(to_entity, currency, amount)

        # Record trade
        trade = TradeRecord(
            trade_id="",
            from_entity=from_entity,
            to_entity=to_entity,
            currency=currency,
            amount=amount,
            charge_at_trade=invocation.charge,
            timestamp=datetime.now(),
            reason=f"Ritual trade at charge {invocation.charge}",
        )
        self._trade_ledger.append(trade)

        return {
            "status": "completed",
            "trade": trade.to_dict(),
            "from_balance": self._get_balance(from_entity, currency),
            "to_balance": self._get_balance(to_entity, currency),
        }

    def _mint_currency(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Mint new symbolic currency."""
        # Check charge threshold
        if invocation.charge < VALUATION_CONFIG["mint_charge_threshold"]:
            return {
                "status": "failed",
                "error": "Charge too low for minting",
                "required_charge": VALUATION_CONFIG["mint_charge_threshold"],
                "current_charge": invocation.charge,
            }

        # Determine currency type from flags or default
        if "DREAM+" in invocation.flags:
            currency = SymbolicCurrency.DREAMPOINTS
        elif "ECHO+" in invocation.flags or "LAW_LOOP+" in invocation.flags:
            currency = SymbolicCurrency.LOOPTOKENS
        else:
            currency = SymbolicCurrency.MIRRORCREDITS

        # Calculate mint amount based on charge
        # Higher charge = more currency minted
        base_mint = (invocation.charge - 50) // 5  # 1 per 5 charge above 50
        mint_amount = max(1, base_mint)

        # Check daily limit
        today = datetime.now().strftime("%Y-%m-%d")
        daily_total = self._daily_minted.get(today, 0)
        if daily_total + mint_amount > VALUATION_CONFIG["max_daily_mint"]:
            available = VALUATION_CONFIG["max_daily_mint"] - daily_total
            if available <= 0:
                return {
                    "status": "failed",
                    "error": "Daily mint limit reached",
                    "daily_limit": VALUATION_CONFIG["max_daily_mint"],
                    "minted_today": daily_total,
                }
            mint_amount = available

        # Determine recipient (SELF or from symbol)
        recipient = invocation.symbol.strip().upper() if invocation.symbol else "SELF"

        # Credit the minted amount
        self._credit(recipient, currency, mint_amount)

        # Track daily minting
        self._daily_minted[today] = daily_total + mint_amount

        # Record mint
        mint = MintRecord(
            mint_id="",
            currency=currency,
            amount=mint_amount,
            recipient=recipient,
            source_ritual=f"charge_{invocation.charge}",
            charge_at_mint=invocation.charge,
            timestamp=datetime.now(),
        )
        self._mint_ledger.append(mint)

        return {
            "status": "minted",
            "mint": mint.to_dict(),
            "new_balance": self._get_balance(recipient, currency),
            "daily_remaining": VALUATION_CONFIG["max_daily_mint"] - self._daily_minted[today],
        }

    def _query_ledger(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Query the trade ledger."""
        entity_filter = invocation.symbol.strip().upper() if invocation.symbol else None

        # Filter trades
        if entity_filter:
            trades = [
                t.to_dict() for t in self._trade_ledger
                if t.from_entity == entity_filter or t.to_entity == entity_filter
            ]
            mints = [
                m.to_dict() for m in self._mint_ledger
                if m.recipient == entity_filter
            ]
        else:
            trades = [t.to_dict() for t in self._trade_ledger[-50:]]  # Last 50
            mints = [m.to_dict() for m in self._mint_ledger[-50:]]

        return {
            "status": "ledger_retrieved",
            "filter": entity_filter,
            "trades": trades,
            "mints": mints,
            "total_trades": len(self._trade_ledger),
            "total_mints": len(self._mint_ledger),
        }

    def _check_balance(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Check balance for an entity."""
        entity = invocation.symbol.strip().upper() if invocation.symbol else "SELF"

        balances = self._balances.get(entity, {})

        return {
            "status": "balance_retrieved",
            "entity": entity,
            "balances": {
                currency.value: balances.get(currency.value, 0)
                for currency in SymbolicCurrency
            },
            "total_value": sum(balances.values()),
        }

    def _default_economy(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Return economy status."""
        total_trades = len(self._trade_ledger)
        total_mints = len(self._mint_ledger)

        # Calculate total currency in circulation
        circulation = {currency.value: 0 for currency in SymbolicCurrency}
        for entity_balances in self._balances.values():
            for currency, amount in entity_balances.items():
                circulation[currency] = circulation.get(currency, 0) + amount

        return {
            "status": "economy_status",
            "total_trades": total_trades,
            "total_mints": total_mints,
            "entities_count": len(self._balances),
            "currency_in_circulation": circulation,
            "today_minted": self._daily_minted.get(datetime.now().strftime("%Y-%m-%d"), 0),
            "valuation_config": VALUATION_CONFIG,
        }

    def _get_balance(self, entity: str, currency: SymbolicCurrency) -> int:
        """Get balance for entity and currency."""
        if entity not in self._balances:
            return 0
        return self._balances[entity].get(currency.value, 0)

    def _credit(self, entity: str, currency: SymbolicCurrency, amount: int) -> None:
        """Credit amount to entity."""
        if entity not in self._balances:
            self._balances[entity] = {}
        current = self._balances[entity].get(currency.value, 0)
        self._balances[entity][currency.value] = current + amount

    def _debit(self, entity: str, currency: SymbolicCurrency, amount: int) -> None:
        """Debit amount from entity."""
        if entity not in self._balances:
            self._balances[entity] = {}
        current = self._balances[entity].get(currency.value, 0)
        self._balances[entity][currency.value] = max(0, current - amount)

    def grant_balance(self, entity: str, currency: SymbolicCurrency, amount: int) -> Dict[str, Any]:
        """Grant balance directly (for testing/admin)."""
        self._credit(entity, currency, amount)
        return {
            "status": "granted",
            "entity": entity,
            "currency": currency.value,
            "amount": amount,
            "new_balance": self._get_balance(entity, currency),
        }

    def get_valid_modes(self) -> List[str]:
        return ["value", "trade", "mint", "ledger", "balance", "default"]

    def get_output_types(self) -> List[str]:
        return ["valuation", "trade_record", "mint_record", "ledger", "balance", "economy_status"]

    def get_state(self) -> Dict[str, Any]:
        """Get current organ state for checkpointing."""
        state = super().get_state()
        state["state"].update({
            "balances": self._balances,
            "trade_ledger": [t.to_dict() for t in self._trade_ledger],
            "mint_ledger": [m.to_dict() for m in self._mint_ledger],
            "daily_minted": self._daily_minted,
        })
        return state

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore organ state from checkpoint."""
        super().restore_state(state)
        inner_state = state.get("state", {})
        self._balances = inner_state.get("balances", {})
        self._daily_minted = inner_state.get("daily_minted", {})
        # Note: ledger restoration would require TradeRecord/MintRecord deserialization

    def reset(self) -> None:
        """Reset organ to initial state."""
        super().reset()
        self._balances = {}
        self._trade_ledger = []
        self._mint_ledger = []
        self._daily_minted = {}
        self._valuation_cache = {}
