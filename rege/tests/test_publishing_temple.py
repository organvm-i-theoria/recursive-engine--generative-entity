"""
Tests for Publishing Temple organ.
"""

import pytest
from rege.organs.publishing_temple import (
    PublishingTemple,
    RitualExport,
    PublicationFormat,
    ScarcityLevel,
    PUBLICATION_CONFIG,
)
from rege.core.models import Invocation, Patch, DepthLevel
from datetime import datetime


class TestPublicationFormat:
    """Tests for PublicationFormat enum."""

    def test_all_formats_defined(self):
        """Test all formats are defined."""
        formats = [f.value for f in PublicationFormat]

        assert "digital" in formats
        assert "print" in formats
        assert "nft" in formats
        assert "archive" in formats
        assert "ritual" in formats


class TestScarcityLevel:
    """Tests for ScarcityLevel enum."""

    def test_all_scarcity_levels_defined(self):
        """Test all scarcity levels are defined."""
        levels = [l.value for l in ScarcityLevel]

        assert "unlimited" in levels
        assert "limited" in levels
        assert "unique" in levels
        assert "timed" in levels


class TestRitualExport:
    """Tests for RitualExport data class."""

    def test_ritual_export_creation(self):
        """Test creating a RitualExport."""
        export = RitualExport(
            export_id="TEST_EXPORT",
            source_id="SOURCE_123",
            format=PublicationFormat.DIGITAL,
            scarcity=ScarcityLevel.UNLIMITED,
            scarcity_count=None,
            metadata={"key": "value"},
            sealed_at=None,
            published_at=None,
            risk_score=40,
        )

        assert export.format == PublicationFormat.DIGITAL
        assert export.scarcity == ScarcityLevel.UNLIMITED
        assert export.status == "pending"

    def test_ritual_export_auto_id(self):
        """Test auto-generated export ID."""
        export = RitualExport(
            export_id="",
            source_id="AUTO",
            format=PublicationFormat.PRINT,
            scarcity=ScarcityLevel.LIMITED,
            scarcity_count=100,
            metadata={},
            sealed_at=None,
            published_at=None,
            risk_score=50,
        )

        assert export.export_id.startswith("EXPORT_")

    def test_ritual_export_to_dict(self):
        """Test serializing export."""
        export = RitualExport(
            export_id="SERIALIZE",
            source_id="SRC",
            format=PublicationFormat.NFT,
            scarcity=ScarcityLevel.UNIQUE,
            scarcity_count=1,
            metadata={"artist": "creator"},
            sealed_at=datetime.now(),
            published_at=None,
            risk_score=30,
            law_references=["LAW_01"],
        )

        data = export.to_dict()

        assert data["format"] == "nft"
        assert data["scarcity"] == "unique"
        assert data["scarcity_count"] == 1


