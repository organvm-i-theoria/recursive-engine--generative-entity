"""
Extended coverage tests for Invocation Validator.

Targets untested paths:
- Multiple simultaneous validation errors
- validate_or_raise exception types
- Case sensitivity handling
- get_organ_config/get_valid_modes with non-existent organs
- is_valid_output_type edge cases
- describe_organ edge cases
- InvocationLogger truncation and filtering
- list_organs completeness
"""

import pytest

from rege.parser.validator import (
    InvocationValidator,
    InvocationLogger,
    ORGAN_REGISTRY,
    VALID_FLAGS,
)
from rege.core.models import Invocation, DepthLevel
from rege.core.exceptions import ValidationError, InvalidModeError, OrganNotFoundError


@pytest.fixture
def validator():
    """Create a fresh InvocationValidator instance."""
    return InvocationValidator()


@pytest.fixture
def logger():
    """Create a fresh InvocationLogger instance."""
    return InvocationLogger()


def make_invocation(
    organ="HEART_OF_CANON",
    symbol="test",
    mode="default",
    charge=50,
    depth=DepthLevel.STANDARD,
    flags=None,
):
    """Helper to create test invocations."""
    return Invocation(
        organ=organ,
        symbol=symbol,
        mode=mode,
        charge=charge,
        depth=depth,
        expect="default_output",
        flags=flags or [],
    )


class TestMultipleErrors:
    """Test validation with multiple simultaneous errors."""

    def test_multiple_errors_reported(self, validator):
        """All validation errors should be collected."""
        inv = make_invocation(
            organ="NONEXISTENT_ORGAN",
            mode="invalid_mode",
            charge=5,
            flags=["INVALID_FLAG+"],
        )

        is_valid, errors = validator.validate(inv)

        assert is_valid is False
        assert len(errors) >= 2  # At least organ error and flag error

    def test_organ_and_flag_errors(self, validator):
        """Test organ error combined with invalid flag."""
        inv = make_invocation(
            organ="FAKE_ORGAN",
            flags=["TOTALLY_FAKE_FLAG+"],
        )

        is_valid, errors = validator.validate(inv)

        assert is_valid is False
        # Should have organ error
        assert any("FAKE_ORGAN" in e for e in errors)
        # Should have flag error
        assert any("TOTALLY_FAKE_FLAG" in e for e in errors)

    def test_mode_and_charge_errors(self, validator):
        """Test mode error combined with charge error."""
        inv = make_invocation(
            organ="MYTHIC_SENATE",  # Requires charge 51
            mode="totally_invalid_mode",
            charge=10,  # Below minimum
        )

        is_valid, errors = validator.validate(inv)

        assert is_valid is False
        # Should have mode error
        assert any("mode" in e.lower() for e in errors)
        # Should have charge error
        assert any("charge" in e.lower() for e in errors)


class TestValidateOrRaise:
    """Test validate_or_raise exception types."""

    def test_raises_organ_not_found_error(self, validator):
        """Unknown organ raises OrganNotFoundError."""
        inv = make_invocation(organ="DOES_NOT_EXIST")

        with pytest.raises(OrganNotFoundError) as exc_info:
            validator.validate_or_raise(inv)

        assert "DOES_NOT_EXIST" in str(exc_info.value)

    def test_raises_invalid_mode_error(self, validator):
        """Invalid mode raises InvalidModeError."""
        inv = make_invocation(
            organ="HEART_OF_CANON",
            mode="nonexistent_mode",
        )

        with pytest.raises(InvalidModeError) as exc_info:
            validator.validate_or_raise(inv)

        assert "nonexistent_mode" in str(exc_info.value)

    def test_raises_validation_error_generic(self, validator):
        """Other errors raise generic ValidationError."""
        # Create invocation with invalid flag only (organ and mode valid)
        inv = make_invocation(
            organ="HEART_OF_CANON",
            mode="mythic",
            flags=["TOTALLY_INVALID_FLAG+"],
        )

        with pytest.raises(ValidationError):
            validator.validate_or_raise(inv)

    def test_no_exception_when_valid(self, validator):
        """Valid invocation doesn't raise."""
        inv = make_invocation(
            organ="HEART_OF_CANON",
            mode="mythic",
            charge=50,
            flags=["CANON+"],
        )

        # Should not raise
        validator.validate_or_raise(inv)


class TestCaseSensitivity:
    """Test case sensitivity handling."""

    def test_organ_case_insensitive(self, validator):
        """Organ names should be case insensitive."""
        inv = make_invocation(organ="heart_of_canon", mode="mythic")

        is_valid, errors = validator.validate(inv)

        assert is_valid is True

    def test_get_organ_config_case_insensitive(self, validator):
        """get_organ_config should be case insensitive."""
        config1 = validator.get_organ_config("HEART_OF_CANON")
        config2 = validator.get_organ_config("heart_of_canon")
        config3 = validator.get_organ_config("Heart_Of_Canon")

        assert config1 == config2 == config3

    def test_mode_case_insensitive(self, validator):
        """Mode names should be case insensitive."""
        inv = make_invocation(organ="HEART_OF_CANON", mode="MYTHIC")

        is_valid, errors = validator.validate(inv)

        assert is_valid is True


