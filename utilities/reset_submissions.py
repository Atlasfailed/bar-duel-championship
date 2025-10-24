"""
Reset Submissions - Local Utility
Clears all submission history
Use with caution!
"""

import json
import os
from pathlib import Path

def reset_submissions():
    """Reset submission tracking"""
    submissions_file = "../bot/data/submissions_index.json"
    
    if os.path.exists(submissions_file):
        # Backup first
        backup = submissions_file + ".backup"
        os.makedirs("backups", exist_ok=True)
        backup_path = f"backups/submissions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        if os.path.exists(submissions_file):
            with open(submissions_file, 'r') as f:
                data = json.load(f)
            with open(backup_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"📁 Backup saved to {backup_path}")
        
        # Reset
        with open(submissions_file, 'w') as f:
            json.dump([], f, indent=2)
        print("✅ Submissions reset")
    else:
        print("⚠️ No submissions file found")

if __name__ == "__main__":
    from datetime import datetime
    
    confirm = input("⚠️ This will reset ALL submissions. Continue? (yes/no): ")
    if confirm.lower() == "yes":
        reset_submissions()
    else:
        print("❌ Cancelled")