# GitHub Actions Workflows

This directory contains workflows for managing the BAR Duel Championship leaderboard.

## Workflows

### 1. Process New Submissions (`update-leaderboard.yml`)
**Purpose**: Automatically process new match submissions from the Discord bot.

**Triggers**:
- When a bot submission PR is merged to `main`
- When commits containing "Bo3 Submission" are pushed to `submissions/bo3/**`
- Hourly schedule (catches any missed updates)

**What it does**:
- Incrementally updates the leaderboard based on new submissions
- Extracts replay data from new matches
- Updates player match histories
- Commits changes back to the repository with `[skip ci]` tag

**Use this for**: Normal operation when the bot submits new matches.

---

### 2. Recalculate Full Leaderboard (`recalculate-leaderboard.yml`)
**Purpose**: Complete recalculation of the entire leaderboard from scratch.

**Triggers**:
- Manual trigger only (`workflow_dispatch`)
- Requires a reason for the recalculation

**What it does**:
- Reprocesses ALL submissions from the beginning
- Recalculates all rankings, ratings, and statistics
- Regenerates the complete replay database
- Updates all match histories
- Commits changes back to the repository with `[skip ci]` tag

**Use this for**:
- After changing tier definitions or rating configuration
- After fixing bugs in the ranking algorithm
- After modifying the leaderboard calculation logic
- When you need a clean slate recalculation

**How to trigger**:
1. Go to the [Actions tab](https://github.com/Atlasfailed/bar-duel-championship/actions)
2. Select "Recalculate Full Leaderboard" from the workflows list
3. Click "Run workflow"
4. Enter a reason (e.g., "Updated tier thresholds in config")
5. Click "Run workflow"

---

## Why Two Workflows?

Having separate workflows prevents conflicts between:
- **Local development**: You can tinker with config locally and test changes
- **GitHub state**: The authoritative leaderboard lives in GitHub and is updated by actions

When you modify configuration files (like `actions/config.py`), you should:
1. Edit and test locally
2. Commit and push your config changes
3. Manually trigger the **Recalculate Full Leaderboard** workflow
4. Let it regenerate everything from scratch

This way, the leaderboard files (`public/data/leaderboard.json`, etc.) are ONLY modified by GitHub Actions, preventing merge conflicts between local and remote versions.

---

## Output Files

Both workflows update the same files:
- `public/data/leaderboard.json` - Main leaderboard data
- `public/data/replay_database.json` - Detailed replay information
- `public/data/player_match_history.json` - Individual player match histories
- `docs/data/*.json` - Copies for GitHub Pages

All commits include `[skip ci]` to prevent triggering the workflow again.
