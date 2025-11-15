"""
GitHub Actions - Replay Data Extraction Script
Extracts detailed replay information for match history and casting discovery.

Creates a comprehensive database of all replays with:
- Replay links, winners, dates, OpenSkill values
- Factions, match durations, maps
- Player match histories
- Searchable/filterable data for casters

Outputs to public/data/replay_database.json for web consumption
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import requests
import time

# Import extraction configuration
from extraction_config import (
    SUBMISSIONS_DIR,
    REPLAY_DATABASE_FILE,
    PLAYER_MATCH_HISTORY_FILE,
    BAR_API_BASE,
    REQUEST_DELAY,
    API_TIMEOUT_SECONDS,
    DEFAULT_MU,
    DEFAULT_SIGMA,
    SUBMISSION_FIELDS,
    MATCH_FIELDS,
    REPLAY_FIELDS,
    API_FIELDS,
    PLAYER_API_FIELDS,
    SEED_RATING_FIELDS,
    REPLAY_VIEW_BASE_URL,
    DURATION_TAG_THRESHOLDS,
    SKILL_TAG_THRESHOLDS,
    MAX_RECENT_MATCHES,
    DEFAULT_VALUES,
)


# ==============================
# BAR API utilities
# ==============================

def fetch_replay_details(replay_id: str) -> Optional[Dict[str, Any]]:
    """Fetch detailed replay information from BAR API."""
    try:
        url = f"{BAR_API_BASE}/replays/{replay_id}"
        response = requests.get(url, timeout=API_TIMEOUT_SECONDS)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch replay {replay_id}: HTTP {response.status_code}")
            return None
        
    except Exception as e:
        print(f"Error fetching replay {replay_id}: {e}")
        return None


def get_field_value(obj: Dict[str, Any], field_list: List[str], default: Any = None) -> Any:
    """Get value from object using field list (in order of preference)."""
    for field in field_list:
        value = obj.get(field)
        if value is not None:
            return value
    return default

def extract_faction_info(replay_data: Dict[str, Any]) -> Dict[str, str]:
    """Extract faction information for each player from replay data."""
    factions = {}
    
    # Try to get faction info from different possible locations in the API response
    ally_teams_field = API_FIELDS["AllyTeams"][0]
    teams = replay_data.get(ally_teams_field, [])
    if teams:
        for team in teams:
            players = team.get("Players", [])
            for player in players:
                name = get_field_value(player, PLAYER_API_FIELDS["name"], "")
                side = get_field_value(player, PLAYER_API_FIELDS["side"], "")
                if name and side:
                    factions[name] = side
    
    # Fallback: check other possible locations
    players_field = API_FIELDS["Players"][0]
    if not factions and players_field in replay_data:
        for player in replay_data[players_field]:
            name = get_field_value(player, PLAYER_API_FIELDS["name"], "")
            side = get_field_value(player, PLAYER_API_FIELDS["side"], "")
            if name and side:
                factions[name] = side
    
    return factions


# ==============================
# Data extraction
# ==============================

def process_submissions_for_replay_data() -> List[Dict[str, Any]]:
    """Process all submissions and extract detailed replay information."""
    submissions = []
    submissions_path = Path(SUBMISSIONS_DIR)

    if not submissions_path.exists():
        print("No submissions directory found")
        return []

    print("Loading submissions...")
    for file in sorted(submissions_path.glob("*.json")):
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                submissions.append(data)
                print(f"Loaded submission: {file.name}")
        except Exception as e:
            print(f"Failed to load {file.name}: {e}")

    return submissions


def extract_replay_database(submissions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract comprehensive replay database from submissions."""
    print("Extracting replay data...")
    
    replay_database = []
    processed_replays = set()  # Track already processed replay IDs
    
    for submission in submissions:
        submission_date = get_field_value(submission, SUBMISSION_FIELDS["submitted_at"], "")
        submitted_by = get_field_value(submission, SUBMISSION_FIELDS["submitted_by"], DEFAULT_VALUES["submitted_by"])
        players = get_field_value(submission, SUBMISSION_FIELDS["players"], [])
        series_winner = get_field_value(submission, SUBMISSION_FIELDS["series_winner"], DEFAULT_VALUES["series_winner"])
        
        # Process matches (newer format)
        matches = get_field_value(submission, SUBMISSION_FIELDS["matches"], [])
        for match in matches:
            replay_id = get_field_value(match, MATCH_FIELDS["id"], "")
            if not replay_id or replay_id in processed_replays:
                continue
                
            processed_replays.add(replay_id)
            
            # Extract basic info from submission
            winner = get_field_value(match, MATCH_FIELDS["winner"], "")
            map_name = get_field_value(match, MATCH_FIELDS["map"], DEFAULT_VALUES["map"])
            duration_ms = get_field_value(match, MATCH_FIELDS["duration_ms"], 0)
            seed_ratings = get_field_value(match, MATCH_FIELDS["seed_ratings"], {})
            
            # Fetch additional details from BAR API
            print(f"  Fetching details for replay {replay_id}...")
            api_data = fetch_replay_details(replay_id)
            time.sleep(REQUEST_DELAY)  # Be respectful to the API
            
            # Extract faction information
            factions = {}
            start_time = None
            engine_version = DEFAULT_VALUES["engine_version"]
            game_version = DEFAULT_VALUES["game_version"]
            
            if api_data:
                factions = extract_faction_info(api_data)
                start_time = get_field_value(api_data, API_FIELDS["startTime"], None)
                engine_version = get_field_value(api_data, API_FIELDS["engineVersion"], DEFAULT_VALUES["engine_version"])
                game_version = get_field_value(api_data, API_FIELDS["gameVersion"], DEFAULT_VALUES["game_version"])
            
            # Build player info
            player_info = []
            for player in players:
                player_data = {
                    "name": player,
                    "faction": factions.get(player, DEFAULT_VALUES["faction"]),
                    "is_winner": player == winner
                }
                
                # Add OpenSkill info if available
                if player in seed_ratings:
                    mu = get_field_value(seed_ratings[player], SEED_RATING_FIELDS["mu"], DEFAULT_MU)
                    sigma = get_field_value(seed_ratings[player], SEED_RATING_FIELDS["sigma"], DEFAULT_SIGMA)
                    player_data["mu"] = mu
                    player_data["sigma"] = sigma
                    player_data["skill_estimate"] = mu - sigma
                
                player_info.append(player_data)
            
            # Create replay entry
            replay_entry = {
                "id": replay_id,
                "url": f"{REPLAY_VIEW_BASE_URL}{replay_id}",
                "date": start_time or submission_date,
                "submitted_at": submission_date,
                "submitted_by": submitted_by,
                "map": map_name,
                "duration_ms": duration_ms,
                "duration_formatted": format_duration(duration_ms),
                "winner": winner,
                "players": player_info,
                "player_names": players,
                "series_winner": series_winner,
                "engine_version": engine_version,
                "game_version": game_version,
                "is_tournament": True,  # All submissions are tournament games
                "tags": generate_replay_tags(player_info, duration_ms, map_name)
            }
            
            replay_database.append(replay_entry)
        
        # Process replays (older format)
        replays = get_field_value(submission, SUBMISSION_FIELDS["replays"], [])
        for replay in replays:
            replay_id = get_field_value(replay, REPLAY_FIELDS["id"], "")
            if not replay_id or replay_id in processed_replays:
                continue
                
            processed_replays.add(replay_id)
            
            # Extract basic info
            winner = get_field_value(replay, REPLAY_FIELDS["winner"], "")
            map_name = get_field_value(replay, REPLAY_FIELDS["mapname"], DEFAULT_VALUES["map"])
            duration_ms = get_field_value(replay, REPLAY_FIELDS["duration_ms"], 0)
            start_time = get_field_value(replay, REPLAY_FIELDS["startTime"], "")
            replay_players = get_field_value(replay, REPLAY_FIELDS["players"], [])
            
            # Fetch additional details from BAR API
            print(f"  Fetching details for replay {replay_id}...")
            api_data = fetch_replay_details(replay_id)
            time.sleep(REQUEST_DELAY)
            
            # Extract faction information
            factions = {}
            engine_version = DEFAULT_VALUES["engine_version"]
            game_version = DEFAULT_VALUES["game_version"]
            
            if api_data:
                factions = extract_faction_info(api_data)
                engine_version = get_field_value(api_data, API_FIELDS["engineVersion"], DEFAULT_VALUES["engine_version"])
                game_version = get_field_value(api_data, API_FIELDS["gameVersion"], DEFAULT_VALUES["game_version"])
            
            # Build player info
            player_info = []
            for player_data in replay_players:
                name = get_field_value(player_data, ["name"], "")
                skill = get_field_value(player_data, ["skill"], DEFAULT_MU)
                
                player_entry = {
                    "name": name,
                    "faction": factions.get(name, DEFAULT_VALUES["faction"]),
                    "is_winner": name == winner,
                    "skill_estimate": skill
                }
                
                player_info.append(player_entry)
            
            # Create replay entry
            replay_entry = {
                "id": replay_id,
                "url": f"{REPLAY_VIEW_BASE_URL}{replay_id}",
                "date": start_time or submission_date,
                "submitted_at": submission_date,
                "submitted_by": submitted_by,
                "map": map_name,
                "duration_ms": duration_ms,
                "duration_formatted": format_duration(duration_ms),
                "winner": winner,
                "players": player_info,
                "player_names": [p["name"] for p in player_info],
                "series_winner": series_winner,
                "engine_version": engine_version,
                "game_version": game_version,
                "is_tournament": True,
                "tags": generate_replay_tags(player_info, duration_ms, map_name)
            }
            
            replay_database.append(replay_entry)
    
    # Sort by date (newest first)
    replay_database.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    print(f"Extracted {len(replay_database)} replay entries")
    return replay_database


