"""
GitHub Actions - Leaderboard Update Script (OpenSkill + SoS Tiers)
Processes submissions and updates the leaderboard.
- OpenSkill (ordinal = mu - 3*sigma) is your SKILL SCORE (display/MMR).
- Strength of Schedule (SoS) drives LEADERBOARD POSITION and TIERS.
Runs automatically on schedule or PR merge.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple

# ==============================
# Configuration
# ==============================

LEADERBOARD_FILE = "public/data/leaderboard.json"
SUBMISSIONS_DIR = "submissions/bo3"

# Rating model config (OpenSkill defaults are sensible)
# You can tune via margin/tau/beta in the future.
from openskill.models import PlackettLuce
MODEL = PlackettLuce()

# Seed values if no prior rating exists
DEFAULT_MU = 25.0
DEFAULT_SIGMA = 25.0 / 3.0

# Activity window (for median/health checks if needed later)
ACTIVE_WINDOW_DAYS = 60

# Use a GLOBAL calibration for SoS tiers (fixed mapping) or COHORT (dynamic, per run)
USE_GLOBAL_SOS_SCALE = False  # set True to lock tiers to the table below

# If using global scale, map percentile→SoS values (example provided earlier).
# These values should be on the SAME SoS scale you compute. If your SoS is defined
# as average opponent ORDINAL, populate this with that scale's empirical cut points.
PERCENTILE_SOS_POINTS = [
    (1, 2.60),
    (5, 7.26),
    (10, 9.58),
    (20, 12.21),
    (30, 13.84),
    (40, 14.86),
    (50, 16.45),
    (60, 18.17),
    (70, 19.57),
    (80, 21.80),
    (90, 25.45),
    (95, 29.43),
    (96, 31.02),
    (97, 32.61),
    (98, 35.30),
    (99, 39.68),
]

# Tier bands by percentile (if using cohort-based percentiles)
TIER_BANDS = [
    ("Bronze",      0,   20),  # < P20
    ("Silver",     20,   40),  # P20–P40
    ("Gold",       40,   60),  # P40–P60
    ("Platinum",   60,   80),  # P60–P80
    ("Diamond",    80,   95),  # P80–P95
    ("Master",     95,   98),  # P95–P98
    ("Grandmaster",98,  101),  # ≥ P98
]

# Optional: scale ordinal to a visible MMR (0–3000 range for UI niceness)
SCALE_OS_TO_MMR = True


# ==============================
# I/O: load submissions
# ==============================

def process_submissions() -> List[Dict[str, Any]]:
    """Process all Bo3 submissions from the submissions directory"""
    submissions = []
    submissions_path = Path(SUBMISSIONS_DIR)

    if not submissions_path.exists():
        print("⚠️ No submissions directory found")
        return []

    # Sort by filename for deterministic processing
    for file in sorted(submissions_path.glob("*.json")):
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                submissions.append(data)
                print(f"✅ Loaded submission: {file.name}")
        except Exception as e:
            print(f"⚠️ Failed to load {file.name}: {e}")

    return submissions


# ==============================
# Rating persistence helpers
# ==============================

def _load_previous_ratings() -> Dict[str, Dict[str, Any]]:
    """
    If a prior leaderboard exists, seed μ/σ so ratings persist run-to-run.
    Returns {player: {'mu': float, 'sigma': float, 'matches': int, 'wins': int, 'losses': int, 'last_played': iso}}
    """
    if not os.path.exists(LEADERBOARD_FILE):
        return {}
    try:
        with open(LEADERBOARD_FILE, "r") as f:
            prev = json.load(f)
        out = {}
        for row in prev:
            out[row["player"]] = {
                "mu": row.get("mu", DEFAULT_MU),
                "sigma": row.get("sigma", DEFAULT_SIGMA),
                "matches": row.get("matches", 0),
                "wins": row.get("wins", 0),
                "losses": row.get("losses", 0),
                "last_played": row.get("last_played"),
            }
        return out
    except Exception as e:
        print(f"⚠️ Failed to read previous leaderboard for seeding: {e}")
        return {}

def _ensure_player(store: Dict[str, Dict[str, Any]], name: str):
    if name not in store:
        store[name] = {
            "mu": DEFAULT_MU,
            "sigma": DEFAULT_SIGMA,
            "matches": 0,
            "wins": 0,
            "losses": 0,
            "last_played": None,
        }

def _names_to_team(names: List[str], store: Dict[str, Dict[str, Any]]):
    team = []
    for n in names:
        _ensure_player(store, n)
        team.append(MODEL.create_rating([store[n]["mu"], store[n]["sigma"]], name=n))
    return team

def _write_back(updated_teams, team_names: List[List[str]], ranks: Optional[List[int]], store: Dict[str, Dict[str, Any]], now_iso: str):
    for idx, team in enumerate(updated_teams):
        for p in team:
            name = p.name or team_names[idx][0]
            store[name]["mu"] = float(p.mu)
            store[name]["sigma"] = float(p.sigma)
            store[name]["matches"] += 1
            store[name]["last_played"] = now_iso

    # wins/losses for simple 1v1 case
    if ranks and len(ranks) == 2:
        if ranks[0] < ranks[1]:  # team 1 wins
            for n in team_names[0]:
                store[n]["wins"] += 1
            for n in team_names[1]:
                store[n]["losses"] += 1
        elif ranks[1] < ranks[0]:  # team 2 wins
            for n in team_names[1]:
                store[n]["wins"] += 1
            for n in team_names[0]:
                store[n]["losses"] += 1


# ==============================
# Core calculation
# ==============================

def calculate_rankings(submissions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    1) Recompute OpenSkill ratings (ordinal = μ − 3σ) across all submissions.
    2) Compute SoS per player as the average of opponents' ORDINAL.
    3) Rank by SoS (desc), using ordinal as a tiebreaker.
    4) Assign tiers based on SoS percentiles.
    """
    store: Dict[str, Dict[str, Any]] = _load_previous_ratings()

    # For SoS we need to know who each player faced.
    opponents: Dict[str, List[str]] = {}

    now_iso = datetime.now(timezone.utc).isoformat()

    for sub in submissions:
        players = sub.get("players", [])
        if len(players) != 2:
            print(f"⚠️ Skipping non-1v1 submission: {players}")
            continue
        pA, pB = players[0], players[1]

        team1 = _names_to_team([pA], store)
        team2 = _names_to_team([pB], store)

        winner = sub.get("series_winner")
        if winner == pA:
            ranks = [1, 2]
        elif winner == pB:
            ranks = [2, 1]
        else:
            ranks = [1, 1]  # tie

        updated_teams = MODEL.rate([team1, team2], ranks=ranks)
        _write_back(updated_teams, [[pA], [pB]], ranks, store, now_iso)

        # Track for SoS
        opponents.setdefault(pA, []).append(pB)
        opponents.setdefault(pB, []).append(pA)

    # Build initial rows with OS fields
    rows: List[Dict[str, Any]] = []
    for name, data in store.items():
        mu = float(data["mu"])
        sigma = float(data["sigma"])
        ordinal = mu - 3 * sigma
        matches = int(data["matches"])
        wins = int(data["wins"])
        losses = int(data["losses"])
        winrate = round((wins / matches) * 100.0, 1) if matches > 0 else 0.0

        rows.append({
            "player": name,
            "mu": round(mu, 6),
            "sigma": round(sigma, 6),
            "ordinal": round(ordinal, 6),  # OpenSkill score (confidence-adjusted)
            "matches": matches,
            "wins": wins,
            "losses": losses,
            "winrate": winrate,
            "last_played": data.get("last_played"),
        })

    # Compute SoS = avg opponent ordinal
    ordinal_by_player = {r["player"]: r["ordinal"] for r in rows}
    for r in rows:
        opps = opponents.get(r["player"], [])
        if opps:
            vals = [ordinal_by_player.get(o) for o in opps if o in ordinal_by_player]
            if vals:
                r["sos"] = round(sum(vals) / len(vals), 6)
            else:
                r["sos"] = 0.0
        else:
            r["sos"] = 0.0

    # Assign SoS percentile & Tier
    rows = _apply_sos_percentiles_and_tiers(rows)

    # Optional: scale OS to MMR for UI
    if SCALE_OS_TO_MMR:
        _scale_os_to_mmr(rows)

    # Rank by SoS (desc), then ordinal (desc), then wins (desc), then matches (desc)
    rows.sort(key=lambda x: (-x.get("sos", 0.0), -x.get("ordinal", 0.0), -x.get("wins", 0), -x.get("matches", 0)))

    for i, r in enumerate(rows, 1):
        r["rank"] = i

    return rows


