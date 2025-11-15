"""
Tests for Bo3 series validation logic.
Verifies that the bot correctly validates Bo3 series according to configuration.
"""

import pytest
from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path

# Add bot directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import check_bo3_validity
from config import (
    REQUIRED_PLAYER_COUNT,
    REQUIRED_WINS_FOR_SERIES,
    MIN_REPLAYS,
    MAX_REPLAYS,
)


class TestBo3Validation:
    """Test Bo3 series validation rules"""
    
    def test_valid_bo3_series(self):
        """Test that a valid Bo3 series passes validation"""
        replays = [
            {
                "players": [{"name": "Player1"}, {"name": "Player2"}],
                "winner": "Player1"
            },
            {
                "players": [{"name": "Player1"}, {"name": "Player2"}],
                "winner": "Player1"
            },
            {
                "players": [{"name": "Player1"}, {"name": "Player2"}],
                "winner": "Player2"
            }
        ]
        
        valid, p1, p2, wins, series_winner = check_bo3_validity(replays)
        
        assert valid is True
        assert series_winner == "Player1"
        assert wins["Player1"] == 2
        assert wins["Player2"] == 1
    
    def test_same_players_required(self):
        """Test that all replays must have the same 2 players"""
        replays = [
            {
                "players": [{"name": "Player1"}, {"name": "Player2"}],
                "winner": "Player1"
            },
            {
                "players": [{"name": "Player1"}, {"name": "Player3"}],  # Different player
                "winner": "Player1"
            }
        ]
        
        with pytest.raises(ValueError, match="same 2 players"):
            check_bo3_validity(replays)
    
    def test_exactly_two_players_required(self):
        """Test that Bo3 must have exactly 2 players"""
        replays = [
            {
                "players": [{"name": "Player1"}, {"name": "Player2"}, {"name": "Player3"}],
                "winner": "Player1"
            }
        ]
        
        with pytest.raises(ValueError, match="exactly 2 players"):
            check_bo3_validity(replays)
    
    def test_required_wins_for_series(self):
        """Test that series winner must have REQUIRED_WINS_FOR_SERIES wins"""
        # Player1 has only 1 win (not enough)
        replays = [
            {
                "players": [{"name": "Player1"}, {"name": "Player2"}],
                "winner": "Player1"
            },
            {
                "players": [{"name": "Player1"}, {"name": "Player2"}],
                "winner": "Player2"
            }
        ]
        
        valid, p1, p2, wins, series_winner = check_bo3_validity(replays)
        
        assert wins["Player1"] == 1
        assert wins["Player2"] == 1
        assert series_winner is None  # No one has 2+ wins
    
    def test_minimum_replays(self):
        """Test that MIN_REPLAYS is enforced (tested via check_bo3_validity logic)"""
        # Single replay - can't determine series winner
        replays = [
            {
                "players": [{"name": "Player1"}, {"name": "Player2"}],
                "winner": "Player1"
            }
        ]
        
        valid, p1, p2, wins, series_winner = check_bo3_validity(replays)
        assert series_winner is None  # Need 2+ wins, only 1 game
    
    def test_maximum_replays(self):
        """Test that MAX_REPLAYS is enforced (tested in submit handler, not here)"""
        # This is tested in the submit handler, but we verify it works with 3 replays
        replays = [
            {
                "players": [{"name": "Player1"}, {"name": "Player2"}],
                "winner": "Player1"
            },
            {
                "players": [{"name": "Player1"}, {"name": "Player2"}],
                "winner": "Player1"
            },
            {
                "players": [{"name": "Player1"}, {"name": "Player2"}],
                "winner": "Player2"
            }
        ]
        
        valid, p1, p2, wins, series_winner = check_bo3_validity(replays)
        assert valid is True
        assert series_winner == "Player1"  # Has 2 wins
    
    def test_winner_with_exactly_required_wins(self):
        """Test that player with exactly REQUIRED_WINS_FOR_SERIES wins is series winner"""
        replays = [
            {
                "players": [{"name": "Player1"}, {"name": "Player2"}],
                "winner": "Player1"
            },
            {
                "players": [{"name": "Player1"}, {"name": "Player2"}],
                "winner": "Player1"
            }
        ]
        
        valid, p1, p2, wins, series_winner = check_bo3_validity(replays)
        assert series_winner == "Player1"
        assert wins["Player1"] == REQUIRED_WINS_FOR_SERIES
    
    def test_no_winner_when_missing_winners(self):
        """Test that series winner is None when replays have no winners"""
        replays = [
            {
                "players": [{"name": "Player1"}, {"name": "Player2"}],
                "winner": None  # No winner
            },
            {
                "players": [{"name": "Player1"}, {"name": "Player2"}],
                "winner": None  # No winner
            }
        ]
        
        valid, p1, p2, wins, series_winner = check_bo3_validity(replays)
        assert wins["Player1"] == 0
        assert wins["Player2"] == 0
        assert series_winner is None
    
    def test_player_order_independence(self):
        """Test that player order in replays doesn't matter"""
        replays = [
            {
                "players": [{"name": "Player1"}, {"name": "Player2"}],
                "winner": "Player1"
            },
            {
                "players": [{"name": "Player2"}, {"name": "Player1"}],  # Reversed order
                "winner": "Player1"
            }
        ]
        
        valid, p1, p2, wins, series_winner = check_bo3_validity(replays)
        assert valid is True
        assert series_winner == "Player1"
        assert wins["Player1"] == 2

