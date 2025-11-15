"""
Bot verification configuration for replay submissions.
Defines validation rules and limits for replay file submissions.
"""

import re

# ==============================
# Replay URL Validation
# ==============================

# Pattern for valid BAR replay URLs
REPLAY_URL_PATTERN = re.compile(r"https?://api\.bar-rts\.com/replays/([A-Za-z0-9]+)$")

# ==============================
# Replay Validation Rules
# ==============================

# Required number of players per replay
REQUIRED_PLAYER_COUNT = 2

# Team size (players per team)
TEAM_SIZE = 1

# Valid team ID range (exclude spectators and invalid IDs)
MIN_TEAM_ID = 0

# Default OpenSkill sigma if missing or zero
DEFAULT_SIGMA = 8.333  # OpenSkill default uncertainty

# ==============================
# Bo3 Series Validation Rules
# ==============================

# Minimum number of replays in a Bo3 submission
MIN_REPLAYS = 2

# Maximum number of replays in a Bo3 submission
MAX_REPLAYS = 3

# Required wins to determine series winner
REQUIRED_WINS_FOR_SERIES = 2

# ==============================
# Replay Age Limits
# ==============================

# Maximum age of replay in days (default: 30 days)
MAX_REPLAY_AGE_DAYS = 40

# Maximum time between replays in days (default: 1 day)
MAX_TIME_BETWEEN_REPLAYS_DAYS = 10

# ==============================
# API Request Settings
# ==============================

# Timeout for API requests in seconds
API_TIMEOUT_SECONDS = 12

# ==============================
# Player Data Extraction
# ==============================

# Field names to check for player name (in order of preference)
PLAYER_NAME_FIELDS = ["name", "Name"]

# Field names to check for skill/mu (in order of preference)
SKILL_FIELDS = ["skill", "Skill"]

# Field names to check for skill uncertainty/sigma (in order of preference)
SIGMA_FIELDS = ["skillUncertainty", "SkillUncertainty"]

# Field names to check for team ID (in order of preference)
TEAM_ID_FIELDS = ["teamId", "TeamId"]

# Field names to check for winner ID (in order of preference)
WINNER_ID_FIELDS = ["winningTeamId"]

# Field names to check for start time (in order of preference)
START_TIME_FIELDS = ["startTime", "Start Time"]

# Field names to check for duration (in order of preference)
DURATION_FIELDS = ["durationMs"]

# Field names to check for map name (in order of preference)
MAP_NAME_FIELDS = ["mapname"]

# ==============================
# Data Structure Paths
# ==============================

# Path to AllyTeams in replay data
ALLY_TEAMS_PATH = "AllyTeams"

# Path to Players within AllyTeams
PLAYERS_PATH = "Players"

# Path to hostSettings in replay data
HOST_SETTINGS_PATH = "hostSettings"

# Path to gamestats in replay data
GAMESTATS_PATH = "gamestats"

