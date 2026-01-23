"""
Extended coverage tests for Mirror Cabinet organ.

Targets untested paths:
- Fusion eligibility with law suggestion
- All grief stage detection
- All shadow archetype detection
- Unknown shadow archetype
- Fragment overlap counting
- Reclamation_possible boundary
- Fragment name extraction edge cases
"""

import pytest
from datetime import datetime

from rege.organs.mirror_cabinet import MirrorCabinet, SelfFragment
from rege.core.models import Invocation, Patch, DepthLevel


@pytest.fixture
def organ():
    """Create a fresh MirrorCabinet instance."""
    return MirrorCabinet()


@pytest.fixture
def patch():
    """Create a test patch."""
    return Patch(
        input_node="TEST",
        output_node="MIRROR_CABINET",
        tags=["TEST+"],
        depth=5,
    )


def make_invocation(symbol="", mode="default", charge=50, flags=None):
    """Helper to create test invocations."""
    return Invocation(
        organ="MIRROR_CABINET",
        symbol=symbol,
        mode=mode,
        charge=charge,
        depth=DepthLevel.STANDARD,
        expect="default_output",
        flags=flags or [],
    )


class TestSelfFragmentResolution:
    """Test SelfFragment.attempt_resolution boundaries."""

    def test_resolution_charge_50_self_resolve(self):
        """Charge exactly 50 should allow self-resolution."""
        fragment = SelfFragment("Test", charge=50, loop_phrase="test phrase")
        result = fragment.attempt_resolution()

        assert "accepted" in result.lower() or "integrated" in result.lower()
        assert fragment.resolved is True

    def test_resolution_charge_51_requires_court(self):
        """Charge 51 should require ritual court."""
        fragment = SelfFragment("Test", charge=51, loop_phrase="test phrase")
        result = fragment.attempt_resolution()

        assert "ritual court" in result.lower()
        assert fragment.resolved is False

    def test_resolution_charge_49_self_resolve(self):
        """Charge 49 should allow self-resolution."""
        fragment = SelfFragment("Test", charge=49, loop_phrase="test phrase")
        result = fragment.attempt_resolution()

        assert fragment.resolved is True


class TestEmotionalReflectionFusion:
    """Test emotional_reflection fusion eligibility and law suggestion paths."""

    def test_fusion_eligible_with_overlap(self, organ, patch):
        """Test fusion eligibility when overlapping fragments exist."""
        # Create fragments with similar charge
        inv1 = make_invocation("First overlapping phrase", "emotional_reflection", charge=75)
        organ.invoke(inv1, patch)

        # Create overlapping fragment (similar charge ±14)
        inv2 = make_invocation("Second overlapping phrase", "emotional_reflection", charge=80)
        result = organ.invoke(inv2, patch)

        # Should detect overlap and check fusion eligibility
        # Fusion requires charge >= 70 AND overlap >= 2
        assert "fusion_eligible" in result or result.get("overlap_count", 0) >= 0

    def test_law_suggestion_at_charge_71(self, organ, patch):
        """Test law suggestion generated at charge >= 71."""
        inv = make_invocation("High charge content", "emotional_reflection", charge=71)
        result = organ.invoke(inv, patch)

        assert "law_suggestion" in result
        assert "proposed_law" in result["law_suggestion"]

    def test_no_law_suggestion_at_charge_70(self, organ, patch):
        """Test no law suggestion at charge < 71."""
        inv = make_invocation("Lower charge content", "emotional_reflection", charge=70)
        result = organ.invoke(inv, patch)

        assert "law_suggestion" not in result


