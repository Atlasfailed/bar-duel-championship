#!/usr/bin/env python3
"""
Simple CSV to submissions converter - creates local submission files
"""

import csv
import json
import os
from datetime import datetime, timezone

def create_submission_from_csv_row(row, index):
    """Create a submission file from a CSV row"""
    
    # Parse CSV data
    players_str = row['players']
    winner = row['winner']
    score = row['score']
    replay_urls = row['replay_urls'].split(',')
    
    # Parse players
    players = [p.strip() for p in players_str.split(' vs ')]
    if len(players) != 2:
        print(f"❌ Invalid players: {players_str}")
        return False
    
    player1, player2 = players
    
    # Extract replay IDs from URLs
    replay_ids = []
    matches = []
    
    for i, url in enumerate(replay_urls):
        replay_id = url.strip().split('/')[-1]
        replay_ids.append(replay_id)
        
        # Create match data with fake but realistic values
        match = {
            "id": replay_id,
            "map": f"Map_{i+1}",
            "winner": winner if i == len(replay_urls) - 1 else (player1 if i % 2 == 0 else player2),
            "duration_ms": 600000 + (i * 120000),  # 10-30 min matches
            "seed_ratings": {
                player1: {"mu": 16.67, "sigma": 5.56},
                player2: {"mu": 16.67, "sigma": 5.56}
            }
        }
        matches.append(match)
    
    # Count wins based on score
    if '3-0' in score:
        if winner == player1:
            wins = {player1: 3, player2: 0}
        else:
            wins = {player2: 3, player1: 0}
    elif '2-1' in score:
        if winner == player1:
            wins = {player1: 2, player2: 1}
        else:
            wins = {player2: 2, player1: 1}
    elif '2-0' in score:
        if winner == player1:
            wins = {player1: 2, player2: 0}
        else:
            wins = {player2: 2, player1: 0}
    else:
        # Default to 2-1
        if winner == player1:
            wins = {player1: 2, player2: 1}
        else:
            wins = {player2: 2, player1: 1}
    
    # Create submission data
    submission_data = {
        "players": players,
        "series_winner": winner,
        "wins": wins,
        "total_games": len(matches),
        "matches": matches
    }
    
    # Create filename
    timestamp = int(datetime.now(timezone.utc).timestamp()) + index  # Add index to avoid duplicates
    filename = f"{timestamp}_{player1}_vs_{player2}_{'_'.join(replay_ids[:3])}.json"
    
    # Ensure directory exists
    os.makedirs("submissions/bo3", exist_ok=True)
    
    # Write file
    filepath = f"submissions/bo3/{filename}"
    with open(filepath, 'w') as f:
        json.dump(submission_data, f, indent=2)
    
    print(f"✅ Created: {filename}")
    print(f"   {players_str} → {winner} wins {score}")
    
    return True

def main():
    """Process CSV and create submissions"""
    csv_file = "examples/bo3_samples.csv"
    limit = 30
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    print(f"🚀 Creating submissions from {csv_file}")
    print(f"🎯 Limit: {limit} submissions")
    
    created = 0
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            if created >= limit:
                break
                
            if create_submission_from_csv_row(row, i):
                created += 1
    
    print(f"\n🎉 Created {created} submission files!")
    print(f"📁 Files saved to submissions/bo3/")
    print(f"🔄 Next: Run 'python3 actions/recalculate_leaderboard.py' to update rankings")

if __name__ == "__main__":
    main()