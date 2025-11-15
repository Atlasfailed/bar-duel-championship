"""
Integration tests using real-like replay structures.
Tests the full validation flow with realistic data.
"""

import pytest
from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path

# Add bot directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import validate_replay, check_bo3_validity
from config import (
    REQUIRED_PLAYER_COUNT,
    REQUIRED_WINS_FOR_SERIES,
    MAX_REPLAY_AGE_DAYS,
)


class TestIntegration:
    """Integration tests with realistic replay data"""
    
    def test_full_validation_flow_realistic(self):
        """Test full validation flow with realistic replay structure"""
        # Based on examples/replay-example.json structure
        now = datetime.now(timezone.utc)
        recent_date = (now - timedelta(days=5)).isoformat()
        
        replay = {
            "id": "9b001768e1e004286a06b7de3bea6fce",
            "startTime": recent_date,
            "durationMs": 13477101,
            "hostSettings": {
                "mapname": "Omega Valley V1.01"
            },
            "gamestats": {
                "winningTeamId": 0
            },
            "AllyTeams": [
                {
                    "allyTeamId": 0,
                    "winningTeam": True,
                    "Players": [
                        {
                            "name": "FailedLight",
                            "teamId": 0,
                            "skill": "[17.12]",
                            "skillUncertainty": 8.06
                        }
                    ]
                },
                {
                    "allyTeamId": 1,
                    "winningTeam": False,
                    "Players": [
                        {
                            "name": "DocStudios",
                            "teamId": 1,
                            "skill": "[14.8]",
                            "skillUncertainty": 8.18
                        }
                    ]
                }
            ]
        }
        
        result = validate_replay(replay)
        
        # Verify all fields are extracted correctly
        assert result["id"] == "9b001768e1e004286a06b7de3bea6fce"
        assert result["mapname"] == "Omega Valley V1.01"
        assert len(result["players"]) == REQUIRED_PLAYER_COUNT
        assert result["winner"] == "FailedLight"
        assert result["duration_ms"] == 13477101
        assert result["startTime"] == recent_date
        
        # Verify seed ratings
        assert "FailedLight" in result["seed_ratings"]
        assert "DocStudios" in result["seed_ratings"]
        assert result["seed_ratings"]["FailedLight"]["mu"] == 17.12
        assert result["seed_ratings"]["DocStudios"]["mu"] == 14.8
        assert result["seed_ratings"]["FailedLight"]["sigma"] == 8.06
        assert result["seed_ratings"]["DocStudios"]["sigma"] == 8.18
    
    def test_bo3_series_realistic(self):
        """Test Bo3 validation with realistic series"""
        now = datetime.now(timezone.utc)
        recent_date = (now - timedelta(days=5)).isoformat()
        
        # Create 3 replays for a Bo3 series
        replays = []
        for i in range(3):
            replay = {
                "id": f"replay_{i}",
                "startTime": recent_date,
                "hostSettings": {"mapname": "Test Map"},
                "AllyTeams": [
                    {
                        "Players": [
                            {
                                "name": "Player1",
                                "teamId": 0,
                                "skill": 20.0,
                                "skillUncertainty": 8.33
                            }
                        ],
                        "winningTeam": (i < 2)  # Player1 wins first 2 games
                    },
                    {
                        "Players": [
                            {
                                "name": "Player2",
                                "teamId": 1,
                                "skill": 18.0,
                                "skillUncertainty": 8.33
                            }
                        ],
                        "winningTeam": (i >= 2)  # Player2 wins 3rd game
                    }
                ]
            }
            validated = validate_replay(replay)
            replays.append(validated)
        
        # Check Bo3 validity
        valid, p1, p2, wins, series_winner = check_bo3_validity(replays)
        
        assert valid is True
        assert series_winner == "Player1"
        assert wins["Player1"] == 2
        assert wins["Player2"] == 1
        assert wins["Player1"] >= REQUIRED_WINS_FOR_SERIES
    
    def test_old_replay_rejected(self):
        """Test that old replays are properly structured for age rejection"""
        now = datetime.now(timezone.utc)
        old_date = (now - timedelta(days=MAX_REPLAY_AGE_DAYS + 10)).isoformat()
        
        replay = {
            "id": "old_replay",
            "startTime": old_date,  # Too old
            "hostSettings": {"mapname": "Test Map"},
            "AllyTeams": [
                {
                    "Players": [
                        {"name": "Player1", "teamId": 0, "skill": 20.0}
                    ],
                    "winningTeam": True
                },
                {
                    "Players": [
                        {"name": "Player2", "teamId": 1, "skill": 18.0}
                    ],
                    "winningTeam": False
                }
            ]
        }
        
        # validate_replay extracts the date (age check happens in submit handler)
        result = validate_replay(replay)
        assert result["startTime"] == old_date
        
        # Verify age calculation would reject it
        start_str = old_date.replace("Z", "+00:00") if old_date.endswith("Z") else old_date
        start = datetime.fromisoformat(start_str)
        age = (now - start).days
        assert age > MAX_REPLAY_AGE_DAYS
    
    def test_spectator_exclusion_realistic(self):
        """Test spectator exclusion with realistic structure"""
        replay = {
            "id": "test123",
            "hostSettings": {"mapname": "Test Map"},
            "AllyTeams": [
                {
                    "Players": [
                        {
                            "name": "Player1",
                            "teamId": 0,
                            "skill": 20.0,
                            "skillUncertainty": 8.33
                        },
                        {
                            "name": "SpectatorUser",
                            "teamId": -1,  # Spectator (excluded)
                            "skill": 0.0,
                            "skillUncertainty": 0.0
                        }
                    ],
                    "winningTeam": True
                },
                {
                    "Players": [
                        {
                            "name": "Player2",
                            "teamId": 1,
                            "skill": 18.0,
                            "skillUncertainty": 8.33
                        }
                    ],
                    "winningTeam": False
                }
            ]
        }
        
        result = validate_replay(replay)
        
        # Should only have 2 players (spectator excluded)
        assert len(result["players"]) == REQUIRED_PLAYER_COUNT
        player_names = [p["name"] for p in result["players"]]
        assert "SpectatorUser" not in player_names
        assert "Player1" in player_names
        assert "Player2" in player_names

