"""
Extended coverage tests for Heart of Canon organ.

Targets untested paths:
- High recurrence boost with charge cap
- Canonization boundary conditions
- Pulse check cache hit path
- Mythic weight saturation
- Devotional charge boost cap
- Blessing generation for all tiers
"""

import pytest
from datetime import datetime

from rege.organs.heart_of_canon import HeartOfCanon
from rege.core.models import Invocation, Patch, CanonEvent, DepthLevel


@pytest.fixture
def organ():
    """Create a fresh HeartOfCanon instance."""
    return HeartOfCanon()


@pytest.fixture
def patch():
    """Create a test patch."""
    return Patch(
        input_node="TEST",
        output_node="HEART_OF_CANON",
        tags=["TEST+"],
        depth=5,
    )


def make_invocation(symbol="", mode="default", charge=50, flags=None):
    """Helper to create test invocations."""
    return Invocation(
        organ="HEART_OF_CANON",
        symbol=symbol,
        mode=mode,
        charge=charge,
        depth=DepthLevel.STANDARD,
        expect="default_output",
        flags=flags or [],
    )


class TestRecursiveChargeBoost:
    """Test charge boost mechanics in recursive mode."""

    def test_high_recurrence_boost_below_cap(self, organ, patch):
        """Test recurrence >= 3 boosts charge."""
        # Call recursive 4 times to get recurrence = 4
        inv = make_invocation("BoostTest", "recursive", charge=50)
        for _ in range(3):
            organ.invoke(inv, patch)
        result = organ.invoke(inv, patch)

        # 4th call, recurrence=4, boost = 4*5=20
        # charge = min(100, 50 + 20) = 70
        assert result["event"]["charge"] == 70

    def test_high_recurrence_caps_at_100(self, organ, patch):
        """Test charge caps at 100 with very high recurrence."""
        # With charge=70 and recurrence=10, boost = 50
        # charge = min(100, 70 + 50) = 100
        inv = make_invocation("CapTest", "recursive", charge=70)
        for _ in range(10):
            organ.invoke(inv, patch)

        # Check the event charge is capped at 100
        result = organ.invoke(inv, patch)
        assert result["event"]["charge"] == 100

    def test_recurrence_below_3_no_boost(self, organ, patch):
        """Test recurrence < 3 does not boost charge."""
        inv = make_invocation("LowRecurrence", "recursive", charge=50)
        result = organ.invoke(inv, patch)

        # First call, no boost
        assert result["event"]["charge"] == 50
        assert result["recurrence_count"] == 1

    def test_recommended_action_monitor_vs_canonize(self, organ, patch):
        """Test recommended action threshold at recurrence=6."""
        inv = make_invocation("ActionTest", "recursive", charge=50)

        # Recurrence < 6 should recommend "monitor"
        for i in range(5):
            result = organ.invoke(inv, patch)
        assert result["recommended_action"] == "monitor"

        # Recurrence = 6 should recommend "canonize"
        result = organ.invoke(inv, patch)
        assert result["recommended_action"] == "canonize"

    def test_pattern_strength_calculation(self, organ, patch):
        """Test pattern_strength = min(1.0, recurrence/10)."""
        inv = make_invocation("StrengthTest", "recursive", charge=50)

        # 5 calls: strength = 0.5
        for _ in range(5):
            result = organ.invoke(inv, patch)
        assert result["pattern_strength"] == 0.5

        # 10 calls: strength = 1.0
        for _ in range(5):
            result = organ.invoke(inv, patch)
        assert result["pattern_strength"] == 1.0

        # 15 calls: strength still = 1.0 (capped)
        for _ in range(5):
            result = organ.invoke(inv, patch)
        assert result["pattern_strength"] == 1.0


class TestCanonizationBoundaries:
    """Test canonization threshold boundary values."""

    def test_canonize_event_charge_68_fails(self, organ, patch):
        """Charge 68 should fail canonization (threshold 71)."""
        event = CanonEvent(
            event_id="TEST_68",
            content="Below threshold",
            charge=68,
            status="pulse",
            linked_nodes=["TEST"],
        )
        result = organ.canonize_event(event)

        assert result["canonized"] is False
        assert "68" in result["reason"]
        assert "71" in result["reason"]

    def test_canonize_event_charge_70_fails(self, organ, patch):
        """Charge 70 should fail canonization."""
        event = CanonEvent(
            event_id="TEST_70",
            content="Just below",
            charge=70,
            status="pulse",
            linked_nodes=["TEST"],
        )
        result = organ.canonize_event(event)

        assert result["canonized"] is False

    def test_canonize_event_charge_71_succeeds(self, organ, patch):
        """Charge 71 should succeed canonization."""
        event = CanonEvent(
            event_id="TEST_71",
            content="At threshold",
            charge=71,
            status="pulse",
            linked_nodes=["TEST"],
        )
        result = organ.canonize_event(event)

        assert result["canonized"] is True
        assert result["tier"] == "INTENSE"

    def test_canonize_event_sets_timestamp(self, organ, patch):
        """Canonization should set canonized_at timestamp."""
        event = CanonEvent(
            event_id="TIMESTAMP_TEST",
            content="Timestamp test",
            charge=80,
            status="pulse",
            linked_nodes=["TEST"],
        )
        result = organ.canonize_event(event)

        assert "canonized_at" in result
        assert event.canonized_at is not None


