"""
Tests for replay validation logic.
Verifies that the bot correctly validates replay data according to configuration.
"""

import pytest
from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path

# Add bot directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import validate_replay, extract_replay_ids
from config import (
    REQUIRED_PLAYER_COUNT,
    MIN_TEAM_ID,
    MAX_REPLAY_AGE_DAYS,
    REPLAY_URL_PATTERN,
    DEFAULT_SIGMA,
)


class TestReplayValidation:
    """Test replay validation rules"""
    
    def test_valid_replay_structure(self):
        """Test that a valid replay structure passes validation"""
        replay = {
            "id": "test123",
            "startTime": datetime.now(timezone.utc).isoformat(),
            "durationMs": 1000000,
            "hostSettings": {
                "mapname": "Test Map"
            },
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
        
        assert result["id"] == "test123"
        assert len(result["players"]) == REQUIRED_PLAYER_COUNT
        assert result["winner"] == "Player1"
        assert "Player1" in result["seed_ratings"]
        assert "Player2" in result["seed_ratings"]
    
    def test_exactly_two_players_required(self):
        """Test that replay must have exactly 2 players"""
        # Too few players
        replay_few = {
            "id": "test123",
            "hostSettings": {"mapname": "Test Map"},
            "AllyTeams": [
                {
                    "Players": [
                        {"name": "Player1", "teamId": 0, "skill": 20.0}
                    ]
                }
            ]
        }
        
        with pytest.raises(ValueError, match="exactly 2 players"):
            validate_replay(replay_few)
        
        # Too many players
        replay_many = {
            "id": "test123",
            "hostSettings": {"mapname": "Test Map"},
            "AllyTeams": [
                {
                    "Players": [
                        {"name": "Player1", "teamId": 0, "skill": 20.0},
                        {"name": "Player2", "teamId": 1, "skill": 18.0},
                        {"name": "Player3", "teamId": 2, "skill": 19.0}
                    ]
                }
            ]
        }
        
        with pytest.raises(ValueError, match="exactly 2 players"):
            validate_replay(replay_many)
    
    def test_spectators_excluded(self):
        """Test that spectators (teamId < MIN_TEAM_ID) are excluded"""
        replay = {
            "id": "test123",
            "hostSettings": {"mapname": "Test Map"},
            "AllyTeams": [
                {
                    "Players": [
                        {"name": "Player1", "teamId": 0, "skill": 20.0},
                        {"name": "Spectator", "teamId": -1, "skill": 0.0}  # Spectator (excluded)
                    ]
                },
                {
                    "Players": [
                        {"name": "Player2", "teamId": 1, "skill": 18.0}
                    ]
                }
            ]
        }
        
        result = validate_replay(replay)
        assert len(result["players"]) == 2
        player_names = [p["name"] for p in result["players"]]
        assert "Spectator" not in player_names
        assert "Player1" in player_names
        assert "Player2" in player_names
    
    def test_skill_parsing(self):
        """Test that skill values are parsed correctly"""
        replay = {
            "id": "test123",
            "hostSettings": {"mapname": "Test Map"},
            "AllyTeams": [
                {
                    "Players": [
                        {"name": "Player1", "teamId": 0, "skill": "[16.67]", "skillUncertainty": 8.33}
                    ]
                },
                {
                    "Players": [
                        {"name": "Player2", "teamId": 1, "skill": 18.5, "skillUncertainty": 8.33}
                    ]
                }
            ]
        }
        
        result = validate_replay(replay)
        assert result["seed_ratings"]["Player1"]["mu"] == 16.67
        assert result["seed_ratings"]["Player2"]["mu"] == 18.5
    
    def test_default_sigma_when_zero(self):
        """Test that default sigma is used when skillUncertainty is 0"""
        replay = {
            "id": "test123",
            "hostSettings": {"mapname": "Test Map"},
            "AllyTeams": [
                {
                    "Players": [
                        {"name": "Player1", "teamId": 0, "skill": 20.0, "skillUncertainty": 0}
                    ],
                    "winningTeam": True
                },
                {
                    "Players": [
                        {"name": "Player2", "teamId": 1, "skill": 18.0, "skillUncertainty": 0}
                    ],
                    "winningTeam": False
                }
            ]
        }
        
        result = validate_replay(replay)
        assert result["seed_ratings"]["Player1"]["sigma"] == DEFAULT_SIGMA
        assert result["seed_ratings"]["Player2"]["sigma"] == DEFAULT_SIGMA
    
    def test_winner_detection_from_gamestats(self):
        """Test winner detection from gamestats.winningTeamId"""
        replay = {
            "id": "test123",
            "hostSettings": {"mapname": "Test Map"},
            "gamestats": {
                "winningTeamId": 0
            },
            "AllyTeams": [
                {
                    "Players": [
                        {"name": "Player1", "teamId": 0, "skill": 20.0}
                    ],
                    "winningTeam": False  # Should use gamestats instead
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
        assert result["winner"] == "Player1"
    
    def test_winner_detection_gamestats_none_fallback(self):
        """Test that when gamestats.winningTeamId is None, fallback to AllyTeams"""
        replay = {
            "id": "test123",
            "hostSettings": {"mapname": "Test Map"},
            "gamestats": {
                "winningTeamId": None  # API sometimes returns None
            },
            "AllyTeams": [
                {
                    "Players": [
                        {"name": "Player1", "teamId": 0, "skill": 20.0}
                    ],
                    "winningTeam": True  # Should use this fallback
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
        assert result["winner"] == "Player1"
    
    def test_winner_detection_from_allyteams_fallback(self):
        """Test winner detection fallback to AllyTeams[].winningTeam"""
        replay = {
            "id": "test123",
            "hostSettings": {"mapname": "Test Map"},
            "gamestats": {},  # No winningTeamId
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
        assert result["winner"] == "Player1"
    
    def test_no_winner_when_both_false(self):
        """Test that winner is None when both teams have winningTeam=False and no gamestats"""
        replay = {
            "id": "test123",
            "hostSettings": {"mapname": "Test Map"},
            "AllyTeams": [
                {
                    "Players": [
                        {"name": "Player1", "teamId": 0, "skill": 20.0}
                    ],
                    "winningTeam": False
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
        assert result["winner"] is None
    
    def test_missing_start_time_handled(self):
        """Test that missing startTime is handled (validation extracts it, age check happens in submit)"""
        replay = {
            "id": "test123",
            "hostSettings": {"mapname": "Test Map"},
            # No startTime field
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
        # validate_replay extracts startTime (empty string if missing)
        # Age check happens in submit handler
        assert result["startTime"] == ""


class TestReplayAgeValidation:
    """Test replay age validation"""
    
    def test_recent_replay_passes(self):
        """Test that recent replays pass age validation"""
        now = datetime.now(timezone.utc)
        recent_date = (now - timedelta(days=5)).isoformat()
        
        replay = {
            "id": "test123",
            "startTime": recent_date,
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
        assert result["startTime"] == recent_date
    
    def test_old_replay_structure(self):
        """Test that old replays have correct startTime in structure"""
        now = datetime.now(timezone.utc)
        old_date = (now - timedelta(days=50)).isoformat()
        
        replay = {
            "id": "test123",
            "startTime": old_date,
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
        # Validation should extract the date (age check happens in submit handler)
        assert result["startTime"] == old_date


class TestURLValidation:
    """Test URL validation and extraction"""
    
    def test_valid_replay_urls(self):
        """Test that valid replay URLs are extracted correctly"""
        urls = [
            "https://api.bar-rts.com/replays/abc123",
            "http://api.bar-rts.com/replays/def456"
        ]
        
        ids = extract_replay_ids(urls)
        assert ids == ["abc123", "def456"]
    
    def test_invalid_replay_url_format(self):
        """Test that invalid URL formats raise ValueError"""
        invalid_urls = [
            "https://bar-rts.com/replays/abc123",  # Wrong domain
            "https://api.bar-rts.com/abc123",  # Missing /replays/
            "not-a-url",
            "https://api.bar-rts.com/replays/",  # No ID
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValueError, match="Invalid replay URL"):
                extract_replay_ids([url])
    
    def test_url_pattern_matches(self):
        """Test that REPLAY_URL_PATTERN matches correct URLs"""
        valid_urls = [
            "https://api.bar-rts.com/replays/abc123",
            "http://api.bar-rts.com/replays/ABC123",
            "https://api.bar-rts.com/replays/123abc456"
        ]
        
        for url in valid_urls:
            assert REPLAY_URL_PATTERN.match(url) is not None
        
        invalid_urls = [
            "https://bar-rts.com/replays/abc123",
            "https://api.bar-rts.com/abc123",
            "not-a-url"
        ]
        
        for url in invalid_urls:
            assert REPLAY_URL_PATTERN.match(url) is None