class TestGetOrganConfig:
    """Test get_organ_config edge cases."""

    def test_nonexistent_organ_returns_none(self, validator):
        """Non-existent organ returns None."""
        result = validator.get_organ_config("TOTALLY_FAKE_ORGAN")

        assert result is None

    def test_existing_organ_returns_config(self, validator):
        """Existing organ returns config dict."""
        result = validator.get_organ_config("HEART_OF_CANON")

        assert result is not None
        assert "valid_modes" in result
        assert "output_types" in result


class TestGetValidModes:
    """Test get_valid_modes edge cases."""

    def test_nonexistent_organ_returns_empty(self, validator):
        """Non-existent organ returns empty list."""
        result = validator.get_valid_modes("FAKE_ORGAN")

        assert result == []

    def test_existing_organ_returns_modes(self, validator):
        """Existing organ returns mode list."""
        result = validator.get_valid_modes("HEART_OF_CANON")

        assert "mythic" in result
        assert "recursive" in result


class TestGetOutputTypes:
    """Test get_output_types edge cases."""

    def test_nonexistent_organ_returns_empty(self, validator):
        """Non-existent organ returns empty list."""
        result = validator.get_output_types("FAKE_ORGAN")

        assert result == []

    def test_existing_organ_returns_types(self, validator):
        """Existing organ returns output types."""
        result = validator.get_output_types("HEART_OF_CANON")

        assert "canon_event" in result


class TestIsValidOutputType:
    """Test is_valid_output_type edge cases."""

    def test_valid_output_type(self, validator):
        """Valid output type returns True."""
        result = validator.is_valid_output_type("HEART_OF_CANON", "canon_event")

        assert result is True

    def test_invalid_output_type(self, validator):
        """Invalid output type returns False."""
        result = validator.is_valid_output_type("HEART_OF_CANON", "totally_invalid")

        assert result is False

    def test_nonexistent_organ_returns_false(self, validator):
        """Non-existent organ returns False."""
        result = validator.is_valid_output_type("FAKE_ORGAN", "any_type")

        assert result is False

    def test_case_insensitive(self, validator):
        """Output type matching is case insensitive."""
        result1 = validator.is_valid_output_type("HEART_OF_CANON", "CANON_EVENT")
        result2 = validator.is_valid_output_type("HEART_OF_CANON", "Canon_Event")

        assert result1 is True
        assert result2 is True


class TestListOrgans:
    """Test list_organs."""

    def test_list_organs_returns_all(self, validator):
        """list_organs returns all registered organs."""
        organs = validator.list_organs()

        assert len(organs) >= 20  # At least 20 organs
        assert "HEART_OF_CANON" in organs
        assert "MIRROR_CABINET" in organs


class TestDescribeOrgan:
    """Test describe_organ edge cases."""

    def test_describe_existing_organ(self, validator):
        """Existing organ returns description."""
        result = validator.describe_organ("HEART_OF_CANON")

        assert result is not None
        assert len(result) > 0

    def test_describe_nonexistent_organ(self, validator):
        """Non-existent organ returns None."""
        result = validator.describe_organ("FAKE_ORGAN")

        assert result is None


class TestInvocationLoggerLog:
    """Test InvocationLogger.log method."""

    def test_log_generates_id_if_missing(self, logger):
        """Log generates invocation_id if missing."""
        inv = make_invocation()
        inv.invocation_id = None

        entry = logger.log(inv, {"result": "ok"}, 100, "success")

        assert "invocation_id" in entry
        assert entry["invocation_id"].startswith("INV_")

    def test_log_truncates_long_result(self, logger):
        """Log truncates result longer than 500 chars."""
        inv = make_invocation()
        long_result = "x" * 1000

        entry = logger.log(inv, long_result, 100, "success")

        assert len(entry["result"]) <= 500

    def test_log_handles_none_result(self, logger):
        """Log handles None result."""
        inv = make_invocation()

        entry = logger.log(inv, None, 100, "success")

        assert entry["result"] is None


class TestInvocationLoggerGetByOrgan:
    """Test InvocationLogger.get_by_organ method."""

    def test_get_by_organ_case_insensitive(self, logger):
        """get_by_organ is case insensitive."""
        inv = make_invocation(organ="HEART_OF_CANON")
        logger.log(inv, {}, 100, "success")

        result1 = logger.get_by_organ("HEART_OF_CANON")
        result2 = logger.get_by_organ("heart_of_canon")

        assert len(result1) == 1
        assert len(result2) == 1

    def test_get_by_organ_filters_correctly(self, logger):
        """get_by_organ filters correctly."""
        inv1 = make_invocation(organ="HEART_OF_CANON")
        inv2 = make_invocation(organ="MIRROR_CABINET")
        logger.log(inv1, {}, 100, "success")
        logger.log(inv2, {}, 100, "success")

        result = logger.get_by_organ("HEART_OF_CANON")

        assert len(result) == 1
        assert result[0]["organ"] == "HEART_OF_CANON"


