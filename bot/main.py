#!IMPORTANT
# bot is running at https://www.pella.app/server/d6b8888df5f04ad18463ce985baabe21/overview

"""
Standalone Discord Bot for BAR League
Single-file implementation - only handles /submit command
Optimized for minimal hosting costs
"""

import asyncio
import aiohttp
import json
import os
import re
import base64
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Tuple
import discord
from discord import app_commands
from dotenv import load_dotenv

# Import bot verification configuration
from config import (
    REPLAY_URL_PATTERN,
    REQUIRED_PLAYER_COUNT,
    MIN_TEAM_ID,
    DEFAULT_SIGMA,
    MIN_REPLAYS,
    MAX_REPLAYS,
    REQUIRED_WINS_FOR_SERIES,
    MAX_REPLAY_AGE_DAYS as CONFIG_MAX_REPLAY_AGE_DAYS,
    MAX_TIME_BETWEEN_REPLAYS_DAYS as CONFIG_MAX_TIME_BETWEEN_REPLAYS_DAYS,
    API_TIMEOUT_SECONDS,
    PLAYER_NAME_FIELDS,
    SKILL_FIELDS,
    SIGMA_FIELDS,
    TEAM_ID_FIELDS,
    WINNER_ID_FIELDS,
    START_TIME_FIELDS,
    DURATION_FIELDS,
    MAP_NAME_FIELDS,
    ALLY_TEAMS_PATH,
    PLAYERS_PATH,
    HOST_SETTINGS_PATH,
    GAMESTATS_PATH,
)

# Load environment
load_dotenv()

# Configuration (environment variables)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.getenv("GITHUB_REPO", "Atlasfailed/bar-duel-championship").strip()
GITHUB_BASE_BRANCH = os.getenv("GITHUB_BASE_BRANCH", "main").strip()

# Allow environment override for replay age (defaults to config value)
MAX_REPLAY_AGE_DAYS = int(os.getenv("MAX_REPLAY_AGE_DAYS", str(CONFIG_MAX_REPLAY_AGE_DAYS)))
MAX_TIME_BETWEEN_REPLAYS_DAYS = int(os.getenv("MAX_TIME_BETWEEN_REPLAYS_DAYS", str(CONFIG_MAX_TIME_BETWEEN_REPLAYS_DAYS)))

if not DISCORD_TOKEN:
    raise RuntimeError("❌ DISCORD_TOKEN required in .env file")

# Submission tracking
SUBMISSIONS_FILE = "data/submissions_index.json"

# ====== HELPER FUNCTIONS ======

def load_submissions() -> set:
    """Load previously submitted replay IDs"""
    if not os.path.exists(SUBMISSIONS_FILE):
        return set()
    try:
        with open(SUBMISSIONS_FILE, "r") as f:
            data = json.load(f)
            return set(data) if isinstance(data, list) else set()
    except:
        return set()

def save_submissions(submissions: set):
    """Save submitted replay IDs"""
    os.makedirs(os.path.dirname(SUBMISSIONS_FILE), exist_ok=True)
    with open(SUBMISSIONS_FILE, "w") as f:
        json.dump(sorted(list(submissions)), f, indent=2)

def extract_replay_ids(urls: List[str]) -> List[str]:
    """Extract replay IDs from URLs"""
    ids = []
    for url in urls:
        match = REPLAY_URL_PATTERN.match(url.strip())
        if not match:
            raise ValueError(f"Invalid replay URL format: {url}")
        ids.append(match.group(1))
    return ids

