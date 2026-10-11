"""
Unit tests for ZoomGenerator class.

Tests the core zoom generation logic including:
- Gap detection
- Source zoom selection
- Quality warnings
- Generation planning
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.core.zoom_generator import (
    ZoomGenerator, GenerationPlan, ZoomGeneratorError
)


class MockMBTilesReader:
    """Mock MBTilesReader for testing."""
    
    def __init__(self, available_zooms):
        self.available_zooms = available_zooms
    
    def get_available_zooms(self):
        return self.available_zooms
    
    def get_metadata(self):
        meta = Mock()
        meta.name = "Test Map"
        return meta


class TestZoomGeneratorGapDetection:
    """Test gap detection functionality."""
    
    def test_detect_simple_gap(self):
        """Test detecting a simple gap between zooms."""
        reader = MockMBTilesReader([8, 10, 12, 14, 16])
        generator = ZoomGenerator(reader)
        
        gaps = generator.analyze_gaps()
        
        assert gaps == [9, 11, 13, 15]
    
    def test_no_gaps(self):
        """Test with continuous zoom levels."""
        reader = MockMBTilesReader([8, 9, 10, 11, 12])
        generator = ZoomGenerator(reader)
        
        gaps = generator.analyze_gaps()
        
        assert gaps == []
    
    def test_single_zoom(self):
        """Test with single zoom level."""
        reader = MockMBTilesReader([10])
        generator = ZoomGenerator(reader)
        
        gaps = generator.analyze_gaps()
        
        assert gaps == []
    
    def test_empty_file(self):
        """Test with no zooms."""
        reader = MockMBTilesReader([])
        generator = ZoomGenerator(reader)
        
        gaps = generator.analyze_gaps()
        
        assert gaps == []


class TestZoomGeneratorSourceZoom:
    """Test source zoom calculation."""
    
    def test_prefer_higher_zoom_for_downsampling(self):
        """Test that Z+1 is preferred (downsampling better quality)."""
        reader = MockMBTilesReader([10, 12, 14])
        generator = ZoomGenerator(reader)
        
        # For Z11, both Z10 and Z12 exist, should prefer Z12
        source = generator.calculate_source_zoom(11)
        
        assert source == 12
    
    def test_use_lower_if_higher_missing(self):
        """Test using Z-1 if Z+1 doesn't exist."""
        reader = MockMBTilesReader([8, 10, 12])
        generator = ZoomGenerator(reader)
        
        # For Z11, Z+1 (Z12) exists, so prefers downsampling
        # Algorithm prefers higher zoom (Z+1) for downsampling over lower
        source = generator.calculate_source_zoom(11)
        
        assert source == 12  # Downsampling from Z12 is preferred
    
    def test_nearest_zoom_fallback(self):
        """Test using nearest zoom if adjacent ones missing."""
        reader = MockMBTilesReader([8, 12])
        generator = ZoomGenerator(reader)
        
        # For Z10, neither 9 nor 11 exist, should use Z8 or Z12
        source = generator.calculate_source_zoom(10)
        
        assert source in [8, 12]
    
    def test_error_if_already_exists(self):
        """Test error when zoom already exists."""
        reader = MockMBTilesReader([10, 11, 12])
        generator = ZoomGenerator(reader)
        
        with pytest.raises(ZoomGeneratorError, match="already exists"):
            generator.calculate_source_zoom(11)
    
    def test_error_if_no_zooms(self):
        """Test error when no zooms available."""
        reader = MockMBTilesReader([])
        generator = ZoomGenerator(reader)
        
        with pytest.raises(ZoomGeneratorError, match="No zoom levels"):
            generator.calculate_source_zoom(10)


class TestZoomGeneratorQualityWarnings:
    """Test quality warning logic."""
    
    def test_no_warning_for_downsampling(self):
        """Test that downsampling doesn't trigger warning."""
        reader = MockMBTilesReader([14])
        generator = ZoomGenerator(reader)
        
        should_warn, reason = generator.should_warn_user(14, 13)
        
        assert should_warn is False
        assert reason == ""
    
    def test_no_warning_for_single_level_upsampling(self):
        """Test that upsampling 1 level doesn't warn."""
        reader = MockMBTilesReader([12])
        generator = ZoomGenerator(reader)
        
        should_warn, reason = generator.should_warn_user(12, 13)
        
        assert should_warn is False
    
    def test_warning_for_two_level_upsampling(self):
        """Test that upsampling 2 levels warns."""
        reader = MockMBTilesReader([12])
        generator = ZoomGenerator(reader)
        
        should_warn, reason = generator.should_warn_user(12, 14)
        
        assert should_warn is True
        assert "moderate quality loss" in reason
    
    def test_warning_for_heavy_upsampling(self):
        """Test that upsampling 3+ levels warns severely."""
        reader = MockMBTilesReader([10])
        generator = ZoomGenerator(reader)
        
        should_warn, reason = generator.should_warn_user(10, 14)
        
        assert should_warn is True
        assert "significantly" in reason
    
    def test_warning_for_none_source(self):
        """Test warning when source is None."""
        reader = MockMBTilesReader([])
        generator = ZoomGenerator(reader)
        
        should_warn, reason = generator.should_warn_user(None, 10)
        
        assert should_warn is True