# ==============================
# SoS percentile / tiers
# ==============================

def _percentile_rank(value: float, sorted_values: List[float]) -> float:
    """Return percentile (0-100) of value within sorted_values using rank-based method."""
    if not sorted_values:
        return 0.0
    # number of values strictly less than value
    import bisect
    idx = bisect.bisect_left(sorted_values, value)
    # handle ties by averaging positions of equals
    left = bisect.bisect_left(sorted_values, value)
    right = bisect.bisect_right(sorted_values, value)
    # mid-rank position
    pos = (left + right - 1) / 2.0
    p = (pos + 1) / len(sorted_values) * 100.0
    return p

def _interp_percentile_from_sos_global(sos: float) -> float:
    """Piecewise-linear interpolation using PERCENTILE_SOS_POINTS."""
    pts = PERCENTILE_SOS_POINTS
    if not pts:
        return 50.0
    if sos <= pts[0][1]:
        # Proportional to first point
        base_p, base_v = pts[0]
        if base_v <= 1e-12:
            return float(base_p)
        return float(base_p) * sos / base_v
    if sos >= pts[-1][1]:
        # Gentle extrapolation
        top_p, top_v = pts[-1]
        extra = (sos - top_v) / max(1e-9, top_v * 0.15)
        return min(100.0, top_p + extra)

    for i in range(1, len(pts)):
        p0, v0 = pts[i-1]
        p1, v1 = pts[i]
        if v0 <= sos <= v1:
            t = (sos - v0) / max(1e-9, (v1 - v0))
            return p0 + t * (p1 - p0)
    return 50.0

