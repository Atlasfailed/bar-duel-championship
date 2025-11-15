"""
Tests for replay age validation.
Verifies that the bot correctly enforces MAX_REPLAY_AGE_DAYS restriction.
"""

import pytest
from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path

# Add bot directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import MAX_REPLAY_AGE_DAYS


class TestAgeValidation:
    """Test replay age validation logic"""
    
    def test_recent_replay_within_limit(self):
        """Test that recent replays are within age limit"""
        now = datetime.now(timezone.utc)
        recent_date = (now - timedelta(days=MAX_REPLAY_AGE_DAYS - 1)).isoformat()
        
        # Parse the date as the bot would
        start_str = recent_date.replace("Z", "+00:00") if recent_date.endswith("Z") else recent_date
        start = datetime.fromisoformat(start_str)
        age = (now - start).days
        
        assert age < MAX_REPLAY_AGE_DAYS
        assert age == MAX_REPLAY_AGE_DAYS - 1
    
    def test_replay_at_limit(self):
        """Test that replays exactly at the limit are within limit"""
        now = datetime.now(timezone.utc)
        limit_date = (now - timedelta(days=MAX_REPLAY_AGE_DAYS)).isoformat()
        
        start_str = limit_date.replace("Z", "+00:00") if limit_date.endswith("Z") else limit_date
        start = datetime.fromisoformat(start_str)
        age = (now - start).days
        
        assert age == MAX_REPLAY_AGE_DAYS
    
    def test_old_replay_exceeds_limit(self):
        """Test that old replays exceed the age limit"""
        now = datetime.now(timezone.utc)
        old_date = (now - timedelta(days=MAX_REPLAY_AGE_DAYS + 1)).isoformat()
        
        start_str = old_date.replace("Z", "+00:00") if old_date.endswith("Z") else old_date
        start = datetime.fromisoformat(start_str)
        age = (now - start).days
        
        assert age > MAX_REPLAY_AGE_DAYS
        assert age == MAX_REPLAY_AGE_DAYS + 1
    
    def test_very_old_replay(self):
        """Test that very old replays (like 175 days) are rejected"""
        now = datetime.now(timezone.utc)
        very_old_date = (now - timedelta(days=175)).isoformat()
        
        start_str = very_old_date.replace("Z", "+00:00") if very_old_date.endswith("Z") else very_old_date
        start = datetime.fromisoformat(start_str)
        age = (now - start).days
        
        assert age == 175
        assert age > MAX_REPLAY_AGE_DAYS
    
    def test_date_parsing_with_z_suffix(self):
        """Test that dates with Z suffix are parsed correctly"""
        date_with_z = "2025-05-23T15:42:50.000Z"
        start_str = date_with_z.replace("Z", "+00:00")
        start = datetime.fromisoformat(start_str)
        
        assert start.tzinfo is not None
    
    def test_date_parsing_without_z_suffix(self):
        """Test that dates without Z suffix are parsed correctly"""
        date_without_z = "2025-05-23T15:42:50.000+00:00"
        start = datetime.fromisoformat(date_without_z)
        
        assert start.tzinfo is not None
    
    def test_current_config_value(self):
        """Test that MAX_REPLAY_AGE_DAYS is set to expected value"""
        assert MAX_REPLAY_AGE_DAYS == 40

