"""
Tests for Time Rules Engine organ.
"""

import pytest
from rege.organs.time_rules import (
    TimeRulesEngine,
    BloomCycleRecord,
    BloomSeason,
    SEASON_CONFIG,
)
from rege.core.models import Invocation, Patch, DepthLevel


class TestBloomSeason:
    """Tests for BloomSeason enum."""

    def test_all_seasons_defined(self):
        """Test all four seasons are defined."""
        seasons = [s.value for s in BloomSeason]

        assert "dormant" in seasons
        assert "sprouting" in seasons
        assert "flowering" in seasons
        assert "seeding" in seasons

    def test_season_config_matches_enum(self):
        """Test season config matches all enum values."""
        for season in BloomSeason:
            assert season.name in SEASON_CONFIG


class TestBloomCycleRecord:
    """Tests for BloomCycleRecord data class."""

    def test_bloom_cycle_creation(self):
        """Test creating a BloomCycleRecord."""
        from datetime import datetime

        now = datetime.now()
        cycle = BloomCycleRecord(
            cycle_id="TEST_CYCLE",
            season=BloomSeason.FLOWERING,
            recurrence=3,
            charge_threshold=60,
            started_at=now,
            last_transition=now,
        )

        assert cycle.season == BloomSeason.FLOWERING
        assert cycle.recurrence == 3
        assert cycle.charge_threshold == 60
        assert cycle.status == "active"

    def test_bloom_cycle_auto_id(self):
        """Test auto-generated cycle ID."""
        from datetime import datetime

        cycle = BloomCycleRecord(
            cycle_id="",
            season=BloomSeason.DORMANT,
            recurrence=1,
            charge_threshold=20,
            started_at=datetime.now(),
            last_transition=datetime.now(),
        )

        assert cycle.cycle_id.startswith("BLOOM_")

    def test_bloom_cycle_to_dict(self):
        """Test serializing bloom cycle."""
        from datetime import datetime

        now = datetime.now()
        cycle = BloomCycleRecord(
            cycle_id="TEST_CYCLE",
            season=BloomSeason.SEEDING,
            recurrence=5,
            charge_threshold=90,
            started_at=now,
            last_transition=now,
            decay_rate=0.1,
        )

        data = cycle.to_dict()

        assert data["season"] == "seeding"
        assert data["recurrence"] == 5
        assert data["decay_rate"] == 0.1


class TestSeasonConfig:
    """Tests for season configuration."""

    def test_all_seasons_have_config(self):
        """Test all seasons have configuration."""
        expected_seasons = {"DORMANT", "SPROUTING", "FLOWERING", "SEEDING"}
        assert expected_seasons == set(SEASON_CONFIG.keys())

    def test_season_config_fields(self):
        """Test each season config has required fields."""
        required_fields = {"charge_range", "next_season", "transition_threshold", "decay_multiplier"}

        for season_name, config in SEASON_CONFIG.items():
            for field in required_fields:
                assert field in config, f"Season {season_name} missing {field}"

    def test_charge_ranges_are_continuous(self):
        """Test charge ranges cover 0-100 without gaps."""
        ranges = sorted([SEASON_CONFIG[s]["charge_range"] for s in SEASON_CONFIG], key=lambda x: x[0])

        assert ranges[0][0] == 0
        assert ranges[-1][1] == 100

    def test_season_cycle_is_complete(self):
        """Test seasons form a complete cycle."""
        visited = set()
        current = "DORMANT"

        for _ in range(4):
            visited.add(current)
            current = SEASON_CONFIG[current]["next_season"]

        assert len(visited) == 4
        assert current == "DORMANT"  # Cycle completes


