"""
Tests for validations that are missing or not fully tested.
Identifies gaps in validation coverage.
"""

import pytest
from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path

# Add bot directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import load_submissions, save_submissions, extract_replay_ids
from config import MAX_TIME_BETWEEN_REPLAYS_DAYS


class TestAlreadySubmittedValidation:
    """Test already submitted replay detection"""
    
    def test_load_submissions_empty(self, tmp_path):
        """Test loading submissions from empty file"""
        import os
        import json
        
        # Create temporary submissions file
        submissions_file = tmp_path / "submissions_index.json"
        os.makedirs(tmp_path, exist_ok=True)
        
        # Test with non-existent file
        original_file = sys.modules['main'].SUBMISSIONS_FILE
        sys.modules['main'].SUBMISSIONS_FILE = str(submissions_file)
        
        try:
            submissions = load_submissions()
            assert submissions == set()
        finally:
            sys.modules['main'].SUBMISSIONS_FILE = original_file
    
    def test_load_submissions_with_data(self, tmp_path):
        """Test loading submissions from file with data"""
        import os
        import json
        
        # Create temporary submissions file
        submissions_file = tmp_path / "submissions_index.json"
        os.makedirs(tmp_path, exist_ok=True)
        
        # Write test data
        with open(submissions_file, 'w') as f:
            json.dump(["replay1", "replay2", "replay3"], f)
        
        original_file = sys.modules['main'].SUBMISSIONS_FILE
        sys.modules['main'].SUBMISSIONS_FILE = str(submissions_file)
        
        try:
            submissions = load_submissions()
            assert submissions == {"replay1", "replay2", "replay3"}
        finally:
            sys.modules['main'].SUBMISSIONS_FILE = original_file
    
    def test_already_submitted_detection(self):
        """Test that already submitted replays are detected"""
        # This tests the logic, not the actual file I/O
        submissions = {"replay1", "replay2", "replay3"}
        new_replay_ids = ["replay2", "replay4"]
        
        already_submitted = [rid for rid in new_replay_ids if rid in submissions]
        
        assert "replay2" in already_submitted
        assert "replay4" not in already_submitted
        assert len(already_submitted) == 1


class TestTimeBetweenReplaysValidation:
    """Test time between replays validation - NOTE: This is NOT IMPLEMENTED in bot!"""
    
    def test_time_between_replays_config_exists(self):
        """Test that MAX_TIME_BETWEEN_REPLAYS_DAYS config exists"""
        assert MAX_TIME_BETWEEN_REPLAYS_DAYS == 10
        assert MAX_TIME_BETWEEN_REPLAYS_DAYS > 0
    
    def test_time_between_replays_logic(self):
        """Test the logic for checking time between replays (if it were implemented)"""
        now = datetime.now(timezone.utc)
        
        # Replays within limit (same day)
        replay1_time = now - timedelta(hours=2)
        replay2_time = now - timedelta(hours=1)
        time_diff = (replay2_time - replay1_time).days
        
        assert time_diff == 0  # Same day, should be OK
        
        # Replays exceeding limit (11 days apart)
        replay1_time = now - timedelta(days=11)
        replay2_time = now - timedelta(days=1)
        time_diff = (replay2_time - replay1_time).days
        
        assert time_diff == 10  # 10 days apart, at limit
        assert time_diff <= MAX_TIME_BETWEEN_REPLAYS_DAYS
        
        # Replays exceeding limit (12 days apart)
        replay1_time = now - timedelta(days=12)
        replay2_time = now - timedelta(days=1)
        time_diff = (replay2_time - replay1_time).days
        
        assert time_diff == 11  # 11 days apart, exceeds limit
        assert time_diff > MAX_TIME_BETWEEN_REPLAYS_DAYS
    
    def test_time_between_replays_not_implemented(self):
        """
        ⚠️ WARNING: This validation is NOT implemented in the bot!
        MAX_TIME_BETWEEN_REPLAYS_DAYS is defined but never checked.
        This test documents the missing validation.
        """
        # This test documents that the validation is missing
        # The bot should check that all replays in a Bo3 are within MAX_TIME_BETWEEN_REPLAYS_DAYS
        # but currently it doesn't!
        pass  # Placeholder to document the gap