class TestPublishingTemple:
    """Tests for PublishingTemple organ."""

    def setup_method(self):
        """Set up test fixtures."""
        self.organ = PublishingTemple()

    def test_organ_properties(self):
        """Test organ name and description."""
        assert self.organ.name == "PUBLISHING_TEMPLE"
        assert "Final gate" in self.organ.description

    def test_valid_modes(self):
        """Test valid modes list."""
        modes = self.organ.get_valid_modes()

        assert "sanctify" in modes
        assert "publish" in modes
        assert "seal" in modes
        assert "withdraw" in modes
        assert "queue" in modes
        assert "default" in modes

    def test_sanctify_acceptable_risk(self):
        """Test sanctification with acceptable risk."""
        invocation = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="safe content",
            mode="sanctify",
            depth=DepthLevel.FULL_SPIRAL,
            expect="sanctification",
            charge=80,
            flags=["CANON+"],
        )
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=80)
        patch.depth = 7

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "sanctified"
        assert result["risk_assessment"]["acceptable"]
        assert result["ready_to_publish"]

    def test_sanctify_high_risk_blocked(self):
        """Test sanctification blocked for high risk."""
        invocation = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="risky content",
            mode="sanctify",
            depth=DepthLevel.LIGHT,
            expect="sanctification",
            charge=30,
            flags=["VOLATILE+", "INCOMPLETE+"],
        )
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=30)
        patch.depth = 1

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "blocked"
        assert not result["risk_assessment"]["acceptable"]
        assert not result["ready_to_publish"]

    def test_sanctify_auto_generates_source_id(self):
        """Test sanctification auto-generates source ID."""
        invocation = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="",
            mode="sanctify",
            depth=DepthLevel.STANDARD,
            expect="sanctification",
            charge=70,
        )
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=70)
        patch.depth = 5

        result = self.organ.invoke(invocation, patch)

        assert result["export"]["source_id"].startswith("SOURCE_")

    def test_publish_from_queue(self):
        """Test publishing from queue."""
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=80)
        patch.depth = 7

        # Sanctify first
        sanctify_inv = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="queue publish",
            mode="sanctify",
            depth=DepthLevel.FULL_SPIRAL,
            expect="sanctification",
            charge=80,
        )
        self.organ.invoke(sanctify_inv, patch)

        # Publish without ID (from queue)
        publish_inv = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="",
            mode="publish",
            depth=DepthLevel.STANDARD,
            expect="publication",
            charge=50,
        )
        result = self.organ.invoke(publish_inv, patch)

        assert result["status"] == "published"
        assert result["export"]["status"] == "published"

    def test_publish_by_id(self):
        """Test publishing by specific ID."""
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=80)
        patch.depth = 7

        # Sanctify first
        sanctify_inv = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="specific publish",
            mode="sanctify",
            depth=DepthLevel.FULL_SPIRAL,
            expect="sanctification",
            charge=80,
        )
        sanctify_result = self.organ.invoke(sanctify_inv, patch)
        export_id = sanctify_result["export"]["export_id"]

        # Publish by ID
        publish_inv = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol=export_id,
            mode="publish",
            depth=DepthLevel.STANDARD,
            expect="publication",
            charge=50,
        )
        result = self.organ.invoke(publish_inv, patch)

        assert result["status"] == "published"
        assert result["export"]["export_id"] == export_id

    def test_publish_empty_queue_fails(self):
        """Test publishing with empty queue fails."""
        invocation = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="",
            mode="publish",
            depth=DepthLevel.STANDARD,
            expect="publication",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "failed"
        assert "queue is empty" in result["error"]

    def test_publish_not_found_fails(self):
        """Test publishing non-existent export fails."""
        invocation = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="NONEXISTENT_123",
            mode="publish",
            depth=DepthLevel.STANDARD,
            expect="publication",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "failed"
        assert "not found" in result["error"]

    def test_seal_metadata(self):
        """Test sealing metadata."""
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=80)
        patch.depth = 7

        # Sanctify first
        sanctify_inv = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="seal me",
            mode="sanctify",
            depth=DepthLevel.FULL_SPIRAL,
            expect="sanctification",
            charge=80,
        )
        sanctify_result = self.organ.invoke(sanctify_inv, patch)
        export_id = sanctify_result["export"]["export_id"]

        # Seal
        seal_inv = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol=export_id,
            mode="seal",
            depth=DepthLevel.STANDARD,
            expect="seal_record",
            charge=70,
            flags=["LAW_01", "LAW_06"],
        )
        result = self.organ.invoke(seal_inv, patch)

        assert result["status"] == "sealed"
        assert "LAW_01" in result["law_references"]
        assert "LAW_06" in result["law_references"]

    def test_seal_already_sealed(self):
        """Test sealing already sealed export."""
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=80)
        patch.depth = 7

        # Sanctify
        sanctify_inv = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="double seal",
            mode="sanctify",
            depth=DepthLevel.FULL_SPIRAL,
            expect="sanctification",
            charge=80,
        )
        sanctify_result = self.organ.invoke(sanctify_inv, patch)
        export_id = sanctify_result["export"]["export_id"]

        # Seal once
        seal_inv = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol=export_id,
            mode="seal",
            depth=DepthLevel.STANDARD,
            expect="seal_record",
            charge=70,
        )
        self.organ.invoke(seal_inv, patch)

        # Try to seal again
        result = self.organ.invoke(seal_inv, patch)

        assert result["status"] == "already_sealed"

    def test_seal_no_id_fails(self):
        """Test sealing without ID fails."""
        invocation = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="",
            mode="seal",
            depth=DepthLevel.STANDARD,
            expect="seal_record",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "failed"
        assert "required" in result["error"]

    def test_withdraw_export(self):
        """Test withdrawing an export."""
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=80)
        patch.depth = 7

        # Sanctify first
        sanctify_inv = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="withdraw me",
            mode="sanctify",
            depth=DepthLevel.FULL_SPIRAL,
            expect="sanctification",
            charge=80,
        )
        sanctify_result = self.organ.invoke(sanctify_inv, patch)
        export_id = sanctify_result["export"]["export_id"]

        # Withdraw
        withdraw_inv = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol=export_id,
            mode="withdraw",
            depth=DepthLevel.STANDARD,
            expect="withdrawal",
            charge=50,
        )
        result = self.organ.invoke(withdraw_inv, patch)

        assert result["status"] == "withdrawn"
        assert result["previous_status"] == "sanctified"

    def test_view_queue(self):
        """Test viewing publication queue."""
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=80)
        patch.depth = 7

        # Sanctify some exports
        for i in range(3):
            sanctify_inv = Invocation(
                organ="PUBLISHING_TEMPLE",
                symbol=f"queued_{i}",
                mode="sanctify",
                depth=DepthLevel.FULL_SPIRAL,
                expect="sanctification",
                charge=80,
            )
            self.organ.invoke(sanctify_inv, patch)

        # View queue
        queue_inv = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="",
            mode="queue",
            depth=DepthLevel.STANDARD,
            expect="queue_status",
            charge=50,
        )
        result = self.organ.invoke(queue_inv, patch)

        assert result["status"] == "queue_retrieved"
        assert result["queue_length"] == 3

    def test_default_status(self):
        """Test default mode returns status."""
        invocation = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="temple_status",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "temple_status"
        assert "total_exports" in result
        assert "status_breakdown" in result

    def test_format_determination_by_flags(self):
        """Test format determined by flags."""
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=90)
        patch.depth = 7

        invocation = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="print format",
            mode="sanctify",
            depth=DepthLevel.FULL_SPIRAL,
            expect="sanctification",
            charge=90,
            flags=["PRINT+"],
        )
        result = self.organ.invoke(invocation, patch)

        assert result["export"]["format"] == "print"

    def test_format_nft_requires_critical_charge(self):
        """Test NFT format requires critical charge."""
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=70)
        patch.depth = 7

        invocation = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="low charge nft",
            mode="sanctify",
            depth=DepthLevel.FULL_SPIRAL,
            expect="sanctification",
            charge=70,  # Below NFT threshold
            flags=["NFT+"],
        )
        result = self.organ.invoke(invocation, patch)

        # Should default to something other than NFT
        assert result["export"]["format"] != "nft"

    def test_scarcity_unique(self):
        """Test unique scarcity setting."""
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=90)
        patch.depth = 7

        invocation = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="unique item",
            mode="sanctify",
            depth=DepthLevel.FULL_SPIRAL,
            expect="sanctification",
            charge=90,
            flags=["UNIQUE+"],
        )
        result = self.organ.invoke(invocation, patch)

        assert result["export"]["scarcity"] == "unique"
        assert result["export"]["scarcity_count"] == 1

    def test_scarcity_limited_with_count(self):
        """Test limited scarcity with custom count."""
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=80)
        patch.depth = 7

        invocation = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="limited edition",
            mode="sanctify",
            depth=DepthLevel.FULL_SPIRAL,
            expect="sanctification",
            charge=80,
            flags=["LIMITED+", "COUNT_50"],
        )
        result = self.organ.invoke(invocation, patch)

        assert result["export"]["scarcity"] == "limited"
        assert result["export"]["scarcity_count"] == 50

    def test_record_distribution(self):
        """Test recording distribution."""
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=80)
        patch.depth = 7

        # Full workflow: sanctify, publish
        sanctify_inv = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="distribute me",
            mode="sanctify",
            depth=DepthLevel.FULL_SPIRAL,
            expect="sanctification",
            charge=80,
        )
        sanctify_result = self.organ.invoke(sanctify_inv, patch)
        export_id = sanctify_result["export"]["export_id"]

        publish_inv = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol=export_id,
            mode="publish",
            depth=DepthLevel.STANDARD,
            expect="publication",
            charge=50,
        )
        self.organ.invoke(publish_inv, patch)

        # Record distribution
        dist_result = self.organ.record_distribution(export_id, "RECIPIENT_1")

        assert dist_result["status"] == "distributed"
        assert dist_result["distribution_number"] == 1

    def test_distribution_unique_limit(self):
        """Test unique item can only be distributed once."""
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=90)
        patch.depth = 7

        # Sanctify unique item
        sanctify_inv = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="unique distribution",
            mode="sanctify",
            depth=DepthLevel.FULL_SPIRAL,
            expect="sanctification",
            charge=90,
            flags=["UNIQUE+"],
        )
        sanctify_result = self.organ.invoke(sanctify_inv, patch)
        export_id = sanctify_result["export"]["export_id"]

        # Publish
        publish_inv = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol=export_id,
            mode="publish",
            depth=DepthLevel.STANDARD,
            expect="publication",
            charge=50,
        )
        self.organ.invoke(publish_inv, patch)

        # First distribution
        dist1 = self.organ.record_distribution(export_id, "FIRST")
        assert dist1["status"] == "distributed"

        # Second distribution should fail
        dist2 = self.organ.record_distribution(export_id, "SECOND")
        assert dist2["status"] == "failed"
        assert "already distributed" in dist2["error"]

    def test_get_export_by_id(self):
        """Test getting export by ID."""
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=80)
        patch.depth = 7

        sanctify_inv = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="get by id",
            mode="sanctify",
            depth=DepthLevel.FULL_SPIRAL,
            expect="sanctification",
            charge=80,
        )
        sanctify_result = self.organ.invoke(sanctify_inv, patch)
        export_id = sanctify_result["export"]["export_id"]

        export = self.organ.get_export(export_id)
        assert export is not None
        assert export.source_id == "get by id"

    def test_reset_organ(self):
        """Test resetting organ to initial state."""
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=80)
        patch.depth = 7

        # Create some state
        invocation = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="reset me",
            mode="sanctify",
            depth=DepthLevel.FULL_SPIRAL,
            expect="sanctification",
            charge=80,
        )
        self.organ.invoke(invocation, patch)

        # Reset
        self.organ.reset()

        assert len(self.organ._exports) == 0
        assert len(self.organ._publication_queue) == 0


