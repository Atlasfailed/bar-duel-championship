"""
GitHub Actions - Full Leaderboard Recalculation Script
Performs complete recalculation of the leaderboard from scratch.

TIER-BASED CHAMPION RATING SYSTEM:
- Players are placed in tiers based on their INITIAL OpenSkill (mu - sigma)
- Initial CR = middle of their tier's CR range
- CR changes per game: min 2, max 30 based on opponent strength
- Current tier displayed based on CURRENT CR

USE THIS SCRIPT FOR:
- Config changes (tier boundaries, CR ranges)
- Bug fixes that require recalculation
- Development and testing
- Manual recalculation via workflow_dispatch

FOR BOT SUBMISSIONS: Use process_submission.py instead (incremental updates)
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple

# Add actions directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Import configuration
from config import TIER_DEFINITIONS, TIER_LOGOS

# Import shared tier utilities
from tier_utils import (
    MODEL, DEFAULT_MU, DEFAULT_SIGMA,
    get_os_percentile, get_tier_from_os, get_tier_from_cr,
    get_initial_champion_rating, calculate_dynamic_cr_change
)

# ==============================
# Configuration
# ==============================

LEADERBOARD_FILE = "public/data/leaderboard.json"
SUBMISSIONS_DIR = "submissions/bo3"



# ==============================
# I/O: load submissions
# ==============================

def process_submissions() -> List[Dict[str, Any]]:
    """Process all Bo3 submissions from the submissions directory"""
    submissions = []
    submissions_path = Path(SUBMISSIONS_DIR)

    if not submissions_path.exists():
        print("No submissions directory found")
        return []

    # Sort by filename for deterministic processing
    for file in sorted(submissions_path.glob("*.json")):
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                submissions.append(data)
                print(f"Loaded submission: {file.name}")
        except Exception as e:
            print(f"Failed to load {file.name}: {e}")

    return submissions


# ==============================
# Player data management
# ==============================

def get_player_initial_os(submissions: List[Dict[str, Any]], player: str) -> float:
    """Get a player's initial OpenSkill (mu - sigma) from their first appearance."""
    # Look through all submissions to find the earliest appearance of this player
    for sub in submissions:
        matches = sub.get("matches", [])
        replays = sub.get("replays", [])
        
        # Check seed_ratings in matches (newer format)
        for match in matches:
            seed_ratings = match.get("seed_ratings", {})
            if player in seed_ratings:
                mu = float(seed_ratings[player].get("mu", DEFAULT_MU))
                sigma = float(seed_ratings[player].get("sigma", DEFAULT_SIGMA))
                return mu - sigma
        
        # Check skill in replays (older format)
        for replay in replays:
            players_data = replay.get("players", [])
            for p_data in players_data:
                if p_data.get("name") == player and "skill" in p_data:
                    # Assume skill is mu and sigma is mu/3 (standard assumption)
                    mu = float(p_data["skill"])
                    sigma = mu / 3.0
                    return mu - sigma
    
    # Fallback to default values
    return DEFAULT_MU - DEFAULT_SIGMA


