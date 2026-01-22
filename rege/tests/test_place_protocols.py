"""
Tests for Place Protocols organ.
"""

import pytest
from rege.organs.place_protocols import PlaceProtocols, RitualPlace, CANONICAL_ZONES
from rege.core.models import Invocation, Patch, DepthLevel


class TestRitualPlace:
    """Tests for RitualPlace data class."""

    def test_ritual_place_creation(self):
        """Test creating a RitualPlace."""
        place = RitualPlace(
            place_id="TEST_PLACE",
            zone="TEST_ZONE",
            functions=["testing", "validation"],
            time_behavior="linear",
        )

        assert place.zone == "TEST_ZONE"
        assert "testing" in place.functions
        assert place.time_behavior == "linear"
        assert place.charge_modifier == 0
        assert place.access_level == "open"

    def test_ritual_place_to_dict(self):
        """Test serializing RitualPlace."""
        place = RitualPlace(
            place_id="TEST_PLACE",
            zone="TEST_ZONE",
            functions=["testing"],
            time_behavior="linear",
            charge_modifier=10,
            linked_organs=["HEART_OF_CANON"],
        )

        data = place.to_dict()

        assert data["zone"] == "TEST_ZONE"
        assert data["charge_modifier"] == 10
        assert "HEART_OF_CANON" in data["linked_organs"]

    def test_ritual_place_auto_id(self):
        """Test auto-generated place ID."""
        place = RitualPlace(
            place_id="",
            zone="AUTO_ZONE",
            functions=[],
            time_behavior="instant",
        )

        assert place.place_id.startswith("PLACE_")


class TestCanonicalZones:
    """Tests for canonical zone definitions."""

    def test_all_canonical_zones_defined(self):
        """Test that all 10 canonical zones are defined."""
        expected_zones = {
            "HERE", "THERE", "NOWHERE", "SOMEWHERE", "BACKTHEN",
            "NEVERW4S", "MAIN_STREET", "MULHOLLAND_DRIVE", "THE_ARCHIVE", "THE_STAGE"
        }

        assert expected_zones == set(CANONICAL_ZONES.keys())

    def test_canonical_zones_have_required_fields(self):
        """Test that all zones have required configuration fields."""
        required_fields = {"functions", "time_behavior", "charge_modifier", "access_level", "linked_organs"}

        for zone_name, zone_config in CANONICAL_ZONES.items():
            for field in required_fields:
                assert field in zone_config, f"Zone {zone_name} missing field {field}"

    def test_here_zone_is_default(self):
        """Test that HERE zone is the neutral default."""
        here = CANONICAL_ZONES["HERE"]

        assert here["charge_modifier"] == 0
        assert here["access_level"] == "open"
        assert "presence" in here["functions"]

    def test_nowhere_zone_is_restricted(self):
        """Test that NOWHERE zone is restricted."""
        nowhere = CANONICAL_ZONES["NOWHERE"]

        assert nowhere["access_level"] == "restricted"
        assert nowhere["charge_modifier"] < 0

    def test_mulholland_drive_is_conditional(self):
        """Test that MULHOLLAND_DRIVE requires conditional access."""
        mulholland = CANONICAL_ZONES["MULHOLLAND_DRIVE"]

        assert mulholland["access_level"] == "conditional"
        assert mulholland["charge_modifier"] > 0