class TestPulseCheckCacheHit:
    """Test pulse_check with pre-canonized memories."""

    def test_pulse_check_finds_canonized_memory(self, organ, patch):
        """Pulse check should find and return canonized memory status."""
        # First, canonize a memory
        inv = make_invocation("CachedMemory", "mythic", charge=80)
        result = organ._mythic_process(inv, patch)
        event_id = result["event"]["event_id"]

        # Canonize it
        event = CanonEvent(
            event_id=event_id,
            content="CachedMemory",
            charge=80,
            status="pulse",
            linked_nodes=["TEST"],
        )
        organ.canonize_event(event)

        # Now pulse_check should find it
        result = organ.pulse_check("CachedMemory", charge=50)

        assert result["status"] == "glowing"
        assert result["in_canon"] is True
        assert "event_id" in result

    def test_pulse_check_not_in_canon(self, organ, patch):
        """Pulse check on non-canonized memory."""
        result = organ.pulse_check("NewMemory", charge=50)

        assert result["status"] == "echo"
        assert result["in_canon"] is False


class TestPulseCheckBoundaries:
    """Test pulse_check charge tier boundaries."""

    def test_pulse_check_charge_85_canon_candidate(self, organ, patch):
        """Charge 85 should be canon_candidate."""
        result = organ.pulse_check("Test", charge=85)
        assert result["status"] == "canon_candidate"

    def test_pulse_check_charge_86_emergent_canon(self, organ, patch):
        """Charge 86 should be emergent_canon."""
        result = organ.pulse_check("Test", charge=86)
        assert result["status"] == "emergent_canon"

    def test_pulse_check_charge_71_canon_candidate(self, organ, patch):
        """Charge 71 should be canon_candidate."""
        result = organ.pulse_check("Test", charge=71)
        assert result["status"] == "canon_candidate"

    def test_pulse_check_charge_70_echo(self, organ, patch):
        """Charge 70 should be echo."""
        result = organ.pulse_check("Test", charge=70)
        assert result["status"] == "echo"


class TestMythicWeight:
    """Test mythic weight calculation."""

    def test_mythic_weight_saturation(self, organ, patch):
        """Test recurrence_bonus caps at 0.3."""
        event = CanonEvent(
            event_id="WEIGHT_TEST",
            content="High recurrence",
            charge=50,
            status="pulse",
            linked_nodes=["TEST"],
            recurrence=10,  # 10 * 0.05 = 0.5, capped to 0.3
        )

        weight = organ._calculate_mythic_weight(event)

        # base = 50/100 = 0.5
        # recurrence_bonus = min(0.3, 0.5) = 0.3
        # total = min(1.0, 0.5 + 0.3) = 0.8
        assert weight == pytest.approx(0.8)

    def test_mythic_weight_caps_at_1(self, organ, patch):
        """Test mythic weight caps at 1.0."""
        event = CanonEvent(
            event_id="WEIGHT_CAP",
            content="Max weight",
            charge=90,
            status="pulse",
            linked_nodes=["TEST"],
            recurrence=10,
        )

        weight = organ._calculate_mythic_weight(event)

        # base = 0.9, recurrence_bonus = 0.3
        # total = min(1.0, 0.9 + 0.3) = 1.0
        assert weight == 1.0


class TestDevotionalChargeCap:
    """Test devotional mode charge boost capping."""

    def test_devotional_boost_below_cap(self, organ, patch):
        """Devotional +10 boost when charge is low."""
        inv = make_invocation("DevTest", "devotional", charge=50)
        result = organ.invoke(inv, patch)

        assert result["event"]["charge"] == 60

    def test_devotional_boost_caps_at_100(self, organ, patch):
        """Devotional +10 should cap at 100."""
        inv = make_invocation("DevCapTest", "devotional", charge=95)
        result = organ.invoke(inv, patch)

        assert result["event"]["charge"] == 100