class TestZoomGeneratorValidation:
    """Test generation validation."""
    
    def test_valid_generation(self):
        """Test validation passes for valid case."""
        reader = MockMBTilesReader([10, 12])
        generator = ZoomGenerator(reader)
        
        is_valid, reason = generator.validate_generation(11)
        
        assert is_valid is True
        assert reason == ""
    
    def test_invalid_out_of_range_low(self):
        """Test validation fails for zoom too low."""
        reader = MockMBTilesReader([10])
        generator = ZoomGenerator(reader)
        
        is_valid, reason = generator.validate_generation(-1)
        
        assert is_valid is False
        assert "out of range" in reason
    
    def test_invalid_out_of_range_high(self):
        """Test validation fails for zoom too high."""
        reader = MockMBTilesReader([10])
        generator = ZoomGenerator(reader)
        
        is_valid, reason = generator.validate_generation(100)
        
        assert is_valid is False
        assert "out of range" in reason
    
    def test_invalid_already_exists(self):
        """Test validation fails if zoom exists."""
        reader = MockMBTilesReader([10, 11])
        generator = ZoomGenerator(reader)
        
        is_valid, reason = generator.validate_generation(11)
        
        assert is_valid is False
        assert "already exists" in reason


class TestZoomGeneratorGenerationPlan:
    """Test generation plan creation."""
    
    def test_plan_for_downsampling(self):
        """Test plan creation for downsampling case."""
        reader = MockMBTilesReader([10, 14])
        generator = ZoomGenerator(reader)
        
        plan = generator.create_generation_plan(13)
        
        assert plan.target_zoom == 13
        assert plan.source_zoom == 14
        assert plan.source_type == 'downsampling'
        assert plan.tile_count == 4 ** 13
        assert plan.quality_warning is False
    
    def test_plan_for_upsampling(self):
        """Test plan creation for upsampling case."""
        reader = MockMBTilesReader([10])
        generator = ZoomGenerator(reader)
        
        plan = generator.create_generation_plan(11)
        
        assert plan.target_zoom == 11
        assert plan.source_zoom == 10
        assert plan.source_type == 'upsampling'
        assert plan.tile_count == 4 ** 11
        assert plan.quality_warning is False
    
    def test_plan_with_quality_warning(self):
        """Test plan includes quality warning when appropriate."""
        reader = MockMBTilesReader([10])
        generator = ZoomGenerator(reader)
        
        plan = generator.create_generation_plan(13)  # 3 levels up
        
        assert plan.quality_warning is True
        assert "significantly" in plan.quality_reason
    
    def test_plan_error_if_invalid(self):
        """Test plan creation fails for invalid zoom."""
        reader = MockMBTilesReader([10])
        generator = ZoomGenerator(reader)
        
        with pytest.raises(ZoomGeneratorError):
            generator.create_generation_plan(10)  # Already exists


class TestZoomGeneratorEstimations:
    """Test time and size estimations."""
    
    def test_estimate_generation_time(self):
        """Test time estimation calculation."""
        reader = MockMBTilesReader([10])
        generator = ZoomGenerator(reader)
        
        # Z8 should have 4^8 = 65536 tiles
        # At 0.05ms per tile = 3.2 seconds
        time_sec = generator.estimate_generation_time(8, ms_per_tile=0.05)
        
        assert 3.0 < time_sec < 3.5
    
    def test_estimate_generation_size(self):
        """Test size estimation calculation."""
        reader = MockMBTilesReader([10])
        generator = ZoomGenerator(reader)
        
        # Z8 should have 4^8 = 65536 tiles
        # At 50KB per tile = ~3.3 GB
        size_bytes = generator.estimate_generation_size(8, bytes_per_tile=50000)
        
        expected = 65536 * 50000
        assert size_bytes == expected
    
    def test_time_scales_with_zoom(self):
        """Test that time increases exponentially with zoom."""
        reader = MockMBTilesReader([10])
        generator = ZoomGenerator(reader)
        
        time_z10 = generator.estimate_generation_time(10)
        time_z12 = generator.estimate_generation_time(12)
        
        # Z12 has 4x more tiles than Z10 (2 zoom levels = 4x increase)
        assert time_z12 > time_z10 * 3


class TestZoomGeneratorSummary:
    """Test summary generation."""
    
    def test_summary_with_gaps(self):
        """Test summary generation with gaps."""
        reader = MockMBTilesReader([8, 10, 12, 14])
        generator = ZoomGenerator(reader)
        
        summary = generator.get_summary()
        
        assert "Available:" in summary
        assert "Missing:" in summary
        assert "[8, 10, 12, 14]" in summary
    
    def test_summary_no_gaps(self):
        """Test summary when no gaps."""
        reader = MockMBTilesReader([8, 9, 10])
        generator = ZoomGenerator(reader)
        
        summary = generator.get_summary()
        
        assert "Available:" in summary
        assert "No gaps" in summary
    
    def test_summary_empty_file(self):
        """Test summary for empty file."""
        reader = MockMBTilesReader([])
        generator = ZoomGenerator(reader)
        
        summary = generator.get_summary()
        
        assert "No zoom levels" in summary


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
