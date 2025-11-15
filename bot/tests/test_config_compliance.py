"""
Tests to verify bot follows all configuration rules and restrictions.
Ensures the bot enforces all limits and validations from config.py.
"""

import pytest
import sys
from pathlib import Path

# Add bot directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    REQUIRED_PLAYER_COUNT,
    MIN_REPLAYS,
    MAX_REPLAYS,
    REQUIRED_WINS_FOR_SERIES,
    MAX_REPLAY_AGE_DAYS,
    MAX_TIME_BETWEEN_REPLAYS_DAYS,
    MIN_TEAM_ID,
    DEFAULT_SIGMA,
    API_TIMEOUT_SECONDS,
)


class TestConfigCompliance:
    """Test that bot configuration values are correct and enforced"""
    
    def test_required_player_count(self):
        """Verify REQUIRED_PLAYER_COUNT is 2"""
        assert REQUIRED_PLAYER_COUNT == 2
    
    def test_min_replays(self):
        """Verify MIN_REPLAYS is 2"""
        assert MIN_REPLAYS == 2
    
    def test_max_replays(self):
        """Verify MAX_REPLAYS is 3"""
        assert MAX_REPLAYS == 3
    
    def test_required_wins_for_series(self):
        """Verify REQUIRED_WINS_FOR_SERIES is 2"""
        assert REQUIRED_WINS_FOR_SERIES == 2
    
    def test_max_replay_age_days(self):
        """Verify MAX_REPLAY_AGE_DAYS is set correctly"""
        assert MAX_REPLAY_AGE_DAYS == 40
        assert MAX_REPLAY_AGE_DAYS > 0
    
    def test_max_time_between_replays(self):
        """Verify MAX_TIME_BETWEEN_REPLAYS_DAYS is set correctly"""
        assert MAX_TIME_BETWEEN_REPLAYS_DAYS == 10
        assert MAX_TIME_BETWEEN_REPLAYS_DAYS > 0
    
    def test_min_team_id(self):
        """Verify MIN_TEAM_ID is 0 (excludes negative team IDs like spectators)"""
        assert MIN_TEAM_ID == 0
    
    def test_default_sigma(self):
        """Verify DEFAULT_SIGMA is set correctly"""
        assert DEFAULT_SIGMA == 8.333
        assert DEFAULT_SIGMA > 0
    
    def test_api_timeout(self):
        """Verify API_TIMEOUT_SECONDS is reasonable"""
        assert API_TIMEOUT_SECONDS == 12
        assert API_TIMEOUT_SECONDS > 0
        assert API_TIMEOUT_SECONDS <= 60  # Shouldn't be too long
    
    def test_replay_count_limits_are_valid(self):
        """Verify MIN_REPLAYS <= MAX_REPLAYS"""
        assert MIN_REPLAYS <= MAX_REPLAYS
        assert MIN_REPLAYS >= 2  # Bo3 needs at least 2 games
        assert MAX_REPLAYS <= 3  # Bo3 has max 3 games
    
    def test_required_wins_makes_sense(self):
        """Verify REQUIRED_WINS_FOR_SERIES is reasonable for Bo3"""
        assert REQUIRED_WINS_FOR_SERIES == 2
        assert REQUIRED_WINS_FOR_SERIES <= MAX_REPLAYS
        assert REQUIRED_WINS_FOR_SERIES > MIN_REPLAYS / 2  # Should be majority

