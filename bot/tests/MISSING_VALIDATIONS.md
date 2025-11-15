# Missing Validations and Test Gaps

## Critical Missing Validation

### ⚠️ Time Between Replays Validation - NOT IMPLEMENTED

**Config exists:** `MAX_TIME_BETWEEN_REPLAYS_DAYS = 10` in `bot/config.py`

**Problem:** The bot does NOT check if replays in a Bo3 are within 10 days of each other.

**Impact:** Users could submit replays from different months/years as a single Bo3 series.

**Location:** Should be checked after age validation, before creating submission payload.

**Proposed Implementation:**
```python
# After age validation (line 419)
# Check time between replays
if len(validated) > 1:
    replay_times = []
    for replay in validated:
        start_time = replay.get("startTime")
        if start_time:
            start_str = start_time.replace("Z", "+00:00") if start_time.endswith("Z") else start_time
            start = datetime.fromisoformat(start_str)
            replay_times.append(start)
    
    if len(replay_times) > 1:
        replay_times.sort()
        for i in range(len(replay_times) - 1):
            time_diff = (replay_times[i+1] - replay_times[i]).days
            if time_diff > MAX_TIME_BETWEEN_REPLAYS_DAYS:
                return await interaction.followup.send(
                    f"❌ Replays are {time_diff} days apart (max: {MAX_TIME_BETWEEN_REPLAYS_DAYS} days)",
                    ephemeral=True
                )
```

## Missing Tests

### 1. Already Submitted Replay Detection
- ✅ Logic exists in code
- ❌ Not tested
- **Test file:** `test_missing_validations.py::TestAlreadySubmittedValidation`

### 2. URL Parsing Edge Cases
- ✅ Basic URL validation tested
- ❌ Edge cases not tested:
  - Whitespace handling
  - Trailing commas
  - Extra spaces
- **Test file:** `test_missing_validations.py::TestURLParsingEdgeCases`

### 3. API Error Handling
- ✅ Basic fetch logic exists
- ❌ Error scenarios not tested:
  - HTTP 404/500 errors
  - Timeout handling
  - Invalid JSON responses
- **Note:** Requires async mocking

### 4. Duplicate Detection
- ✅ Basic duplicate detection tested
- ⚠️ Could be more comprehensive
- **Test file:** `test_missing_validations.py::TestDuplicateDetection`

### 5. Validation Order
- ❌ Not tested that validations happen in correct order
- **Impact:** Could allow invalid submissions if order is wrong
- **Test file:** `test_missing_validations.py::TestValidationOrder`

## Test Coverage Summary

| Validation | Implemented | Tested | Notes |
|------------|-------------|--------|-------|
| URL format | ✅ | ✅ | Basic cases tested |
| MIN/MAX replays | ✅ | ✅ | Tested in test_submit_restrictions.py |
| Duplicate IDs | ✅ | ⚠️ | Basic test exists, could be more comprehensive |
| Already submitted | ✅ | ❌ | **NOT TESTED** |
| Replay structure | ✅ | ✅ | Comprehensive tests |
| Bo3 validation | ✅ | ✅ | Comprehensive tests |
| Age validation | ✅ | ✅ | Now properly tested |
| Time between replays | ❌ | ❌ | **NOT IMPLEMENTED** |
| API error handling | ⚠️ | ❌ | Basic error handling exists, not tested |

## Recommendations

### High Priority
1. **Implement time between replays validation** - Config exists but validation is missing
2. **Add tests for already submitted detection** - Logic exists but untested
3. **Add URL parsing edge case tests** - Could cause user confusion

### Medium Priority
4. **Add API error handling tests** - Requires async mocking
5. **Add validation order tests** - Ensures correct flow

### Low Priority
6. **Enhance duplicate detection tests** - Already has basic coverage

## Next Steps

1. Implement time between replays validation
2. Add comprehensive tests for missing validations
3. Add integration tests for full submit flow
4. Consider adding end-to-end tests with mocked Discord API