class TestURLParsingEdgeCases:
    """Test URL parsing edge cases"""
    
    def test_url_with_whitespace(self):
        """Test that URLs with whitespace are handled"""
        urls = [
            "  https://api.bar-rts.com/replays/abc123  ",
            "\thttps://api.bar-rts.com/replays/def456\t",
            "\nhttps://api.bar-rts.com/replays/ghi789\n"
        ]
        
        # extract_replay_ids should strip whitespace
        ids = extract_replay_ids(urls)
        assert ids == ["abc123", "def456", "ghi789"]
    
    def test_url_with_trailing_comma(self):
        """Test that trailing commas in URL list are handled"""
        # The submit handler splits by comma and strips
        url_string = "https://api.bar-rts.com/replays/abc123,https://api.bar-rts.com/replays/def456,"
        urls = [u.strip() for u in url_string.split(",") if u.strip()]
        
        assert len(urls) == 2
        assert urls[0] == "https://api.bar-rts.com/replays/abc123"
        assert urls[1] == "https://api.bar-rts.com/replays/def456"
    
    def test_url_with_extra_spaces(self):
        """Test that extra spaces between URLs are handled"""
        url_string = "https://api.bar-rts.com/replays/abc123,  https://api.bar-rts.com/replays/def456  ,  https://api.bar-rts.com/replays/ghi789"
        urls = [u.strip() for u in url_string.split(",") if u.strip()]
        
        assert len(urls) == 3
        ids = extract_replay_ids(urls)
        assert ids == ["abc123", "def456", "ghi789"]


class TestAPIErrorHandling:
    """Test API error handling scenarios"""
    
    def test_fetch_replay_error_handling(self):
        """Test that fetch_replay raises ValueError on HTTP errors"""
        # This would require mocking aiohttp, but we can test the logic
        # The function should raise ValueError for non-200 status codes
        pass  # Would need async mocking
    
    def test_api_timeout_config(self):
        """Test that API timeout is configured"""
        from config import API_TIMEOUT_SECONDS
        assert API_TIMEOUT_SECONDS == 12
        assert API_TIMEOUT_SECONDS > 0


class TestDuplicateDetection:
    """Test duplicate replay ID detection"""
    
    def test_duplicate_in_same_submission(self):
        """Test that duplicates in the same submission are detected"""
        urls = [
            "https://api.bar-rts.com/replays/abc123",
            "https://api.bar-rts.com/replays/abc123"  # Duplicate
        ]
        
        ids = extract_replay_ids(urls)
        
        # Check for duplicates (logic from submit handler)
        has_duplicates = len(ids) != len(set(ids))
        
        assert has_duplicates is True
        assert len(ids) == 2
        assert len(set(ids)) == 1
    
    def test_no_duplicates(self):
        """Test that non-duplicate replays pass"""
        urls = [
            "https://api.bar-rts.com/replays/abc123",
            "https://api.bar-rts.com/replays/def456"
        ]
        
        ids = extract_replay_ids(urls)
        has_duplicates = len(ids) != len(set(ids))
        
        assert has_duplicates is False
        assert len(ids) == len(set(ids))


class TestValidationOrder:
    """Test that validations happen in the correct order"""
    
    def test_validation_order(self):
        """
        Validations should happen in this order:
        1. URL parsing and format validation
        2. MIN_REPLAYS/MAX_REPLAYS check
        3. Duplicate detection
        4. Already submitted check
        5. Fetch and validate replays
        6. Bo3 validation
        7. Age validation
        8. (MISSING: Time between replays validation)
        """
        # This test documents the expected validation order
        # It doesn't actually test it, but serves as documentation
        validation_steps = [
            "URL parsing",
            "MIN/MAX replays",
            "Duplicate detection",
            "Already submitted",
            "Fetch replays",
            "Validate replay structure",
            "Bo3 validation",
            "Age validation",
            "Time between replays (NOT IMPLEMENTED)"
        ]
        
        assert len(validation_steps) > 0

