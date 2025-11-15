# Bot Tests

Comprehensive test suite to verify the bot follows all instructions and restrictions.

## Running Tests

```bash
# Install pytest if not already installed
pip install pytest

# Run all tests
pytest bot/tests/

# Run specific test file
pytest bot/tests/test_replay_validation.py

# Run with verbose output
pytest bot/tests/ -v

# Run with coverage
pytest bot/tests/ --cov=bot --cov-report=html
```

## Test Structure

- **`test_replay_validation.py`** - Tests for replay structure validation
  - Player count validation
  - Spectator exclusion
  - Skill parsing
  - Winner detection (both methods)
  - URL validation

- **`test_bo3_validation.py`** - Tests for Bo3 series validation
  - Same players requirement
  - Winner determination
  - Win counting
  - Series winner detection

- **`test_age_validation.py`** - Tests for replay age restrictions
  - Age limit enforcement
  - Date parsing
  - Edge cases

- **`test_config_compliance.py`** - Tests that verify config values
  - All limits are set correctly
  - Values are reasonable
  - Relationships between values are valid

- **`test_field_extraction.py`** - Tests for data extraction
  - Field name fallbacks work
  - Data is extracted correctly
  - All config fields are used

## What Gets Tested

### Validation Rules
- ✅ Exactly 2 players per replay (REQUIRED_PLAYER_COUNT)
- ✅ Spectators excluded (teamId < MIN_TEAM_ID)
- ✅ Replay age limit (MAX_REPLAY_AGE_DAYS = 40 days)
- ✅ Bo3 same players requirement
- ✅ Bo3 winner requirement (REQUIRED_WINS_FOR_SERIES = 2)
- ✅ URL format validation (REPLAY_URL_PATTERN)
- ✅ MIN_REPLAYS = 2, MAX_REPLAYS = 3 enforcement

### Data Extraction
- ✅ Player name extraction (with fallbacks: "name", "Name")
- ✅ Skill/sigma extraction (with fallbacks: "skill"/"Skill", "skillUncertainty"/"SkillUncertainty")
- ✅ Winner detection (gamestats.winningTeamId + AllyTeams[].winningTeam fallback)
- ✅ Map name extraction from hostSettings.mapname
- ✅ Duration extraction (durationMs)
- ✅ Start time extraction (startTime)
- ✅ Team ID extraction (teamId/TeamId)

### Configuration Compliance
- ✅ All config values are set correctly
- ✅ Limits are reasonable (e.g., MAX_REPLAY_AGE_DAYS = 40)
- ✅ Relationships between values are valid (MIN_REPLAYS <= MAX_REPLAYS)
- ✅ Default sigma when skillUncertainty is 0 (DEFAULT_SIGMA = 8.333)
- ✅ API timeout is reasonable (API_TIMEOUT_SECONDS = 12)

### Edge Cases
- ✅ Missing startTime field handling
- ✅ Invalid date format handling
- ✅ Very old replays (e.g., 175 days) rejection
- ✅ gamestats.winningTeamId = None fallback
- ✅ Both teams have winningTeam=False scenario
- ✅ Duplicate replay IDs detection
- ✅ Skill parsing with brackets: "[16.67]" format

## Adding New Tests

When adding new validation rules or restrictions:

1. Add test cases to the appropriate test file
2. Test both valid and invalid cases
3. Test edge cases
4. Update this README if needed

## Continuous Integration

These tests should be run:
- Before deploying bot updates
- When changing validation logic
- When updating configuration values
- In CI/CD pipeline (if set up)

