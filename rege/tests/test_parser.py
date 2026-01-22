"""
Tests for the invocation parser.
"""

import pytest
from rege.parser.invocation_parser import InvocationParser, parse_invocation
from rege.parser.validator import InvocationValidator, ORGAN_REGISTRY
from rege.core.models import DepthLevel


class TestInvocationParser:
    """Tests for InvocationParser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = InvocationParser()

    def test_parse_basic_invocation(self):
        """Test parsing a basic invocation."""
        text = """
        ::CALL_ORGAN MIRROR_CABINET
        ::WITH "I cant finish anything"
        ::MODE emotional_reflection
        ::DEPTH full spiral
        ::EXPECT fragment_map
        """

        result = self.parser.parse(text)

        assert result is not None
        assert result.organ == "MIRROR_CABINET"
        assert result.symbol == "I cant finish anything"
        assert result.mode == "emotional_reflection"
        assert result.depth == DepthLevel.FULL_SPIRAL
        assert result.expect == "fragment_map"

    def test_parse_with_flags(self):
        """Test parsing invocation with flags."""
        text = """
        ::CALL_ORGAN HEART_OF_CANON
        ::WITH "test memory"
        ::MODE mythic
        ::LAW_LOOP+
        ::FUSE+
        """

        result = self.parser.parse(text)

        assert result is not None
        assert "LAW_LOOP+" in result.flags
        assert "FUSE+" in result.flags

    def test_parse_depth_levels(self):
        """Test parsing different depth levels."""
        for depth_str, expected in [
            ("light", DepthLevel.LIGHT),
            ("standard", DepthLevel.STANDARD),
            ("full spiral", DepthLevel.FULL_SPIRAL),
        ]:
            text = f"::CALL_ORGAN TEST\n::DEPTH {depth_str}"
            result = self.parser.parse(text)
            assert result.depth == expected

    def test_parse_chain(self):
        """Test parsing chained invocations."""
        text = """
        ::CALL_ORGAN MIRROR_CABINET
        ::WITH "first"
        ::MODE default

        ::CALL_ORGAN BLOOM_ENGINE
        ::WITH "second"
        ::MODE growth
        """

        results = self.parser.parse_chain(text)

        assert len(results) == 2
        assert results[0].organ == "MIRROR_CABINET"
        assert results[1].organ == "BLOOM_ENGINE"

    def test_parse_invalid_returns_none(self):
        """Test that invalid input returns None."""
        result = self.parser.parse("not an invocation")
        assert result is None

    def test_extract_fragment_refs(self):
        """Test extracting fragment references."""
        text = 'Fragment_v2.6: "Dream Witch" and fragment: "test"'

        refs = self.parser.extract_fragment_refs(text)

        assert "Fragment_v2.6" in refs
        assert "test" in refs


class TestInvocationValidator:
    """Tests for InvocationValidator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = InvocationValidator()
        self.parser = InvocationParser()

    def test_validate_valid_invocation(self):
        """Test validating a valid invocation."""
        text = """
        ::CALL_ORGAN MIRROR_CABINET
        ::WITH "test"
        ::MODE emotional_reflection
        """

        invocation = self.parser.parse(text)
        is_valid, errors = self.validator.validate(invocation)

        assert is_valid
        assert len(errors) == 0

    def test_validate_unknown_organ(self):
        """Test validation fails for unknown organ."""
        text = """
        ::CALL_ORGAN UNKNOWN_ORGAN
        ::WITH "test"
        """

        invocation = self.parser.parse(text)
        is_valid, errors = self.validator.validate(invocation)

        assert not is_valid
        assert any("Unknown organ" in e for e in errors)

    def test_validate_invalid_mode(self):
        """Test validation fails for invalid mode."""
        text = """
        ::CALL_ORGAN MIRROR_CABINET
        ::WITH "test"
        ::MODE invalid_mode
        """

        invocation = self.parser.parse(text)
        is_valid, errors = self.validator.validate(invocation)

        assert not is_valid
        assert any("Invalid mode" in e for e in errors)

    def test_validate_unrecognized_flag(self):
        """Test validation catches unrecognized flags."""
        text = """
        ::CALL_ORGAN HEART_OF_CANON
        ::INVALID_FLAG+
        """

        invocation = self.parser.parse(text)
        is_valid, errors = self.validator.validate(invocation)

        assert not is_valid
        assert any("Unrecognized flag" in e for e in errors)

    def test_get_valid_modes(self):
        """Test getting valid modes for organ."""
        modes = self.validator.get_valid_modes("MIRROR_CABINET")

        assert "emotional_reflection" in modes
        assert "grief_mirroring" in modes
        assert "shadow_work" in modes

    def test_list_organs(self):
        """Test listing all organs."""
        organs = self.validator.list_organs()

        assert "HEART_OF_CANON" in organs
        assert "MIRROR_CABINET" in organs
        assert "SOUL_PATCHBAY" in organs


class TestConvenienceFunctions:
    """Test convenience parsing functions."""

    def test_parse_invocation(self):
        """Test parse_invocation convenience function."""
        result = parse_invocation("::CALL_ORGAN TEST\n::WITH data")
        assert result is not None
        assert result.organ == "TEST"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
