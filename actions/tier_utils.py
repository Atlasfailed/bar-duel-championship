"""
Shared tier and rating utilities for leaderboard calculations.
This module contains common functions used by both process_submission.py
and recalculate_leaderboard.py to avoid code duplication.
"""

from typing import Tuple
from openskill.models import PlackettLuce

# Import configuration
from config import TIER_DEFINITIONS, CR_BASE_CHANGE, CR_MIN_CHANGE, CR_MAX_CHANGE, SKILL_DIFF_THRESHOLD

# ==============================
# OpenSkill Model Configuration
# ==============================

# Rating model config (OpenSkill PlackettLuce with reduced volatility)
MODEL = PlackettLuce(mu=25.0, sigma=25.0/6.0, beta=25.0/6.0, tau=25.0/300.0)

# Default seed values if replay data missing
DEFAULT_MU = 25.0
DEFAULT_SIGMA = 25.0 / 6.0

# ==============================
# OpenSkill Percentile Distribution
# ==============================

PERCENTILE_OS_POINTS = [
    (1, 2.60), (5, 7.26), (10, 9.58), (20, 12.21), (30, 13.84),
    (40, 14.86), (50, 16.45), (60, 18.17), (70, 19.57),
    (80, 21.80), (90, 25.45), (95, 29.43), (96, 31.02),
    (97, 32.61), (98, 35.30), (99, 39.68),
]

# ==============================
# Tier System Utilities
# ==============================

def get_os_percentile(os_value: float) -> float:
    """Convert OpenSkill value to percentile using the provided distribution."""
    if os_value <= PERCENTILE_OS_POINTS[0][1]:
        return PERCENTILE_OS_POINTS[0][0]
    if os_value >= PERCENTILE_OS_POINTS[-1][1]:
        return PERCENTILE_OS_POINTS[-1][0]
    
    # Linear interpolation between points
    for i in range(len(PERCENTILE_OS_POINTS) - 1):
        p1, os1 = PERCENTILE_OS_POINTS[i]
        p2, os2 = PERCENTILE_OS_POINTS[i + 1]
        
        if os1 <= os_value <= os2:
            ratio = (os_value - os1) / (os2 - os1)
            return p1 + ratio * (p2 - p1)
    
    return 50.0  # fallback to median


def get_tier_from_os(os_value: float) -> Tuple[str, int, int]:
    """Get tier name and Champion Rating range from OpenSkill value."""
    for tier_name, min_os, max_os, min_cr, max_cr in TIER_DEFINITIONS:
        if min_os <= os_value < max_os:
            return tier_name, min_cr, max_cr
    
    # Default to highest tier for values at or above the final threshold
    return TIER_DEFINITIONS[-1][0], TIER_DEFINITIONS[-1][3], TIER_DEFINITIONS[-1][4]


def get_tier_from_cr(champion_rating: int) -> str:
    """Get tier name from Champion Rating."""
    for tier_name, _, _, min_cr, max_cr in TIER_DEFINITIONS:
        if min_cr <= champion_rating < max_cr:
            return tier_name
    
    # If CR is below lowest tier, return lowest tier
    if champion_rating < TIER_DEFINITIONS[0][3]:  # Below Bronze minimum
        return TIER_DEFINITIONS[0][0]  # Return Bronze
    
    # If CR is above highest tier, return highest tier
    return TIER_DEFINITIONS[-1][0]


def get_initial_champion_rating(tier_name: str, min_cr: int, max_cr: int) -> int:
    """Get the middle Champion Rating for a tier (assigned to new players)."""
    return (min_cr + max_cr) // 2


def calculate_dynamic_cr_change(winner_os: float, loser_os: float, is_winner: bool) -> int:
    """
    Calculate dynamic CR change based on OpenSkill difference.
    - Base change: 15 CR
    - Range: 2-30 CR per game
    - When beating stronger opponent (OS diff > threshold): higher CR gain (up to 30)
    - When beating weaker opponent (OS diff > threshold): lower CR gain (down to 2)
    - Symmetric: loser loses what winner gains
    """
    os_difference = winner_os - loser_os
    
    # Normalize the difference to [-1, 1] range
    normalized_diff = max(-1.0, min(1.0, os_difference / SKILL_DIFF_THRESHOLD))
    
    if is_winner:
        # Winner gains more when beating stronger opponent (negative normalized_diff)
        # Winner gains less when beating weaker opponent (positive normalized_diff)
        cr_change = CR_BASE_CHANGE - (normalized_diff * (CR_BASE_CHANGE - CR_MIN_CHANGE))
    else:
        # Loser loses more when losing to weaker opponent (positive normalized_diff)
        # Loser loses less when losing to stronger opponent (negative normalized_diff)
        cr_change = -(CR_BASE_CHANGE + (normalized_diff * (CR_MAX_CHANGE - CR_BASE_CHANGE)))
    
    # Ensure we stay within bounds
    if is_winner:
        cr_change = max(CR_MIN_CHANGE, min(CR_MAX_CHANGE, cr_change))
    else:
        cr_change = max(-CR_MAX_CHANGE, min(-CR_MIN_CHANGE, cr_change))
    
    return int(round(cr_change))

