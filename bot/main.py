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

# Load environment
load_dotenv()

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.getenv("GITHUB_REPO", "Atlasfailed/bar-duel-championship").strip()
GITHUB_BASE_BRANCH = os.getenv("GITHUB_BASE_BRANCH", "main").strip()
TEAM_SIZE = int(os.getenv("TEAM_SIZE", "1"))
MAX_REPLAY_AGE_DAYS = int(os.getenv("MAX_REPLAY_AGE_DAYS", "30"))
MAX_TIME_BETWEEN_REPLAYS_SEC = int(os.getenv("MAX_TIME_BETWEEN_REPLAYS_SEC", "86400"))

if not DISCORD_TOKEN:
    raise RuntimeError("❌ DISCORD_TOKEN required in .env file")

# Submission tracking
SUBMISSIONS_FILE = "data/submissions_index.json"
REPLAY_URL_PATTERN = re.compile(r"https?://api\.bar-rts\.com/replays/([A-Za-z0-9]+)$")

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
    async with session.get(url, timeout=12) as response:
        if response.status != 200:
            raise ValueError(f"Failed to fetch replay: HTTP {response.status}")
        return await response.json()

def validate_replay(replay: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and extract replay data"""
    host_settings = replay.get("hostSettings", {})
    map_name = host_settings.get("mapname", "Unknown")
    
    # Get all players from ALL AllyTeams (not just the first one)
    players_data = []
    ally_teams = replay.get("AllyTeams", [])
    
    for ally_team in ally_teams:
        team_players = ally_team.get("Players", [])
        for player in team_players:
            # Only include actual players (with valid team IDs), exclude spectators/bots
            team_id = player.get("teamId")
            if team_id is not None and team_id >= 0:
                players_data.append(player)
    
    if len(players_data) != 2:
        raise ValueError(f"Replay must have exactly 2 players, found {len(players_data)} (excluding spectators)")
    
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
    
    players = []
    seed_ratings = {}
    for p in players_data:
        name = p.get("name") or p.get("Name") or "Unknown"
        mu = parse_skill(p.get("skill") or p.get("Skill"))
        sigma = parse_skill(p.get("skillUncertainty") or p.get("SkillUncertainty"))
        
        # If sigma is 0, use default OpenSkill initial uncertainty
        if sigma == 0.0:
            sigma = 8.333  # OpenSkill default
        
        players.append({"name": name, "skill": mu})
        seed_ratings[name] = {"mu": mu, "sigma": sigma}
    
    winner_id = replay.get("gamestats", {}).get("winningTeamId")
    winner = None
    for p in players_data:
        if p.get("teamId") == winner_id or p.get("TeamId") == winner_id:
            winner = p.get("name") or p.get("Name")
    
    start_time = replay.get("startTime") or replay.get("Start Time", "")
    duration_ms = replay.get("durationMs", 0)
    
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
    """Check if replays form a valid Bo3"""
    all_player_sets = []
    for r in replays:
        player_names = {p["name"] for p in r["players"]}
        all_player_sets.append(player_names)
    
    if not all(s == all_player_sets[0] for s in all_player_sets):
        raise ValueError("All replays must have the same 2 players")
    
    player_names = sorted(list(all_player_sets[0]))
    if len(player_names) != 2:
        raise ValueError("Must have exactly 2 players")
    
    wins = {name: 0 for name in player_names}
    for r in replays:
        if r["winner"] and r["winner"] in wins:
            wins[r["winner"]] += 1
    
    series_winner = None
    for name, count in wins.items():
        if count >= 2:
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
                          headers=headers, timeout=12) as r:
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
                           timeout=12) as r:
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
                          timeout=12) as r:
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
                           timeout=12) as r:
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
    if len(urls) < 2:
        return await interaction.followup.send("❌ Need at least 2 replay URLs", ephemeral=True)
    if len(urls) > 3:
        return await interaction.followup.send("❌ Maximum 3 replay URLs", ephemeral=True)
    
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
        return await interaction.followup.send("❌ No clear winner (need 2+ wins)", ephemeral=True)
    
    # Check replay age
    now = datetime.now(timezone.utc)
    for replay in validated:
        if replay["startTime"]:
            try:
                start = datetime.fromisoformat(replay["startTime"].replace("Z", "+00:00"))
                age = (now - start).days
                if age > MAX_REPLAY_AGE_DAYS:
                    return await interaction.followup.send(
                        f"❌ Replay `{replay['id']}` is {age} days old (max: {MAX_REPLAY_AGE_DAYS})",
                        ephemeral=True
                    )
            except:
                pass
    
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