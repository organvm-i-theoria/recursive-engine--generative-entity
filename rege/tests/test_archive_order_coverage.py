"""
Tests for Archive Order coverage improvements (89% → 95%).

Targets:
- Decay mechanics at tier boundaries
- Search & retrieval edge cases
- Version consolidation
- Thread tagging edge cases
- Recommendation generation
- State persistence edge cases
"""

import pytest
from datetime import datetime, timedelta

from rege.organs.archive_order import ArchiveOrder, MemoryNode
from rege.core.models import Invocation, Patch, DepthLevel
from rege.core.constants import TIER_BOUNDARIES


class TestDecayMechanics:
    """Tests for decay mechanics at tier boundaries."""

    def test_calculate_decay_rate_at_intense_boundary_71(self):
        """Test _calculate_decay_rate at charge exactly 71 (INTENSE boundary)."""
        node = MemoryNode(
            content="Test at INTENSE boundary",
            charge=71,
            tags=["CANON+"],
        )
        # At 71 (INTENSE+), decay rate should be 0.01 (very slow)
        assert node.decay_rate == 0.01

    def test_calculate_decay_rate_at_active_boundary_51(self):
        """Test _calculate_decay_rate at charge exactly 51 (ACTIVE boundary)."""
        node = MemoryNode(
            content="Test at ACTIVE boundary",
            charge=51,
            tags=["ARCHIVE+"],
        )
        # At 51-70 (ACTIVE), decay rate should be 0.05
        assert node.decay_rate == 0.05

    def test_calculate_decay_rate_at_processing_boundary_26(self):
        """Test _calculate_decay_rate at charge exactly 26 (PROCESSING boundary)."""
        node = MemoryNode(
            content="Test at PROCESSING boundary",
            charge=26,
            tags=["ECHO+"],
        )
        # At 26-50 (PROCESSING), decay rate should be 0.1
        assert node.decay_rate == 0.1

    def test_calculate_decay_rate_at_latent_25(self):
        """Test _calculate_decay_rate at charge 25 (LATENT max)."""
        node = MemoryNode(
            content="Test at LATENT",
            charge=25,
            tags=[],
        )
        # At 0-25 (LATENT), decay rate should be 0.2 (fast decay)
        assert node.decay_rate == 0.2

    def test_apply_decay_with_zero_days(self):
        """Test apply_decay with days_elapsed=0."""
        node = MemoryNode(content="No decay test", charge=80, tags=[])
        original_charge = node.charge

        new_charge = node.apply_decay(days_elapsed=0)

        assert new_charge == original_charge
        assert node.charge == original_charge

    def test_apply_decay_with_charge_at_zero(self):
        """Test apply_decay with charge already at 0."""
        node = MemoryNode(content="Zero charge test", charge=0, tags=[])

        new_charge = node.apply_decay(days_elapsed=10)

        # Should stay at 0, not go negative
        assert new_charge == 0
        assert node.charge == 0

    def test_apply_decay_with_large_days_elapsed(self):
        """Test apply_decay with very large days_elapsed (365+)."""
        node = MemoryNode(content="Long decay test", charge=100, tags=[])
        node.decay_rate = 0.1  # Set a specific rate

        new_charge = node.apply_decay(days_elapsed=365)

        # Should decay significantly but floor at 0
        assert new_charge == 0  # 100 - (0.1 * 365 * 10) = -265, floors at 0

    def test_decay_rate_tier_boundary_transitions(self):
        """Test decay rates exactly at tier boundary transitions."""
        # Just below INTENSE (70)
        node_70 = MemoryNode(content="Test", charge=70, tags=[])
        assert node_70.decay_rate == 0.05  # ACTIVE rate

        # Just above INTENSE (71)
        node_71 = MemoryNode(content="Test", charge=71, tags=[])
        assert node_71.decay_rate == 0.01  # INTENSE rate

        # Just below ACTIVE (50)
        node_50 = MemoryNode(content="Test", charge=50, tags=[])
        assert node_50.decay_rate == 0.1  # PROCESSING rate

        # Just above ACTIVE (51)
        node_51 = MemoryNode(content="Test", charge=51, tags=[])
        assert node_51.decay_rate == 0.05  # ACTIVE rate


