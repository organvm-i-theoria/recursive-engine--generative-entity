"""
Tests for Process→Product Converter organ.
"""

import pytest
from rege.organs.process_product import (
    ProcessProductConverter,
    RitualProduct,
    ProductFormat,
    VisibilityTier,
    READINESS_CONFIG,
    COMPRESSION_LOSS,
)
from rege.core.models import Invocation, Patch, DepthLevel
from datetime import datetime


class TestProductFormat:
    """Tests for ProductFormat enum."""

    def test_all_formats_defined(self):
        """Test all formats are defined."""
        formats = [f.value for f in ProductFormat]

        assert "scroll" in formats
        assert "pdf" in formats
        assert "app" in formats
        assert "maxpatch" in formats
        assert "drop" in formats
        assert "glyph" in formats
        assert "ritual_code" in formats


class TestVisibilityTier:
    """Tests for VisibilityTier enum."""

    def test_all_tiers_defined(self):
        """Test all tiers are defined."""
        tiers = [t.value for t in VisibilityTier]

        assert "sacred" in tiers
        assert "public" in tiers
        assert "paid" in tiers
        assert "collectible" in tiers


class TestRitualProduct:
    """Tests for RitualProduct data class."""

    def test_ritual_product_creation(self):
        """Test creating a RitualProduct."""
        product = RitualProduct(
            product_id="TEST_PRODUCT",
            source_symbol="test symbol",
            format=ProductFormat.SCROLL,
            tier=VisibilityTier.PUBLIC,
            charge_at_conversion=75,
            depth_at_conversion=6,
            compression_loss=0.1,
            created_at=datetime.now(),
        )

        assert product.format == ProductFormat.SCROLL
        assert product.tier == VisibilityTier.PUBLIC
        assert product.compression_loss == 0.1

    def test_ritual_product_auto_id(self):
        """Test auto-generated product ID."""
        product = RitualProduct(
            product_id="",
            source_symbol="auto",
            format=ProductFormat.DROP,
            tier=VisibilityTier.SACRED,
            charge_at_conversion=50,
            depth_at_conversion=3,
            compression_loss=0.4,
            created_at=datetime.now(),
        )

        assert product.product_id.startswith("PRODUCT_")

    def test_ritual_product_to_dict(self):
        """Test serializing product."""
        product = RitualProduct(
            product_id="SERIALIZE",
            source_symbol="serialize me",
            format=ProductFormat.APP,
            tier=VisibilityTier.PAID,
            charge_at_conversion=85,
            depth_at_conversion=8,
            compression_loss=0.05,
            created_at=datetime.now(),
        )

        data = product.to_dict()

        assert data["format"] == "app"
        assert data["tier"] == "paid"
        assert data["compression_loss"] == 0.05


