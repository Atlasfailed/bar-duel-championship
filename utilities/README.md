# 🛠️ Local Utilities

**Admin tools and testing scripts for sporadic use.**

## 📁 Structure

```
utilities/
├── test_bot.py              # Test Discord connection
├── reset_submissions.py     # Clear submission history
└── analyze_submissions.py   # Stats and insights
```

## 🎯 Purpose

These scripts are for **manual/sporadic operations**:
- Testing configurations
- Data maintenance
- Analysis and reporting
- Emergency fixes

**Run locally only** - not for automation or hosting.

## 📋 Scripts

### 1️⃣ `test_bot.py`

**Purpose:** Verify Discord bot connection and configuration.

**Usage:**
```bash
cd utilities
python test_bot.py
```

**What it does:**
- Loads environment from `../bot/.env`
- Connects to Discord
- Prints bot info (username, ID, guilds)
- Shuts down cleanly

**When to use:**
- After configuration changes
- Before deploying to hosting
- Troubleshooting connection issues

**Expected output:**
```
Testing Discord bot connection...
✅ Connected as: BotName#1234 (ID: 1234567890)
✅ Guilds: 2
   - Guild 1 (123 members)
   - Guild 2 (456 members)
✅ Test successful!
```

---

### 2️⃣ `reset_submissions.py`

**Purpose:** Clear submission history with backup.

**Usage:**
```bash
cd utilities
python reset_submissions.py
```

**What it does:**
1. Creates timestamped backup of `submissions_index.json`
2. Saves to `../data/backups/`
3. Clears all entries (empty list)
4. Preserves file structure

**When to use:**
- Starting new season
- Clearing test data
- After major bugs/corruption
- Emergency reset

**⚠️ Warning:** This is **destructive**! Always verify backup created.

**Expected output:**
```
📦 Created backup: data/backups/submissions_index.json.20250123_143022
🗑️  Cleared submissions (123 entries removed)
✅ Submissions reset complete!
   - Backup: ../data/backups/submissions_index.json.20250123_143022
   - New state: 0 submissions
```

**Recovery:**
```bash
# If you made a mistake:
cp data/backups/submissions_index.json.20250123_143022 data/submissions_index.json
```

---

### 3️⃣ `analyze_submissions.py`

**Purpose:** Generate statistics and insights from submissions.

**Usage:**
```bash
cd utilities
python analyze_submissions.py
```

**What it does:**
- Loads all submissions
- Counts total matches
- Identifies unique players
- Finds most active players
- Calculates time range
- Shows submission trends

**When to use:**
- Monthly reports
- Understanding activity
- Planning features
- Data validation

**Expected output:**
```
📊 Submission Analysis Report
════════════════════════════════════════════════

📈 Overall Statistics:
   Total Submissions: 42
   Unique Players: 18
   Date Range: 2024-10-15 to 2025-01-23
   Duration: 100 days

👥 Most Active Players:
   1. PlayerA - 12 matches
   2. PlayerB - 10 matches
   3. PlayerC - 8 matches
   4. PlayerD - 7 matches
   5. PlayerE - 5 matches

📅 Submissions by Month:
   2024-10: 8 matches
   2024-11: 12 matches
   2024-12: 15 matches
   2025-01: 7 matches

⏰ Submissions by Day:
   Monday: 8
   Tuesday: 6
   Wednesday: 5
   Thursday: 7
   Friday: 9
   Saturday: 4
   Sunday: 3

🏆 Bo3 Completion Rate:
   Complete Bo3s: 14 (33.3%)
   Incomplete: 28 (66.7%)
```

---

## 🔧 Setup

### Prerequisites
```bash
# Python 3.11+
python --version

# Install dependencies (if needed)
pip install python-dotenv  # For test_bot.py
```

### Environment
Most scripts use paths relative to repo root:
```
utilities/
   └── script.py          (you are here)
        ↓
   ../data/               (data files)
   ../bot/.env            (for test_bot.py)
   ../data/backups/       (backups)
```

Make sure you run from the `utilities/` directory or adjust paths.

## 📊 Data Files

Scripts access these files:
- `../data/submissions_index.json` - Match submissions
- `../data/players_new.json` - Player data (read-only)
- `../bot/.env` - Environment config (test_bot.py only)

**Never edit these manually** - use scripts or the bot.

## 🚨 Safety

### Backups
- `reset_submissions.py` always creates backup
- Backups include timestamp
- Stored in `../data/backups/`
- Never auto-deleted (manual cleanup)

### Data validation
- Scripts verify file structure
- Fail gracefully on corruption
- Print clear error messages

### Dry-run mode
Some scripts support `--dry-run`:
```bash
# Not implemented yet, but planned:
python reset_submissions.py --dry-run
```

## 🎯 Best Practices

1. **Always run from `utilities/` directory**
   ```bash
   cd utilities
   python script.py
   ```

2. **Check backups before destructive operations**
   ```bash
   ls -lh ../data/backups/
   ```

3. **Test in development first**
   - Copy data files to test environment
   - Run script on test data
   - Verify results

4. **Document custom scripts**
   - Add new utilities here
   - Follow same structure
   - Include usage examples

## 🔮 Future Utilities

**Potential additions:**
- `migrate_season.py` - Move to new season
- `export_stats.py` - CSV export for analysis
- `validate_data.py` - Check data integrity
- `simulate_matches.py` - Test ranking system
- `generate_report.py` - Detailed analytics

**Adding new scripts:**
1. Create in `utilities/`
2. Follow same structure (header, main, if __name__)
3. Update this README
4. Test thoroughly

## 📈 Monitoring

**Check script health:**
```bash
# Verify files exist
ls -lh ../data/*.json

# Check backup count
ls -1 ../data/backups/ | wc -l

# View recent backups
ls -lht ../data/backups/ | head -5
```

## 🐛 Troubleshooting

### "File not found"
- Run from `utilities/` directory
- Check `../data/` exists
- Verify file permissions

### "Invalid JSON"
- Data file might be corrupted
- Restore from backup
- Check file encoding (UTF-8)

### "Permission denied"
- Check file ownership
- Verify write permissions
- Run as correct user

### "Module not found"
- Install dependencies: `pip install -r ../bot/requirements.txt`
- Check Python version
- Verify virtual environment activated

## 📝 Notes

- These are **local tools only**
- Don't run in production/hosting
- Not called by GitHub Actions
- Not exposed via Discord
- Manual execution only
- Always create backups first