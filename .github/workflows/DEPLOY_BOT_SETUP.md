# Bot Deployment Workflow Setup

⚠️ **IMPORTANT**: GitHub Actions runners run in the cloud and **cannot access devices on your local network** unless:
- You use a **self-hosted runner** on your local network, OR
- You use the **local deployment script** instead

## Option 1: Local Deployment Script (Recommended for Local Network)

If your Pi Zero is on your local network, use the local script:

```bash
# From your local machine (on same network as Pi Zero)
cd /path/to/bar-duel-championship
./scripts/deploy-bot-local.sh

# Custom settings:
PI_HOST=192.168.1.100 PI_USER=pi ./scripts/deploy-bot-local.sh

# Restart only (no git pull):
./scripts/deploy-bot-local.sh --restart-only
```

The script will:
- Pull latest code from GitHub
- Restart the bot service
- Verify it's running

## Option 2: GitHub Actions Workflow (Cloud Runner)

This workflow allows you to deploy the bot to your Pi Zero with a single click from GitHub Actions, but **requires your Pi Zero to be accessible from the internet** (not recommended for security).

## Required GitHub Secrets

You need to set up the following secrets in your GitHub repository:

1. Go to: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

### Required Secrets:

- **`SSH_HOST`** - IP address or hostname of your Pi Zero (e.g., `192.168.1.100` or `raspberrypi.local`)
- **`SSH_USER`** - SSH username for Pi Zero (usually `pi` or your username)
- **`SSH_KEY`** - Private SSH key for authentication (contents of `~/.ssh/id_rsa` or your SSH key file)
- **`BOT_PATH`** (optional) - Path to bot directory on Pi Zero (default: `~/bar-duel-championship/bot`)

## Setting up SSH Key

If you don't have an SSH key set up:

1. **Generate SSH key** (if you don't have one):
   ```bash
   ssh-keygen -t rsa -b 4096 -C "github-actions"
   ```

2. **Copy public key to Pi Zero**:
   ```bash
   ssh-copy-id pi@<PI_ZERO_IP>
   ```

3. **Copy private key** to GitHub Secrets:
   ```bash
   cat ~/.ssh/id_rsa
   ```
   Copy the entire output (including `-----BEGIN` and `-----END` lines) and paste it into the `SSH_KEY` secret.

## Using the Workflow

### Via GitHub Web Interface:

1. Go to: `Actions` → `Deploy Bot to Pi Zero`
2. Click `Run workflow`
3. Select branch: `main`
4. Optionally check "Only restart bot (skip git pull)" if you just want to restart without pulling code
5. Click `Run workflow`

### Via GitHub CLI (locally):

```bash
# Full deployment (pull + restart)
gh workflow run "Deploy Bot to Pi Zero"

# Restart only (no git pull)
gh workflow run "Deploy Bot to Pi Zero" -f restart_only=true
```

## What the Workflow Does

1. **Pulls latest code** (unless restart_only is true):
   - SSHs into Pi Zero
   - Changes to bot directory
   - Runs `git pull origin main`

2. **Restarts the bot**:
   - Tries to restart systemd service `bar-bot` if it exists
   - Falls back to killing/restarting the Python process if no systemd service
   - Starts bot in background if not running

3. **Verifies deployment**:
   - Checks that bot process is running
   - Shows status information

## Troubleshooting

### Bot not restarting:
- Check that the bot path (`BOT_PATH` secret) is correct
- Verify SSH connection works: `ssh pi@<PI_ZERO_IP>`
- Check bot logs on Pi Zero: `tail -f ~/bar-duel-championship/bot/bot.log`

### SSH connection fails:
- Verify `SSH_HOST` and `SSH_USER` are correct
- Ensure `SSH_KEY` includes the full private key (with BEGIN/END lines)
- Check that Pi Zero is accessible from the internet (or use GitHub Actions self-hosted runner)

### Bot service not found:
- The workflow will fall back to process management if systemd service doesn't exist
- You can create a systemd service for better management (see below)

## Optional: Setting up systemd Service

For better bot management, create a systemd service:

```bash
# On Pi Zero, create service file
sudo nano /etc/systemd/system/bar-bot.service
```

Add:
```ini
[Unit]
Description=BAR Duel Championship Discord Bot
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/bar-duel-championship/bot
ExecStart=/usr/bin/python3 /home/pi/bar-duel-championship/bot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bar-bot
sudo systemctl start bar-bot
```

Now the workflow will use systemd to manage the bot.

