"""
GitHub Actions - Leaderboard Update Script
Processes submissions and updates the leaderboard
Runs automatically on schedule or PR merge
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
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
    
    for sub in submissions:
        winner = sub.get("series_winner")
        wins_data = sub.get("wins", {})
        
        for player in sub.get("players", []):
            if player not in players:
                players[player] = {
                    "player": player,
                    "wins": 0,
                    "losses": 0,
                    "matches": 0,
                    "points": 0
                }
            
            players[player]["matches"] += 1
            
            if player == winner:
                players[player]["wins"] += 1
                players[player]["points"] += 3  # Win points
            else:
                players[player]["losses"] += 1
    
    # Convert to list and sort by points
    leaderboard = list(players.values())
    leaderboard.sort(key=lambda x: (-x["points"], -x["wins"], x["losses"]))
    
    # Add ranks
    for i, player in enumerate(leaderboard, 1):
        player["rank"] = i
        player["winrate"] = round(player["wins"] / player["matches"] * 100, 1) if player["matches"] > 0 else 0
    
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
    print(f"📅 Updated at {datetime.utcnow().isoformat()}Z")
    
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