class TestPlaceProtocols:
    """Tests for PlaceProtocols organ."""

    def setup_method(self):
        """Set up test fixtures."""
        self.organ = PlaceProtocols()

    def test_organ_properties(self):
        """Test organ name and description."""
        assert self.organ.name == "PLACE_PROTOCOLS"
        assert "Spatial context" in self.organ.description

    def test_valid_modes(self):
        """Test valid modes list."""
        modes = self.organ.get_valid_modes()

        assert "enter" in modes
        assert "exit" in modes
        assert "map" in modes
        assert "rules" in modes
        assert "default" in modes

    def test_output_types(self):
        """Test output types list."""
        output_types = self.organ.get_output_types()

        assert "place_state" in output_types
        assert "transition_record" in output_types

    def test_default_place_is_here(self):
        """Test that default starting place is HERE."""
        assert self.organ.get_current_place() == "HERE"

    def test_enter_canonical_zone(self):
        """Test entering a canonical zone."""
        invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="THE_ARCHIVE",
            mode="enter",
            depth=DepthLevel.STANDARD,
            expect="place_state",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "entered"
        assert result["zone"] == "THE_ARCHIVE"
        assert result["previous_zone"] == "HERE"
        assert self.organ.get_current_place() == "THE_ARCHIVE"

    def test_enter_restricted_zone_denied(self):
        """Test entering restricted zone with low charge."""
        invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="NOWHERE",
            mode="enter",
            depth=DepthLevel.STANDARD,
            expect="place_state",
            charge=50,  # Below INTENSE threshold
        )
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "access_denied"
        assert result["required_charge"] == 71

    def test_enter_restricted_zone_allowed(self):
        """Test entering restricted zone with high charge."""
        invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="NOWHERE",
            mode="enter",
            depth=DepthLevel.STANDARD,
            expect="place_state",
            charge=80,  # Above INTENSE threshold
        )
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=80)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "entered"
        assert result["zone"] == "NOWHERE"

    def test_enter_conditional_zone_denied(self):
        """Test entering conditional zone with low charge."""
        invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="MULHOLLAND_DRIVE",
            mode="enter",
            depth=DepthLevel.STANDARD,
            expect="place_state",
            charge=40,  # Below ACTIVE threshold
        )
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=40)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "access_denied"
        assert result["required_charge"] == 51

    def test_enter_conditional_zone_allowed(self):
        """Test entering conditional zone with sufficient charge."""
        invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="THE_STAGE",
            mode="enter",
            depth=DepthLevel.STANDARD,
            expect="place_state",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "entered"
        assert result["zone"] == "THE_STAGE"

    def test_enter_unknown_zone(self):
        """Test entering unknown zone fails."""
        invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="FANTASY_LAND",
            mode="enter",
            depth=DepthLevel.STANDARD,
            expect="place_state",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "failed"
        assert "Unknown zone" in result["error"]
        assert "available_zones" in result

    def test_exit_place_returns_to_here(self):
        """Test exiting returns to HERE."""
        # First enter a place
        enter_invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="THE_ARCHIVE",
            mode="enter",
            depth=DepthLevel.STANDARD,
            expect="place_state",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=50)
        self.organ.invoke(enter_invocation, patch)

        # Then exit
        exit_invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="",
            mode="exit",
            depth=DepthLevel.STANDARD,
            expect="place_state",
            charge=50,
        )
        result = self.organ.invoke(exit_invocation, patch)

        assert result["status"] == "exited"
        assert result["previous_zone"] == "THE_ARCHIVE"
        assert result["current_zone"] == "HERE"
        assert self.organ.get_current_place() == "HERE"

    def test_exit_from_here(self):
        """Test exiting when already at HERE."""
        invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="",
            mode="exit",
            depth=DepthLevel.STANDARD,
            expect="place_state",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "already_here"

    def test_map_location(self):
        """Test mapping current location."""
        invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="",
            mode="map",
            depth=DepthLevel.STANDARD,
            expect="location_map",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "mapped"
        assert result["current_zone"] == "HERE"
        assert "available_zones" in result
        assert len(result["available_zones"]) == 10

    def test_get_zone_rules(self):
        """Test getting zone rules."""
        invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="BACKTHEN",
            mode="rules",
            depth=DepthLevel.STANDARD,
            expect="zone_rules",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "rules_retrieved"
        assert result["zone"] == "BACKTHEN"
        assert "rules" in result
        assert len(result["rules"]) > 0

    def test_get_rules_unknown_zone(self):
        """Test getting rules for unknown zone."""
        invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="FAKE_ZONE",
            mode="rules",
            depth=DepthLevel.STANDARD,
            expect="zone_rules",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "unknown_zone"

    def test_default_mode(self):
        """Test default mode returns status."""
        invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="test symbol",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="place_state",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "location_status"
        assert result["current_zone"] == "HERE"

    def test_charge_modifier_applied(self):
        """Test charge modifier is applied on zone entry."""
        invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="MULHOLLAND_DRIVE",
            mode="enter",
            depth=DepthLevel.STANDARD,
            expect="place_state",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "entered"
        assert result["charge_modifier"] == 20
        assert result["modified_charge"] == 80  # 60 + 20

    def test_charge_modifier_capped_at_100(self):
        """Test charge modifier is capped at 100."""
        invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="MULHOLLAND_DRIVE",
            mode="enter",
            depth=DepthLevel.STANDARD,
            expect="place_state",
            charge=95,
        )
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=95)

        result = self.organ.invoke(invocation, patch)

        assert result["modified_charge"] == 100  # Capped

    def test_negative_charge_modifier(self):
        """Test negative charge modifier."""
        invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="NOWHERE",
            mode="enter",
            depth=DepthLevel.STANDARD,
            expect="place_state",
            charge=80,
        )
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=80)

        result = self.organ.invoke(invocation, patch)

        assert result["charge_modifier"] == -20
        assert result["modified_charge"] == 60  # 80 - 20

    def test_place_history_tracking(self):
        """Test place transition history is tracked."""
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=60)

        # Make several transitions
        zones = ["THE_ARCHIVE", "SOMEWHERE", "BACKTHEN"]
        for zone in zones:
            invocation = Invocation(
                organ="PLACE_PROTOCOLS",
                symbol=zone,
                mode="enter",
                depth=DepthLevel.STANDARD,
                expect="place_state",
                charge=60,
            )
            self.organ.invoke(invocation, patch)

        history = self.organ.get_place_history()

        assert len(history) == 3
        assert history[0]["to_place"] == "THE_ARCHIVE"
        assert history[1]["to_place"] == "SOMEWHERE"
        assert history[2]["to_place"] == "BACKTHEN"

    def test_register_custom_place(self):
        """Test registering a custom place."""
        custom_place = RitualPlace(
            place_id="CUSTOM_1",
            zone="MY_CUSTOM_ZONE",
            functions=["custom_function"],
            time_behavior="custom_time",
            charge_modifier=5,
        )

        result = self.organ.register_custom_place(custom_place)

        assert result["status"] == "registered"
        assert result["zone"] == "MY_CUSTOM_ZONE"

        # Now enter the custom zone
        invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="MY_CUSTOM_ZONE",
            mode="enter",
            depth=DepthLevel.STANDARD,
            expect="place_state",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=50)

        enter_result = self.organ.invoke(invocation, patch)
        assert enter_result["status"] == "entered"

    def test_add_zone_rule(self):
        """Test adding custom zone rule."""
        result = self.organ.add_zone_rule("HERE", "Custom rule: Always be present")

        assert result["status"] == "rule_added"
        assert result["total_rules"] == 1

        # Check rule appears in rules query
        invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="HERE",
            mode="rules",
            depth=DepthLevel.STANDARD,
            expect="zone_rules",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=50)

        rules_result = self.organ.invoke(invocation, patch)
        assert "Custom rule: Always be present" in rules_result["rules"]

    def test_state_checkpoint_and_restore(self):
        """Test checkpointing and restoring state."""
        # Make some changes
        invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="THE_STAGE",
            mode="enter",
            depth=DepthLevel.STANDARD,
            expect="place_state",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=60)
        self.organ.invoke(invocation, patch)

        # Checkpoint
        state = self.organ.get_state()
        assert state["state"]["current_place"] == "THE_STAGE"

        # Reset and restore
        self.organ.reset()
        assert self.organ.get_current_place() == "HERE"

        self.organ.restore_state(state)
        assert self.organ.get_current_place() == "THE_STAGE"

    def test_reset_organ(self):
        """Test resetting organ to initial state."""
        # Make some changes
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=60)
        invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="BACKTHEN",
            mode="enter",
            depth=DepthLevel.STANDARD,
            expect="place_state",
            charge=60,
        )
        self.organ.invoke(invocation, patch)
        self.organ.add_zone_rule("HERE", "test rule")

        # Reset
        self.organ.reset()

        assert self.organ.get_current_place() == "HERE"
        assert len(self.organ.get_place_history()) == 0


