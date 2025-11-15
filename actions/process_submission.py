"""
GitHub Actions - Process New Submission Script
Handles incremental updates when bot creates new submissions.

This script:
1. Loads existing leaderboard
2. Processes only NEW submissions since last update
3. Updates affected players' CR and stats
4. Saves updated leaderboard

PERFORMANCE: Much faster than full recalculation for bot submissions
USE CASE: Triggered by bot PRs with new submissions
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

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
PROCESSED_SUBMISSIONS_FILE = "public/data/.processed_submissions.json"

# ==============================
# Incremental update logic
# ==============================

def load_existing_leaderboard() -> Optional[Dict[str, Any]]:
    """Load existing leaderboard data."""
    if not os.path.exists(LEADERBOARD_FILE):
        return None
    
    try:
        with open(LEADERBOARD_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load existing leaderboard: {e}")
        return None

def load_processed_submissions() -> set:
    """Load set of already processed submission filenames."""
    if not os.path.exists(PROCESSED_SUBMISSIONS_FILE):
        return set()
    
    try:
        with open(PROCESSED_SUBMISSIONS_FILE, 'r') as f:
            data = json.load(f)
            return set(data.get("processed", []))
    except Exception as e:
        print(f"Failed to load processed submissions: {e}")
        return set()

def save_processed_submissions(processed: set):
    """Save set of processed submission filenames."""
    os.makedirs(os.path.dirname(PROCESSED_SUBMISSIONS_FILE), exist_ok=True)
    with open(PROCESSED_SUBMISSIONS_FILE, 'w') as f:
        json.dump({"processed": sorted(list(processed))}, f, indent=2)

def get_new_submissions(processed: set) -> List[tuple]:
    """Get list of new submission files and their data."""
    submissions_path = Path(SUBMISSIONS_DIR)
    if not submissions_path.exists():
        return []
    
    new_submissions = []
    for file in sorted(submissions_path.glob("*.json")):
        if file.name not in processed:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    new_submissions.append((file.name, data))
                    print(f"New submission: {file.name}")
            except Exception as e:
                print(f"Failed to load {file.name}: {e}")
    
    return new_submissions

def get_player_initial_os_from_submission(submission: Dict[str, Any], player: str) -> Optional[float]:
    """Extract initial OS for a player from a submission."""
    matches = submission.get("matches", [])
    for match in matches:
        seed_ratings = match.get("seed_ratings", {})
        if player in seed_ratings:
            mu = float(seed_ratings[player].get("mu", DEFAULT_MU))
            sigma = float(seed_ratings[player].get("sigma", DEFAULT_SIGMA))
            return mu - sigma
    
    replays = submission.get("replays", [])
    for replay in replays:
        players_data = replay.get("players", [])
        for p_data in players_data:
            if p_data.get("name") == player and "skill" in p_data:
                mu = float(p_data["skill"])
                sigma = mu / 3.0
                return mu - sigma
    
    return None

def create_new_player_entry(player: str, initial_os: float) -> Dict[str, Any]:
    """Create a new player entry for the leaderboard."""
    percentile = get_os_percentile(initial_os)
    tier_name, min_cr, max_cr = get_tier_from_os(initial_os)
    initial_cr = get_initial_champion_rating(tier_name, min_cr, max_cr)
    
    return {
        "player": player,
        "tier": tier_name,
        "initial_cr": initial_cr,
        "current_cr": initial_cr,
        "matches": 0,
        "wins": 0,
        "losses": 0,
        "winrate": 0.0,
        "initial_os": round(initial_os, 6),
        "percentile": round(percentile, 2),
        "latest_os": round(initial_os, 2),
        "tier_rank": 1,
        "type": "player"
    }

def process_match_incremental(match: Dict[str, Any], players: List[str], player_entries: Dict[str, Dict]):
    """Process a single match and update player entries."""
    if len(players) != 2:
        return
    
    seed_ratings = match.get("seed_ratings", {})
    winner = match.get("winner")
    
    if not seed_ratings or not winner:
        return
    
    p1, p2 = players[0], players[1]
    
    # Get pre-match ratings
    p1_mu = float(seed_ratings.get(p1, {}).get("mu", DEFAULT_MU))
    p1_sigma = float(seed_ratings.get(p1, {}).get("sigma", DEFAULT_SIGMA))
    p2_mu = float(seed_ratings.get(p2, {}).get("mu", DEFAULT_MU))
    p2_sigma = float(seed_ratings.get(p2, {}).get("sigma", DEFAULT_SIGMA))
    
    p1_pre_os = p1_mu - p1_sigma
    p2_pre_os = p2_mu - p2_sigma
    
    # Calculate updated ratings
    team1 = [MODEL.create_rating([p1_mu, p1_sigma], name=p1)]
    team2 = [MODEL.create_rating([p2_mu, p2_sigma], name=p2)]
    
    ranks = [1, 2] if winner == p1 else [2, 1] if winner == p2 else [1, 1]
    updated_teams = MODEL.rate([team1, team2], ranks=ranks)
    
    p1_new_mu = float(updated_teams[0][0].mu)
    p1_new_sigma = float(updated_teams[0][0].sigma)
    p2_new_mu = float(updated_teams[1][0].mu)
    p2_new_sigma = float(updated_teams[1][0].sigma)
    
    p1_new_os = p1_new_mu - p1_new_sigma
    p2_new_os = p2_new_mu - p2_new_sigma
    
    # Calculate CR changes
    if winner == p1:
        p1_cr_delta = calculate_dynamic_cr_change(p1_pre_os, p2_pre_os, is_winner=True)
        p2_cr_delta = calculate_dynamic_cr_change(p1_pre_os, p2_pre_os, is_winner=False)
    elif winner == p2:
        p2_cr_delta = calculate_dynamic_cr_change(p2_pre_os, p1_pre_os, is_winner=True)
        p1_cr_delta = calculate_dynamic_cr_change(p2_pre_os, p1_pre_os, is_winner=False)
    else:
        p1_cr_delta = p2_cr_delta = 0
    
    # Update player entries
    for player, cr_delta, new_os, is_win in [
        (p1, p1_cr_delta, p1_new_os, winner == p1),
        (p2, p2_cr_delta, p2_new_os, winner == p2)
    ]:
        if player in player_entries:
            entry = player_entries[player]
            entry["current_cr"] += cr_delta
            entry["matches"] += 1
            if is_win:
                entry["wins"] += 1
            else:
                entry["losses"] += 1
            entry["winrate"] = round((entry["wins"] / entry["matches"]) * 100.0, 1)
            entry["latest_os"] = round(new_os, 2)
            entry["tier"] = get_tier_from_cr(entry["current_cr"])

def rebuild_leaderboard_structure(player_entries: Dict[str, Dict]) -> List[Dict]:
    """Rebuild leaderboard with tier headers and proper ranking."""
    # Convert to list and sort
    results = list(player_entries.values())
    tier_order = {name: i for i, (name, _, _, _, _) in enumerate(TIER_DEFINITIONS)}
    results.sort(key=lambda x: (-tier_order.get(x["tier"], -1), -x["current_cr"]))
    
    # Add tier headers and separators
    final_leaderboard = []
    current_tier = None
    tier_rank = 0
    
    for player in results:
        if current_tier != player["tier"]:
            if current_tier is not None:
                final_leaderboard.append({
                    "type": "tier_separator",
                    "tier": "",
                    "tier_logo": "",
                    "separator": True
                })
            
            current_tier = player["tier"]
            tier_rank = 0
            
            tier_info = next((f"CR {min_cr}-{max_cr}" for name, _, _, min_cr, max_cr in TIER_DEFINITIONS if name == current_tier), "")
            final_leaderboard.append({
                "type": "tier_header",
                "tier": current_tier,
                "tier_logo": TIER_LOGOS.get(current_tier, ""),
                "tier_info": tier_info,
                "tier_header": True
            })
        
        tier_rank += 1
        player["tier_rank"] = tier_rank
        final_leaderboard.append(player)
    
    return final_leaderboard

def process_new_submissions():
    """Main incremental update function."""
    print("Loading existing leaderboard...")
    leaderboard_data = load_existing_leaderboard()
    
    if leaderboard_data is None:
        print("No existing leaderboard found. Please run recalculate_leaderboard.py first.")
        sys.exit(1)
    
    # Extract player entries from existing leaderboard
    player_entries = {}
    for entry in leaderboard_data.get("entries", []):
        if entry.get("type") == "player":
            player_entries[entry["player"]] = entry
    
    print(f"Loaded {len(player_entries)} existing players")
    
    # Load processed submissions
    processed = load_processed_submissions()
    print(f"Already processed: {len(processed)} submissions")
    
    # Get new submissions
    new_submissions = get_new_submissions(processed)
    
    if not new_submissions:
        print("No new submissions to process")
        return
    
    print(f"Processing {len(new_submissions)} new submissions...")
    
    # Process each new submission
    for filename, submission in new_submissions:
        players = submission.get("players", [])
        if len(players) != 2:
            print(f"Skipping {filename}: invalid player count")
            continue
        
        # Check if players need to be added
        for player in players:
            if player not in player_entries:
                initial_os = get_player_initial_os_from_submission(submission, player)
                if initial_os is not None:
                    player_entries[player] = create_new_player_entry(player, initial_os)
                    print(f"  New player: {player} (OS={initial_os:.2f})")
                else:
                    print(f"  Warning: Could not determine initial OS for {player}")
        
        # Process matches
        matches = submission.get("matches", [])
        for match in matches:
            process_match_incremental(match, players, player_entries)
        
        # Mark as processed
        processed.add(filename)
        print(f"  Processed: {filename}")
    
    # Rebuild leaderboard structure
    print("Rebuilding leaderboard structure...")
    final_leaderboard = rebuild_leaderboard_structure(player_entries)
    player_count = len(player_entries)
    
    # Save updated leaderboard
    update_timestamp = datetime.now(timezone.utc).isoformat()
    leaderboard_data = {
        "updated_at": update_timestamp,
        "player_count": player_count,
        "entries": final_leaderboard
    }
    
    os.makedirs(os.path.dirname(LEADERBOARD_FILE), exist_ok=True)
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(leaderboard_data, f, indent=2)
    
    # Save processed submissions list
    save_processed_submissions(processed)
    
    print(f"\nLeaderboard updated: {player_count} players")
    print(f"Saved to {LEADERBOARD_FILE}")
    print(f"Updated at {update_timestamp}Z")

if __name__ == "__main__":
    try:
        process_new_submissions()
        print("\nIncremental update complete!")
        sys.exit(0)
    except Exception as e:
        print(f"\nUpdate failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