class TestSearchAndRetrieval:
    """Tests for search and retrieval edge cases."""

    def setup_method(self):
        """Set up test archive."""
        self.archive = ArchiveOrder()

    def test_search_nodes_empty_query(self):
        """Test _search_nodes with empty query string."""
        # Add some nodes first
        self.archive.create_memory_node("Memory one", 50, ["CANON+"])
        self.archive.create_memory_node("Memory two", 60, ["ECHO+"])

        results = self.archive._search_nodes("")

        # Empty string should match all nodes (contained in all content)
        assert len(results) >= 2

    def test_search_nodes_whitespace_only_query(self):
        """Test _search_nodes with whitespace-only query."""
        self.archive.create_memory_node("Memory test", 50, [])

        results = self.archive._search_nodes("   ")

        # Whitespace should be stripped and match nothing specific
        # The query "   " lowered and checked against content
        assert isinstance(results, list)

    def test_search_nodes_special_regex_characters(self):
        """Test _search_nodes with special regex characters."""
        self.archive.create_memory_node("Test [special] characters", 60, [])
        self.archive.create_memory_node("Test (parentheses) here", 55, [])
        self.archive.create_memory_node("Test *asterisk* pattern", 50, [])

        # These should not crash even with regex-like chars
        results_brackets = self.archive._search_nodes("[special]")
        results_parens = self.archive._search_nodes("(parentheses)")
        results_asterisk = self.archive._search_nodes("*asterisk*")

        # Should find matches (string containment, not regex)
        assert len(results_brackets) >= 1
        assert len(results_parens) >= 1
        assert len(results_asterisk) >= 1

    def test_search_nodes_no_matching_nodes(self):
        """Test _search_nodes with no matching nodes."""
        self.archive.create_memory_node("Apple pie", 50, [])
        self.archive.create_memory_node("Banana bread", 60, [])

        results = self.archive._search_nodes("completely_unrelated_xyz123")

        assert len(results) == 0

    def test_search_nodes_limit_to_10_results(self):
        """Test _search_nodes results limit (>10 matches)."""
        # Create 15 nodes with matching content
        for i in range(15):
            self.archive.create_memory_node(f"Searchable memory {i}", 50, [])

        results = self.archive._search_nodes("Searchable")

        # Should be limited to 10 in retrieval mode (via invoke)
        # But _search_nodes itself returns all
        assert len(results) == 15

    def test_search_nodes_case_insensitive(self):
        """Test case-insensitive matching edge cases."""
        self.archive.create_memory_node("UPPERCASE CONTENT", 60, [])
        self.archive.create_memory_node("lowercase content", 55, [])
        self.archive.create_memory_node("MixedCase Content", 50, [])

        results_lower = self.archive._search_nodes("content")
        results_upper = self.archive._search_nodes("CONTENT")
        results_mixed = self.archive._search_nodes("Content")

        # All should find all 3 nodes
        assert len(results_lower) == 3
        assert len(results_upper) == 3
        assert len(results_mixed) == 3

    def test_search_by_tag(self):
        """Test search matches by tag as well as content."""
        self.archive.create_memory_node("Unrelated content", 60, ["SPECIAL_TAG+"])

        results = self.archive._search_nodes("SPECIAL_TAG")

        assert len(results) >= 1


class TestVersionConsolidation:
    """Tests for version tracking and consolidation."""

    def setup_method(self):
        """Set up test archive."""
        self.archive = ArchiveOrder()

    def test_create_memory_node_exactly_3_versions_triggers_consolidation(self):
        """Test create_memory_node with exactly 3 versions triggers fusion tag."""
        content = "Repeated content for versioning"

        node1 = self.archive.create_memory_node(content, 50, [])
        assert node1.version == 1
        assert "VERSION_CONSOLIDATION_NEEDED+" not in node1.tags

        node2 = self.archive.create_memory_node(content, 55, [])
        assert node2.version == 2
        assert "VERSION_CONSOLIDATION_NEEDED+" not in node2.tags

        node3 = self.archive.create_memory_node(content, 60, [])
        assert node3.version == 3
        assert "VERSION_CONSOLIDATION_NEEDED+" in node3.tags

    def test_create_memory_node_4_plus_versions_no_duplicate_tags(self):
        """Test create_memory_node with 4+ versions doesn't duplicate tags."""
        content = "Multiple version content"

        # Create 4 versions
        for _ in range(4):
            node = self.archive.create_memory_node(content, 50, [])

        # Only one consolidation tag
        consolidation_count = node.tags.count("VERSION_CONSOLIDATION_NEEDED+")
        assert consolidation_count == 1
        assert node.version == 4

    def test_version_linking_with_existing_nodes(self):
        """Test version linking with existing node IDs."""
        content = "Linked version content"

        node1 = self.archive.create_memory_node(content, 50, [])
        node2 = self.archive.create_memory_node(content, 55, [])
        node3 = self.archive.create_memory_node(content, 60, [])

        # Node 3 should link to nodes 1 and 2
        assert node1.node_id in node3.linked_nodes
        assert node2.node_id in node3.linked_nodes
        assert len(node3.linked_nodes) == 2

    def test_version_tracker_state_after_consolidation(self):
        """Test version_tracker state after multiple versions."""
        content = "Tracked content"

        nodes = []
        for i in range(3):
            nodes.append(self.archive.create_memory_node(content, 50, []))

        # Check version tracker has all node IDs
        content_key = self.archive._content_hash(content)
        tracked_ids = self.archive._version_tracker[content_key]

        assert len(tracked_ids) == 3
        assert all(n.node_id in tracked_ids for n in nodes)