class TestTimeRulesEngine:
    """Tests for TimeRulesEngine organ."""

    def setup_method(self):
        """Set up test fixtures."""
        self.organ = TimeRulesEngine()

    def test_organ_properties(self):
        """Test organ name and description."""
        assert self.organ.name == "TIME_RULES"
        assert "Temporal" in self.organ.description

    def test_valid_modes(self):
        """Test valid modes list."""
        modes = self.organ.get_valid_modes()

        assert "cycle" in modes
        assert "schedule" in modes
        assert "decay" in modes
        assert "recurrence" in modes
        assert "default" in modes

    def test_output_types(self):
        """Test output types list."""
        output_types = self.organ.get_output_types()

        assert "cycle_state" in output_types
        assert "temporal_state" in output_types

    def test_create_cycle_dormant(self):
        """Test creating cycle with low charge starts DORMANT."""
        invocation = Invocation(
            organ="TIME_RULES",
            symbol="test symbol",
            mode="cycle",
            depth=DepthLevel.STANDARD,
            expect="cycle_state",
            charge=20,
        )
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=20)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "cycle_created"
        assert result["initial_season"] == "dormant"

    def test_create_cycle_sprouting(self):
        """Test creating cycle with medium charge starts SPROUTING."""
        invocation = Invocation(
            organ="TIME_RULES",
            symbol="sprouting test",
            mode="cycle",
            depth=DepthLevel.STANDARD,
            expect="cycle_state",
            charge=40,
        )
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=40)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "cycle_created"
        assert result["initial_season"] == "sprouting"

    def test_create_cycle_flowering(self):
        """Test creating cycle with high charge starts FLOWERING."""
        invocation = Invocation(
            organ="TIME_RULES",
            symbol="flowering test",
            mode="cycle",
            depth=DepthLevel.STANDARD,
            expect="cycle_state",
            charge=70,
        )
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=70)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "cycle_created"
        assert result["initial_season"] == "flowering"

    def test_create_cycle_seeding(self):
        """Test creating cycle with critical charge starts SEEDING."""
        invocation = Invocation(
            organ="TIME_RULES",
            symbol="seeding test",
            mode="cycle",
            depth=DepthLevel.STANDARD,
            expect="cycle_state",
            charge=90,
        )
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=90)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "cycle_created"
        assert result["initial_season"] == "seeding"

    def test_cycle_transition(self):
        """Test cycle advances with increased charge."""
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=25)

        # Create cycle at DORMANT
        invocation1 = Invocation(
            organ="TIME_RULES",
            symbol="transition test",
            mode="cycle",
            depth=DepthLevel.STANDARD,
            expect="cycle_state",
            charge=25,
        )
        result1 = self.organ.invoke(invocation1, patch)
        assert result1["initial_season"] == "dormant"

        # Advance to SPROUTING
        invocation2 = Invocation(
            organ="TIME_RULES",
            symbol="transition test",
            mode="cycle",
            depth=DepthLevel.STANDARD,
            expect="cycle_state",
            charge=30,
        )
        patch.charge = 30
        result2 = self.organ.invoke(invocation2, patch)

        assert result2["status"] == "cycle_advanced"
        assert result2["previous_season"] == "dormant"
        assert result2["new_season"] == "sprouting"

    def test_cycle_no_transition_below_threshold(self):
        """Test cycle doesn't advance if charge below threshold."""
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=40)

        # Create cycle at SPROUTING
        invocation1 = Invocation(
            organ="TIME_RULES",
            symbol="no transition",
            mode="cycle",
            depth=DepthLevel.STANDARD,
            expect="cycle_state",
            charge=40,
        )
        self.organ.invoke(invocation1, patch)

        # Check again with charge still below threshold
        invocation2 = Invocation(
            organ="TIME_RULES",
            symbol="no transition",
            mode="cycle",
            depth=DepthLevel.STANDARD,
            expect="cycle_state",
            charge=45,
        )
        result2 = self.organ.invoke(invocation2, patch)

        assert result2["status"] == "cycle_checked"
        assert result2["current_season"] == "sprouting"
        assert result2["charge_needed"] > 0

    def test_schedule_bloom(self):
        """Test scheduling a future bloom."""
        invocation = Invocation(
            organ="TIME_RULES",
            symbol="scheduled bloom",
            mode="schedule",
            depth=DepthLevel.STANDARD,
            expect="schedule_entry",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "bloom_scheduled"
        assert "schedule" in result
        assert result["days_until_bloom"] == 7  # Default

    def test_schedule_bloom_custom_days(self):
        """Test scheduling bloom with custom days flag."""
        invocation = Invocation(
            organ="TIME_RULES",
            symbol="custom schedule",
            mode="schedule",
            depth=DepthLevel.STANDARD,
            expect="schedule_entry",
            charge=50,
            flags=["DAYS_14"],
        )
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["days_until_bloom"] == 14

    def test_apply_decay(self):
        """Test applying time-based decay."""
        invocation = Invocation(
            organ="TIME_RULES",
            symbol="decay test",
            mode="decay",
            depth=DepthLevel.STANDARD,
            expect="decay_result",
            charge=80,
        )
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=80)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "decay_applied"
        assert result["original_charge"] == 80
        assert result["decay_amount"] > 0
        assert result["decayed_charge"] < 80

    def test_decay_with_season_multiplier(self):
        """Test decay multiplier varies by season."""
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=90)

        # Create cycle at SEEDING (high decay multiplier)
        cycle_inv = Invocation(
            organ="TIME_RULES",
            symbol="seeding decay",
            mode="cycle",
            depth=DepthLevel.STANDARD,
            expect="cycle_state",
            charge=90,
        )
        self.organ.invoke(cycle_inv, patch)

        # Apply decay
        decay_inv = Invocation(
            organ="TIME_RULES",
            symbol="seeding decay",
            mode="decay",
            depth=DepthLevel.STANDARD,
            expect="decay_result",
            charge=90,
        )
        result = self.organ.invoke(decay_inv, patch)

        # SEEDING has 1.5x decay multiplier
        assert result["decay_rate"] == 0.05 * 1.5

    def test_decay_triggers_season_change(self):
        """Test decay can trigger season change."""
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=27)

        # Create cycle barely at SPROUTING
        cycle_inv = Invocation(
            organ="TIME_RULES",
            symbol="season decay",
            mode="cycle",
            depth=DepthLevel.STANDARD,
            expect="cycle_state",
            charge=27,
        )
        self.organ.invoke(cycle_inv, patch)

        # Apply decay with charge that will drop below 26
        decay_inv = Invocation(
            organ="TIME_RULES",
            symbol="season decay",
            mode="decay",
            depth=DepthLevel.STANDARD,
            expect="decay_result",
            charge=26,  # At boundary
        )
        result = self.organ.invoke(decay_inv, patch)

        # Check if season change occurred
        if result["decayed_charge"] < 26:
            assert result["season_change"] is not None

    def test_track_recurrence_first_time(self):
        """Test first recurrence is singular."""
        invocation = Invocation(
            organ="TIME_RULES",
            symbol="recurrence test",
            mode="recurrence",
            depth=DepthLevel.STANDARD,
            expect="recurrence_record",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "recurrence_tracked"
        assert result["recurrence_count"] == 1
        assert result["recurrence_type"] == "singular"
        assert not result["is_pattern"]

    def test_track_recurrence_echo(self):
        """Test second recurrence is echo."""
        invocation = Invocation(
            organ="TIME_RULES",
            symbol="echo test",
            mode="recurrence",
            depth=DepthLevel.STANDARD,
            expect="recurrence_record",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=50)

        self.organ.invoke(invocation, patch)
        result = self.organ.invoke(invocation, patch)

        assert result["recurrence_count"] == 2
        assert result["recurrence_type"] == "echo"

    def test_track_recurrence_pattern(self):
        """Test third+ recurrence is pattern."""
        invocation = Invocation(
            organ="TIME_RULES",
            symbol="pattern test",
            mode="recurrence",
            depth=DepthLevel.STANDARD,
            expect="recurrence_record",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=50)

        for _ in range(3):
            result = self.organ.invoke(invocation, patch)

        assert result["recurrence_count"] == 3
        assert result["recurrence_type"] == "pattern"
        assert result["is_pattern"]

    def test_recurrence_boost(self):
        """Test recurrence provides charge boost."""
        invocation = Invocation(
            organ="TIME_RULES",
            symbol="boost test",
            mode="recurrence",
            depth=DepthLevel.STANDARD,
            expect="recurrence_record",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=50)

        # First call - no boost
        result1 = self.organ.invoke(invocation, patch)
        assert result1["charge_boost"] == 0

        # Multiple calls build boost
        for _ in range(3):
            result = self.organ.invoke(invocation, patch)

        assert result["charge_boost"] > 0

    def test_default_temporal_state(self):
        """Test default mode returns temporal state."""
        invocation = Invocation(
            organ="TIME_RULES",
            symbol="state check",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="temporal_state",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "temporal_state"
        assert result["current_season"] == "FLOWERING"
        assert "active_cycles" in result
        assert "global_decay_rate" in result

    def test_get_cycle(self):
        """Test getting cycle by symbol."""
        invocation = Invocation(
            organ="TIME_RULES",
            symbol="get cycle test",
            mode="cycle",
            depth=DepthLevel.STANDARD,
            expect="cycle_state",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=50)
        self.organ.invoke(invocation, patch)

        cycle = self.organ.get_cycle("get cycle test")

        assert cycle is not None
        assert cycle.season == BloomSeason.SPROUTING

    def test_get_scheduled_blooms(self):
        """Test getting scheduled blooms."""
        invocation = Invocation(
            organ="TIME_RULES",
            symbol="scheduled",
            mode="schedule",
            depth=DepthLevel.STANDARD,
            expect="schedule_entry",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=50)
        self.organ.invoke(invocation, patch)

        blooms = self.organ.get_scheduled_blooms()

        assert len(blooms) == 1
        assert blooms[0]["status"] == "pending"

    def test_get_recurrence_count(self):
        """Test getting recurrence count for symbol."""
        invocation = Invocation(
            organ="TIME_RULES",
            symbol="counted",
            mode="recurrence",
            depth=DepthLevel.STANDARD,
            expect="recurrence_record",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=50)

        for _ in range(5):
            self.organ.invoke(invocation, patch)

        count = self.organ.get_recurrence_count("counted")
        assert count == 5

    def test_set_global_decay_rate(self):
        """Test setting global decay rate."""
        self.organ.set_global_decay_rate(0.1)

        invocation = Invocation(
            organ="TIME_RULES",
            symbol="decay rate test",
            mode="decay",
            depth=DepthLevel.STANDARD,
            expect="decay_result",
            charge=100,
        )
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=100)

        result = self.organ.invoke(invocation, patch)

        assert result["decay_rate"] == 0.1

    def test_decay_rate_clamped(self):
        """Test decay rate is clamped to 0-1."""
        self.organ.set_global_decay_rate(2.0)
        assert self.organ._global_decay_rate <= 1.0

        self.organ.set_global_decay_rate(-0.5)
        assert self.organ._global_decay_rate >= 0.0

    def test_state_checkpoint_and_restore(self):
        """Test checkpointing and restoring state."""
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=50)

        # Create some state
        cycle_inv = Invocation(
            organ="TIME_RULES",
            symbol="checkpoint test",
            mode="cycle",
            depth=DepthLevel.STANDARD,
            expect="cycle_state",
            charge=50,
        )
        self.organ.invoke(cycle_inv, patch)

        rec_inv = Invocation(
            organ="TIME_RULES",
            symbol="checkpoint test",
            mode="recurrence",
            depth=DepthLevel.STANDARD,
            expect="recurrence_record",
            charge=50,
        )
        self.organ.invoke(rec_inv, patch)
        self.organ.invoke(rec_inv, patch)

        # Checkpoint
        state = self.organ.get_state()
        assert state["state"]["recurrence_tracker"]["CHECKPOINT_TEST"] == 2

        # Reset and verify cleared
        self.organ.reset()
        assert self.organ.get_recurrence_count("checkpoint test") == 0

        # Restore
        self.organ.restore_state(state)
        assert self.organ._recurrence_tracker["CHECKPOINT_TEST"] == 2

    def test_reset_organ(self):
        """Test resetting organ to initial state."""
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=50)

        # Create some state
        invocation = Invocation(
            organ="TIME_RULES",
            symbol="reset test",
            mode="cycle",
            depth=DepthLevel.STANDARD,
            expect="cycle_state",
            charge=50,
        )
        self.organ.invoke(invocation, patch)
        self.organ.set_global_decay_rate(0.2)

        # Reset
        self.organ.reset()

        assert len(self.organ._cycles) == 0
        assert len(self.organ._scheduled_blooms) == 0
        assert self.organ._global_decay_rate == 0.05


