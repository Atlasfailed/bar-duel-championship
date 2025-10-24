## Quick context for AI coding agents

This repository implements a minimal Discord submission bot plus Github Actions that calculate and publish a public leaderboard. Keep the guidance below short and concrete — it's written for an automated coding assistant that will make small, safety-conscious edits and create patches/PRs.

### Big picture
- `bot/main.py` — single-file Discord bot. Handles a single `/submit` command, validates BAR replay URLs, and creates a GitHub PR containing a submission JSON.
- `actions/update_leaderboard.py` — run in CI to process files in `submissions/bo3` and write `public/data/leaderboard.json`.
- `utilities/` — local admin scripts (test connection, analyze submissions, reset submissions).
- Data files under `data/` and `public/data/` are the canonical on-disk state used by utilities and CI. Submissions appear as JSON files under `submissions/bo3` (created by the bot via PRs).

### Developer workflows & commands (concrete)
- Run bot locally: `cd bot && pip install -r requirements.txt && python main.py`. Bot expects `bot/.env` with `DISCORD_TOKEN`, `GITHUB_TOKEN`, `GITHUB_REPO=Atlasfailed/bar-duel-championship`.
- Test Discord connectivity: `cd utilities && python test_bot.py` (loads `../bot/.env`).
- Run leaderboard update locally (mirrors CI): `python actions/update_leaderboard.py` from repo root.
- Inspect/repair data: `cd utilities && python analyze_submissions.py` and `python reset_submissions.py` (create backups before reset).

### Important file & path conventions
- Submission files: `submissions/bo3/*.json`. The bot creates a file path like `submissions/bo3/{timestamp}_{p1}_vs_{p2}_{-joined-replayids}.json` and a branch `submissions/bo3-{timestamp}-{p1}-vs-{p2}`.
- Leaderboard output: `public/data/leaderboard.json` (served via GitHub Pages at the project's site).
- Local submission index tracked by the bot: `bot/data/submissions_index.json` (utilities reference this path via relative paths, e.g. `../bot/data/submissions_index.json`).
- Hardcoded paths in `actions/update_leaderboard.py`: `SUBMISSIONS_DIR = "submissions/bo3"` and `LEADERBOARD_FILE = "public/data/leaderboard.json"`. Prefer editing those files when changing layout.

### Patterns and conventions to follow when editing
- The bot is intentionally single-file and minimal: prefer small, localized edits in `bot/main.py` rather than refactoring into packages unless the user requests a larger redesign.
- CI script is authoritative for ranking logic. Changes to ranking behavior should update `actions/update_leaderboard.py` and be validated locally before pushing.
- Keep dependencies minimal. `actions/requirements.txt` is intentionally empty; only add deps when necessary and update workflow files.
- Preserve PR creation behavior: the bot creates branches and files so CI can run on merged PRs; do not remove or change the PR creation flow without updating workflows.

### Integration points & external deps
- External services:
  - BAR replay API (bot fetches replay JSON via `https://api.bar-rts.com/replays/<id>`).
  - GitHub API (bot creates branch, file, PR). `GITHUB_TOKEN` must have `repo` scope.
  - Discord (discord.py). `DISCORD_TOKEN` required.
- Environment variables to watch for edits: `DISCORD_TOKEN`, `GITHUB_TOKEN`, `GITHUB_REPO`, `GITHUB_BASE_BRANCH`, `TEAM_SIZE`, `MAX_REPLAY_AGE_DAYS` (refer to `bot/main.py`).

### Testing and safety checks that agents should run
- Run unit / smoke checks locally after code edits:
  - `python -m pyflakes .` or runtime smoke by running `python bot/main.py` (requires tokens).
  - For leaderboard edits: run `python actions/update_leaderboard.py` and verify `public/data/leaderboard.json` is written and valid JSON.
- When editing any code that writes data or commits: ensure commit messages include `[skip ci]` when appropriate to avoid CI loops, and preserve the repository's current commit/branch patterns.

### Examples to reference in code changes
- Replay URL pattern and validation: `REPLAY_URL_PATTERN = re.compile(r"https?://api\.bar-rts\.com/replays/([A-Za-z0-9]+)$")` in `bot/main.py` (use this exact pattern when parsing replay links).
- GitHub PR creation flow: see `create_github_pr()` in `bot/main.py` — branch naming and file creation format are implemented there.
- Leaderboard sort & rank logic: `calculate_rankings()` in `actions/update_leaderboard.py` — points are currently `+3` per match win and sorting is by `(-points, -wins, losses)`; preserve semantics unless explicitly changing ranking rules.

### When to ask the human
- If a change touches authentication scopes (GitHub token scopes, or adding secrets) or CI workflow triggers, stop and confirm.
- If you need to refactor the bot into multiple files or introduce a DB: confirm since this is a deliberate design choice to keep the bot single-file and low-cost.

If anything in this file is unclear or you want the instructions expanded for extra automation tasks (tests, linting, or a local dev Docker), tell me which area to elaborate and I'll iterate.