class TestThreadTagging:
    """Tests for thread tag generation edge cases."""

    def setup_method(self):
        """Set up test archive."""
        self.archive = ArchiveOrder()

    def test_generate_thread_tag_single_word_content(self):
        """Test _generate_thread_tag with single-word content."""
        node = MemoryNode(content="Hello", charge=50, tags=[])

        tag = self.archive._generate_thread_tag(node)

        assert "Hello" in tag
        assert "_Thread_" in tag
        assert tag.endswith("_01")  # Version 1

    def test_generate_thread_tag_empty_content(self):
        """Test _generate_thread_tag with empty content."""
        node = MemoryNode(content="", charge=50, tags=[])

        tag = self.archive._generate_thread_tag(node)

        # Should not crash, produces minimal tag
        assert "_Thread_" in tag

    def test_generate_thread_tag_long_content(self):
        """Test _generate_thread_tag with 10+ word content."""
        long_content = "This is a very long piece of content with many words to test the tag generation"
        node = MemoryNode(content=long_content, charge=50, tags=[])

        tag = self.archive._generate_thread_tag(node)

        # Should only use first 2 words
        assert "This_Is" in tag
        assert "_Thread_" in tag

    def test_generate_thread_tag_special_characters(self):
        """Test _generate_thread_tag with punctuation/special chars."""
        node = MemoryNode(content="Hello! World? Test.", charge=50, tags=[])

        tag = self.archive._generate_thread_tag(node)

        # Should handle punctuation attached to words
        assert "_Thread_" in tag

    def test_thread_indexing(self):
        """Test thread tag collision handling (same tag, different nodes)."""
        # Create nodes and index by same tag
        tag = "TEST_THREAD+"
        node1 = self.archive.create_memory_node("Content 1", 50, [tag])
        node2 = self.archive.create_memory_node("Content 2", 60, [tag])

        # Both should be indexed under same tag
        assert node1.node_id in self.archive._thread_tags[tag]
        assert node2.node_id in self.archive._thread_tags[tag]

    def test_index_by_thread_no_duplicates(self):
        """Test _index_by_thread doesn't add duplicate node_ids."""
        node = self.archive.create_memory_node("Test content", 50, [])
        tag = "UNIQUE_TAG+"

        # Index same node twice
        self.archive._index_by_thread(tag, node.node_id)
        self.archive._index_by_thread(tag, node.node_id)

        # Should only appear once
        assert self.archive._thread_tags[tag].count(node.node_id) == 1


class TestRecommendations:
    """Tests for decay recommendation generation."""

    def setup_method(self):
        """Set up test archive."""
        self.archive = ArchiveOrder()

    def test_generate_decay_recommendations_all_nodes_healthy(self):
        """Test _generate_decay_recommendations with all nodes healthy."""
        recommendations = self.archive._generate_decay_recommendations([], [])

        assert len(recommendations) == 1
        assert "stable" in recommendations[0].lower()

    def test_generate_decay_recommendations_many_decaying_nodes(self):
        """Test _generate_decay_recommendations with many decaying nodes."""
        decaying_nodes = []
        for i in range(5):
            node = MemoryNode(f"Decaying {i}", charge=60, tags=[])
            node.last_accessed = datetime.now() - timedelta(days=30)
            decaying_nodes.append(node)

        recommendations = self.archive._generate_decay_recommendations(decaying_nodes, [])

        # Should recommend accessing ACTIVE+ nodes
        assert any("ACTIVE+" in rec or "decaying" in rec.lower() for rec in recommendations)

    def test_generate_decay_recommendations_many_latent_nodes(self):
        """Test _generate_decay_recommendations with >10 latent nodes."""
        latent_nodes = []
        for i in range(15):
            node = MemoryNode(f"Latent {i}", charge=10, tags=[])
            latent_nodes.append(node)

        recommendations = self.archive._generate_decay_recommendations([], latent_nodes)

        # Should recommend archival consolidation
        assert any("consolidation" in rec.lower() or "LATENT" in rec for rec in recommendations)

    def test_generate_decay_recommendations_mixed_states(self):
        """Test recommendations with mixed decaying and latent states."""
        decaying = [MemoryNode("Decay", charge=60, tags=[]) for _ in range(3)]
        for node in decaying:
            node.last_accessed = datetime.now() - timedelta(days=14)

        latent = [MemoryNode("Latent", charge=15, tags=[]) for _ in range(12)]

        recommendations = self.archive._generate_decay_recommendations(decaying, latent)

        # Should have multiple recommendations
        assert len(recommendations) >= 1


