"""
Data extraction configuration for replay processing.
Defines what data is extracted from replay files and how it's processed.
"""

# ==============================
# API Configuration
# ==============================

# BAR API base URL
BAR_API_BASE = "https://api.bar-rts.com"

# Delay between API requests (seconds) - be respectful to the API
REQUEST_DELAY = 0.5

# API request timeout (seconds)
API_TIMEOUT_SECONDS = 10

# ==============================
# Default Values
# ==============================

# Default OpenSkill mu (mean) if missing from replay
DEFAULT_MU = 25.0

# Default OpenSkill sigma (uncertainty) if missing from replay
DEFAULT_SIGMA = 25.0 / 6.0

# ==============================
# Data Fields to Extract
# ==============================

# Fields to extract from submission data
SUBMISSION_FIELDS = {
    "submitted_at": ["submitted_at", "timestamp"],  # Submission timestamp
    "submitted_by": ["submitted_by"],  # Who submitted
    "players": ["players"],  # List of player names
    "series_winner": ["series_winner"],  # Bo3 series winner
    "matches": ["matches"],  # Match data (newer format)
    "replays": ["replays"],  # Replay data (older format)
}

# Fields to extract from match data (newer format)
MATCH_FIELDS = {
    "id": ["id"],  # Replay ID
    "winner": ["winner"],  # Match winner
    "map": ["map"],  # Map name
    "duration_ms": ["duration_ms"],  # Match duration in milliseconds
    "seed_ratings": ["seed_ratings"],  # Pre-match OpenSkill ratings
}

# Fields to extract from replay data (older format)
REPLAY_FIELDS = {
    "id": ["id"],  # Replay ID
    "winner": ["winner"],  # Match winner
    "mapname": ["mapname"],  # Map name
    "duration_ms": ["duration_ms"],  # Match duration in milliseconds
    "startTime": ["startTime"],  # Start time
    "players": ["players"],  # Player data
}

# Fields to extract from BAR API response
API_FIELDS = {
    "startTime": ["startTime"],  # Game start time
    "engineVersion": ["engineVersion"],  # Engine version
    "gameVersion": ["gameVersion"],  # Game version
    "AllyTeams": ["AllyTeams"],  # Team data
    "Players": ["Players"],  # Direct player data (fallback)
}

# Fields to extract from player data in API response
PLAYER_API_FIELDS = {
    "name": ["Name", "name"],  # Player name
    "side": ["Side", "side"],  # Faction/side
}

# Fields to extract from seed ratings
SEED_RATING_FIELDS = {
    "mu": ["mu"],  # OpenSkill mean
    "sigma": ["sigma"],  # OpenSkill uncertainty
}

# ==============================
# Output Fields Configuration
# ==============================

# Fields included in replay database entry
REPLAY_DATABASE_FIELDS = [
    "id",  # Replay ID
    "url",  # Replay URL
    "date",  # Game date
    "submitted_at",  # Submission timestamp
    "submitted_by",  # Submitter
    "map",  # Map name
    "duration_ms",  # Duration in milliseconds
    "duration_formatted",  # Human-readable duration
    "winner",  # Winner name
    "players",  # Player info list
    "player_names",  # List of player names
    "series_winner",  # Bo3 series winner
    "engine_version",  # Engine version
    "game_version",  # Game version
    "is_tournament",  # Tournament flag
    "tags",  # Searchable tags
]

# Fields included in player info within replay entry
PLAYER_INFO_FIELDS = [
    "name",  # Player name
    "faction",  # Faction/side
    "is_winner",  # Win flag
    "mu",  # OpenSkill mu (if available)
    "sigma",  # OpenSkill sigma (if available)
    "skill_estimate",  # mu - sigma (if available)
]

# ==============================
# URL Generation
# ==============================

# Base URL for replay viewing
REPLAY_VIEW_BASE_URL = "https://www.beyondallreason.info/replays?gameId="

# ==============================
# Tag Generation Rules
# ==============================

# Duration thresholds for tags (in minutes)
DURATION_TAG_THRESHOLDS = {
    "short": 10,  # < 10 minutes
    "medium": 30,  # 10-30 minutes
    "long": 60,  # 30-60 minutes
    "epic": float("inf"),  # >= 60 minutes
}

# Skill thresholds for tags
SKILL_TAG_THRESHOLDS = {
    "high-skill": 25,  # Average skill > 25
    "mid-skill": 15,  # Average skill 15-25
    "beginner-friendly": 0,  # Average skill < 15
}

# ==============================
# Data Processing Rules
# ==============================

# Maximum recent matches to keep in player history
MAX_RECENT_MATCHES = 10

# Default values for missing data
DEFAULT_VALUES = {
    "map": "Unknown",
    "faction": "Unknown",
    "submitted_by": "unknown",
    "series_winner": "",
    "engine_version": "",
    "game_version": "",
}

# ==============================
# File Paths
# ==============================

# Directory containing submission files
SUBMISSIONS_DIR = "submissions/bo3"

# Output file paths
REPLAY_DATABASE_FILE = "public/data/replay_database.json"
PLAYER_MATCH_HISTORY_FILE = "public/data/player_match_history.json"

