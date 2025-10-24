"""
Analyze Submissions - Local Utility
Get statistics about submitted matches
"""

import json
import os
from pathlib import Path
from collections import Counter
from datetime import datetime

def analyze_submissions():
    """Analyze submission data"""
    submissions_dir = Path("../submissions/bo3")
    
    if not submissions_dir.exists():
        print("⚠️ No submissions directory found")
        return
    
    submissions = []
    for file in submissions_dir.glob("*.json"):
        with open(file, 'r') as f:
            submissions.append(json.load(f))
    
    print(f"📊 Analyzing {len(submissions)} submissions...\n")
    
    # Player stats
    players = Counter()
    wins = Counter()
    
    for sub in submissions:
        for player in sub.get("players", []):
            players[player] += 1
        
        winner = sub.get("series_winner")
        if winner:
            wins[winner] += 1
    
    # Print stats
    print("🏆 Top Players by Matches:")
    for player, count in players.most_common(10):
        win_count = wins.get(player, 0)
        winrate = (win_count / count * 100) if count > 0 else 0
        print(f"  {player}: {count} matches, {win_count} wins ({winrate:.1f}% WR)")
    
    print(f"\n📈 Total unique players: {len(players)}")
    print(f"📈 Total matches: {len(submissions)}")
    
    # Recent activity
    recent = sorted(submissions, key=lambda x: x.get("submitted_at", ""), reverse=True)[:5]
    print("\n🕒 Recent Submissions:")
    for sub in recent:
        players_str = " vs ".join(sub.get("players", []))
        winner = sub.get("series_winner", "Unknown")
        submitted = sub.get("submitted_at", "Unknown")
        print(f"  {players_str} - Winner: {winner} ({submitted})")

if __name__ == "__main__":
    analyze_submissions()