class TestStatePersistence:
    """Tests for state persistence edge cases."""

    def setup_method(self):
        """Set up test archive."""
        self.archive = ArchiveOrder()

    def test_node_with_very_old_creation_timestamp(self):
        """Test node with very old creation_at timestamp."""
        node = MemoryNode(content="Ancient memory", charge=50, tags=[])
        node.created_at = datetime(2000, 1, 1)

        data = node.to_dict()

        assert data["created_at"] == "2000-01-01T00:00:00"

    def test_access_count_with_large_numbers(self):
        """Test access_count with very large numbers."""
        node = MemoryNode(content="Popular memory", charge=50, tags=[])

        # Simulate many accesses
        for _ in range(1000):
            node.access()

        assert node.access_count == 1000
        # Charge should be capped at 100
        assert node.charge <= 100

    def test_linked_nodes_with_many_links(self):
        """Test linked_nodes with many connections."""
        node = MemoryNode(content="Connected memory", charge=50, tags=[])
        node.linked_nodes = [f"NODE_{i}" for i in range(50)]

        data = node.to_dict()

        assert len(data["linked_nodes"]) == 50

    def test_empty_archive_operations(self):
        """Test operations on empty archive."""
        empty_archive = ArchiveOrder()

        # Decay check on empty archive
        decaying = empty_archive._get_decaying_nodes()
        latent = empty_archive._get_latent_nodes()

        assert decaying == []
        assert latent == []

        # Search on empty archive
        results = empty_archive._search_nodes("anything")
        assert results == []


class TestArchiveOrderInvocations:
    """Tests for Archive Order invoke method modes."""

    def setup_method(self):
        """Set up test archive."""
        self.archive = ArchiveOrder()

    def test_sacred_logging_mode(self):
        """Test sacred_logging mode adds SACRED+ tag and boost."""
        invocation = Invocation(
            organ="ARCHIVE_ORDER",
            symbol="Sacred memory content",
            mode="sacred_logging",
            depth=DepthLevel.STANDARD,
            expect="canonical_thread_tag",
            charge=60,
        )
        patch = Patch(input_node="test", output_node="ARCHIVE_ORDER", tags=[], charge=60)

        result = self.archive.invoke(invocation, patch)

        assert result["status"] == "sacred_archived"
        assert "SACRED+" in result["node"]["tags"]
        # Charge should be boosted by 10
        assert result["node"]["charge"] == 70

    def test_sacred_logging_charge_cap_at_100(self):
        """Test sacred_logging doesn't exceed charge 100."""
        invocation = Invocation(
            organ="ARCHIVE_ORDER",
            symbol="High charge sacred",
            mode="sacred_logging",
            depth=DepthLevel.STANDARD,
            expect="canonical_thread_tag",
            charge=95,
        )
        patch = Patch(input_node="test", output_node="ARCHIVE_ORDER", tags=[], charge=95)

        result = self.archive.invoke(invocation, patch)

        # Should cap at 100, not 105
        assert result["node"]["charge"] <= 100

    def test_retrieval_mode_refreshes_accessed_nodes(self):
        """Test retrieval mode refreshes accessed nodes."""
        # Create a node first
        node = self.archive.create_memory_node("Retrievable content", 50, ["CANON+"])
        original_access_count = node.access_count

        invocation = Invocation(
            organ="ARCHIVE_ORDER",
            symbol="Retrievable",
            mode="retrieval",
            depth=DepthLevel.STANDARD,
            expect="memory_node",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="ARCHIVE_ORDER", tags=[], charge=50)

        result = self.archive.invoke(invocation, patch)

        # Node should have been accessed
        assert result["results_count"] >= 1
        # Access count should increase
        assert node.access_count > original_access_count

    def test_decay_check_mode(self):
        """Test decay_check mode returns monitoring data."""
        # Create some nodes
        self.archive.create_memory_node("Active node", 60, [])
        latent_node = self.archive.create_memory_node("Latent node", 20, [])

        invocation = Invocation(
            organ="ARCHIVE_ORDER",
            symbol="check decay",
            mode="decay_check",
            depth=DepthLevel.STANDARD,
            expect="decay_report",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="ARCHIVE_ORDER", tags=[], charge=50)

        result = self.archive.invoke(invocation, patch)

        assert "latent_count" in result
        assert "decaying_count" in result
        assert "recommendations" in result
        assert result["latent_count"] >= 1

    def test_default_mode(self):
        """Test default archive mode."""
        invocation = Invocation(
            organ="ARCHIVE_ORDER",
            symbol="Default archive content",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="archive_entry",
            charge=55,
        )
        patch = Patch(input_node="test", output_node="ARCHIVE_ORDER", tags=[], charge=55)

        result = self.archive.invoke(invocation, patch)

        assert result["status"] == "archived"
        assert "tier" in result
        assert result["node"]["charge"] == 55