def generate_replay_tags(player_info: List[Dict[str, Any]], duration_ms: int, map_name: str) -> List[str]:
    """Generate searchable tags for the replay using configuration."""
    tags = []
    
    # Duration-based tags
    duration_minutes = duration_ms / (1000 * 60)
    for tag_name, threshold in sorted(DURATION_TAG_THRESHOLDS.items(), key=lambda x: x[1]):
        if duration_minutes < threshold:
            tags.append(tag_name)
            break
    
    # Skill-based tags
    skills = [p.get("skill_estimate", 0) for p in player_info if "skill_estimate" in p]
    if skills:
        avg_skill = sum(skills) / len(skills)
        for tag_name, threshold in sorted(SKILL_TAG_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if avg_skill > threshold:
                tags.append(tag_name)
                break
    
    # Faction tags
    factions = [p.get("faction", "") for p in player_info]
    unique_factions = set(f for f in factions if f and f != DEFAULT_VALUES["faction"])
    if len(unique_factions) > 1:
        tags.append("mixed-factions")
    elif len(unique_factions) == 1:
        faction = list(unique_factions)[0].lower()
        tags.append(f"all-{faction}")
    
    # Map tags
    if map_name and map_name != DEFAULT_VALUES["map"]:
        # Clean map name for tag
        clean_map = map_name.lower().replace(" ", "-").replace(".", "")
        tags.append(f"map-{clean_map}")
    
    return tags


def generate_player_match_history(replay_database: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate player-specific match history."""
    print("Generating player match histories...")
    
    player_histories = {}
    
    for replay in replay_database:
        for player_data in replay["players"]:
            player_name = player_data["name"]
            
            if player_name not in player_histories:
                player_histories[player_name] = {
                    "player": player_name,
                    "total_matches": 0,
                    "wins": 0,
                    "losses": 0,
                    "recent_matches": [],
                    "favorite_factions": {},
                    "maps_played": {},
                    "opponents_faced": {},
                    "avg_match_duration": 0,
                    "skill_progression": []
                }
            
            history = player_histories[player_name]
            
            # Basic stats
            history["total_matches"] += 1
            if player_data["is_winner"]:
                history["wins"] += 1
            else:
                history["losses"] += 1
            
            # Track faction usage
            faction = player_data.get("faction", "Unknown")
            if faction != "Unknown":
                history["favorite_factions"][faction] = history["favorite_factions"].get(faction, 0) + 1
            
            # Track maps
            map_name = replay["map"]
            if map_name:
                history["maps_played"][map_name] = history["maps_played"].get(map_name, 0) + 1
            
            # Track opponents
            for other_player in replay["players"]:
                if other_player["name"] != player_name:
                    opp_name = other_player["name"]
                    history["opponents_faced"][opp_name] = history["opponents_faced"].get(opp_name, 0) + 1
            
            # Add to recent matches (keep last N)
            match_summary = {
                "date": replay["date"],
                "replay_id": replay["id"],
                "map": replay["map"],
                "duration_formatted": replay["duration_formatted"],
                "won": player_data["is_winner"],
                "opponent": [p["name"] for p in replay["players"] if p["name"] != player_name][0] if len(replay["players"]) == 2 else "Multiple",
                "faction": faction
            }
            
            history["recent_matches"].append(match_summary)
            if len(history["recent_matches"]) > MAX_RECENT_MATCHES:
                history["recent_matches"] = history["recent_matches"][-MAX_RECENT_MATCHES:]
            
            # Track skill progression
            if "skill_estimate" in player_data:
                history["skill_progression"].append({
                    "date": replay["date"],
                    "skill": player_data["skill_estimate"],
                    "replay_id": replay["id"]
                })
    
    # Calculate derived stats
    for player, history in player_histories.items():
        # Win rate
        total = history["total_matches"]
        history["win_rate"] = round((history["wins"] / total) * 100, 1) if total > 0 else 0
        
        # Most played faction
        if history["favorite_factions"]:
            history["most_played_faction"] = max(history["favorite_factions"].items(), key=lambda x: x[1])[0]
        else:
            history["most_played_faction"] = "Unknown"
        
        # Sort recent matches by date (newest first)
        history["recent_matches"].sort(key=lambda x: x["date"], reverse=True)
        
        # Sort skill progression by date
        history["skill_progression"].sort(key=lambda x: x["date"])
    
    return player_histories


def format_duration(duration_ms: int) -> str:
    """Format duration from milliseconds to human readable format."""
    if duration_ms <= 0:
        return "Unknown"
    
    total_seconds = duration_ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    
    if minutes >= 60:
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours}h {minutes}m {seconds}s"
    else:
        return f"{minutes}m {seconds}s"


# ==============================
# Main functions
# ==============================

def extract_replay_data():
    """Main function to extract replay data."""
    print("Extracting replay data...")
    
    # Load submissions
    submissions = process_submissions_for_replay_data()
    print(f"Found {len(submissions)} submissions")
    
    # Extract replay database
    replay_database = extract_replay_database(submissions)
    
    # Generate player match histories
    player_histories = generate_player_match_history(replay_database)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(REPLAY_DATABASE_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(PLAYER_MATCH_HISTORY_FILE), exist_ok=True)
    
    # Save replay database
    with open(REPLAY_DATABASE_FILE, 'w') as f:
        json.dump(replay_database, f, indent=2)
    
    # Save player match histories
    with open(PLAYER_MATCH_HISTORY_FILE, 'w') as f:
        json.dump(player_histories, f, indent=2)
    
    print(f"Replay database saved to {REPLAY_DATABASE_FILE}")
    print(f"Player match histories saved to {PLAYER_MATCH_HISTORY_FILE}")
    print(f"Updated at {datetime.now(timezone.utc).isoformat()}Z")
    
    # Print summary
    if replay_database:
        print(f"\nSummary:")
        print(f"  Total replays: {len(replay_database)}")
        print(f"  Players tracked: {len(player_histories)}")
        
        # Show some interesting stats
        maps_played = {}
        total_duration = 0
        for replay in replay_database:
            map_name = replay.get("map", "Unknown")
            maps_played[map_name] = maps_played.get(map_name, 0) + 1
            total_duration += replay.get("duration_ms", 0)
        
        print(f"  Total playtime: {format_duration(total_duration)}")
        print(f"  Unique maps: {len(maps_played)}")
        
        if maps_played:
            most_popular_map = max(maps_played.items(), key=lambda x: x[1])
            print(f"  Most popular map: {most_popular_map[0]} ({most_popular_map[1]} games)")


if __name__ == "__main__":
    try:
        extract_replay_data()
        print("\nReplay data extraction complete!")
        sys.exit(0)
    except Exception as e:
        print(f"\nExtraction failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)