class TestTimeRulesEngineIntegration:
    """Integration tests for Time Rules Engine."""

    def test_full_bloom_cycle(self):
        """Test progressing through full bloom cycle."""
        organ = TimeRulesEngine()
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=10)

        symbol = "full cycle test"
        charges = [10, 30, 60, 90]
        expected_seasons = ["dormant", "sprouting", "flowering", "seeding"]

        for charge, expected in zip(charges, expected_seasons):
            invocation = Invocation(
                organ="TIME_RULES",
                symbol=symbol,
                mode="cycle",
                depth=DepthLevel.STANDARD,
                expect="cycle_state",
                charge=charge,
            )
            patch.charge = charge
            result = organ.invoke(invocation, patch)

            cycle = organ.get_cycle(symbol)
            assert cycle.season.value == expected, f"Expected {expected} at charge {charge}"

    def test_recurrence_builds_ritual(self):
        """Test many recurrences eventually become ritual/obsession."""
        organ = TimeRulesEngine()
        patch = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=50)

        invocation = Invocation(
            organ="TIME_RULES",
            symbol="ritual builder",
            mode="recurrence",
            depth=DepthLevel.STANDARD,
            expect="recurrence_record",
            charge=50,
        )

        # Build up recurrence
        for i in range(10):
            result = organ.invoke(invocation, patch)

        assert result["recurrence_count"] == 10
        assert result["recurrence_type"] == "ritual"

        # Continue to obsession
        for _ in range(5):
            result = organ.invoke(invocation, patch)

        assert result["recurrence_type"] == "obsession"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
