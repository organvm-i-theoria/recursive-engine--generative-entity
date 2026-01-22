"""
Extended tests for organ handlers to improve coverage.

Tests for: ArchiveOrder, CodeForge, DreamCouncil, EchoShell, MaskEngine, MythicSenate, RitualCourt
"""

import pytest
from datetime import datetime, timedelta

from rege.organs.archive_order import ArchiveOrder, MemoryNode
from rege.organs.code_forge import CodeForge
from rege.organs.dream_council import DreamCouncil, Dream
from rege.organs.echo_shell import EchoShell, Echo
from rege.organs.mask_engine import MaskEngine, Mask
from rege.organs.mythic_senate import MythicSenate
from rege.organs.ritual_court import RitualCourt, Verdict
from rege.core.models import Invocation, Patch, DepthLevel


# =============================================================================
# ArchiveOrder Tests
# =============================================================================

class TestArchiveOrderExtended:
    """Extended tests for ArchiveOrder organ."""

    def setup_method(self):
        """Set up test fixtures."""
        self.organ = ArchiveOrder()

    def test_create_memory_node(self):
        """Test creating a memory node."""
        node = self.organ.create_memory_node(
            content="test memory",
            charge=50,
            tags=["TEST+"],
            origin="TEST",
        )

        assert node.node_id.startswith("MEM_")
        assert node.content == "test memory"
        assert node.charge == 50
        assert "TEST+" in node.tags

    def test_decay_check_by_tier(self):
        """Test decay rates vary by tier."""
        latent_node = MemoryNode("latent", charge=20, tags=[], origin="TEST")
        processing_node = MemoryNode("processing", charge=40, tags=[], origin="TEST")
        active_node = MemoryNode("active", charge=60, tags=[], origin="TEST")
        intense_node = MemoryNode("intense", charge=80, tags=[], origin="TEST")

        # Latent decays fastest
        assert latent_node.decay_rate == 0.2
        # Processing decays moderately
        assert processing_node.decay_rate == 0.1
        # Active decays slower
        assert active_node.decay_rate == 0.05
        # Intense decays slowest
        assert intense_node.decay_rate == 0.01

    def test_version_consolidation(self):
        """Test that 3+ versions triggers consolidation tag."""
        # Create multiple versions of same content
        node1 = self.organ.create_memory_node("same content", 50, [])
        node2 = self.organ.create_memory_node("same content", 55, [])
        node3 = self.organ.create_memory_node("same content", 60, [])

        # Third node should have consolidation tag
        assert node3.version == 3
        assert "VERSION_CONSOLIDATION_NEEDED+" in node3.tags

    def test_memory_access_refresh(self):
        """Test that accessing memory refreshes it."""
        node = MemoryNode("test", charge=50, tags=[], origin="TEST")
        original_charge = node.charge

        node.access()

        assert node.access_count == 1
        assert node.charge == original_charge + 1

    def test_search_nodes(self):
        """Test searching nodes by content and tags."""
        self.organ.create_memory_node("findme in content", 50, ["UNIQUE+"])
        self.organ.create_memory_node("other content", 60, ["SEARCHABLE+"])

        # Search by content
        results = self.organ._search_nodes("findme")
        assert len(results) == 1
        assert "findme" in results[0].content

        # Search by tag
        results = self.organ._search_nodes("SEARCHABLE")
        assert len(results) == 1

    def test_get_decaying_nodes(self):
        """Test getting decaying nodes."""
        node = self.organ.create_memory_node("old memory", 50, [])
        # Simulate old access time
        node.last_accessed = datetime.now() - timedelta(days=10)

        decaying = self.organ._get_decaying_nodes()

        assert len(decaying) >= 1

    def test_sacred_logging_mode(self):
        """Test sacred logging mode adds SACRED+ tag."""
        invocation = Invocation(
            organ="ARCHIVE_ORDER",
            symbol="sacred memory",
            mode="sacred_logging",
            depth=DepthLevel.STANDARD,
            expect="canonical_thread_tag",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="ARCHIVE_ORDER", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "sacred_archived"
        assert "SACRED+" in result["node"]["tags"]

    def test_retrieval_mode(self):
        """Test retrieval mode searches and refreshes."""
        self.organ.create_memory_node("searchable content", 50, [])

        invocation = Invocation(
            organ="ARCHIVE_ORDER",
            symbol="searchable",
            mode="retrieval",
            depth=DepthLevel.STANDARD,
            expect="memory_node",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="ARCHIVE_ORDER", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "retrieved"
        assert result["results_count"] >= 1

    def test_decay_check_mode(self):
        """Test decay check mode returns decay status."""
        self.organ.create_memory_node("test", 20, [])  # Latent charge

        invocation = Invocation(
            organ="ARCHIVE_ORDER",
            symbol="check",
            mode="decay_check",
            depth=DepthLevel.STANDARD,
            expect="decay_report",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="ARCHIVE_ORDER", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert "latent_count" in result
        assert "recommendations" in result

    def test_get_node(self):
        """Test getting a specific node by ID."""
        node = self.organ.create_memory_node("test", 50, [])

        retrieved = self.organ.get_node(node.node_id)

        assert retrieved is not None
        assert retrieved.node_id == node.node_id

    def test_get_all_nodes(self):
        """Test getting all nodes."""
        self.organ.create_memory_node("node1", 50, [])
        self.organ.create_memory_node("node2", 60, [])

        nodes = self.organ.get_all_nodes()

        assert len(nodes) >= 2


# =============================================================================
# CodeForge Tests
# =============================================================================

class TestCodeForgeExtended:
    """Extended tests for CodeForge organ."""

    def setup_method(self):
        """Set up test fixtures."""
        self.organ = CodeForge()

    def test_func_mode_generates_function(self):
        """Test func_mode generates Python function code."""
        invocation = Invocation(
            organ="CODE_FORGE",
            symbol="process user input",
            mode="func_mode",
            depth=DepthLevel.STANDARD,
            expect=".py",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="CODE_FORGE", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["output_type"] == ".py"
        assert result["mode"] == "func_mode"
        assert "def " in result["code"]
        assert "function_name" in result

    def test_class_mode_generates_class(self):
        """Test class_mode generates Python class code."""
        invocation = Invocation(
            organ="CODE_FORGE",
            symbol="Hero archetype brave warrior",
            mode="class_mode",
            depth=DepthLevel.STANDARD,
            expect=".py",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="CODE_FORGE", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert result["output_type"] == ".py"
        assert result["mode"] == "class_mode"
        assert "class " in result["code"]
        assert "class_name" in result

    def test_wave_mode_generates_waveform(self):
        """Test wave_mode generates Max/MSP waveform spec."""
        invocation = Invocation(
            organ="CODE_FORGE",
            symbol="emotional wave pattern",
            mode="wave_mode",
            depth=DepthLevel.STANDARD,
            expect=".maxpat",
            charge=75,
        )
        patch = Patch(input_node="test", output_node="CODE_FORGE", tags=[], charge=75)

        result = self.organ.invoke(invocation, patch)

        assert result["output_type"] == ".maxpat"
        assert result["mode"] == "wave_mode"
        assert "wave_spec" in result
        assert "waveform" in result["wave_spec"]

    def test_wave_spec_varies_by_charge(self):
        """Test that waveform type varies by charge."""
        low_charge_spec = self.organ._generate_wave_spec("test", 30)
        mid_charge_spec = self.organ._generate_wave_spec("test", 60)
        high_charge_spec = self.organ._generate_wave_spec("test", 80)

        assert low_charge_spec["waveform"] == "sine"
        assert mid_charge_spec["waveform"] == "triangle"
        assert high_charge_spec["waveform"] == "saw"

    def test_tree_mode_generates_decision_tree(self):
        """Test tree_mode generates decision tree JSON."""
        invocation = Invocation(
            organ="CODE_FORGE",
            symbol="if this then that decision",
            mode="tree_mode",
            depth=DepthLevel.STANDARD,
            expect=".json",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="CODE_FORGE", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["output_type"] == ".json"
        assert result["mode"] == "tree_mode"
        assert "decision_tree" in result
        assert "branches" in result["decision_tree"]

    def test_sim_mode_generates_simulation(self):
        """Test sim_mode generates simulation spec."""
        invocation = Invocation(
            organ="CODE_FORGE",
            symbol="myth simulation test",
            mode="sim_mode",
            depth=DepthLevel.STANDARD,
            expect=".json",
            charge=80,
        )
        patch = Patch(input_node="test", output_node="CODE_FORGE", tags=[], charge=80)

        result = self.organ.invoke(invocation, patch)

        assert result["output_type"] == ".json"
        assert result["mode"] == "sim_mode"
        assert "simulation" in result
        assert result["complexity"] == "high"  # charge >= 71

    def test_default_mode_auto_detection(self):
        """Test default mode auto-detects appropriate mode."""
        # Should detect func_mode from "do" keyword
        invocation = Invocation(
            organ="CODE_FORGE",
            symbol="do something action",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="auto",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="CODE_FORGE", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["mode"] == "func_mode"

    def test_default_mode_class_detection(self):
        """Test default mode detects class/archetype keywords."""
        invocation = Invocation(
            organ="CODE_FORGE",
            symbol="archetype of the hero type",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="auto",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="CODE_FORGE", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["mode"] == "class_mode"

    def test_valid_modes(self):
        """Test getting valid modes."""
        modes = self.organ.get_valid_modes()

        assert "func_mode" in modes
        assert "class_mode" in modes
        assert "wave_mode" in modes
        assert "tree_mode" in modes
        assert "sim_mode" in modes


# =============================================================================
# DreamCouncil Tests
# =============================================================================

class TestDreamCouncilExtended:
    """Extended tests for DreamCouncil organ."""

    def setup_method(self):
        """Set up test fixtures."""
        self.organ = DreamCouncil()

    def test_extract_symbols(self):
        """Test symbol extraction from dream content."""
        content = "I was falling into water while walking through a door"

        symbols = self.organ._extract_symbols(content)

        assert "falling" in symbols
        assert "water" in symbols
        assert "door" in symbols

    def test_extract_symbols_unknown(self):
        """Test symbol extraction returns unknown_glyph when none found."""
        content = "abstract undefined content"

        symbols = self.organ._extract_symbols(content)

        assert symbols == ["unknown_glyph"]

    def test_symbol_decode(self):
        """Test symbol dictionary lookup."""
        water_meaning = self.organ._decode_symbol("water")
        unknown_meaning = self.organ._decode_symbol("xyz123")

        assert "emotion" in water_meaning
        assert "deeper analysis" in unknown_meaning

    def test_propose_law_from_dream(self):
        """Test law proposal from high-charge dream."""
        dream = Dream(content="I saw water rising", charge=80, dreamer="SELF")
        dream.symbols = ["water"]

        proposal = self.organ._propose_law_from_dream(dream)

        assert proposal is not None
        assert "Water" in proposal["name"]

    def test_emotional_layer_detection(self):
        """Test emotional layer analysis."""
        dream = Dream(content="I was afraid and scared", charge=70, dreamer="SELF")

        emotional_layer = self.organ._analyze_emotional_layer(dream)

        assert "fear" in emotional_layer["detected_emotions"]

    def test_ritual_recommendation_by_charge(self):
        """Test ritual recommendations vary by charge."""
        low_dream = Dream(content="test", charge=40, dreamer="SELF")
        high_dream = Dream(content="test", charge=80, dreamer="SELF")
        critical_dream = Dream(content="test", charge=90, dreamer="SELF")

        low_ritual = self.organ._recommend_ritual(low_dream)
        high_ritual = self.organ._recommend_ritual(high_dream)
        critical_ritual = self.organ._recommend_ritual(critical_dream)

        assert low_ritual["type"] == "gentle_observation"
        assert high_ritual["type"] == "active_integration"
        assert critical_ritual["type"] == "emergency_processing"

    def test_prophetic_lawmaking_mode(self):
        """Test prophetic lawmaking mode."""
        invocation = Invocation(
            organ="DREAM_COUNCIL",
            symbol="I saw water rising around me",
            mode="prophetic_lawmaking",
            depth=DepthLevel.STANDARD,
            expect="law_proposal",
            charge=80,
        )
        patch = Patch(input_node="test", output_node="DREAM_COUNCIL", tags=[], charge=80)

        result = self.organ.invoke(invocation, patch)

        assert "symbols_extracted" in result
        assert result["law_proposal"] is not None  # High charge

    def test_glyph_decode_mode(self):
        """Test glyph decode mode."""
        invocation = Invocation(
            organ="DREAM_COUNCIL",
            symbol="water and mirror imagery",
            mode="glyph_decode",
            depth=DepthLevel.STANDARD,
            expect="decodings",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="DREAM_COUNCIL", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert "symbols_found" in result
        assert "decodings" in result

    def test_interpretation_mode(self):
        """Test full interpretation mode."""
        invocation = Invocation(
            organ="DREAM_COUNCIL",
            symbol="I dreamed of falling through darkness",
            mode="interpretation",
            depth=DepthLevel.FULL_SPIRAL,
            expect="dream_map",
            charge=70,
        )
        patch = Patch(input_node="test", output_node="DREAM_COUNCIL", tags=[], charge=70)

        result = self.organ.invoke(invocation, patch)

        assert "dream_map" in result
        assert "emotional_layer" in result
        assert "recommended_ritual" in result

    def test_get_dream(self):
        """Test getting a dream by ID."""
        invocation = Invocation(
            organ="DREAM_COUNCIL",
            symbol="test dream",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="dream",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="DREAM_COUNCIL", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)
        dream_id = result["dream"]["dream_id"]

        retrieved = self.organ.get_dream(dream_id)

        assert retrieved is not None

    def test_get_review_queue(self):
        """Test getting dreams pending review."""
        invocation = Invocation(
            organ="DREAM_COUNCIL",
            symbol="queued dream",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="dream",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="DREAM_COUNCIL", tags=[], charge=50)

        self.organ.invoke(invocation, patch)
        queue = self.organ.get_review_queue()

        assert len(queue) >= 1


# =============================================================================
# EchoShell Tests
# =============================================================================

class TestEchoShellExtended:
    """Extended tests for EchoShell organ."""

    def setup_method(self):
        """Set up test fixtures."""
        self.organ = EchoShell()

    def test_pulse_increments_charge(self):
        """Test that pulsing an echo increments charge."""
        echo = Echo(content="test", charge=50, source="TEST")
        original_charge = echo.charge

        result = echo.pulse()

        assert echo.pulse_count == 1
        assert echo.charge > original_charge

    def test_decay_reduces_charge(self):
        """Test that decay reduces charge."""
        echo = Echo(content="test", charge=50, source="TEST")
        original_charge = echo.charge

        new_charge = echo.decay(days=1)

        assert new_charge < original_charge

    def test_whisper_adds_charge(self):
        """Test that whispering adds to charge."""
        echo = Echo(content="test", charge=50, source="TEST")
        original_charge = echo.charge

        echo.whisper("whispered message")

        assert echo.charge == original_charge + 1
        assert "whispered message" in echo.whispers

    def test_fading_at_zero_charge(self):
        """Test that echo status becomes 'faded' at zero charge."""
        echo = Echo(content="test", charge=5, source="TEST")

        echo.decay(days=10)  # Should decay to 0

        assert echo.status == "faded"

    def test_latent_pool_updates(self):
        """Test latent pool membership updates."""
        invocation = Invocation(
            organ="ECHO_SHELL",
            symbol="latent echo",
            mode="whisper",
            depth=DepthLevel.STANDARD,
            expect="echo_log",
            charge=20,  # LATENT tier
        )
        patch = Patch(input_node="test", output_node="ECHO_SHELL", tags=[], charge=20)

        result = self.organ.invoke(invocation, patch)

        assert result["latent_status"] is True

    def test_recursion_depth_tracking(self):
        """Test depth tracking for patches."""
        patch = Patch(input_node="test", output_node="ECHO_SHELL", tags=[], charge=50)
        patch.depth = 6  # Near threshold

        result = self.organ.track_depth(patch)

        assert result["tracked"] is True
        assert result["at_risk"] is True

    def test_decay_mode(self):
        """Test decay mode applies decay cycle."""
        # Create an echo first
        invocation = Invocation(
            organ="ECHO_SHELL",
            symbol="decay test",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="echo_log",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="ECHO_SHELL", tags=[], charge=50)
        self.organ.invoke(invocation, patch)

        # Run decay mode
        decay_invocation = Invocation(
            organ="ECHO_SHELL",
            symbol="apply decay",
            mode="decay",
            depth=DepthLevel.STANDARD,
            expect="decay_summary",
            charge=50,
        )

        result = self.organ.invoke(decay_invocation, patch)

        assert "decay_cycle_applied" in result
        assert "decay_summary" in result

    def test_pulse_mode(self):
        """Test pulse mode refreshes echoes."""
        invocation = Invocation(
            organ="ECHO_SHELL",
            symbol="pulse me",
            mode="pulse",
            depth=DepthLevel.STANDARD,
            expect="pulse_result",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="ECHO_SHELL", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert "pulse_result" in result
        assert "echo" in result

    def test_get_echo(self):
        """Test getting an echo by ID."""
        invocation = Invocation(
            organ="ECHO_SHELL",
            symbol="findable echo",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="echo_log",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="ECHO_SHELL", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)
        echo_id = result["echo"]["echo_id"]

        retrieved = self.organ.get_echo(echo_id)

        assert retrieved is not None

    def test_get_latent_echoes(self):
        """Test getting echoes in latent pool."""
        invocation = Invocation(
            organ="ECHO_SHELL",
            symbol="latent",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="echo_log",
            charge=20,
        )
        patch = Patch(input_node="test", output_node="ECHO_SHELL", tags=[], charge=20)

        self.organ.invoke(invocation, patch)
        latent = self.organ.get_latent_echoes()

        assert len(latent) >= 1


# =============================================================================
# MaskEngine Tests
# =============================================================================

class TestMaskEngineExtended:
    """Extended tests for MaskEngine organ."""

    def setup_method(self):
        """Set up test fixtures."""
        self.organ = MaskEngine()

    def test_assembly_creates_mask(self):
        """Test assembly mode creates a new mask."""
        invocation = Invocation(
            organ="MASK_ENGINE",
            symbol="brave hero warrior",
            mode="assembly",
            depth=DepthLevel.STANDARD,
            expect="persona",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="MASK_ENGINE", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "assembled"
        assert "mask" in result
        assert result["mask"]["archetype"] == "Hero"

    def test_archetype_identification(self):
        """Test that different keywords map to different archetypes."""
        hero_type = self.organ._identify_archetype("brave hero fighting")
        sage_type = self.organ._identify_archetype("wise knowledge truth")
        rebel_type = self.organ._identify_archetype("rebel break rules")
        lover_type = self.organ._identify_archetype("love passion heart")
        creator_type = self.organ._identify_archetype("create make art")
        default_type = self.organ._identify_archetype("undefined content")

        assert hero_type == "Hero"
        assert sage_type == "Sage"
        assert rebel_type == "Rebel"
        assert lover_type == "Lover"
        assert creator_type == "Creator"
        assert default_type == "Orphan"  # Default

    def test_trait_extraction(self):
        """Test trait extraction from symbol."""
        traits = self.organ._extract_traits("I am strong and brave but also fearful")

        assert "strong" in traits
        assert "brave" in traits
        assert "fearful" in traits

    def test_inheritance_chain(self):
        """Test mask inheritance creates parent-child lineage."""
        # Create parent mask
        parent_inv = Invocation(
            organ="MASK_ENGINE",
            symbol="original hero",
            mode="assembly",
            depth=DepthLevel.STANDARD,
            expect="persona",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="MASK_ENGINE", tags=[], charge=60)
        parent_result = self.organ.invoke(parent_inv, patch)
        parent_name = parent_result["mask"]["name"]

        # Inherit from parent
        child_inv = Invocation(
            organ="MASK_ENGINE",
            symbol=parent_name,
            mode="inheritance",
            depth=DepthLevel.STANDARD,
            expect="persona",
            charge=60,
        )

        child_result = self.organ.invoke(child_inv, patch)

        assert child_result["status"] == "inherited"
        assert "inheritance_chain" in child_result

    def test_mask_wear_remove(self):
        """Test wearing and removing masks."""
        mask = Mask(
            name="Test Mask",
            archetype="Hero",
            charge=60,
            traits=["brave"],
        )

        wear_result = mask.wear()
        assert mask.active is True
        assert wear_result["status"] == "worn"

        remove_result = mask.remove()
        assert mask.active is False
        assert remove_result["status"] == "removed"

    def test_shift_between_personas(self):
        """Test shifting between masks."""
        # Create two masks
        inv1 = Invocation(
            organ="MASK_ENGINE",
            symbol="First Persona",
            mode="assembly",
            depth=DepthLevel.STANDARD,
            expect="persona",
            charge=60,
        )
        inv2 = Invocation(
            organ="MASK_ENGINE",
            symbol="Second Persona",
            mode="assembly",
            depth=DepthLevel.STANDARD,
            expect="persona",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="MASK_ENGINE", tags=[], charge=60)

        self.organ.invoke(inv1, patch)
        result2 = self.organ.invoke(inv2, patch)
        second_name = result2["mask"]["name"]

        # Shift to second persona
        shift_inv = Invocation(
            organ="MASK_ENGINE",
            symbol=second_name,
            mode="shift",
            depth=DepthLevel.STANDARD,
            expect="shift_result",
            charge=50,
        )

        shift_result = self.organ.invoke(shift_inv, patch)

        assert shift_result["status"] == "shifted"

    def test_get_active_mask(self):
        """Test getting the currently active mask."""
        invocation = Invocation(
            organ="MASK_ENGINE",
            symbol="Active Persona",
            mode="assembly",
            depth=DepthLevel.STANDARD,
            expect="persona",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="MASK_ENGINE", tags=[], charge=60)
        result = self.organ.invoke(invocation, patch)
        mask_name = result["mask"]["name"]

        # Shift to wear it
        shift_inv = Invocation(
            organ="MASK_ENGINE",
            symbol=mask_name,
            mode="shift",
            depth=DepthLevel.STANDARD,
            expect="shift_result",
            charge=50,
        )
        self.organ.invoke(shift_inv, patch)

        active = self.organ.get_active_mask()

        assert active is not None


# =============================================================================
# MythicSenate Tests
# =============================================================================

class TestMythicSenateExtended:
    """Extended tests for MythicSenate organ."""

    def setup_method(self):
        """Set up test fixtures."""
        self.organ = MythicSenate()

    def test_create_law(self):
        """Test law proposal creation."""
        law = self.organ.create_law(
            name="Test Law",
            description="A test law description",
            proposed_by="TEST",
            charge=70,
            tags=["TEST+"],
        )

        assert law.law_id.startswith("LAW_")
        assert law.name == "Test Law"
        assert law.vote_status == "pending"

    def test_ritual_vote_weight(self):
        """Test voting weight varies by charge tier."""
        intense_weight = self.organ._calculate_voting_weight(80)
        active_weight = self.organ._calculate_voting_weight(60)
        processing_weight = self.organ._calculate_voting_weight(40)
        latent_weight = self.organ._calculate_voting_weight(20)

        assert intense_weight == 1.0
        assert active_weight == 0.75
        assert processing_weight == 0.5
        assert latent_weight == 0.25

    def test_vote_tally_approval(self):
        """Test law approval when votes_for > votes_against."""
        law = self.organ.create_law(
            name="Approve Me",
            description="Should be approved",
            proposed_by="TEST",
            charge=70,
        )

        # Cast 3 votes for (majority)
        self.organ.ritual_vote(law.law_id, True, 80)
        self.organ.ritual_vote(law.law_id, True, 80)
        self.organ.ritual_vote(law.law_id, True, 80)

        assert law.vote_status == "approved"

    def test_vote_tally_rejection(self):
        """Test law rejection when votes_against > votes_for."""
        law = self.organ.create_law(
            name="Reject Me",
            description="Should be rejected",
            proposed_by="TEST",
            charge=70,
        )

        # Cast 3 votes against (majority)
        self.organ.ritual_vote(law.law_id, False, 80)
        self.organ.ritual_vote(law.law_id, False, 80)
        self.organ.ritual_vote(law.law_id, False, 80)

        assert law.vote_status == "rejected"

    def test_debate_arguments(self):
        """Test debate argument generation."""
        law = self.organ.create_law(
            name="Debate Target",
            description="For debate",
            proposed_by="TEST",
            charge=60,
        )

        arguments = self.organ._generate_debate_arguments(law, "extra context")

        assert "for" in arguments
        assert "against" in arguments
        assert len(arguments["for"]) > 0
        assert len(arguments["against"]) > 0

    def test_law_lookup(self):
        """Test finding laws by ID or name."""
        law = self.organ.create_law(
            name="FindMe Law",
            description="Searchable",
            proposed_by="TEST",
            charge=60,
        )

        found_by_id = self.organ._find_law_by_content(law.law_id)
        # Search by full name (case sensitive match required)
        found_by_name = self.organ._find_law_by_content("FindMe Law")

        assert found_by_id == law.law_id
        assert found_by_name == law.law_id

    def test_legislative_mode(self):
        """Test legislative mode creates law proposal."""
        invocation = Invocation(
            organ="MYTHIC_SENATE",
            symbol="A new law about recursion",
            mode="legislative",
            depth=DepthLevel.STANDARD,
            expect="law_proposal",
            charge=70,
        )
        patch = Patch(input_node="test", output_node="MYTHIC_SENATE", tags=[], charge=70)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "proposed"
        assert "law_proposal" in result

    def test_vote_mode(self):
        """Test vote mode casts votes."""
        law = self.organ.create_law(
            name="Vote Target",
            description="Vote on me",
            proposed_by="TEST",
            charge=60,
        )

        invocation = Invocation(
            organ="MYTHIC_SENATE",
            symbol=f"yes approve {law.law_id}",
            mode="vote",
            depth=DepthLevel.STANDARD,
            expect="vote_result",
            charge=80,
        )
        patch = Patch(input_node="test", output_node="MYTHIC_SENATE", tags=[], charge=80)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "voted"
        assert result["vote"] == "for"


# =============================================================================
# RitualCourt Tests
# =============================================================================

class TestRitualCourtExtended:
    """Extended tests for RitualCourt organ."""

    def setup_method(self):
        """Set up test fixtures."""
        self.organ = RitualCourt()

    def test_contradiction_trial(self):
        """Test contradiction trial mode."""
        invocation = Invocation(
            organ="RITUAL_COURT",
            symbol="I believe X but also believe Y",
            mode="contradiction_trial",
            depth=DepthLevel.STANDARD,
            expect="verdict",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="RITUAL_COURT", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)

        assert "session_id" in result
        assert "verdict" in result
        assert "analysis" in result

    def test_grief_ritual_steps(self):
        """Test grief ritual step generation varies by charge."""
        low_steps = self.organ._design_grief_ritual("loss", 50)
        high_steps = self.organ._design_grief_ritual("loss", 75)
        critical_steps = self.organ._design_grief_ritual("loss", 90)

        assert len(low_steps) == 3  # Base steps only
        assert len(high_steps) == 6  # Base + additional
        assert len(critical_steps) == 8  # All steps

    def test_fusion_verdict_authorized(self):
        """Test fusion verdict authorization when charge >= 70."""
        invocation = Invocation(
            organ="RITUAL_COURT",
            symbol="fusion request",
            mode="fusion_verdict",
            depth=DepthLevel.STANDARD,
            expect="authorization_verdict",
            charge=75,
        )
        patch = Patch(input_node="test", output_node="RITUAL_COURT", tags=[], charge=75)

        result = self.organ.invoke(invocation, patch)

        assert result["authorization"] is True

    def test_fusion_verdict_denied(self):
        """Test fusion verdict denial when charge insufficient."""
        invocation = Invocation(
            organ="RITUAL_COURT",
            symbol="fusion request",
            mode="fusion_verdict",
            depth=DepthLevel.STANDARD,
            expect="authorization_verdict",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="RITUAL_COURT", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["authorization"] is False

    def test_fusion_verdict_with_fuse_flag(self):
        """Test fusion verdict authorization with FUSE+ flag."""
        invocation = Invocation(
            organ="RITUAL_COURT",
            symbol="fusion request",
            mode="fusion_verdict",
            depth=DepthLevel.STANDARD,
            expect="authorization_verdict",
            flags=["FUSE+"],
            charge=50,  # Low charge but has flag
        )
        patch = Patch(input_node="test", output_node="RITUAL_COURT", tags=["FUSE+"], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["authorization"] is True

    def test_emergency_session_threshold(self):
        """Test emergency session requires CRITICAL charge."""
        low_invocation = Invocation(
            organ="RITUAL_COURT",
            symbol="emergency",
            mode="emergency_session",
            depth=DepthLevel.STANDARD,
            expect="emergency_result",
            charge=70,  # Not critical
        )
        patch = Patch(input_node="test", output_node="RITUAL_COURT", tags=[], charge=70)

        result = self.organ.invoke(low_invocation, patch)

        assert result["status"] == "rejected"
        assert "below CRITICAL threshold" in result["reason"]

    def test_emergency_session_critical(self):
        """Test emergency session with CRITICAL charge."""
        invocation = Invocation(
            organ="RITUAL_COURT",
            symbol="critical emergency",
            mode="emergency_session",
            depth=DepthLevel.STANDARD,
            expect="emergency_result",
            charge=90,
        )
        patch = Patch(input_node="test", output_node="RITUAL_COURT", tags=[], charge=90)

        result = self.organ.invoke(invocation, patch)

        assert result["emergency_level"] == "CRITICAL"
        assert "notifications_sent" in result

    def test_verdict_storage(self):
        """Test that verdicts are stored."""
        invocation = Invocation(
            organ="RITUAL_COURT",
            symbol="matter for court",
            mode="contradiction_trial",
            depth=DepthLevel.STANDARD,
            expect="verdict",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="RITUAL_COURT", tags=[], charge=60)

        result = self.organ.invoke(invocation, patch)
        verdict_id = result["verdict"]["verdict_id"]

        retrieved = self.organ.get_verdict(verdict_id)

        assert retrieved is not None

    def test_get_all_verdicts(self):
        """Test getting all verdicts."""
        invocation = Invocation(
            organ="RITUAL_COURT",
            symbol="matter",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="verdict",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="RITUAL_COURT", tags=[], charge=60)

        self.organ.invoke(invocation, patch)
        verdicts = self.organ.get_all_verdicts()

        # Default mode doesn't create verdicts, but test the method works
        assert isinstance(verdicts, list)

    def test_perform_ritual(self):
        """Test direct ritual performance."""
        result = self.organ.perform_ritual("grief", "loss of friend", 70)

        assert "ritual_id" in result
        assert result["charge_after"] < result["charge_before"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