class TestProcessProductConverter:
    """Tests for ProcessProductConverter organ."""

    def setup_method(self):
        """Set up test fixtures."""
        self.organ = ProcessProductConverter()

    def test_organ_properties(self):
        """Test organ name and description."""
        assert self.organ.name == "PROCESS_PRODUCT"
        assert "Converts" in self.organ.description

    def test_valid_modes(self):
        """Test valid modes list."""
        modes = self.organ.get_valid_modes()

        assert "evaluate" in modes
        assert "convert" in modes
        assert "tier" in modes
        assert "formats" in modes
        assert "default" in modes

    def test_evaluate_not_ready_low_charge(self):
        """Test evaluation fails with low charge."""
        invocation = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="low charge process",
            mode="evaluate",
            depth=DepthLevel.STANDARD,
            expect="readiness_report",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=50)
        patch.depth = 6

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "not_ready"
        assert not result["is_ready"]
        assert not result["readiness_report"]["charge"]["ready"]
        assert result["readiness_report"]["charge"]["gap"] > 0

    def test_evaluate_not_ready_low_depth(self):
        """Test evaluation fails with low depth."""
        invocation = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="low depth process",
            mode="evaluate",
            depth=DepthLevel.LIGHT,
            expect="readiness_report",
            charge=80,
        )
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=80)
        patch.depth = 2  # Below threshold

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "not_ready"
        assert not result["readiness_report"]["depth"]["ready"]

    def test_evaluate_ready(self):
        """Test evaluation passes with sufficient charge and depth."""
        invocation = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="ready process",
            mode="evaluate",
            depth=DepthLevel.FULL_SPIRAL,
            expect="readiness_report",
            charge=80,
        )
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=80)
        patch.depth = 6

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "ready"
        assert result["is_ready"]
        assert len(result["suggested_formats"]) > 0

    def test_evaluate_incomplete_flag(self):
        """Test evaluation handles INCOMPLETE+ flag."""
        invocation = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="incomplete process",
            mode="evaluate",
            depth=DepthLevel.STANDARD,
            expect="readiness_report",
            charge=80,
            flags=["INCOMPLETE+"],
        )
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=80)
        patch.depth = 6

        result = self.organ.invoke(invocation, patch)

        assert not result["readiness_report"]["resolution"]["resolved"]

    def test_convert_fails_low_charge(self):
        """Test conversion fails with low charge."""
        invocation = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="low charge",
            mode="convert",
            depth=DepthLevel.STANDARD,
            expect="product",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=50)
        patch.depth = 6

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "failed"
        assert "Charge below" in result["error"]

    def test_convert_fails_low_depth(self):
        """Test conversion fails with low depth."""
        invocation = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="low depth",
            mode="convert",
            depth=DepthLevel.LIGHT,
            expect="product",
            charge=80,
        )
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=80)
        patch.depth = 2

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "failed"
        assert "Depth below" in result["error"]

    def test_convert_successful(self):
        """Test successful conversion."""
        invocation = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="ready to convert",
            mode="convert",
            depth=DepthLevel.FULL_SPIRAL,
            expect="product",
            charge=80,
        )
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=80)
        patch.depth = 6

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "converted"
        assert "product" in result
        assert result["product"]["charge_at_conversion"] == 80
        assert result["compression_loss_percent"] >= 0

    def test_convert_with_format_flag(self):
        """Test conversion with explicit format flag."""
        invocation = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="scroll format",
            mode="convert",
            depth=DepthLevel.FULL_SPIRAL,
            expect="product",
            charge=80,
            flags=["SCROLL+"],
        )
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=80)
        patch.depth = 6

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "converted"
        assert result["product"]["format"] == "scroll"

    def test_convert_with_tier_flag(self):
        """Test conversion with explicit tier flag."""
        invocation = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="sacred tier",
            mode="convert",
            depth=DepthLevel.FULL_SPIRAL,
            expect="product",
            charge=80,
            flags=["SACRED+"],
        )
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=80)
        patch.depth = 6

        result = self.organ.invoke(invocation, patch)

        assert result["product"]["tier"] == "sacred"

    def test_convert_compression_loss_varies_by_format(self):
        """Test compression loss varies by format."""
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=90)
        patch.depth = 6

        # App format (low loss)
        app_inv = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="app format",
            mode="convert",
            depth=DepthLevel.FULL_SPIRAL,
            expect="product",
            charge=90,
            flags=["APP+"],
        )
        app_result = self.organ.invoke(app_inv, patch)

        # Drop format (high loss)
        drop_inv = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="drop format",
            mode="convert",
            depth=DepthLevel.FULL_SPIRAL,
            expect="product",
            charge=90,
            flags=["DROP+"],
        )
        drop_result = self.organ.invoke(drop_inv, patch)

        assert drop_result["compression_loss_percent"] > app_result["compression_loss_percent"]

    def test_assign_tier_recommendation(self):
        """Test tier recommendation without product ID."""
        invocation = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="recommend tier",
            mode="tier",
            depth=DepthLevel.STANDARD,
            expect="tier_assignment",
            charge=75,
        )
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=75)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "tier_recommended"
        assert result["recommended_tier"] == "paid"  # 71-85 = paid tier

    def test_assign_tier_to_product(self):
        """Test assigning tier to existing product."""
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=80)
        patch.depth = 6

        # Create a product first
        convert_inv = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="tier target",
            mode="convert",
            depth=DepthLevel.FULL_SPIRAL,
            expect="product",
            charge=80,
        )
        convert_result = self.organ.invoke(convert_inv, patch)
        product_id = convert_result["product"]["product_id"]

        # Assign new tier
        tier_inv = Invocation(
            organ="PROCESS_PRODUCT",
            symbol=f"{product_id}:collectible",
            mode="tier",
            depth=DepthLevel.STANDARD,
            expect="tier_assignment",
            charge=50,
        )
        result = self.organ.invoke(tier_inv, patch)

        assert result["status"] == "tier_assigned"
        assert result["new_tier"] == "collectible"

    def test_assign_tier_invalid_tier(self):
        """Test assigning invalid tier."""
        invocation = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="PRODUCT_123:invalid_tier",
            mode="tier",
            depth=DepthLevel.STANDARD,
            expect="tier_assignment",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "failed"
        assert "Invalid tier" in result["error"]

    def test_assign_tier_product_not_found(self):
        """Test assigning tier to non-existent product."""
        invocation = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="NONEXISTENT:public",
            mode="tier",
            depth=DepthLevel.STANDARD,
            expect="tier_assignment",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "failed"
        assert "not found" in result["error"]

    def test_list_formats(self):
        """Test listing formats with recommendations."""
        invocation = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="",
            mode="formats",
            depth=DepthLevel.STANDARD,
            expect="format_list",
            charge=80,
        )
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=80)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "formats_listed"
        assert len(result["formats"]) == len(ProductFormat)
        assert len(result["recommended"]) > 0

    def test_default_status(self):
        """Test default mode returns status."""
        invocation = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="converter_status",
            charge=50,
        )
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=50)

        result = self.organ.invoke(invocation, patch)

        assert result["status"] == "converter_status"
        assert "total_products" in result

    def test_get_product_by_id(self):
        """Test getting product by ID."""
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=80)
        patch.depth = 6

        # Create product
        invocation = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="get by id",
            mode="convert",
            depth=DepthLevel.FULL_SPIRAL,
            expect="product",
            charge=80,
        )
        result = self.organ.invoke(invocation, patch)
        product_id = result["product"]["product_id"]

        # Get by ID
        product = self.organ.get_product(product_id)
        assert product is not None
        assert product.source_symbol == "get by id"

    def test_get_products_by_tier(self):
        """Test getting products by tier."""
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=80)
        patch.depth = 6

        # Create products with different tiers
        for tier_flag in ["SACRED+", "PUBLIC+", "SACRED+"]:
            invocation = Invocation(
                organ="PROCESS_PRODUCT",
                symbol=f"tier {tier_flag}",
                mode="convert",
                depth=DepthLevel.FULL_SPIRAL,
                expect="product",
                charge=80,
                flags=[tier_flag],
            )
            self.organ.invoke(invocation, patch)

        sacred_products = self.organ.get_products_by_tier(VisibilityTier.SACRED)
        assert len(sacred_products) == 2

    def test_get_products_by_format(self):
        """Test getting products by format."""
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=90)
        patch.depth = 6

        # Create products with different formats
        for fmt_flag in ["SCROLL+", "PDF+", "SCROLL+"]:
            invocation = Invocation(
                organ="PROCESS_PRODUCT",
                symbol=f"format {fmt_flag}",
                mode="convert",
                depth=DepthLevel.FULL_SPIRAL,
                expect="product",
                charge=90,
                flags=[fmt_flag],
            )
            self.organ.invoke(invocation, patch)

        scroll_products = self.organ.get_products_by_format(ProductFormat.SCROLL)
        assert len(scroll_products) == 2

    def test_charge_based_tier_determination(self):
        """Test tier determination based on charge."""
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=90)
        patch.depth = 6

        # Critical charge -> collectible
        critical_inv = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="critical",
            mode="convert",
            depth=DepthLevel.FULL_SPIRAL,
            expect="product",
            charge=90,
        )
        critical_result = self.organ.invoke(critical_inv, patch)
        assert critical_result["product"]["tier"] == "collectible"

    def test_depth_reduces_compression_loss(self):
        """Test deeper processing reduces compression loss."""
        # Shallow depth
        shallow_patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=80)
        shallow_patch.depth = 5

        shallow_inv = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="shallow",
            mode="convert",
            depth=DepthLevel.STANDARD,
            expect="product",
            charge=80,
            flags=["PDF+"],
        )
        shallow_result = self.organ.invoke(shallow_inv, shallow_patch)

        # Deep depth
        deep_patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=80)
        deep_patch.depth = 10

        deep_inv = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="deep",
            mode="convert",
            depth=DepthLevel.FULL_SPIRAL,
            expect="product",
            charge=80,
            flags=["PDF+"],
        )
        deep_result = self.organ.invoke(deep_inv, deep_patch)

        # Deeper should have less loss
        assert deep_result["compression_loss_percent"] < shallow_result["compression_loss_percent"]

    def test_state_checkpoint_and_restore(self):
        """Test checkpointing and restoring state."""
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=80)
        patch.depth = 6

        # Create some products
        invocation = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="checkpoint me",
            mode="convert",
            depth=DepthLevel.FULL_SPIRAL,
            expect="product",
            charge=80,
        )
        self.organ.invoke(invocation, patch)

        # Checkpoint
        state = self.organ.get_state()
        assert len(state["state"]["conversion_history"]) == 1

        # Reset
        self.organ.reset()
        assert len(self.organ._products) == 0

        # Restore
        self.organ.restore_state(state)
        assert len(self.organ._conversion_history) == 1

    def test_reset_organ(self):
        """Test resetting organ to initial state."""
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=80)
        patch.depth = 6

        invocation = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="reset me",
            mode="convert",
            depth=DepthLevel.FULL_SPIRAL,
            expect="product",
            charge=80,
        )
        self.organ.invoke(invocation, patch)

        # Reset
        self.organ.reset()

        assert len(self.organ._products) == 0
        assert len(self.organ._conversion_history) == 0