class TestBlessingGeneration:
    """Test blessing generation for all tiers."""

    def test_blessing_latent(self, organ, patch):
        """Test LATENT tier blessing."""
        inv = make_invocation("LatentTest", "devotional", charge=10)
        result = organ.invoke(inv, patch)

        # charge becomes 20 after +10 boost, still LATENT
        assert "seed" in result["blessing"].lower()

    def test_blessing_processing(self, organ, patch):
        """Test PROCESSING tier blessing."""
        inv = make_invocation("ProcessTest", "devotional", charge=30)
        result = organ.invoke(inv, patch)

        # charge becomes 40 after +10 boost, PROCESSING
        assert "work" in result["blessing"].lower() or "silence" in result["blessing"].lower()

    def test_blessing_active(self, organ, patch):
        """Test ACTIVE tier blessing."""
        inv = make_invocation("ActiveTest", "devotional", charge=50)
        result = organ.invoke(inv, patch)

        # charge becomes 60 after +10 boost, ACTIVE
        assert "attention" in result["blessing"].lower() or "witnessed" in result["blessing"].lower()

    def test_blessing_intense(self, organ, patch):
        """Test INTENSE tier blessing."""
        inv = make_invocation("IntenseTest", "devotional", charge=70)
        result = organ.invoke(inv, patch)

        # charge becomes 80 after +10 boost, INTENSE
        assert "heart" in result["blessing"].lower() or "recognizes" in result["blessing"].lower()

    def test_blessing_critical(self, organ, patch):
        """Test CRITICAL tier blessing."""
        inv = make_invocation("CriticalTest", "devotional", charge=80)
        result = organ.invoke(inv, patch)

        # charge becomes 90 after +10 boost, CRITICAL
        assert "canon" in result["blessing"].lower()


class TestMythicProcessEmergentCanon:
    """Test mythic process emergent canon path."""

    def test_mythic_emergent_canon_status(self, organ, patch):
        """Test mythic with CRITICAL charge gets emergent_canon status."""
        inv = make_invocation("EmergentTest", "mythic", charge=90)
        result = organ.invoke(inv, patch)

        assert result["event"]["status"] == "emergent_canon"

    def test_mythic_canon_candidate_status(self, organ, patch):
        """Test mythic with INTENSE charge gets canon_candidate status."""
        inv = make_invocation("CandidateTest", "mythic", charge=75)
        result = organ.invoke(inv, patch)

        assert result["event"]["status"] == "canon_candidate"

    def test_mythic_pulse_status(self, organ, patch):
        """Test mythic with low charge stays as pulse."""
        inv = make_invocation("PulseTest", "mythic", charge=50)
        result = organ.invoke(inv, patch)

        # Not canon eligible, stays as pulse
        assert result["event"]["status"] == "pulse"


class TestBleedIntoArchive:
    """Test bleed_into_archive method."""

    def test_bleed_recurring_status(self, organ, patch):
        """Test loop_status is 'recurring' when recurrence > 1."""
        event = CanonEvent(
            event_id="BLEED_REC",
            content="Recurring event",
            charge=60,
            status="pulse",
            linked_nodes=["TEST"],
            recurrence=5,
        )

        result = organ.bleed_into_archive(event)

        assert result["loop_status"] == "recurring"

    def test_bleed_singular_status(self, organ, patch):
        """Test loop_status is 'singular' when recurrence = 1."""
        event = CanonEvent(
            event_id="BLEED_SING",
            content="Single event",
            charge=60,
            status="pulse",
            linked_nodes=["TEST"],
            recurrence=1,
        )

        result = organ.bleed_into_archive(event)

        assert result["loop_status"] == "singular"

    def test_bleed_zero_recurrence_singular(self, organ, patch):
        """Test loop_status is 'singular' when recurrence = 0."""
        event = CanonEvent(
            event_id="BLEED_ZERO",
            content="Zero recurrence",
            charge=60,
            status="pulse",
            linked_nodes=["TEST"],
            recurrence=0,
        )

        result = organ.bleed_into_archive(event)

        assert result["loop_status"] == "singular"


class TestGetCanonEvents:
    """Test get_canon_events method."""

    def test_get_canon_events_empty(self, organ, patch):
        """Test returns empty list when no events."""
        assert organ.get_canon_events() == []

    def test_get_canon_events_after_canonization(self, organ, patch):
        """Test returns canonized events."""
        event = CanonEvent(
            event_id="GET_TEST",
            content="Test event",
            charge=80,
            status="pulse",
            linked_nodes=["TEST"],
        )
        organ.canonize_event(event)

        events = organ.get_canon_events()
        assert len(events) == 1
        assert events[0].event_id == "GET_TEST"


class TestGetRecurrenceStats:
    """Test recurrence statistics."""

    def test_recurrence_stats_tracking(self, organ, patch):
        """Test recurrence stats are tracked correctly."""
        inv1 = make_invocation("Symbol1", "recursive", charge=50)
        inv2 = make_invocation("Symbol2", "recursive", charge=50)

        for _ in range(3):
            organ.invoke(inv1, patch)
        for _ in range(2):
            organ.invoke(inv2, patch)

        stats = organ.get_recurrence_stats()

        assert stats["Symbol1"] == 3
        assert stats["Symbol2"] == 2
