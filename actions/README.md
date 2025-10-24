# ⚙️ GitHub Actions Scripts

**Automated leaderboard processing and maintenance.**

## 📁 Structure

```
actions/
├── update_leaderboard.py  # Main processing script
└── requirements.txt       # Dependencies (none needed!)
```

## 🎯 Purpose

These scripts run in GitHub Actions workflows to:
1. **Process submissions** from merged PRs
2. **Calculate rankings** using tier-based system
3. **Update leaderboard** JSON file
4. **Trigger website rebuild** (GitHub Pages)

## 🔄 Workflow Integration

### Current Workflow
`.github/workflows/update-leaderboard.yml`

**Triggers:**
- ✅ Pull request merged to main
- ✅ Manual dispatch
- ⏰ Scheduled (if configured)

**Steps:**
1. Checkout repository
2. Set up Python
3. Run `update_leaderboard.py`
4. Commit changes (if any)

### Example Workflow File
```yaml
name: Update Leaderboard

on:
  pull_request:
    types: [closed]
    branches: [main]
  workflow_dispatch:

jobs:
  update:
    if: github.event.pull_request.merged == true || github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Update leaderboard
        run: python actions/update_leaderboard.py
      
      - name: Commit changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add data/ public/
          git diff --quiet && git diff --staged --quiet || \
            git commit -m "Update leaderboard [skip ci]"
          git push
```

## 📊 What It Does

### `update_leaderboard.py`

1. **Loads data files:**
   - `data/players_new.json` - Player stats
   - `data/submissions_index.json` - Match history

2. **Processes each submission:**
   - Fetches replay data from BAR API
   - Updates player statistics
   - Adjusts K-factors based on match count

3. **Calculates rankings:**
   - Tier-based system (Bronze → Grandmaster)
   - Intra-tier ratings (0-1000 within tier)
   - Promotion/demotion logic

4. **Saves results:**
   - Updates `data/players_new.json`
   - Creates `public/data/leaderboard.json`
   - Preserves backups in `data/backups/`

## 🚀 Running Locally

For testing or manual updates:

```bash
# Navigate to repo root
cd /path/to/bar-duel-championship

# Run the script
python actions/update_leaderboard.py
```

**Note:** This processes ALL submissions in `submissions_index.json`. For incremental updates, the workflow only processes new entries.

## 📋 Output Format

### `public/data/leaderboard.json`
```json
{
  "last_updated": "2025-01-23T10:30:00Z",
  "season": 1,
  "rankings": [
    {
      "rank": 1,
      "player_name": "PlayerName",
      "rating": 850.5,
      "tier": "Platinum",
      "matches_played": 42,
      "wins": 28,
      "losses": 14,
      "win_rate": 66.7,
      "streak": 3
    }
  ]
}
```

This file is publicly accessible at:
`https://atlasfailed.github.io/bar-duel-championship/data/leaderboard.json`

## ⚡ Performance

**Typical execution time:**
- 100 players: ~2-3 seconds
- 500 players: ~10-15 seconds
- 1000 players: ~30-45 seconds

**GitHub Actions limits:**
- Free tier: 2,000 minutes/month
- This script: <1 minute per run
- **Cost: $0 (well within free tier)**

## 🔧 Configuration

The script uses these paths (relative to repo root):
```python
DATA_DIR = "data"
PUBLIC_DIR = "public/data"
PLAYERS_FILE = "data/players_new.json"
SUBMISSIONS_FILE = "data/submissions_index.json"
LEADERBOARD_FILE = "public/data/leaderboard.json"
BACKUP_DIR = "data/backups"
```

All paths are hardcoded for consistency in GitHub Actions environment.

## 🐛 Debugging

### Enable verbose output:
```python
# In update_leaderboard.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check workflow logs:
1. Go to GitHub repository
2. Click "Actions" tab
3. Select workflow run
4. View step outputs

### Common issues:

**File not found:**
- Ensure paths are correct
- Check repository structure matches expected layout

**API errors:**
- BAR API might be down
- Replay IDs might be invalid
- Add retry logic if needed

**Git conflicts:**
- Workflow runs concurrently
- Add `concurrency` group to workflow

## 🔄 Maintenance

### Adding new features:
1. Update `update_leaderboard.py`
2. Test locally
3. Push to repository
4. Workflow uses updated script automatically

### No deployment needed!
- Script runs from repository
- Changes take effect immediately
- No build or compile step

## 📈 Monitoring

**Check execution:**
- GitHub Actions tab shows all runs
- Email notifications for failures (if enabled)
- Commit history shows updates

**Data validation:**
- Compare player counts before/after
- Verify leaderboard.json structure
- Check website displays correctly

## 🎯 Best Practices

1. **Always commit with `[skip ci]`** to avoid loops
2. **Backup before major changes** (script does this automatically)
3. **Test locally first** before pushing changes
4. **Monitor first few runs** after updates
5. **Keep dependencies minimal** (currently zero!)