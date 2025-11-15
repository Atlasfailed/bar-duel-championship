"""
Pytest configuration and shared fixtures for bot tests.
"""

import pytest
from datetime import datetime, timezone


@pytest.fixture
def sample_replay():
    """Create a sample valid replay for testing"""
    return {
        "id": "test_replay_123",
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


@pytest.fixture
def sample_bo3_replays():
    """Create sample Bo3 replays for testing"""
    return [
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