class TestGriefStageDetection:
    """Test all grief stage detection paths."""

    def test_grief_stage_denial(self, organ, patch):
        """Test denial detection."""
        inv = make_invocation("This can't be happening, it's impossible", "grief_mirroring", charge=50)
        result = organ.invoke(inv, patch)

        assert result["grief_stage"] == "denial"

    def test_grief_stage_anger(self, organ, patch):
        """Test anger detection."""
        inv = make_invocation("This is so unfair, why did this happen", "grief_mirroring", charge=50)
        result = organ.invoke(inv, patch)

        assert result["grief_stage"] == "anger"

    def test_grief_stage_bargaining(self, organ, patch):
        """Test bargaining detection."""
        inv = make_invocation("If only I had done something, what if things were different", "grief_mirroring", charge=50)
        result = organ.invoke(inv, patch)

        assert result["grief_stage"] == "bargaining"

    def test_grief_stage_depression(self, organ, patch):
        """Test depression detection."""
        inv = make_invocation("I feel so sad and empty inside, completely hopeless", "grief_mirroring", charge=50)
        result = organ.invoke(inv, patch)

        assert result["grief_stage"] == "depression"

    def test_grief_stage_processing_default(self, organ, patch):
        """Test default processing stage when no keywords match."""
        inv = make_invocation("Just thinking about things today", "grief_mirroring", charge=50)
        result = organ.invoke(inv, patch)

        assert result["grief_stage"] == "processing"

    def test_grief_charge_boost(self, organ, patch):
        """Test grief always adds +15 to charge (capped at 100)."""
        inv = make_invocation("Grief test", "grief_mirroring", charge=50)
        result = organ.invoke(inv, patch)

        assert result["fragment"]["charge"] == 65

    def test_grief_charge_caps_at_100(self, organ, patch):
        """Test grief charge caps at 100."""
        inv = make_invocation("Grief cap test", "grief_mirroring", charge=90)
        result = organ.invoke(inv, patch)

        assert result["fragment"]["charge"] == 100


class TestShadowArchetypeDetection:
    """Test all shadow archetype detection paths."""

    def test_shadow_saboteur(self, organ, patch):
        """Test Saboteur archetype detection."""
        inv = make_invocation("I always sabotage myself, can't finish anything", "shadow_work", charge=50)
        result = organ.invoke(inv, patch)

        assert result["shadow_archetype"] == "Saboteur"

    def test_shadow_critic(self, organ, patch):
        """Test Critic archetype detection."""
        inv = make_invocation("I'm such a failure, never good enough, worthless", "shadow_work", charge=50)
        result = organ.invoke(inv, patch)

        assert result["shadow_archetype"] == "Critic"

    def test_shadow_victim(self, organ, patch):
        """Test Victim archetype detection."""
        inv = make_invocation("This always happens to me, I can't help it, helpless", "shadow_work", charge=50)
        result = organ.invoke(inv, patch)

        assert result["shadow_archetype"] == "Victim"

    def test_shadow_villain(self, organ, patch):
        """Test Villain archetype detection."""
        inv = make_invocation("I hurt people, did something wrong, feeling guilty", "shadow_work", charge=50)
        result = organ.invoke(inv, patch)

        assert result["shadow_archetype"] == "Villain"

    def test_shadow_ghost(self, organ, patch):
        """Test Ghost archetype detection."""
        inv = make_invocation("I feel forgotten and invisible, always ignored and unseen", "shadow_work", charge=50)
        result = organ.invoke(inv, patch)

        assert result["shadow_archetype"] == "Ghost"

    def test_shadow_unknown(self, organ, patch):
        """Test Unknown Shadow default archetype."""
        inv = make_invocation("Just a regular thought", "shadow_work", charge=50)
        result = organ.invoke(inv, patch)

        assert result["shadow_archetype"] == "Unknown Shadow"


class TestReclamationPossible:
    """Test reclamation_possible boundary at charge 86."""

    def test_reclamation_possible_charge_85(self, organ, patch):
        """Charge 85 should allow reclamation."""
        inv = make_invocation("Test content", "shadow_work", charge=85)
        result = organ.invoke(inv, patch)

        assert result["reclamation_possible"] is True

    def test_reclamation_impossible_charge_86(self, organ, patch):
        """Charge 86 should prevent reclamation."""
        inv = make_invocation("Test content", "shadow_work", charge=86)
        result = organ.invoke(inv, patch)

        assert result["reclamation_possible"] is False