class TestProcessProductConverterIntegration:
    """Integration tests for Process→Product Converter."""

    def test_full_conversion_workflow(self):
        """Test complete conversion workflow: evaluate, convert, tier."""
        organ = ProcessProductConverter()
        patch = Patch(input_node="test", output_node="PROCESS_PRODUCT", tags=[], charge=85)
        patch.depth = 7

        # 1. Evaluate readiness
        eval_inv = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="my creative process",
            mode="evaluate",
            depth=DepthLevel.FULL_SPIRAL,
            expect="readiness_report",
            charge=85,
        )
        eval_result = organ.invoke(eval_inv, patch)
        assert eval_result["is_ready"]

        # 2. Convert to product
        convert_inv = Invocation(
            organ="PROCESS_PRODUCT",
            symbol="my creative process",
            mode="convert",
            depth=DepthLevel.FULL_SPIRAL,
            expect="product",
            charge=85,
            flags=["SCROLL+"],
        )
        convert_result = organ.invoke(convert_inv, patch)
        assert convert_result["status"] == "converted"
        product_id = convert_result["product"]["product_id"]

        # 3. Upgrade tier
        tier_inv = Invocation(
            organ="PROCESS_PRODUCT",
            symbol=f"{product_id}:collectible",
            mode="tier",
            depth=DepthLevel.STANDARD,
            expect="tier_assignment",
            charge=50,
        )
        tier_result = organ.invoke(tier_inv, patch)
        assert tier_result["status"] == "tier_assigned"

        # Verify final product state
        product = organ.get_product(product_id)
        assert product.tier == VisibilityTier.COLLECTIBLE
        assert product.format == ProductFormat.SCROLL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