class TestPlaceProtocolsIntegration:
    """Integration tests for Place Protocols."""

    def test_full_journey(self):
        """Test a full place journey with multiple transitions."""
        organ = PlaceProtocols()
        patch = Patch(input_node="test", output_node="PLACE_PROTOCOLS", tags=[], charge=80)

        # Start at HERE
        assert organ.get_current_place() == "HERE"

        # Journey through multiple zones
        journey = [
            ("BACKTHEN", "memory"),
            ("NEVERW4S", "grief"),  # Restricted, needs high charge
            ("THE_STAGE", "performance"),
            ("HERE", None),  # Via exit
        ]

        for i, (zone, expected_function) in enumerate(journey[:-1]):
            invocation = Invocation(
                organ="PLACE_PROTOCOLS",
                symbol=zone,
                mode="enter",
                depth=DepthLevel.STANDARD,
                expect="place_state",
                charge=80,
            )
            result = organ.invoke(invocation, patch)
            assert result["status"] == "entered", f"Failed to enter {zone}"
            if expected_function:
                assert expected_function in result["functions"]

        # Exit back to HERE
        exit_invocation = Invocation(
            organ="PLACE_PROTOCOLS",
            symbol="",
            mode="exit",
            depth=DepthLevel.STANDARD,
            expect="place_state",
            charge=80,
        )
        result = organ.invoke(exit_invocation, patch)
        assert result["status"] == "exited"
        assert organ.get_current_place() == "HERE"

        # Verify history
        history = organ.get_place_history()
        assert len(history) == 4  # 3 enters + 1 exit


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