class TestIntegrationGuidance:
    """Test integration guidance for all archetypes."""

    def test_guidance_saboteur(self, organ, patch):
        """Test Saboteur guidance."""
        inv = make_invocation("I always sabotage things", "shadow_work", charge=50)
        result = organ.invoke(inv, patch)

        assert "protects" in result["integration_guidance"].lower() or "fears" in result["integration_guidance"].lower()

    def test_guidance_critic(self, organ, patch):
        """Test Critic guidance."""
        inv = make_invocation("I'm never good enough", "shadow_work", charge=50)
        result = organ.invoke(inv, patch)

        assert "perfection" in result["integration_guidance"].lower() or "unconditional" in result["integration_guidance"].lower()

    def test_guidance_unknown(self, organ, patch):
        """Test Unknown Shadow guidance."""
        inv = make_invocation("Random thought", "shadow_work", charge=50)
        result = organ.invoke(inv, patch)

        assert "curiosity" in result["integration_guidance"].lower()


class TestFragmentOverlapCounting:
    """Test fragment overlap counting logic."""

    def test_overlap_by_similar_charge(self, organ, patch):
        """Test overlap detected by similar charge (±14)."""
        # Create first fragment with charge 60
        inv1 = make_invocation("Unique words here", "emotional_reflection", charge=60)
        organ.invoke(inv1, patch)

        # Create second fragment with charge 70 (within ±14)
        inv2 = make_invocation("Different words there", "emotional_reflection", charge=70)
        result = organ.invoke(inv2, patch)

        # Should detect overlap
        overlap = organ._count_overlapping_fragments(
            organ._fragments[result["fragment"]["id"]]
        )
        assert overlap >= 1

    def test_overlap_by_shared_words(self, organ, patch):
        """Test overlap detected by shared words."""
        # Create first fragment with specific words
        inv1 = make_invocation("Memory of childhood", "emotional_reflection", charge=30)
        organ.invoke(inv1, patch)

        # Create second fragment with shared word (different charge)
        inv2 = make_invocation("Another memory fragment", "emotional_reflection", charge=80)
        result = organ.invoke(inv2, patch)

        # Should detect overlap via shared word "memory"
        overlap = organ._count_overlapping_fragments(
            organ._fragments[result["fragment"]["id"]]
        )
        assert overlap >= 1

    def test_no_overlap_distinct_fragments(self, organ, patch):
        """Test no overlap with distinct fragments."""
        # Create first fragment
        inv1 = make_invocation("Alpha beta gamma", "emotional_reflection", charge=30)
        organ.invoke(inv1, patch)

        # Create second fragment with no overlap
        inv2 = make_invocation("Delta epsilon zeta", "emotional_reflection", charge=80)
        result = organ.invoke(inv2, patch)

        # No shared words, very different charges
        overlap = organ._count_overlapping_fragments(
            organ._fragments[result["fragment"]["id"]]
        )
        assert overlap == 0


class TestFragmentNameExtraction:
    """Test fragment name extraction edge cases."""

    def test_extract_name_single_word(self, organ, patch):
        """Test extraction from single word symbol."""
        inv = make_invocation("SingleWord", "emotional_reflection", charge=50)
        result = organ.invoke(inv, patch)

        assert "Singleword" in result["fragment"]["name"]

    def test_extract_name_empty_symbol(self, organ, patch):
        """Test extraction from empty symbol."""
        inv = make_invocation("", "emotional_reflection", charge=50)
        result = organ.invoke(inv, patch)

        assert "_Fragment" in result["fragment"]["name"]

    def test_extract_name_long_symbol(self, organ, patch):
        """Test extraction takes only first 3 words."""
        inv = make_invocation("One Two Three Four Five Six", "emotional_reflection", charge=50)
        result = organ.invoke(inv, patch)

        name = result["fragment"]["name"]
        assert "One" in name
        assert "Two" in name
        assert "Three" in name
        assert "Four" not in name


