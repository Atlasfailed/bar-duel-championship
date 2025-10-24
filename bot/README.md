# 🤖 Standalone Discord Bot

**Minimal, self-contained bot optimized for low hosting costs.**

## 📁 Structure

```
bot/
├── main.py                 # Single file - complete bot (~350 lines)
├── .env.example           # Environment template
├── .gitignore
└── requirements.txt       # Minimal dependencies (3 packages)
```

**Everything in one file!** No folders, no imports, just `main.py`.

## 🚀 Features

- **Single command**: `/submit` for Bo3 match submissions
- **Minimal dependencies**: Only discord.py, aiohttp, python-dotenv
- **Self-contained**: No external src/ dependencies
- **Stateless**: Only tracks submitted replay IDs locally
- **GitHub integration**: Creates PRs for submissions

## 💰 Hosting Optimization

### Why This Is Minimal:
1. **No database** - Just JSON file for tracking
2. **No leaderboard queries** - Directs users to website
3. **Single command** - Fast command sync, minimal memory
4. **Stateless operation** - No persistent connections
5. **Async I/O** - Efficient resource usage

### Hosting Recommendations:
- **Railway.app** - Free tier sufficient
- **Fly.io** - Free allowance covers this
- **Render.com** - Free tier works
- **Heroku** - Eco dyno ($5/month)

## 📋 Setup

### 1. Install Dependencies
```bash
cd bot
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your tokens
```

Required variables:
- `DISCORD_TOKEN` - Your Discord bot token
- `GITHUB_TOKEN` - GitHub personal access token
- `GITHUB_REPO` - Your repo (e.g., Atlasfailed/bar-duel-championship)

### 3. Run Locally
```bash
python main.py
```

### 4. Deploy to Hosting

Most platforms need a `Procfile` or `start command`:
```
worker: python main.py
```

## 🎯 What It Does

1. **Receives submissions** via `/submit` command
2. **Validates replays** from BAR API
3. **Checks for duplicates** against local tracking
4. **Creates GitHub PR** with submission data
5. **Responds immediately** to user

## 🌐 What It Doesn't Do

- ❌ Display leaderboards (→ Use GitHub Pages)
- ❌ Calculate rankings (→ Done by GitHub Actions)
- ❌ Store match data (→ Stored in GitHub)
- ❌ Query player stats (→ Available on website)

This separation keeps the bot **ultra-lightweight** and **cost-effective**.

## 📊 Data Flow

```
Discord User
    ↓ /submit
Discord Bot (validates)
    ↓ creates PR
GitHub Repository
    ↓ triggers workflow
GitHub Actions (calculates rankings)
    ↓ updates
GitHub Pages (displays leaderboard)
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_TOKEN` | ✅ Yes | - | Discord bot token |
| `GITHUB_TOKEN` | ✅ Yes | - | GitHub PAT with repo access |
| `GITHUB_REPO` | ✅ Yes | - | Repository (owner/name) |
| `GITHUB_BASE_BRANCH` | No | main | Target branch for PRs |
| `TEAM_SIZE` | No | 1 | Players per team |
| `MAX_REPLAY_AGE_DAYS` | No | 30 | Max age for replays |
| `MAX_TIME_BETWEEN_REPLAYS_SEC` | No | 86400 | Max time between games |

## 🛡️ Security

- No sensitive data stored locally
- Replay IDs only (no player data)
- GitHub token should have minimal permissions:
  - `repo` scope only
  - No admin or workflow permissions needed

## 📈 Resource Usage

**Expected usage for 100 users:**
- Memory: ~50-100MB
- CPU: <1% (idle), spikes during submission
- Network: Minimal (API calls only)
- Storage: <1MB (submission tracking)

**Cost: Fits in free tiers of most platforms!**

## 🔄 Updates

To update the bot:
1. Pull latest code
2. Restart the bot
3. Commands auto-sync on startup

No database migrations or data conversion needed!