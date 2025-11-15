"""
Configuration for the BAR Duel Championship leaderboard system.
Adjust these values to tune the rating and tier system.
"""

# ==============================
# Tier Definitions
# ==============================
# Format: (tier_name, min_os_value, max_os_value, min_cr, max_cr)
# Tiers now use OpenSkill (mu - sigma) thresholds directly (e.g., Bronze = OS lower than 10)
# CR ranges define the Champion Rating boundaries for each tier
TIER_DEFINITIONS = [
    # Tier Name       Min OS        Max OS        Min CR  Max CR
    ("Bronze",        float("-inf"), 10.0,         900,    1200),  # OS below 10
    ("Silver",        10.0,          20.0,         1200,   1500),  # 10 ≤ OS < 20
    ("Gold",          20.0,          30.0,         1500,   1800),  # 20 ≤ OS < 30
    ("Platinum",      30.0,          40.0,         1800,   2100),  # 30 ≤ OS < 40
    ("Diamond",       40.0,          50.0,         2100,   2500),  # 40 ≤ OS < 50
    ("Master",        50.0,          60.0,         2500,   3000),  # 50 ≤ OS < 60
    ("Grandmaster",   60.0,          float("inf"), 3000,   5000),  # OS ≥ 60
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

# Note: OpenSkill model parameters are configured in tier_utils.py
# Default OpenSkill values (DEFAULT_MU, DEFAULT_SIGMA) are also defined in tier_utils.py