def calculate_player_champion_ratings(submissions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate Champion Ratings for all players:
    1. Determine initial tier based on first OpenSkill appearance
    2. Assign initial Champion Rating as middle of tier
    3. Calculate Champion Rating changes from OpenSkill changes in matches
    """
    print("Building player profiles...")
    
    # Get all players from submissions
    all_players = set()
    for sub in submissions:
        players = sub.get("players", [])
        all_players.update(players)
    
    player_data = {}
    
    # Initialize each player with their tier and starting Champion Rating
    for player in all_players:
        initial_os = get_player_initial_os(submissions, player)
        percentile = get_os_percentile(initial_os)
        tier_name, min_cr, max_cr = get_tier_from_os(initial_os)
        initial_cr = get_initial_champion_rating(tier_name, min_cr, max_cr)
        
        player_data[player] = {
            "player": player,
            "initial_os": initial_os,
            "percentile": percentile,
            "tier": tier_name,
            "min_cr": min_cr,
            "max_cr": max_cr,
            "initial_cr": initial_cr,
            "current_cr": initial_cr,
            "matches": 0,
            "wins": 0,
            "losses": 0,
            "cr_changes": [],
            "opponents": [],
            "latest_os_mu": None,
            "latest_os_sigma": None
        }
        
        print(f"  {player}: OS={initial_os:.2f}, P{percentile:.1f}, {tier_name}, CR={initial_cr}")
    
    print("Processing match results...")
    
    # Process all matches to calculate Champion Rating changes
    for sub in submissions:
        players = sub.get("players", [])
        if len(players) != 2:
            continue
        
        matches = sub.get("matches", [])
        replays = sub.get("replays", [])
        
        # Process matches with seed_ratings (newer format)
        for match in matches:
            _process_match_for_cr_changes(match, players, player_data)
        
        # Process replays (older format)
        for replay in replays:
            _process_replay_for_cr_changes(replay, players, player_data)
    
    # Calculate final stats and rankings
    results = []
    for player, data in player_data.items():
        total_matches = data["matches"]
        if total_matches == 0:
            continue
        
        winrate = round((data["wins"] / total_matches) * 100.0, 1) if total_matches > 0 else 0.0
        
        # Update tier based on current CR only (no match requirements for tournament)
        current_tier = get_tier_from_cr(data["current_cr"])
        
        # Calculate latest OpenSkill (mu - sigma)
        latest_os = None
        if data["latest_os_mu"] is not None and data["latest_os_sigma"] is not None:
            latest_os = round(data["latest_os_mu"] - data["latest_os_sigma"], 2)
        
        results.append({
            "player": player,
            "tier": current_tier,
            "initial_cr": data["initial_cr"],
            "current_cr": data["current_cr"],
            "matches": total_matches,
            "wins": data["wins"],
            "losses": data["losses"],
            "winrate": winrate,
            "initial_os": round(data["initial_os"], 6),
            "percentile": round(data["percentile"], 2),
            "latest_os": latest_os
        })
    
    # Sort by tier first (highest tier first = highest index), then by current Champion Rating within tier
    tier_order = {name: i for i, (name, _, _, _, _) in enumerate(TIER_DEFINITIONS)}
    results.sort(key=lambda x: (-tier_order.get(x["tier"], -1), -x["current_cr"]))
    
    # Create final leaderboard structure with tier separators and per-tier ranking
    final_leaderboard = []
    current_tier = None
    tier_rank = 0
    
    for player in results:
        if current_tier != player["tier"]:
            # Add tier separator
            if current_tier is not None:  # Don't add separator before first tier
                final_leaderboard.append({
                    "type": "tier_separator",
                    "tier": "",
                    "tier_logo": "",
                    "separator": True
                })
            
            current_tier = player["tier"]
            tier_rank = 0
            
            # Add tier header
            tier_info = next((f"CR {min_cr}-{max_cr}" for name, _, _, min_cr, max_cr in TIER_DEFINITIONS if name == current_tier), "")
            final_leaderboard.append({
                "type": "tier_header",
                "tier": current_tier,
                "tier_logo": TIER_LOGOS.get(current_tier, ""),
                "tier_info": tier_info,
                "tier_header": True
            })
        
        # Increment tier rank and add player
        tier_rank += 1
        player["tier_rank"] = tier_rank
        player["type"] = "player"
        final_leaderboard.append(player)
    
    return final_leaderboard


def _process_match_for_cr_changes(match: Dict[str, Any], players: List[str], player_data: Dict[str, Any]):
    """Process a single match with seed_ratings to calculate CR changes."""
    if len(players) != 2:
        return
    
    seed_ratings = match.get("seed_ratings", {})
    winner = match.get("winner")
    
    if not seed_ratings or not winner:
        return
    
    p1, p2 = players[0], players[1]
    
    # Get pre-match ratings from seeds
    p1_mu = float(seed_ratings.get(p1, {}).get("mu", DEFAULT_MU))
    p1_sigma = float(seed_ratings.get(p1, {}).get("sigma", DEFAULT_SIGMA))
    p2_mu = float(seed_ratings.get(p2, {}).get("mu", DEFAULT_MU))
    p2_sigma = float(seed_ratings.get(p2, {}).get("sigma", DEFAULT_SIGMA))
    
    p1_pre_os = p1_mu - p1_sigma
    p2_pre_os = p2_mu - p2_sigma
    
    # Create OpenSkill ratings and calculate updates
    team1 = [MODEL.create_rating([p1_mu, p1_sigma], name=p1)]
    team2 = [MODEL.create_rating([p2_mu, p2_sigma], name=p2)]
    
    if winner == p1:
        ranks = [1, 2]
    elif winner == p2:
        ranks = [2, 1]
    else:
        ranks = [1, 1]  # tie
    
    updated_teams = MODEL.rate([team1, team2], ranks=ranks)
    
    # Calculate new OpenSkill values
    p1_new_mu = float(updated_teams[0][0].mu)
    p1_new_sigma = float(updated_teams[0][0].sigma)
    p2_new_mu = float(updated_teams[1][0].mu)
    p2_new_sigma = float(updated_teams[1][0].sigma)
    
    p1_new_os = p1_new_mu - p1_new_sigma
    p2_new_os = p2_new_mu - p2_new_sigma
    
    # Calculate dynamic CR changes based on winner/loser and skill difference
    if winner == p1:
        p1_cr_delta = calculate_dynamic_cr_change(p1_pre_os, p2_pre_os, is_winner=True)
        p2_cr_delta = calculate_dynamic_cr_change(p1_pre_os, p2_pre_os, is_winner=False)
    elif winner == p2:
        p2_cr_delta = calculate_dynamic_cr_change(p2_pre_os, p1_pre_os, is_winner=True)
        p1_cr_delta = calculate_dynamic_cr_change(p2_pre_os, p1_pre_os, is_winner=False)
    else:
        # Tie - no CR change
        p1_cr_delta = 0
        p2_cr_delta = 0
    
    # Update player data
    if p1 in player_data:
        player_data[p1]["current_cr"] += p1_cr_delta
        player_data[p1]["cr_changes"].append(p1_cr_delta)
        player_data[p1]["matches"] += 1
        player_data[p1]["opponents"].append(p2)
        player_data[p1]["latest_os_mu"] = p1_new_mu
        player_data[p1]["latest_os_sigma"] = p1_new_sigma
        if winner == p1:
            player_data[p1]["wins"] += 1
        else:
            player_data[p1]["losses"] += 1
    
    if p2 in player_data:
        player_data[p2]["current_cr"] += p2_cr_delta
        player_data[p2]["cr_changes"].append(p2_cr_delta)
        player_data[p2]["matches"] += 1
        player_data[p2]["opponents"].append(p1)
        player_data[p2]["latest_os_mu"] = p2_new_mu
        player_data[p2]["latest_os_sigma"] = p2_new_sigma
        if winner == p2:
            player_data[p2]["wins"] += 1
        else:
            player_data[p2]["losses"] += 1


def _process_replay_for_cr_changes(replay: Dict[str, Any], submission_players: List[str], player_data: Dict[str, Any]):
    """Process a single replay to calculate CR changes (older format)."""
    if len(submission_players) != 2:
        return
    
    winner = replay.get("winner")
    players_data = replay.get("players", [])
    
    if not winner or len(players_data) != 2:
        return
    
    # Map player data by name
    player_skills = {}
    for p_data in players_data:
        name = p_data.get("name")
        skill = p_data.get("skill")
        if name and skill:
            # Assume skill is mu and sigma is mu/3
            mu = float(skill)
            sigma = mu / 3.0
            player_skills[name] = (mu, sigma)
    
    if len(player_skills) != 2:
        return
    
    p1, p2 = submission_players[0], submission_players[1]
    
    if p1 not in player_skills or p2 not in player_skills:
        return
    
    p1_mu, p1_sigma = player_skills[p1]
    p2_mu, p2_sigma = player_skills[p2]
    
    p1_pre_os = p1_mu - p1_sigma
    p2_pre_os = p2_mu - p2_sigma
    
    # Create OpenSkill ratings and calculate updates
    team1 = [MODEL.create_rating([p1_mu, p1_sigma], name=p1)]
    team2 = [MODEL.create_rating([p2_mu, p2_sigma], name=p2)]
    
    if winner == p1:
        ranks = [1, 2]
    elif winner == p2:
        ranks = [2, 1]
    else:
        ranks = [1, 1]  # tie
    
    updated_teams = MODEL.rate([team1, team2], ranks=ranks)
    
    # Calculate new OpenSkill values
    p1_new_mu = float(updated_teams[0][0].mu)
    p1_new_sigma = float(updated_teams[0][0].sigma)
    p2_new_mu = float(updated_teams[1][0].mu)
    p2_new_sigma = float(updated_teams[1][0].sigma)
    
    p1_new_os = p1_new_mu - p1_new_sigma
    p2_new_os = p2_new_mu - p2_new_sigma
    
    # Calculate dynamic CR changes based on winner/loser and skill difference
    if winner == p1:
        p1_cr_delta = calculate_dynamic_cr_change(p1_pre_os, p2_pre_os, is_winner=True)
        p2_cr_delta = calculate_dynamic_cr_change(p1_pre_os, p2_pre_os, is_winner=False)
    elif winner == p2:
        p2_cr_delta = calculate_dynamic_cr_change(p2_pre_os, p1_pre_os, is_winner=True)
        p1_cr_delta = calculate_dynamic_cr_change(p2_pre_os, p1_pre_os, is_winner=False)
    else:
        # Tie - no CR change
        p1_cr_delta = 0
        p2_cr_delta = 0
    
    # Update player data
    if p1 in player_data:
        player_data[p1]["current_cr"] += p1_cr_delta
        player_data[p1]["cr_changes"].append(p1_cr_delta)
        player_data[p1]["matches"] += 1
        player_data[p1]["opponents"].append(p2)
        player_data[p1]["latest_os_mu"] = p1_new_mu
        player_data[p1]["latest_os_sigma"] = p1_new_sigma
        if winner == p1:
            player_data[p1]["wins"] += 1
        else:
            player_data[p1]["losses"] += 1
    
    if p2 in player_data:
        player_data[p2]["current_cr"] += p2_cr_delta
        player_data[p2]["cr_changes"].append(p2_cr_delta)
        player_data[p2]["matches"] += 1
        player_data[p2]["opponents"].append(p1)
        player_data[p2]["latest_os_mu"] = p2_new_mu
        player_data[p2]["latest_os_sigma"] = p2_new_sigma
        if winner == p2:
            player_data[p2]["wins"] += 1
        else:
            player_data[p2]["losses"] += 1


# ==============================
# Main ranking calculation
# ==============================

def calculate_rankings(submissions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate rankings using the new tier-based Champion Rating system:
    1. Assign players to tiers based on initial OpenSkill (mu - sigma)
    2. Give each player initial Champion Rating (middle of their tier)
    3. Calculate Champion Rating changes from OpenSkill changes in matches
    4. Rank by tier first, then by current Champion Rating within tier
    """
    return calculate_player_champion_ratings(submissions)


def update_leaderboard():
    """Main function to update leaderboard"""
    print("Processing submissions...")

    # Process submissions
    submissions = process_submissions()
    print(f"Found {len(submissions)} submissions")

    # Calculate rankings using new tier-based Champion Rating system
    leaderboard = calculate_rankings(submissions)
    
    # Count only player entries for display
    player_count = sum(1 for entry in leaderboard if entry.get("type") == "player")
    print(f"Ranked {player_count} players")

    # Add metadata with update timestamp
    update_timestamp = datetime.now(timezone.utc).isoformat()
    leaderboard_data = {
        "updated_at": update_timestamp,
        "player_count": player_count,
        "entries": leaderboard
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(LEADERBOARD_FILE), exist_ok=True)

    # Save leaderboard
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(leaderboard_data, f, indent=2)

    print(f"Leaderboard saved to {LEADERBOARD_FILE}")
    print(f"Updated at {update_timestamp}Z")

    # Print full leaderboard with tier separations
    if leaderboard:
        print("\n" + "="*60)
        print("TOURNAMENT LEADERBOARD (Highest Tier First)")
        print("="*60)
        
        for entry in leaderboard:
            if entry.get("type") == "tier_separator":
                print()  # Empty line between tiers
                
            elif entry.get("type") == "tier_header":
                tier_logo = entry.get("tier_logo", "")
                tier_name = entry.get("tier")
                tier_info = entry.get("tier_info", "")
                print(f"\n{tier_logo} {tier_name.upper()} TIER ({tier_info}) {tier_logo}")
                
            elif entry.get("type") == "player":
                tier_rank = entry.get("tier_rank", 1)
                print(f"  {tier_rank:2d}. {entry['player']:15s} {entry['current_cr']:4d} CR ({entry['wins']:2d}-{entry['losses']:2d}) {entry['winrate']:5.1f}%")
        
        # Print tier distribution summary
        print(f"\n{'-'*60}")
        print("TIER DISTRIBUTION:")
        tier_counts = {}
        
        # Count only player entries
        for entry in leaderboard:
            if entry.get("type") == "player":
                tier = entry['tier']
                tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
        # Print tiers in reverse order (highest first)
        for tier_name, _, _, min_cr, max_cr in reversed(TIER_DEFINITIONS):
            count = tier_counts.get(tier_name, 0)
            if count > 0:
                tier_logo = TIER_LOGOS.get(tier_name, "")
                print(f"  {tier_logo} {tier_name}: {count} players (CR {min_cr}-{max_cr})")


if __name__ == "__main__":
    try:
        update_leaderboard()
        print("\nLeaderboard update complete!")
        sys.exit(0)
    except Exception as e:
        print(f"\nUpdate failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