class TestInvocationLoggerGetByStatus:
    """Test InvocationLogger.get_by_status method."""

    def test_get_by_status_filters(self, logger):
        """get_by_status filters correctly."""
        inv1 = make_invocation()
        inv2 = make_invocation()
        logger.log(inv1, {}, 100, "success")
        logger.log(inv2, {}, 100, "failed")

        successes = logger.get_by_status("success")
        failures = logger.get_by_status("failed")

        assert len(successes) == 1
        assert len(failures) == 1

    def test_get_by_status_empty(self, logger):
        """get_by_status returns empty for no matches."""
        result = logger.get_by_status("nonexistent_status")

        assert result == []


class TestInvocationLoggerOther:
    """Test other InvocationLogger methods."""

    def test_get_recent(self, logger):
        """get_recent returns most recent entries."""
        for i in range(15):
            inv = make_invocation()
            logger.log(inv, {}, i, "success")

        recent = logger.get_recent(5)

        assert len(recent) == 5

    def test_clear(self, logger):
        """clear empties logs and resets counter."""
        inv = make_invocation()
        logger.log(inv, {}, 100, "success")

        logger.clear()

        assert logger.logs == []
        assert logger._id_counter == 0

    def test_to_dict(self, logger):
        """to_dict returns copy of logs."""
        inv = make_invocation()
        logger.log(inv, {}, 100, "success")

        result = logger.to_dict()

        assert len(result) == 1
        assert result is not logger.logs  # Should be a copy


class TestValidFlags:
    """Test VALID_FLAGS set."""

    def test_valid_flags_recognized(self, validator):
        """All VALID_FLAGS are recognized."""
        for flag in VALID_FLAGS:
            inv = make_invocation(flags=[flag])
            is_valid, errors = validator.validate(inv)

            # Should not have flag errors
            flag_errors = [e for e in errors if flag in e]
            assert len(flag_errors) == 0

    def test_invalid_flag_rejected(self, validator):
        """Invalid flags are rejected."""
        inv = make_invocation(flags=["TOTALLY_MADE_UP_FLAG+"])

        is_valid, errors = validator.validate(inv)

        assert is_valid is False
        assert any("TOTALLY_MADE_UP_FLAG" in e for e in errors)


class TestOrganRegistry:
    """Test ORGAN_REGISTRY completeness."""

    def test_registry_has_core_organs(self):
        """Registry includes all core organs."""
        core_organs = [
            "HEART_OF_CANON",
            "MIRROR_CABINET",
            "MYTHIC_SENATE",
            "ARCHIVE_ORDER",
            "RITUAL_COURT",
            "CODE_FORGE",
            "BLOOM_ENGINE",
            "SOUL_PATCHBAY",
            "ECHO_SHELL",
            "DREAM_COUNCIL",
            "MASK_ENGINE",
        ]

        for organ in core_organs:
            assert organ in ORGAN_REGISTRY

    def test_registry_has_extended_organs(self):
        """Registry includes extended organs."""
        extended_organs = [
            "CHAMBER_OF_COMMERCE",
            "BLOCKCHAIN_ECONOMY",
            "PLACE_PROTOCOLS",
            "TIME_RULES",
            "PROCESS_PRODUCT",
            "PUBLISHING_TEMPLE",
            "PROCESS_MONETIZER",
            "AUDIENCE_ENGINE",
            "ANALOG_DIGITAL_ENGINE",
            "CONSUMPTION_PROTOCOL",
            "STAGECRAFT_MODULE",
        ]

        for organ in extended_organs:
            assert organ in ORGAN_REGISTRY


class TestChargeRequirements:
    """Test charge requirement validation."""

    def test_mythic_senate_requires_51(self, validator):
        """MYTHIC_SENATE requires charge >= 51."""
        inv = make_invocation(organ="MYTHIC_SENATE", mode="default", charge=50)

        is_valid, errors = validator.validate(inv)

        assert is_valid is False
        assert any("charge" in e.lower() for e in errors)

    def test_mythic_senate_accepts_51(self, validator):
        """MYTHIC_SENATE accepts charge 51."""
        inv = make_invocation(organ="MYTHIC_SENATE", mode="default", charge=51)

        is_valid, errors = validator.validate(inv)

        assert is_valid is True


class TestCustomRegistry:
    """Test validator with custom registry."""

    def test_custom_registry_used(self):
        """Custom registry is used instead of default."""
        custom_registry = {
            "CUSTOM_ORGAN": {
                "valid_modes": ["custom_mode"],
                "required_charge": 0,
                "output_types": ["custom_output"],
                "description": "A custom organ",
            }
        }

        validator = InvocationValidator(registry=custom_registry)

        # Should recognize custom organ
        config = validator.get_organ_config("CUSTOM_ORGAN")
        assert config is not None

        # Should not recognize default organs
        config = validator.get_organ_config("HEART_OF_CANON")
        assert config is None
