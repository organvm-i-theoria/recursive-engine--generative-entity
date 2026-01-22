"""
Tests for organ handlers.
"""

import pytest
from rege.organs.heart_of_canon import HeartOfCanon
from rege.organs.mirror_cabinet import MirrorCabinet
from rege.organs.bloom_engine import BloomEngine
from rege.organs.registry import OrganRegistry, register_default_organs
from rege.core.models import Invocation, Patch, DepthLevel


class TestHeartOfCanon:
    """Tests for HeartOfCanon organ."""

    def setup_method(self):
        """Set up test fixtures."""
        self.organ = HeartOfCanon()

    def test_pulse_check_low_charge(self):
        """Test pulse check with low charge returns echo."""
        result = self.organ.pulse_check("test memory", charge=30)

        assert result["status"] == "echo"
        assert not result["in_canon"]
        assert not result["canonization_eligible"]

    def test_pulse_check_high_charge(self):
        """Test pulse check with high charge returns canon_candidate."""
        result = self.organ.pulse_check("intense memory", charge=80)

        assert result["status"] == "canon_candidate"
        assert result["canonization_eligible"]

    def test_pulse_check_critical_charge(self):
        """Test pulse check with critical charge returns emergent_canon."""
        result = self.organ.pulse_check("critical memory", charge=90)

        assert result["status"] == "emergent_canon"

    def test_mythic_mode_invocation(self):
        """Test mythic mode processing."""
        invocation = Invocation(
            organ="HEART_OF_CANON",
            symbol="test myth",
            mode="mythic",
            depth=DepthLevel.STANDARD,
            expect="canon_event",
            charge=75,
        )
        patch = Patch(input_node="test", output_node="HEART_OF_CANON", tags=[], charge=75)

        result = self.organ.invoke(invocation, patch)

        assert "event" in result
        assert "tier" in result

    def test_recursive_mode_tracks_recurrence(self):
        """Test that recursive mode tracks recurrence."""
        invocation = Invocation(
            organ="HEART_OF_CANON",
            symbol="recurring pattern",
            mode="recursive",
            depth=DepthLevel.STANDARD,
            expect="default",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="HEART_OF_CANON", tags=[], charge=50)

        # Call multiple times
        result1 = self.organ.invoke(invocation, patch)
        result2 = self.organ.invoke(invocation, patch)
        result3 = self.organ.invoke(invocation, patch)

        assert result3["recurrence_count"] == 3


class TestMirrorCabinet:
    """Tests for MirrorCabinet organ."""

    def setup_method(self):
        """Set up test fixtures."""
        self.organ = MirrorCabinet()

    def test_emotional_reflection(self):
        """Test emotional reflection mode."""
        invocation = Invocation(
            organ="MIRROR_CABINET",
            symbol="I feel stuck",
            mode="emotional_reflection",
            depth=DepthLevel.STANDARD,
            expect="fragment_map",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="MIRROR_CABINET", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert "fragment" in result
        assert "mirror_response" in result

    def test_shadow_work_identifies_archetype(self):
        """Test shadow work mode identifies archetypes."""
        invocation = Invocation(
            organ="MIRROR_CABINET",
            symbol="I can't finish anything, I always sabotage myself",
            mode="shadow_work",
            depth=DepthLevel.FULL_SPIRAL,
            expect="fragment_map",
            charge=70,
        )
        patch = Patch(input_node="test", output_node="MIRROR_CABINET", tags=[], charge=70)

        result = self.organ.invoke(invocation, patch)

        assert "shadow_archetype" in result
        assert result["shadow_archetype"] == "Saboteur"

    def test_high_charge_suggests_court(self):
        """Test high charge triggers ritual court suggestion."""
        invocation = Invocation(
            organ="MIRROR_CABINET",
            symbol="test",
            mode="emotional_reflection",
            depth=DepthLevel.STANDARD,
            expect="fragment_map",
            charge=75,
        )
        patch = Patch(input_node="test", output_node="MIRROR_CABINET", tags=[], charge=75)

        result = self.organ.invoke(invocation, patch)

        assert result["requires_ritual_court"]


class TestBloomEngine:
    """Tests for BloomEngine organ."""

    def setup_method(self):
        """Set up test fixtures."""
        self.organ = BloomEngine()

    def test_initiate_bloom_cycle(self):
        """Test bloom cycle initiation."""
        cycle = self.organ.initiate_bloom(
            phase="Test Phase",
            trigger_event="Test trigger",
            mutation_path="TEST+",
            duration_days=14,
        )

        assert cycle.phase == "Test Phase"
        assert cycle.status == "pending"

        result = cycle.initiate()
        assert cycle.status == "active"

    def test_version_branching_limit(self):
        """Test version branching has limits."""
        cycle = self.organ.initiate_bloom(
            phase="Test",
            trigger_event="test",
            mutation_path="TEST+",
            duration_days=7,
        )

        # Branch up to limit
        for i in range(5):
            assert cycle.branch_version()

        # Should fail at limit
        assert not cycle.branch_version()
        assert cycle.status == "consolidated"

    def test_versioning_mode_tracks_versions(self):
        """Test versioning mode tracks fragment versions."""
        invocation = Invocation(
            organ="BLOOM_ENGINE",
            symbol="Fragment_v1.0",
            mode="versioning",
            depth=DepthLevel.STANDARD,
            expect="version_map",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="BLOOM_ENGINE", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert "new_version" in result
        assert "total_versions" in result


class TestOrganRegistry:
    """Tests for OrganRegistry."""

    def test_register_and_get(self):
        """Test registering and retrieving organs."""
        registry = OrganRegistry()
        organ = HeartOfCanon()

        registry.register(organ)

        assert registry.has("HEART_OF_CANON")
        assert registry.get("HEART_OF_CANON") == organ

    def test_register_default_organs(self):
        """Test registering all default organs."""
        registry = register_default_organs()

        assert "HEART_OF_CANON" in registry
        assert "MIRROR_CABINET" in registry
        assert "MYTHIC_SENATE" in registry
        assert "ARCHIVE_ORDER" in registry
        assert "RITUAL_COURT" in registry
        assert "CODE_FORGE" in registry
        assert "BLOOM_ENGINE" in registry
        assert "ECHO_SHELL" in registry
        assert "DREAM_COUNCIL" in registry
        assert "MASK_ENGINE" in registry

    def test_list_names(self):
        """Test listing organ names."""
        registry = register_default_organs()
        names = registry.list_names()

        assert len(names) >= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