class TestPublishingTempleIntegration:
    """Integration tests for Publishing Temple."""

    def test_full_publication_workflow(self):
        """Test complete publication workflow."""
        organ = PublishingTemple()
        patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=90)
        patch.depth = 8

        # 1. Sanctify
        sanctify_inv = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol="masterpiece",
            mode="sanctify",
            depth=DepthLevel.FULL_SPIRAL,
            expect="sanctification",
            charge=90,
            flags=["NFT+", "UNIQUE+"],
        )
        sanctify_result = organ.invoke(sanctify_inv, patch)
        assert sanctify_result["status"] == "sanctified"
        export_id = sanctify_result["export"]["export_id"]

        # 2. Seal with laws
        seal_inv = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol=export_id,
            mode="seal",
            depth=DepthLevel.STANDARD,
            expect="seal_record",
            charge=70,
            flags=["LAW_01", "LAW_06"],
        )
        seal_result = organ.invoke(seal_inv, patch)
        assert seal_result["status"] == "sealed"

        # 3. Publish
        publish_inv = Invocation(
            organ="PUBLISHING_TEMPLE",
            symbol=export_id,
            mode="publish",
            depth=DepthLevel.STANDARD,
            expect="publication",
            charge=50,
        )
        publish_result = organ.invoke(publish_inv, patch)
        assert publish_result["status"] == "published"

        # 4. Distribute
        dist_result = organ.record_distribution(export_id, "COLLECTOR")
        assert dist_result["status"] == "distributed"

        # Verify final state
        export = organ.get_export(export_id)
        assert export.status == "published"
        assert export.distributed_count == 1
        assert len(export.law_references) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