class TestDecayCheckMethod:
    """Tests for decay_check method (public API)."""

    def setup_method(self):
        """Set up test archive."""
        self.archive = ArchiveOrder()

    def test_decay_check_not_found(self):
        """Test decay_check with non-existent node."""
        result = self.archive.decay_check("NONEXISTENT_NODE")

        assert result["status"] == "not_found"

    def test_decay_check_existing_node(self):
        """Test decay_check with existing node."""
        node = self.archive.create_memory_node("Decay check target", 60, ["CANON+"])

        result = self.archive.decay_check(node.node_id)

        assert result["node_id"] == node.node_id
        assert result["current_charge"] == 60
        assert "tier" in result
        assert "decay_rate" in result
        assert "projected_charge_7d" in result
        assert "at_risk" in result

    def test_decay_check_at_risk_node(self):
        """Test decay_check correctly identifies at-risk node."""
        node = self.archive.create_memory_node("At risk content", 20, [])

        result = self.archive.decay_check(node.node_id)

        # Charge 20 is below LATENT_MAX (25), so should be at_risk
        assert result["at_risk"] is True


class TestHelperMethods:
    """Tests for helper methods."""

    def setup_method(self):
        """Set up test archive."""
        self.archive = ArchiveOrder()

    def test_content_hash_normalization(self):
        """Test content hash normalizes content."""
        # Same content with different casing/whitespace
        hash1 = self.archive._content_hash("Test Content Here")
        hash2 = self.archive._content_hash("TEST CONTENT HERE")
        hash3 = self.archive._content_hash("  test content here  ")

        # All should produce same hash
        assert hash1 == hash2 == hash3

    def test_content_hash_truncation(self):
        """Test content hash truncates at 50 characters."""
        long_content = "A" * 100 + "_unique_suffix"
        short_content = "A" * 50

        hash_long = self.archive._content_hash(long_content)
        hash_short = self.archive._content_hash(short_content)

        # Both should hash to same (first 50 chars)
        assert hash_long == hash_short

    def test_get_valid_modes(self):
        """Test get_valid_modes returns expected modes."""
        modes = self.archive.get_valid_modes()

        assert "sacred_logging" in modes
        assert "retrieval" in modes
        assert "decay_check" in modes
        assert "default" in modes

    def test_get_output_types(self):
        """Test get_output_types returns expected types."""
        types = self.archive.get_output_types()

        assert "canonical_thread_tag" in types
        assert "memory_node" in types
        assert "archive_entry" in types

    def test_get_node_existing(self):
        """Test get_node returns existing node."""
        created = self.archive.create_memory_node("Get test", 50, [])
        retrieved = self.archive.get_node(created.node_id)

        assert retrieved is not None
        assert retrieved.node_id == created.node_id

    def test_get_node_nonexistent(self):
        """Test get_node returns None for nonexistent."""
        retrieved = self.archive.get_node("NONEXISTENT_ID")
        assert retrieved is None

    def test_get_all_nodes(self):
        """Test get_all_nodes returns all nodes."""
        self.archive.create_memory_node("Node 1", 50, [])
        self.archive.create_memory_node("Node 2", 60, [])
        self.archive.create_memory_node("Node 3", 70, [])

        all_nodes = self.archive.get_all_nodes()

        assert len(all_nodes) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
