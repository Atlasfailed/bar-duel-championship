#!/usr/bin/env python3
"""
GitHub Actions - Update Leaderboard Wrapper Script
Wrapper script that updates leaderboard and replay data after new submissions are merged.

This script:
1. Updates the leaderboard using process_submission.py (incremental)
2. Updates replay database and player match history using extract_replay_data.py

Called by GitHub Actions workflows after bot submission PRs are merged.
"""

import sys
import os

# Import main functions
from process_submission import (
    load_processed_submissions, 
    get_new_submissions,
    process_new_submissions
)
from extract_replay_data import extract_replay_data_incremental

if __name__ == "__main__":
    try:
        # Get new submissions BEFORE processing (so we can use them for both steps)
        print("=" * 60)
        print("Loading new submissions...")
        print("=" * 60)
        processed = load_processed_submissions()
        new_submissions = get_new_submissions(processed)
        
        if not new_submissions:
            print("No new submissions to process")
            sys.exit(0)
        
        print(f"Found {len(new_submissions)} new submissions")
        
        # Step 1: Update leaderboard (incremental)
        print("\n" + "=" * 60)
        print("Step 1: Updating leaderboard...")
        print("=" * 60)
        process_new_submissions()
        
        # Step 2: Update replay database and player match history (incremental)
        # Pass the new submissions list so it processes them before they're marked as processed
        print("\n" + "=" * 60)
        print("Step 2: Updating replay database and player match history...")
        print("=" * 60)
        extract_replay_data_incremental(new_submissions)
        
        print("\n✅ All updates complete!")
        
    except Exception as e:
        print(f"Error updating leaderboard: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