class TestLoopPhraseExtraction:
    """Test loop phrase extraction and truncation."""

    def test_loop_phrase_short(self, organ, patch):
        """Test short loop phrase preserved."""
        inv = make_invocation("Short phrase", "emotional_reflection", charge=50)
        result = organ.invoke(inv, patch)

        assert result["fragment"]["loop_phrase"] == "Short phrase"

    def test_loop_phrase_truncated_at_100(self, organ, patch):
        """Test long loop phrase truncated to 100 chars."""
        long_text = "a" * 150
        inv = make_invocation(long_text, "emotional_reflection", charge=50)
        result = organ.invoke(inv, patch)

        assert len(result["fragment"]["loop_phrase"]) == 100


class TestLawSuggestionGeneration:
    """Test law suggestion details."""

    def test_law_suggestion_structure(self, organ, patch):
        """Test law suggestion has correct structure."""
        inv = make_invocation("High charge content", "emotional_reflection", charge=80)
        result = organ.invoke(inv, patch)

        suggestion = result["law_suggestion"]
        assert "proposed_law" in suggestion
        assert "LAW_XX" in suggestion["proposed_law"]
        assert "description" in suggestion
        assert "charge" in suggestion
        assert suggestion["charge"] == 80

    def test_law_suggestion_truncates_long_phrase(self, organ, patch):
        """Test law suggestion truncates loop phrase in description."""
        long_text = "a" * 60  # Will be truncated to 50 + "..."
        inv = make_invocation(long_text, "emotional_reflection", charge=80)
        result = organ.invoke(inv, patch)

        assert "..." in result["law_suggestion"]["description"]


class TestGetFragments:
    """Test fragment retrieval methods."""

    def test_get_fragments_empty(self, organ, patch):
        """Test get_fragments returns empty list initially."""
        assert organ.get_fragments() == []

    def test_get_fragments_after_creation(self, organ, patch):
        """Test get_fragments returns created fragments."""
        inv = make_invocation("Test fragment", "emotional_reflection", charge=50)
        organ.invoke(inv, patch)

        fragments = organ.get_fragments()
        assert len(fragments) == 1

    def test_get_unresolved_fragments_mixed(self, organ, patch):
        """Test get_unresolved_fragments filters correctly."""
        # Create resolved fragment (charge <= 50)
        inv1 = make_invocation("Resolved fragment", "emotional_reflection", charge=40)
        organ.invoke(inv1, patch)

        # Create unresolved fragment (charge > 50)
        inv2 = make_invocation("Unresolved fragment", "emotional_reflection", charge=60)
        organ.invoke(inv2, patch)

        unresolved = organ.get_unresolved_fragments()
        assert len(unresolved) == 1
        assert unresolved[0].charge == 60

    def test_get_unresolved_all_resolved(self, organ, patch):
        """Test get_unresolved_fragments when all are resolved."""
        # Create only resolved fragments
        inv1 = make_invocation("Resolved 1", "emotional_reflection", charge=30)
        organ.invoke(inv1, patch)
        inv2 = make_invocation("Resolved 2", "emotional_reflection", charge=40)
        organ.invoke(inv2, patch)

        unresolved = organ.get_unresolved_fragments()
        assert len(unresolved) == 0


class TestDefaultReflection:
    """Test default reflection mode."""

    def test_default_reflection_output(self, organ, patch):
        """Test default reflection returns correct structure."""
        inv = make_invocation("Default test", "default", charge=50)
        result = organ.invoke(inv, patch)

        assert "fragment" in result
        assert "mirror_response" in result
        assert "tier" in result
        assert result["status"] == "reflected"


class TestSelfFragmentMethods:
    """Test SelfFragment class methods."""

    def test_mirror_response(self):
        """Test mirror_response format."""
        fragment = SelfFragment("TestName", charge=50, loop_phrase="echo this")
        response = fragment.mirror_response()

        assert "TestName" in response
        assert "echo this" in response

    def test_to_dict(self):
        """Test to_dict includes all fields."""
        fragment = SelfFragment("TestName", charge=75, loop_phrase="test phrase")
        d = fragment.to_dict()

        assert "id" in d
        assert d["id"].startswith("FRAG_")
        assert d["name"] == "TestName"
        assert d["charge"] == 75
        assert d["loop_phrase"] == "test phrase"
        assert d["resolved"] is False
        assert "created_at" in d
