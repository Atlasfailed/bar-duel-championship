# Testing Gaps - Why Tests Didn't Catch the Age Validation Issue

## The Problem

Old replays (149-151 days old) were accepted by the bot despite exceeding the 40-day limit. The tests didn't catch this issue.

## Why Tests Failed to Catch It

### 1. **Tests Only Verified Date Parsing, Not Rejection**

The original `test_age_validation.py` only tested:
- ✅ Can we parse dates correctly?
- ✅ Can we calculate age correctly?
- ✅ Is the age > MAX_REPLAY_AGE_DAYS?

But it **didn't test**:
- ❌ Does the bot actually **reject** old replays?
- ❌ Does the rejection logic work in the submit handler?

### 2. **Age Validation Logic Wasn't Extracted**

The age validation happens inside the Discord command handler (`/submit`):
- It's an async function that requires Discord interaction mocking
- The logic is embedded in the handler, not in a testable function
- Tests couldn't easily verify the rejection behavior

### 3. **Missing Integration Tests**

The tests verified:
- ✅ Individual functions (`validate_replay`, `check_bo3_validity`)
- ✅ Date parsing logic
- ✅ Configuration values

But they **didn't test**:
- ❌ The full submit flow with old replays
- ❌ That old replays are actually rejected during submission
- ❌ The interaction between validation steps

## The Fix

### New Test: `test_submit_age_validation.py`

This test:
1. **Extracts the age validation logic** into a testable function
2. **Tests actual rejection behavior** - verifies old replays are rejected
3. **Includes real-world test cases** - uses the actual replay dates that were incorrectly accepted
4. **Tests edge cases** - missing startTime, invalid formats, etc.

### Key Test Case

```python
def test_real_world_old_replays(self):
    """Test with real-world old replay dates that were incorrectly accepted"""
    test_cases = [
        ("2025-06-16T21:15:52.000Z", 151),  # 151 days old
        ("2025-06-19T05:29:32.000Z", 149),  # 149 days old
        ("2025-06-19T06:26:30.000Z", 149),  # 149 days old
    ]
    
    for date_str, expected_age in test_cases:
        should_reject, error_msg = check_replay_age(replay_data, MAX_REPLAY_AGE_DAYS)
        assert should_reject is True  # Should be rejected!
```

## Lessons Learned

1. **Test behavior, not just logic**
   - Don't just test that age is calculated correctly
   - Test that old replays are actually rejected

2. **Extract testable functions**
   - If logic is embedded in handlers, extract it for testing
   - Make rejection logic testable independently

3. **Test integration flows**
   - Test the full flow, not just individual functions
   - Include real-world scenarios

4. **Test what can go wrong**
   - Test edge cases that could cause silent failures
   - Test with actual problematic data

## Prevention

Going forward:
- ✅ Age validation logic is now extracted and testable
- ✅ Tests verify actual rejection behavior
- ✅ Real-world test cases included
- ✅ Integration tests cover full flow

## Running the New Tests

```bash
# Test age validation rejection logic
pytest bot/tests/test_submit_age_validation.py -v

# Test with real-world old replays
pytest bot/tests/test_submit_age_validation.py::TestSubmitAgeValidation::test_real_world_old_replays -v
```

