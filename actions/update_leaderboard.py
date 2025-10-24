"""
GitHub Actions - Leaderboard Update Script
Processes submissions and updates the leaderboard
Runs automatically on schedule or PR merge
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any

# Load configuration
LEADERBOARD_FILE = "public/data/leaderboard.json"
SUBMISSIONS_DIR = "submissions/bo3"

def process_submissions() -> List[Dict[str, Any]]:
    """Process all Bo3 submissions from the submissions directory"""
    submissions = []
    submissions_path = Path(SUBMISSIONS_DIR)
    
    if not submissions_path.exists():
        print("⚠️ No submissions directory found")
        return []
    
    for file in submissions_path.glob("*.json"):
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                submissions.append(data)
                print(f"✅ Loaded submission: {file.name}")
        except Exception as e:
            print(f"⚠️ Failed to load {file.name}: {e}")
    
    return submissions

def calculate_rankings(submissions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate player rankings from submissions"""
    players = {}
    player_opponents = {}  # Track opponents and their skills for SoS calculation
    
    for sub in submissions:
        winner = sub.get("series_winner")
        wins_data = sub.get("wins", {})
        match_players = sub.get("players", [])
        
        # Get average skill for each player in this match
        player_skills = {}
        if sub.get("replays"):
            for replay in sub["replays"]:
                for p in replay.get("players", []):
                    name = p.get("name")
                    skill = p.get("skill", 0)
                    if name and skill:
                        player_skills[name] = skill
        
        for player in match_players:
            if player not in players:
                players[player] = {
                    "player": player,
                    "wins": 0,
                    "losses": 0,
                    "matches": 0,
                    "points": 0,
                    "total_opponent_skill": 0,
                    "skill_rating": player_skills.get(player, 0)
                }
                player_opponents[player] = []
            
            # Track opponents for SoS calculation
            opponents = [p for p in match_players if p != player]
            for opponent in opponents:
                opponent_skill = player_skills.get(opponent, 0)
                player_opponents[player].append(opponent_skill)
                players[player]["total_opponent_skill"] += opponent_skill
            
            players[player]["matches"] += 1
            
            if player == winner:
                players[player]["wins"] += 1
                players[player]["points"] += 3  # Win points
            else:
                players[player]["losses"] += 1
    
    # Calculate Strength of Schedule (SoS) and enhanced rankings
    for player_name, player_data in players.items():
        # Calculate average opponent skill (Strength of Schedule)
        if player_data["matches"] > 0:
            player_data["sos"] = round(player_data["total_opponent_skill"] / player_data["matches"], 2)
        else:
            player_data["sos"] = 0
        
        # Calculate win rate
        player_data["winrate"] = round(player_data["wins"] / player_data["matches"] * 100, 1) if player_data["matches"] > 0 else 0
        
        # Calculate SoS-adjusted points (experimental)
        # Higher SoS gives slight bonus to account for stronger opponents
        sos_multiplier = 1.0 + (player_data["sos"] - 15.0) / 100.0  # Assumes ~15 is average skill
        player_data["adjusted_points"] = round(player_data["points"] * max(0.8, min(1.2, sos_multiplier)), 2)
        
        # Clean up temporary field
        del player_data["total_opponent_skill"]
    
    # Convert to list and sort by points (primary), SoS (secondary), wins (tertiary)
    leaderboard = list(players.values())
    leaderboard.sort(key=lambda x: (-x["points"], -x["sos"], -x["wins"], x["losses"]))
    
    # Add ranks
    for i, player in enumerate(leaderboard, 1):
        player["rank"] = i
    
    return leaderboard

def update_leaderboard():
    """Main function to update leaderboard"""
    print("🔄 Processing submissions...")
    
    # Process submissions
    submissions = process_submissions()
    print(f"📊 Found {len(submissions)} submissions")
    
    # Calculate rankings
    leaderboard = calculate_rankings(submissions)
    print(f"🏆 Ranked {len(leaderboard)} players")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(LEADERBOARD_FILE), exist_ok=True)
    
    # Save leaderboard
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(leaderboard, f, indent=2)
    
    print(f"✅ Leaderboard saved to {LEADERBOARD_FILE}")
    print(f"📅 Updated at {datetime.now(timezone.utc).isoformat()}Z")
    
    # Print top 3
    if leaderboard:
        print("\n🏆 Top 3 Players:")
        for player in leaderboard[:3]:
            print(f"  {player['rank']}. {player['player']} - {player['points']} pts ({player['wins']}-{player['losses']})")

if __name__ == "__main__":
    try:
        update_leaderboard()
        print("\n✅ Leaderboard update complete!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Update failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)