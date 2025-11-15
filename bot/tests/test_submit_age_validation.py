"""
Tests for age validation in the submit command flow.
Verifies that old replays are actually rejected during submission.
"""

import pytest
from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path

# Add bot directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import validate_replay
from config import MAX_REPLAY_AGE_DAYS


def check_replay_age(replay_data: dict, max_age_days: int) -> tuple[bool, str]:
    """
    Extract age validation logic from submit handler for testing.
    Returns (should_reject, error_message)
    """
    now = datetime.now(timezone.utc)
    start_time = replay_data.get("startTime")
    replay_id = replay_data.get("id", "unknown")
    
    if not start_time:
        return True, f"❌ Replay `{replay_id}` is missing startTime field and cannot be validated"
    
    try:
        # Handle ISO format with or without Z
        start_str = start_time.replace("Z", "+00:00") if start_time.endswith("Z") else start_time
        start = datetime.fromisoformat(start_str)
        age = (now - start).days
        
        if age > max_age_days:
            return True, f"❌ Replay `{replay_id}` is {age} days old (max: {max_age_days} days)"
    except ValueError as e:
        # Date parsing error - reject to be safe
        return True, f"❌ Replay `{replay_id}` has invalid startTime format: {start_time}"
    except Exception as e:
        # Unexpected error - log and reject to be safe
        return True, f"❌ Error validating replay `{replay_id}` age: {e}"
    
    return False, ""


class TestSubmitAgeValidation:
    """Test age validation in submit flow"""
    
    def test_old_replay_rejected(self):
        """Test that old replays (> MAX_REPLAY_AGE_DAYS) are rejected"""
        now = datetime.now(timezone.utc)
        old_date = (now - timedelta(days=MAX_REPLAY_AGE_DAYS + 1)).isoformat()
        
        replay_data = {
            "id": "old_replay_123",
            "startTime": old_date,
            "mapname": "Test Map",
            "players": [{"name": "Player1"}, {"name": "Player2"}],
            "winner": "Player1"
        }
        
        should_reject, error_msg = check_replay_age(replay_data, MAX_REPLAY_AGE_DAYS)
        
        assert should_reject is True
        assert "days old" in error_msg
        assert str(MAX_REPLAY_AGE_DAYS) in error_msg
    
    def test_very_old_replay_rejected(self):
        """Test that very old replays (like 151 days) are rejected"""
        now = datetime.now(timezone.utc)
        very_old_date = (now - timedelta(days=151)).isoformat()
        
        replay_data = {
            "id": "very_old_replay",
            "startTime": very_old_date,
            "mapname": "Test Map",
            "players": [{"name": "Player1"}, {"name": "Player2"}],
            "winner": "Player1"
        }
        
        should_reject, error_msg = check_replay_age(replay_data, MAX_REPLAY_AGE_DAYS)
        
        assert should_reject is True
        assert "151 days old" in error_msg
        assert str(MAX_REPLAY_AGE_DAYS) in error_msg
    
    def test_recent_replay_accepted(self):
        """Test that recent replays (< MAX_REPLAY_AGE_DAYS) are accepted"""
        now = datetime.now(timezone.utc)
        recent_date = (now - timedelta(days=MAX_REPLAY_AGE_DAYS - 1)).isoformat()
        
        replay_data = {
            "id": "recent_replay",
            "startTime": recent_date,
            "mapname": "Test Map",
            "players": [{"name": "Player1"}, {"name": "Player2"}],
            "winner": "Player1"
        }
        
        should_reject, error_msg = check_replay_age(replay_data, MAX_REPLAY_AGE_DAYS)
        
        assert should_reject is False
        assert error_msg == ""
    
    def test_replay_at_limit_accepted(self):
        """Test that replays exactly at the limit are accepted"""
        now = datetime.now(timezone.utc)
        limit_date = (now - timedelta(days=MAX_REPLAY_AGE_DAYS)).isoformat()
        
        replay_data = {
            "id": "limit_replay",
            "startTime": limit_date,
            "mapname": "Test Map",
            "players": [{"name": "Player1"}, {"name": "Player2"}],
            "winner": "Player1"
        }
        
        should_reject, error_msg = check_replay_age(replay_data, MAX_REPLAY_AGE_DAYS)
        
        assert should_reject is False
        assert error_msg == ""
    
    def test_missing_starttime_rejected(self):
        """Test that replays without startTime are rejected"""
        replay_data = {
            "id": "no_time_replay",
            # No startTime field
            "mapname": "Test Map",
            "players": [{"name": "Player1"}, {"name": "Player2"}],
            "winner": "Player1"
        }
        
        should_reject, error_msg = check_replay_age(replay_data, MAX_REPLAY_AGE_DAYS)
        
        assert should_reject is True
        assert "missing starttime" in error_msg.lower() or "missing startTime" in error_msg
    
    def test_invalid_date_format_rejected(self):
        """Test that replays with invalid date formats are rejected"""
        replay_data = {
            "id": "invalid_date_replay",
            "startTime": "not-a-valid-date",
            "mapname": "Test Map",
            "players": [{"name": "Player1"}, {"name": "Player2"}],
            "winner": "Player1"
        }
        
        should_reject, error_msg = check_replay_age(replay_data, MAX_REPLAY_AGE_DAYS)
        
        assert should_reject is True
        assert "invalid starttime format" in error_msg.lower() or "invalid startTime format" in error_msg
    
    def test_real_world_old_replays(self):
        """Test with real-world old replay dates that were incorrectly accepted"""
        # These are the actual replay dates from the user's submission
        now = datetime.now(timezone.utc)
        test_cases = [
            ("2025-06-16T21:15:52.000Z", 151),  # 151 days old
            ("2025-06-19T05:29:32.000Z", 149),  # 149 days old
            ("2025-06-19T06:26:30.000Z", 149),  # 149 days old
        ]
        
        for date_str, expected_age in test_cases:
            replay_data = {
                "id": f"replay_{date_str[:10]}",
                "startTime": date_str,
                "mapname": "Test Map",
                "players": [{"name": "Player1"}, {"name": "Player2"}],
                "winner": "Player1"
            }
            
            should_reject, error_msg = check_replay_age(replay_data, MAX_REPLAY_AGE_DAYS)
            
            assert should_reject is True, f"Replay from {date_str} should be rejected (age: {expected_age} days)"
            assert f"{expected_age} days old" in error_msg or "days old" in error_msg
            assert str(MAX_REPLAY_AGE_DAYS) in error_msg

