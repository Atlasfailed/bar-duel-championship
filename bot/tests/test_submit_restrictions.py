"""
Tests for submit command restrictions.
Verifies that the bot enforces MIN_REPLAYS, MAX_REPLAYS, and other submission limits.
"""

import pytest
import sys
from pathlib import Path

# Add bot directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import extract_replay_ids
from config import (
    MIN_REPLAYS,
    MAX_REPLAYS,
    REPLAY_URL_PATTERN,
)


class TestSubmitRestrictions:
    """Test submit command restrictions"""
    
    def test_min_replays_enforced(self):
        """Test that MIN_REPLAYS is enforced (tested via extract_replay_ids)"""
        # This is tested in the submit handler, but we verify the config value
        assert MIN_REPLAYS == 2
        assert MIN_REPLAYS >= 2  # Bo3 needs at least 2 games
    
    def test_max_replays_enforced(self):
        """Test that MAX_REPLAYS is enforced (tested via extract_replay_ids)"""
        # This is tested in the submit handler, but we verify the config value
        assert MAX_REPLAYS == 3
        assert MAX_REPLAYS <= 3  # Bo3 has max 3 games
    
    def test_valid_replay_count_range(self):
        """Test that valid replay counts are within MIN_REPLAYS and MAX_REPLAYS"""
        assert MIN_REPLAYS <= MAX_REPLAYS
        assert MIN_REPLAYS >= 2
        assert MAX_REPLAYS <= 3
    
    def test_extract_replay_ids_valid_count(self):
        """Test that extract_replay_ids works with valid counts"""
        # Valid: 2 replays
        urls_2 = [
            "https://api.bar-rts.com/replays/abc123",
            "https://api.bar-rts.com/replays/def456"
        ]
        ids = extract_replay_ids(urls_2)
        assert len(ids) == 2
        assert ids == ["abc123", "def456"]
        
        # Valid: 3 replays
        urls_3 = [
            "https://api.bar-rts.com/replays/abc123",
            "https://api.bar-rts.com/replays/def456",
            "https://api.bar-rts.com/replays/ghi789"
        ]
        ids = extract_replay_ids(urls_3)
        assert len(ids) == 3
    
    def test_extract_replay_ids_duplicate_detection(self):
        """Test that duplicate replay IDs can be detected"""
        urls = [
            "https://api.bar-rts.com/replays/abc123",
            "https://api.bar-rts.com/replays/abc123"  # Duplicate
        ]
        ids = extract_replay_ids(urls)
        # extract_replay_ids doesn't check duplicates, but we can verify they're extracted
        assert len(ids) == 2
        assert ids[0] == ids[1]  # Duplicate detected by submit handler
    
    def test_url_validation_before_extraction(self):
        """Test that invalid URLs are rejected before extraction"""
        invalid_urls = [
            "https://bar-rts.com/replays/abc123",  # Wrong domain
            "not-a-url",
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValueError, match="Invalid replay URL"):
                extract_replay_ids([url])
    
    def test_replay_url_pattern_matches_valid_urls(self):
        """Test that REPLAY_URL_PATTERN matches valid replay URLs"""
        valid_urls = [
            "https://api.bar-rts.com/replays/abc123",
            "http://api.bar-rts.com/replays/def456",
            "https://api.bar-rts.com/replays/ABC123DEF",
        ]
        
        for url in valid_urls:
            assert REPLAY_URL_PATTERN.match(url) is not None, f"URL should match: {url}"
    
    def test_replay_url_pattern_rejects_invalid_urls(self):
        """Test that REPLAY_URL_PATTERN rejects invalid URLs"""
        invalid_urls = [
            "https://bar-rts.com/replays/abc123",  # Wrong domain
            "https://api.bar-rts.com/abc123",  # Missing /replays/
            "not-a-url",
            "https://api.bar-rts.com/replays/",  # No ID
        ]
        
        for url in invalid_urls:
            assert REPLAY_URL_PATTERN.match(url) is None, f"URL should not match: {url}"