async def fetch_replay(session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
    """Fetch replay JSON from API"""
    async with session.get(url, timeout=API_TIMEOUT_SECONDS) as response:
        if response.status != 200:
            raise ValueError(f"Failed to fetch replay: HTTP {response.status}")
        return await response.json()

def validate_replay(replay: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and extract replay data using configuration"""
    host_settings = replay.get(HOST_SETTINGS_PATH, {})
    map_name = host_settings.get(MAP_NAME_FIELDS[0], "Unknown")
    
    # Get all players from ALL AllyTeams (not just the first one)
    players_data = []
    ally_teams = replay.get(ALLY_TEAMS_PATH, [])
    
    for ally_team in ally_teams:
        team_players = ally_team.get(PLAYERS_PATH, [])
        for player in team_players:
            # Only include actual players (with valid team IDs), exclude spectators/bots
            team_id = None
            for field in TEAM_ID_FIELDS:
                team_id = player.get(field)
                if team_id is not None:
                    break
            
            if team_id is not None and team_id >= MIN_TEAM_ID:
                players_data.append(player)
    
    if len(players_data) != REQUIRED_PLAYER_COUNT:
        raise ValueError(f"Replay must have exactly {REQUIRED_PLAYER_COUNT} players, found {len(players_data)} (excluding spectators)")
    
    def parse_skill(skill_value):
        """Parse skill value, handling formats like '[16.67]' or '16.67' or numbers"""
        if not skill_value:
            return 0.0
        
        # Convert to string and strip whitespace
        skill_str = str(skill_value).strip()
        
        # Remove square brackets if present
        if skill_str.startswith('[') and skill_str.endswith(']'):
            skill_str = skill_str[1:-1]
        
        try:
            return float(skill_str)
        except (ValueError, TypeError):
            return 0.0
    
    def get_field_value(obj: Dict, field_list: List[str], default: Any = None):
        """Get value from object using field list (in order of preference)"""
        for field in field_list:
            value = obj.get(field)
            if value is not None:
                return value
        return default
    
    players = []
    seed_ratings = {}
    for p in players_data:
        name = get_field_value(p, PLAYER_NAME_FIELDS, "Unknown")
        mu = parse_skill(get_field_value(p, SKILL_FIELDS))
        sigma = parse_skill(get_field_value(p, SIGMA_FIELDS))
        
        # If sigma is 0, use default OpenSkill initial uncertainty
        if sigma == 0.0:
            sigma = DEFAULT_SIGMA
        
        players.append({"name": name, "skill": mu})
        seed_ratings[name] = {"mu": mu, "sigma": sigma}
    
    # Try to get winner from gamestats first (preferred method)
    gamestats = replay.get(GAMESTATS_PATH, {})
    winner_id = get_field_value(gamestats, WINNER_ID_FIELDS) if gamestats else None
    winner = None
    
    if winner_id is not None:
        # Winner from gamestats.winningTeamId
        for p in players_data:
            p_team_id = get_field_value(p, TEAM_ID_FIELDS)
            if p_team_id == winner_id:
                winner = get_field_value(p, PLAYER_NAME_FIELDS)
                break
    else:
        # Fallback: Check AllyTeams for winningTeam field
        ally_teams = replay.get(ALLY_TEAMS_PATH, [])
        for ally_team in ally_teams:
            if ally_team.get("winningTeam") is True:
                team_players = ally_team.get(PLAYERS_PATH, [])
                for player in team_players:
                    team_id = get_field_value(player, TEAM_ID_FIELDS)
                    if team_id is not None and team_id >= MIN_TEAM_ID:
                        winner = get_field_value(player, PLAYER_NAME_FIELDS)
                        break
                if winner:
                    break
    
    start_time = get_field_value(replay, START_TIME_FIELDS, "")
    duration_ms = get_field_value(replay, DURATION_FIELDS, 0)
    
    return {
        "id": replay.get("id", ""),
        "mapname": map_name,
        "players": players,
        "seed_ratings": seed_ratings,
        "winner": winner,
        "startTime": start_time,
        "duration_ms": duration_ms,
    }

def check_bo3_validity(replays: List[Dict[str, Any]]) -> Tuple[bool, str, str, Dict[str, int], str]:
    """Check if replays form a valid Bo3 using configuration"""
    all_player_sets = []
    for r in replays:
        player_names = {p["name"] for p in r["players"]}
        all_player_sets.append(player_names)
    
    if not all(s == all_player_sets[0] for s in all_player_sets):
        raise ValueError("All replays must have the same 2 players")
    
    player_names = sorted(list(all_player_sets[0]))
    if len(player_names) != REQUIRED_PLAYER_COUNT:
        raise ValueError(f"Must have exactly {REQUIRED_PLAYER_COUNT} players")
    
    wins = {name: 0 for name in player_names}
    for r in replays:
        if r["winner"] and r["winner"] in wins:
            wins[r["winner"]] += 1
    
    series_winner = None
    for name, count in wins.items():
        if count >= REQUIRED_WINS_FOR_SERIES:
            series_winner = name
            break
    
    return True, player_names[0], player_names[1], wins, series_winner

async def create_github_pr(session: aiohttp.ClientSession, payload: Dict, replay_ids: List[str]) -> str:
    """Create GitHub PR for submission"""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        raise RuntimeError("GitHub integration not configured")
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "bar-duel-championship-bot",
    }
    
    owner, repo = GITHUB_REPO.split("/", 1)
    api = "https://api.github.com"
    
    # Get base ref
    async with session.get(f"{api}/repos/{owner}/{repo}/git/ref/heads/{GITHUB_BASE_BRANCH}", 
                          headers=headers, timeout=API_TIMEOUT_SECONDS) as r:
        if r.status != 200:
            raise RuntimeError(f"Failed to get base branch: HTTP {r.status}")
        ref_data = await r.json()
    base_sha = ref_data["object"]["sha"]
    
    # Create branch
    timestamp = int(datetime.now(timezone.utc).timestamp())
    p1 = re.sub(r"[^A-Za-z0-9_\-]+", "-", payload["players"][0])[:24]
    p2 = re.sub(r"[^A-Za-z0-9_\-]+", "-", payload["players"][1])[:24]
    branch_name = f"submissions/bo3-{timestamp}-{p1}-vs-{p2}"
    
    async with session.post(f"{api}/repos/{owner}/{repo}/git/refs",
                           headers=headers,
                           json={"ref": f"refs/heads/{branch_name}", "sha": base_sha},
                           timeout=API_TIMEOUT_SECONDS) as r:
        if r.status not in (200, 201):
            raise RuntimeError(f"Failed to create branch: HTTP {r.status}")
    
    # Create file
    file_path = f"submissions/bo3/{timestamp}_{p1}_vs_{p2}_{'-'.join(replay_ids)}.json"
    content_b64 = base64.b64encode(json.dumps(payload, indent=2).encode()).decode()
    
    async with session.put(f"{api}/repos/{owner}/{repo}/contents/{file_path}",
                          headers=headers,
                          json={
                              "message": f"Add Bo3: {payload['players'][0]} vs {payload['players'][1]}",
                              "content": content_b64,
                              "branch": branch_name
                          },
                          timeout=API_TIMEOUT_SECONDS) as r:
        if r.status not in (200, 201):
            raise RuntimeError(f"Failed to create file: HTTP {r.status}")
    
    # Create PR
    async with session.post(f"{api}/repos/{owner}/{repo}/pulls",
                           headers=headers,
                           json={
                               "title": f"Bo3 Submission: {payload['players'][0]} vs {payload['players'][1]}",
                               "head": branch_name,
                               "base": GITHUB_BASE_BRANCH,
                               "body": f"Automated Bo3 submission\n\nReplays: {', '.join(replay_ids)}"
                           },
                           timeout=API_TIMEOUT_SECONDS) as r:
        if r.status not in (200, 201):
            raise RuntimeError(f"Failed to create PR: HTTP {r.status}")
        pr_data = await r.json()
    
    return pr_data["html_url"]

# ====== DISCORD BOT SETUP ======

intents = discord.Intents.default()
# Note: message_content intent not needed since we only use slash commands
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@tree.command(name="submit", description="Submit Bo3 match replays")
@app_commands.describe(replays="Comma-separated replay URLs (2-3 replays)")
async def submit(interaction: discord.Interaction, replays: str):
    """Handle /submit command"""
    await interaction.response.defer(ephemeral=True)
    
    # Parse URLs
    urls = [u.strip() for u in replays.split(",") if u.strip()]
    if len(urls) < MIN_REPLAYS:
        return await interaction.followup.send(f"❌ Need at least {MIN_REPLAYS} replay URLs", ephemeral=True)
    if len(urls) > MAX_REPLAYS:
        return await interaction.followup.send(f"❌ Maximum {MAX_REPLAYS} replay URLs", ephemeral=True)
    
    # Extract IDs
    try:
        replay_ids = extract_replay_ids(urls)
    except ValueError as e:
        return await interaction.followup.send(f"❌ {e}", ephemeral=True)
    
    # Check for duplicates
    if len(replay_ids) != len(set(replay_ids)):
        return await interaction.followup.send("❌ Duplicate replay IDs in submission", ephemeral=True)
    
    submissions = load_submissions()
    already_submitted = [rid for rid in replay_ids if rid in submissions]
    if already_submitted:
        return await interaction.followup.send(
            f"❌ Already submitted: {', '.join(already_submitted)}", 
            ephemeral=True
        )
    
    # Fetch and validate replays
    try:
        async with aiohttp.ClientSession() as session:
            replay_data = await asyncio.gather(*[fetch_replay(session, url) for url in urls])
            validated = [validate_replay(r) for r in replay_data]
    except ValueError as e:
        return await interaction.followup.send(f"❌ Validation error: {e}", ephemeral=True)
    except Exception as e:
        return await interaction.followup.send(f"❌ Error fetching replays: {e}", ephemeral=True)
    
    # Validate Bo3
    try:
        valid, p1, p2, wins, series_winner = check_bo3_validity(validated)
    except ValueError as e:
        return await interaction.followup.send(f"❌ {e}", ephemeral=True)
    
    if not series_winner:
        # Check which replays are missing winner info
        missing_winners = []
        for i, replay in enumerate(validated, 1):
            if not replay.get("winner"):
                missing_winners.append(f"{i}. `{replay['id']}`")
        
        if missing_winners:
            error_msg = [
                f"❌ Cannot determine series winner: {len(missing_winners)} replay(s) missing winner information",
                "",
                "**Replays without winner data:**",
                "\n".join(missing_winners),
                "",
                "⚠️ The BAR API doesn't always include winner information for replays.",
                "Please verify the replays manually or try submitting different replays."
            ]
            return await interaction.followup.send("\n".join(error_msg), ephemeral=True)
        else:
            # All replays have winners but no one has 2+ wins (tie scenario)
            wins_str = ", ".join([f"{name}: {count}" for name, count in wins.items()])
            return await interaction.followup.send(
                f"❌ No clear winner (need {REQUIRED_WINS_FOR_SERIES}+ wins). Current wins: {wins_str}",
                ephemeral=True
            )
    
    # Check replay age
    now = datetime.now(timezone.utc)
    for replay in validated:
        start_time = replay.get("startTime")
        replay_id = replay.get("id", "unknown")
        
        if not start_time:
            # No startTime - reject to be safe (replays should have timestamps)
            return await interaction.followup.send(
                f"❌ Replay `{replay_id}` is missing startTime field and cannot be validated",
                ephemeral=True
            )
        
        try:
            # Handle ISO format with or without Z
            start_str = start_time.replace("Z", "+00:00") if start_time.endswith("Z") else start_time
            start = datetime.fromisoformat(start_str)
            age = (now - start).days
            
            if age > MAX_REPLAY_AGE_DAYS:
                return await interaction.followup.send(
                    f"❌ Replay `{replay_id}` is {age} days old (max: {MAX_REPLAY_AGE_DAYS} days)",
                    ephemeral=True
                )
        except ValueError as e:
            # Date parsing error - reject to be safe
            return await interaction.followup.send(
                f"❌ Replay `{replay_id}` has invalid startTime format: {start_time}",
                ephemeral=True
            )
        except Exception as e:
            # Unexpected error - log and reject to be safe
            print(f"Error checking replay age for {replay_id}: {e}")
            return await interaction.followup.send(
                f"❌ Error validating replay `{replay_id}` age: {e}",
                ephemeral=True
            )
    
    # Create submission payload
    payload = {
        "players": [p1, p2],
        "series_winner": series_winner,
        "wins": wins,
        "total_games": len(validated),
        "matches": [
            {
                "id": r["id"],
                "map": r["mapname"],
                "winner": r["winner"],
                "duration_ms": r["duration_ms"],
                "seed_ratings": r["seed_ratings"]
            }
            for r in validated
        ],
        "submitted_at": now.isoformat(),
        "submitted_by": str(interaction.user)
    }
    
    # Create GitHub PR
    try:
        async with aiohttp.ClientSession() as session:
            pr_url = await create_github_pr(session, payload, replay_ids)
    except Exception as e:
        return await interaction.followup.send(f"❌ GitHub error: {e}", ephemeral=True)
    
    # Save submission IDs
    submissions.update(replay_ids)
    save_submissions(submissions)
    
    # Success response
    lines = [
        "✅ **Submission successful!**",
        "",
        f"**Players:** {p1} vs {p2}",
        f"**Winner:** {series_winner}",
        f"**Score:** {wins[p1]}-{wins[p2]}",
        "",
        "**Matches:**"
    ]
    for i, match in enumerate(payload["matches"], 1):
        lines.append(f"{i}. `{match['id']}` - {match['map']} - Winner: {match['winner']}")
    
    lines.append("")
    lines.append(f"**PR:** {pr_url}")
    lines.append("🌐 Leaderboard updates in ~30 minutes")
    
    await interaction.followup.send("\n".join(lines), ephemeral=True)

@client.event
async def on_ready():
    """Bot startup - sync commands"""
    print(f"🤖 {client.user} connected to Discord")
    print(f"📊 Serving {len(client.guilds)} servers")
    
    try:
        synced = await tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
        print("📋 Active command: /submit")
        print("🌐 Leaderboard: https://atlasfailed.github.io/bar-duel-championship/")
    except Exception as e:
        print(f"❌ Failed to sync: {e}")

@tree.error
async def on_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Handle command errors"""
    print(f"❌ Error in /{interaction.command.name}: {error}")
    if not interaction.response.is_done():
        await interaction.response.send_message(f"❌ Error: {error}", ephemeral=True)

def main():
    """Start the bot"""
    print("🚀 Starting BAR League Bot (Submit Only)")
    print("💰 Optimized for minimal hosting costs")
    client.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()