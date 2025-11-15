"""
Configuration for the BAR Duel Championship leaderboard system.
Adjust these values to tune the rating and tier system.
"""

# ==============================
# Tier Definitions
# ==============================
# Format: (tier_name, min_skill, max_skill, min_cr, max_cr, initial_cr)
# Skill ranges are based on BAR 1v1 skill ratings
# CR ranges define the Champion Rating boundaries for each tier
# initial_cr is the starting CR for players in this tier
TIER_DEFINITIONS = [
    # Tier Name    Min Skill  Max Skill  Min CR  Max CR  Initial CR
    ("Bronze",     0,         10,        500,    850,    650),
    ("Silver",     10,        20,        850,    1250,   1050),
    ("Gold",       20,        30,        1250,   1650,   1450),
    ("Platinum",   30,        40,        1650,   2050,   1850),
    ("Diamond",    40,        50,        2050,   2450,   2250),
    ("Master",     50,        999,       2450,   5000,   2650),
]

# Tier logos/icons for visual display
TIER_LOGOS = {
    "Bronze": "🥉",
    "Silver": "🥈", 
    "Gold": "🥇",
    "Platinum": "💎",
    "Diamond": "💠",
    "Master": "⭐",
}

# ==============================
# Dynamic CR Calculation
# ==============================
# CR changes are based on opponent skill difference
CR_BASE_CHANGE = 15        # Base CR change for evenly matched opponents
CR_MIN_CHANGE = 2          # Minimum CR change (beating much weaker opponent)
CR_MAX_CHANGE = 30         # Maximum CR change (beating much stronger opponent)
SKILL_DIFF_THRESHOLD = 15.0  # Skill difference threshold for CR scaling

# ==============================
# OpenSkill Rating Model
# ==============================
# PlackettLuce model parameters for skill rating calculations
OS_MU = 25.0               # Default mean skill rating
OS_SIGMA = 25.0 / 6.0      # Default uncertainty (volatility)
OS_BETA = 25.0 / 6.0       # Skill difference scaling factor
OS_TAU = 25.0 / 300.0      # Dynamics factor (rating volatility over time)

# Default seed values if replay data is missing
DEFAULT_MU = OS_MU
DEFAULT_SIGMA = OS_SIGMA
