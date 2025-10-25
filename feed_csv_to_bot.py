#!/usr/bin/env python3
"""
Script to feed CSV replay data to create submissions like the Discord bot would
Processes bo3_samples.csv and creates JSON files in submissions/bo3/
"""

import csv
import json
import sys
import os
import asyncio
import aiohttp
from datetime import datetime, timezone
from pathlib import Path

async def fetch_replay(session: aiohttp.ClientSession, url: str) -> dict:
    """Fetch replay JSON from API"""
    try:
        async with session.get(url, timeout=15) as response:
            if response.status != 200:
                raise ValueError(f"Failed to fetch replay: HTTP {response.status}")
            return await response.json()
    except Exception as e:
        print(f"   ❌ Error fetching {url}: {e}")
        return None

def validate_replay(replay: dict) -> dict:
    """Validate and extract replay data"""
    if not replay:
        return None
        
    try:
        host_settings = replay.get("hostSettings", {})
        map_name = host_settings.get("mapname", "Unknown")
        
        # Get replay ID from URL or other source
        replay_id = replay.get("id", "unknown")
        
        # Get all players from AllyTeams
        players_data = []
        ally_teams = replay.get("AllyTeams", [])
        
        for ally_team in ally_teams:
            team_players = ally_team.get("Players", [])
            for player in team_players:
                team_id = player.get("teamId")
                if team_id is not None and team_id >= 0:
                    players_data.append(player)
        
        if len(players_data) != 2:
            print(f"   ⚠️  Expected 2 players, found {len(players_data)}")
            return None
        
        # Parse skills and determine winner
        player1, player2 = players_data
        p1_name = player1.get("name", "Unknown")
        p2_name = player2.get("name", "Unknown")
        
        # Simple skill parsing
        def parse_skill(skill_value):
            if isinstance(skill_value, (int, float)):
                return float(skill_value)
            if isinstance(skill_value, str):
                try:
                    # Handle formats like '[16.67]'
                    cleaned = skill_value.strip('[]')
                    return float(cleaned)
                except:
                    return 25.0  # Default
            return 25.0
        
        p1_skill = parse_skill(player1.get("skill"))
        p2_skill = parse_skill(player2.get("skill"))
        
        # Determine winner (this is simplified - in real replays you'd check who won)
        winner = p1_name  # We'll override this with CSV data
        
        return {
            "id": replay_id,
            "map": map_name,
            "winner": winner,
            "duration_ms": replay.get("durationMs", 0),
            "seed_ratings": {
                p1_name: {"mu": p1_skill, "sigma": p1_skill / 3.0},
                p2_name: {"mu": p2_skill, "sigma": p2_skill / 3.0}
            }
        }
    except Exception as e:
        print(f"   ❌ Error validating replay: {e}")
        return None

async def process_csv_submissions(csv_file: str, limit: int = 30):
    """Process CSV file and create bot submissions"""
    print(f"🔄 Processing {csv_file} (limit: {limit} submissions)")
    
    submissions_processed = 0
    
    # Ensure submissions directory exists
    os.makedirs("submissions/bo3", exist_ok=True)
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            if submissions_processed >= limit:
                break
                
            # Extract data from CSV row
            bo3_id = row['bo3_id']
            players_str = row['players']
            winner = row['winner']
            score = row['score']
            replay_urls = row['replay_urls'].split(',')
            description = row['description']
            
            print(f"\n📋 Processing {bo3_id}: {players_str}")
            print(f"   Winner: {winner} ({score})")
            print(f"   Replays: {len(replay_urls)}")
            
            # Parse players
            players = [p.strip() for p in players_str.split(' vs ')]
            if len(players) != 2:
                print(f"❌ Invalid players format: {players_str}")
                continue
            
            # Clean up replay URLs and extract IDs
            replay_urls = [url.strip() for url in replay_urls]
            replay_ids = []
            validated_matches = []
            
            try:
                # Process each replay URL
                print("   🔍 Processing replays...")
                async with aiohttp.ClientSession() as session:
                    for i, url in enumerate(replay_urls):
                        # Extract replay ID from URL
                        replay_id = url.split('/')[-1]
                        replay_ids.append(replay_id)
                        
                        # Fetch replay data
                        replay_data = await fetch_replay(session, url)
                        validated_replay = validate_replay(replay_data)
                        
                        if validated_replay:
                            # Override winner with CSV data for the final match
                            if i == len(replay_urls) - 1:  # Last match determines series
                                validated_replay["winner"] = winner
                            validated_matches.append(validated_replay)
                            print(f"   ✅ Processed replay {replay_id}")
                        else:
                            print(f"   ❌ Failed to validate replay {replay_id}")
                
                if len(validated_matches) < 2:
                    print(f"❌ Not enough valid replays for {bo3_id}")
                    continue
                
                # Count wins for each player based on CSV winner
                player1, player2 = players
                if winner == player1:
                    if '3-0' in score:
                        wins = {player1: 3, player2: 0}
                    elif '2-1' in score:
                        wins = {player1: 2, player2: 1}
                    elif '2-0' in score:
                        wins = {player1: 2, player2: 0}
                    else:
                        wins = {player1: 2, player2: 1}  # Default
                else:
                    if '3-0' in score:
                        wins = {player2: 3, player1: 0}
                    elif '2-1' in score:
                        wins = {player2: 2, player1: 1}
                    elif '2-0' in score:
                        wins = {player2: 2, player1: 0}
                    else:
                        wins = {player2: 2, player1: 1}  # Default
                
                # Create submission data structure
                submission_data = {
                    "players": players,
                    "series_winner": winner,
                    "wins": wins,
                    "total_games": len(validated_matches),
                    "matches": validated_matches
                }
                
                print(f"   📊 Series: {submission_data['wins']}")
                
                # Create submission file
                timestamp = int(datetime.now(timezone.utc).timestamp())
                filename = f"{timestamp}_{player1}_vs_{player2}_{'_'.join(replay_ids[:3])}.json"
                filepath = f"submissions/bo3/{filename}"
                
                with open(filepath, 'w') as f:
                    json.dump(submission_data, f, indent=2)
                
                print(f"   ✅ Created submission: {filename}")
                submissions_processed += 1
                
                # Add delay to avoid hitting API limits
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Error processing {bo3_id}: {e}")
                continue
    
    print(f"\n🎉 Processed {submissions_processed} submissions successfully!")
    print(f"📁 Files created in submissions/bo3/")
    print(f"🔄 Run 'python actions/update_leaderboard.py' to update rankings")

async def main():
    """Main function"""
    csv_file = "examples/bo3_samples.csv"
    limit = 30
    
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    print("🚀 Starting CSV to Bot submission processor")
    print(f"📁 CSV file: {csv_file}")
    print(f"🎯 Limit: {limit} submissions")
    
    await process_csv_submissions(csv_file, limit)

if __name__ == "__main__":
    asyncio.run(main())