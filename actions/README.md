# Actions Scripts

This directory contains Python scripts for managing the BAR Duel Championship leaderboard system.

## Overview

The system uses two separate scripts for different update scenarios:

1. **`process_submission.py`** - Incremental updates for bot submissions (fast)
2. **`recalculate_leaderboard.py`** - Full recalculation from scratch (comprehensive)

## Tier-Based Champion Rating System

### How It Works

1. **Initial Placement**: When a player first appears, their initial OpenSkill (mu - sigma) determines their tier
2. **Starting CR**: Player receives the middle CR value of their tier range
3. **CR Changes**: Each match win/loss changes CR by 2-30 points based on opponent strength
4. **Tier Display**: Current tier is based on current CR, not initial OS

### Example

```
Player with OS 23.11:
- Initial tier: Gold (OS 20-30 range)
- Starting CR: 1650 (middle of 1500-1800 range)
- After 3 losses: CR drops to ~1617
- Still in Gold tier (CR 1500-1800)
```

## Scripts

### process_submission.py (Incremental Updates)

**Purpose**: Fast incremental updates when the Discord bot creates new submissions.

**When to use**:
- Automatically triggered by bot PR merges
- When you want to quickly add new submissions without recalculating everything

**How it works**:
1. Loads existing leaderboard from `public/data/leaderboard.json`
2. Loads processed submissions list from `public/data/.processed_submissions.json`
3. Processes only NEW submission files
4. Updates affected players' CR and statistics
5. Saves updated leaderboard and processed list

**Performance**: Very fast - only processes new data

**Usage**:
```bash
python actions/process_submission.py
```

**Triggered by**:
- `.github/workflows/update-leaderboard.yml` (on bot submission PR merge)

---

### recalculate_leaderboard.py (Full Recalculation)

**Purpose**: Complete recalculation of entire leaderboard from scratch.

**When to use**:
- After changing tier definitions in `config.py`
- After changing CR calculation parameters
- Bug fixes that require recalculation
- Development and testing
- When leaderboard data is corrupted or inconsistent

**How it works**:
1. Processes ALL submissions from `submissions/bo3/` directory
2. Recalculates every player's initial placement based on their first OS
3. Replays all matches to recalculate CR changes
4. Generates fresh leaderboard with correct tier assignments

**Performance**: Slower - processes entire history

**Usage**:
```bash
python actions/recalculate_leaderboard.py
```

**Triggered by**:
- `.github/workflows/recalculate-leaderboard.yml` (manual workflow_dispatch)
- Run manually during development

---

## Configuration

### config.py

Contains tier definitions and CR calculation parameters:

```python
TIER_DEFINITIONS = [
    # Tier Name    Min OS  Max OS  Min CR  Max CR
    ("Bronze",     -inf,   10.0,   900,    1200),
    ("Silver",     10.0,   20.0,   1200,   1500),
    ("Gold",       20.0,   30.0,   1500,   1800),
    ("Platinum",   30.0,   40.0,   1800,   2100),
    ("Diamond",    40.0,   50.0,   2100,   2500),
    ("Master",     50.0,   60.0,   2500,   3000),
    ("Grandmaster",60.0,   +inf,   3000,   5000),
]

# CR change parameters (2-30 range per match)
CR_BASE_CHANGE = 15
CR_MIN_CHANGE = 2
CR_MAX_CHANGE = 30
SKILL_DIFF_THRESHOLD = 15.0
```

**Important**: After changing `TIER_DEFINITIONS` or CR parameters, you MUST run `recalculate_leaderboard.py` to update all player placements.

---

## Workflows

### update-leaderboard.yml

**Trigger**: Bot submission PR merged or push to `submissions/bo3/**`

**Action**: Runs `process_submission.py` for fast incremental update

**Commits**: Incremental data updates with `[skip ci]`

### recalculate-leaderboard.yml

**Trigger**: Manual via GitHub Actions UI (workflow_dispatch)

**Action**: Runs `recalculate_leaderboard.py` for complete recalculation

**Also**: Clears `.processed_submissions.json` cache for fresh state

**Commits**: Full recalculation updates with `[skip ci]`

---

## Development Workflow

### When to use which script:

| Scenario | Use Script | Reason |
|----------|-----------|---------|
| Bot creates new submission | `process_submission.py` | Fast, only processes new data |
| Changed tier boundaries | `recalculate_leaderboard.py` | Need to reprocess all players |
| Changed CR parameters | `recalculate_leaderboard.py` | Need to replay all matches |
| Bug fix in calculation | `recalculate_leaderboard.py` | Need accurate recalculation |
| Data corruption | `recalculate_leaderboard.py` | Rebuild from source submissions |
| Testing tier changes | `recalculate_leaderboard.py` | See impact on all players |

### Testing locally:

```bash
# Test incremental update
python actions/process_submission.py

# Test full recalculation
python actions/recalculate_leaderboard.py

# Compare outputs
git diff public/data/leaderboard.json
```

---

## Output Files

### public/data/leaderboard.json
Main leaderboard file with player rankings, tiers, and stats.

### public/data/.processed_submissions.json
Cache file tracking which submissions have been processed (used by `process_submission.py`).

**Note**: This file is reset during full recalculation to ensure clean state.

### docs/data/
GitHub Pages deployment copies of data files.

---

## Troubleshooting

### "No existing leaderboard found" error

**Solution**: Run `recalculate_leaderboard.py` first to create initial leaderboard.

### Players in wrong tiers after config change

**Solution**: Run `recalculate_leaderboard.py` to recalculate with new tier definitions.

### Incremental updates not working

**Solution**: Check `.processed_submissions.json` - may need to delete and run full recalculation.

### CR values seem incorrect

**Solution**: Verify `config.py` parameters and run full recalculation to apply changes.

---

## Dependencies

```txt
openskill>=5.0.0
```

Install via:
```bash
pip install -r actions/requirements.txt
```