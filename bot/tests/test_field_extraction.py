"""
Tests for field extraction logic.
Verifies that the bot correctly extracts data using config field lists.
"""

import pytest
import sys
from pathlib import Path

# Add bot directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import validate_replay
from config import (
    PLAYER_NAME_FIELDS,
    SKILL_FIELDS,
    SIGMA_FIELDS,
    TEAM_ID_FIELDS,
    START_TIME_FIELDS,
    DURATION_FIELDS,
    MAP_NAME_FIELDS,
)


class TestFieldExtraction:
    """Test field extraction from replay data"""
    
    def test_player_name_extraction(self):
        """Test that player names are extracted using field list"""
        replay = {
            "id": "test123",
            "hostSettings": {"mapname": "Test Map"},
            "AllyTeams": [
                {
                    "Players": [
                        {"name": "Player1", "teamId": 0, "skill": 20.0}  # Uses "name"
                    ]
                },
                {
                    "Players": [
                        {"Name": "Player2", "teamId": 1, "skill": 18.0}  # Uses "Name"
                    ]
                }
            ]
        }
        
        result = validate_replay(replay)
        assert result["players"][0]["name"] == "Player1"
        assert result["players"][1]["name"] == "Player2"
    
    def test_skill_extraction(self):
        """Test that skill values are extracted correctly"""
        replay = {
            "id": "test123",
            "hostSettings": {"mapname": "Test Map"},
            "AllyTeams": [
                {
                    "Players": [
                        {"name": "Player1", "teamId": 0, "skill": "[20.5]"}
                    ]
                },
                {
                    "Players": [
                        {"name": "Player2", "teamId": 1, "Skill": 18.5}  # Capital S
                    ]
                }
            ]
        }
        
        result = validate_replay(replay)
        assert result["seed_ratings"]["Player1"]["mu"] == 20.5
        assert result["seed_ratings"]["Player2"]["mu"] == 18.5
    
    def test_sigma_extraction(self):
        """Test that skill uncertainty is extracted correctly"""
        replay = {
            "id": "test123",
            "hostSettings": {"mapname": "Test Map"},
            "AllyTeams": [
                {
                    "Players": [
                        {"name": "Player1", "teamId": 0, "skill": 20.0, "skillUncertainty": 8.33}
                    ]
                },
                {
                    "Players": [
                        {"name": "Player2", "teamId": 1, "skill": 18.0, "SkillUncertainty": 7.5}  # Capital
                    ]
                }
            ]
        }
        
        result = validate_replay(replay)
        assert result["seed_ratings"]["Player1"]["sigma"] == 8.33
        assert result["seed_ratings"]["Player2"]["sigma"] == 7.5
    
    def test_team_id_extraction(self):
        """Test that team IDs are extracted correctly"""
        replay = {
            "id": "test123",
            "hostSettings": {"mapname": "Test Map"},
            "AllyTeams": [
                {
                    "Players": [
                        {"name": "Player1", "teamId": 0, "skill": 20.0}
                    ]
                },
                {
                    "Players": [
                        {"name": "Player2", "TeamId": 1, "skill": 18.0}  # Capital T
                    ]
                }
            ]
        }
        
        result = validate_replay(replay)
        # Both players should be included (teamId >= MIN_TEAM_ID)
        assert len(result["players"]) == 2
    
    def test_start_time_extraction(self):
        """Test that start time is extracted correctly"""
        test_time = "2025-11-15T14:30:00.000Z"
        replay = {
            "id": "test123",
            "startTime": test_time,
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
        
        result = validate_replay(replay)
        assert result["startTime"] == test_time
    
    def test_duration_extraction(self):
        """Test that duration is extracted correctly"""
        replay = {
            "id": "test123",
            "durationMs": 1234567,
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
        
        result = validate_replay(replay)
        assert result["duration_ms"] == 1234567
    
    def test_map_name_extraction(self):
        """Test that map name is extracted from hostSettings"""
        replay = {
            "id": "test123",
            "hostSettings": {
                "mapname": "Full Metal Plate 1.7"
            },
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
        
        result = validate_replay(replay)
        assert result["mapname"] == "Full Metal Plate 1.7"

