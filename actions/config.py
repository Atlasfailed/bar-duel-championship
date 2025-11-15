"""
Configuration for the BAR Duel Championship leaderboard system.
Adjust these values to tune the rating and tier system.
"""

# ==============================
# Tier Definitions
# ==============================
# Format: (tier_name, min_percentile, max_percentile, min_cr, max_cr)
# Percentile thresholds define tier boundaries (e.g., Bronze = lower than 20th percentile)
# CR ranges define the Champion Rating boundaries for each tier
TIER_DEFINITIONS = [
    # Tier Name       Min %  Max %  Min CR  Max CR
    ("Bronze",        1,     20,    900,    1200),  # Lower than 20th percentile
    ("Silver",        20,    40,    1200,   1500),  # 20th-40th percentile
    ("Gold",          40,    60,    1500,   1800),  # 40th-60th percentile
    ("Platinum",      60,    80,    1800,   2100),  # 60th-80th percentile
    ("Diamond",       80,    95,    2100,   2500),  # 80th-95th percentile
    ("Master",        95,    99,    2500,   3000),  # 95th-99th percentile
    ("Grandmaster",   99,    100,   3000,   5000),  # Top 1% (above 99th percentile)
]

# Tier logos/icons for visual display (SVG file references)
TIER_LOGOS = {
    "Bronze": "static/images/tiers/bronze.svg",
    "Silver": "static/images/tiers/silver.svg", 
    "Gold": "static/images/tiers/gold.svg",
    "Platinum": "static/images/tiers/platinum.svg",
    "Diamond": "static/images/tiers/diamond.svg",
    "Master": "static/images/tiers/master.svg",
    "Grandmaster": "static/images/tiers/master.svg",  # Use master.svg for grandmaster
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