def _tier_from_percentile(p: float) -> str:
    for name, lo, hi in TIER_BANDS:
        if lo <= p < hi:
            return name
    return TIER_BANDS[-1][0]

def _apply_sos_percentiles_and_tiers(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not rows:
        return rows

    if USE_GLOBAL_SOS_SCALE:
        # Use the fixed mapping table
        for r in rows:
            p = _interp_percentile_from_sos_global(float(r.get("sos", 0.0)))
            r["sos_percentile"] = round(p, 2)
            r["tier"] = _tier_from_percentile(p)
        return rows

    # Cohort-based percentiles: compute percentiles from current run's SoS distribution
    sos_vals = sorted([float(r.get("sos", 0.0)) for r in rows])
    for r in rows:
        p = _percentile_rank(float(r.get("sos", 0.0)), sos_vals)
        r["sos_percentile"] = round(p, 2)
        r["tier"] = _tier_from_percentile(p)
    return rows


# ==============================
# Optional: MMR scaling (ordinal → 0..3000)
# ==============================

def _scale_os_to_mmr(rows: List[Dict[str, Any]]):
    if not rows:
        return
    ords = [r["ordinal"] for r in rows]
    mn, mx = min(ords), max(ords)
    span = max(1e-6, mx - mn)
    for r in rows:
        mmr = 300 * (r["ordinal"] - mn) / span  # 0–300, then ×10 = 0–3000
        r["mmr"] = round(mmr * 10)


def update_leaderboard():
    """Main function to update leaderboard"""
    print("🔄 Processing submissions...")

    # Process submissions
    submissions = process_submissions()
    print(f"📊 Found {len(submissions)} submissions")

    # Calculate rankings (OS + SoS + tiers, rank by SoS)
    leaderboard = calculate_rankings(submissions)
    print(f"🏆 Ranked {len(leaderboard)} players")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(LEADERBOARD_FILE), exist_ok=True)

    # Save leaderboard
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(leaderboard, f, indent=2)

    print(f"✅ Leaderboard saved to {LEADERBOARD_FILE}")
    print(f"📅 Updated at {datetime.now(timezone.utc).isoformat()}Z")

    # Print top 3
    if leaderboard:
        print("\n🏆 Top 3 (SoS-ranked):")
        for player in leaderboard[:3]:
            mmr_str = f" | MMR {player['mmr']}" if 'mmr' in player else ""
            print(f"  {player['rank']}. {player['player']} - SoS {player['sos']:.2f} (OS ord {player['ordinal']:.2f}) [{player['tier']}] {mmr_str}")


if __name__ == "__main__":
    try:
        update_leaderboard()
        print("\n✅ Leaderboard update complete!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Update failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
