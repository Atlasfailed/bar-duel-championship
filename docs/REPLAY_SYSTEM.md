# Replay Database System

This system automatically extracts and publishes detailed replay information from tournament submissions, making it easy for players to view match history and for casters to discover interesting games to cast.

## Features

### 🎮 Comprehensive Replay Database
- **Detailed Match Info**: Links, winners, dates, maps, durations, factions
- **Player Statistics**: OpenSkill values, win/loss records, favorite factions
- **Search & Filter**: Find games by player, map, duration, or keywords
- **Caster-Friendly**: Tagged replays for easy discovery of exciting matches

### 📊 Player Match Histories
- **Recent Matches**: Last 10 games for each player
- **Performance Stats**: Win rates, favorite factions, most played maps
- **Skill Progression**: Track OpenSkill changes over time
- **Head-to-Head**: See matchup histories between players

### 🏷️ Intelligent Tagging
Replays are automatically tagged for easy discovery:
- **Duration**: `short`, `medium`, `long`, `epic`
- **Skill Level**: `beginner-friendly`, `mid-skill`, `high-skill`
- **Factions**: `mixed-factions`, `all-cortex`, `all-armada`
- **Maps**: `map-{mapname}` for specific map searches

## Data Files

### `public/data/replay_database.json`
Complete database of all tournament replays with detailed information:

```json
{
  "id": "replay-id-here",
  "url": "https://api.bar-rts.com/replays/replay-id-here",
  "date": "2025-07-03T10:31:54.000Z",
  "map": "Ancient Vault v1.4",
  "duration_ms": 8730233,
  "duration_formatted": "2h 25m 30s",
  "winner": "PlayerName",
  "players": [
    {
      "name": "Player1",
      "faction": "Cortex",
      "is_winner": false,
      "skill_estimate": 16.67
    }
  ],
  "engine_version": "2025.04.08",
  "game_version": "Beyond All Reason test-28342-3044099",
  "tags": ["epic", "high-skill", "mixed-factions"]
}
```

### `public/data/player_match_history.json`
Individual player statistics and match histories:

```json
{
  "PlayerName": {
    "total_matches": 15,
    "wins": 10,
    "losses": 5,
    "win_rate": 66.7,
    "most_played_faction": "Cortex",
    "recent_matches": [...],
    "skill_progression": [...]
  }
}
```

## Web Interface

### Replay Browser (`docs/replays.html`)
Interactive web interface for browsing and searching replays:

- **Filters**: By player, map, duration, or search terms
- **Replay Cards**: Visual display of match details
- **Direct Links**: One-click access to replay files
- **Responsive Design**: Works on desktop and mobile

**Access**: `https://atlasfailed.github.io/bar-duel-championship/replays.html`

## For Casters 🎙️

### Finding Great Games to Cast
1. **Filter by Duration**: Look for `epic` (>60min) games for long-form content
2. **Filter by Skill Level**: `high-skill` tag for competitive analysis
3. **Search Players**: Find matches featuring popular or skilled players
4. **Recent Matches**: Latest tournament games for timely content

### Useful Searches
- `high-skill epic` - Long, high-level games
- `mixed-factions` - Diverse faction matchups
- `Player1 vs Player2` - Specific rivalries
- `map-{mapname}` - Games on particular maps

### Replay Information Available
- Direct download links to replay files
- Player skill levels and OpenSkill values
- Match context (part of series, tournament stage)
- Technical details (engine version, game version)

## For Players 📈

### Viewing Your Match History
1. Filter by your player name to see all your games
2. View recent performance and skill progression
3. See your favorite factions and most-played maps
4. Review head-to-head records against specific opponents

### Performance Analysis
- **Win Rate**: Overall tournament performance
- **Skill Progression**: Track OpenSkill changes over time
- **Faction Performance**: See which factions work best for you
- **Map Statistics**: Identify strong/weak maps

## Technical Details

### Automation
- **GitHub Actions**: Runs automatically when new submissions are merged
- **BAR API Integration**: Fetches detailed replay metadata
- **Rate Limiting**: Respectful API usage with delays between requests
- **Error Handling**: Graceful handling of missing or invalid replays

### Data Sources
1. **Submission Files**: Basic match info (winner, duration, players)
2. **BAR API**: Detailed replay metadata (factions, engine versions, timestamps)
3. **OpenSkill Calculations**: Skill estimates and progressions

### Update Schedule
- **On PR Merge**: When new submissions are added
- **Hourly**: Scheduled updates to catch any missed changes
- **Manual**: Can be triggered manually via GitHub Actions

## File Structure

```
actions/
├── extract_replay_data.py     # Main extraction script
├── recalculate_leaderboard.py  # Full leaderboard recalculation
├── process_submission.py       # Incremental leaderboard updates
└── requirements.txt           # Python dependencies

public/data/
├── replay_database.json       # Complete replay database
├── player_match_history.json  # Player statistics
└── leaderboard.json          # Current rankings

docs/
└── replays.html              # Web interface for browsing

.github/workflows/
└── update-leaderboard.yml    # Automation workflow
```

## Development

### Running Locally
```bash
# Install dependencies
pip install -r actions/requirements.txt

# Extract replay data
python actions/extract_replay_data.py

# View locally (requires local server)
python -m http.server 8000
# Open http://localhost:8000/docs/replays.html
```

### Adding New Features
1. Modify `extract_replay_data.py` for data extraction changes
2. Update `replays.html` for UI improvements
3. Test locally before pushing
4. GitHub Actions will automatically update live data

## API Endpoints

### Raw Data Access
- **Replay Database**: `/public/data/replay_database.json`
- **Player Histories**: `/public/data/player_match_history.json`
- **Leaderboard**: `/public/data/leaderboard.json`

### BAR API Integration
- **Replay Details**: `https://api.bar-rts.com/replays/{replay_id}`
- **Rate Limit**: 0.5s delay between requests
- **Error Handling**: Graceful fallbacks for failed requests

## Future Enhancements

### Planned Features
- **Replay Analysis**: Advanced statistics and insights
- **Tournament Brackets**: Visual tournament progression
- **Live Match Tracking**: Real-time match updates
- **Player Profiles**: Detailed player pages with full statistics
- **Casting Schedule**: Integration with casting announcements

### Data Enhancements
- **Faction-Specific Stats**: Per-faction performance metrics
- **Map Analysis**: Win rates and performance by map
- **Meta Tracking**: Faction and strategy trend analysis
- **Prediction Models**: Expected outcomes based on player skills