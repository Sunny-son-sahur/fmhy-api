# Discord Bot Setup Guide

## Prerequisites

1. **Python 3.10+**
2. **Discord Bot Token** (from Discord Developer Portal)
3. **FMHY API** running (yours is at `https://fmhy-api.onrender.com`)

## Step 1: Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"** → Name it → **"Create"**
3. Go to **"Bot"** tab → Click **"Reset Token"** → Copy the token
4. Enable these **Privileged Gateway Intents**:
   - ✅ Presence Intent
   - ✅ Server Members Intent
   - ✅ Message Content Intent
5. Go to **"OAuth2"** → **"URL Generator"**
6. Select scopes: `bot`, `applications.commands`
7. Select permissions:
   - ✅ Send Messages
   - ✅ Use Voice
   - ✅ Connect
   - ✅ Speak
8. Copy the generated URL → Open in browser → Add bot to your server

## Step 2: Setup Bot

```bash
cd discord-bot

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DISCORD_TOKEN="your-bot-token-here"
export FMHY_API_URL="https://fmhy-api.onrender.com"

# Run the bot
python bot.py
```

## Step 3: Setup Control Roles (Optional)

By default, everyone can use the bot. To restrict to specific roles:

### Option A: Environment Variable
```bash
export CONTROL_ROLES="role_id_1,role_id_2"
```

### Option B: Bot Commands (Admin only)
```
/setrole @RoleName      - Add a control role
/removerole @RoleName   - Remove a control role
/listroles              - List all control roles
```

To get a role ID:
1. Enable Developer Mode in Discord (Settings → Advanced → Developer Mode)
2. Right-click the role → Copy ID

## Bot Commands

### Slash Commands
| Command | Description | Permission |
|---------|-------------|------------|
| `/watch query:anime` | Search for movies/shows | Control Role |
| `/watch url:https://...` | Play a specific URL | Control Role |
| `/stop` | Stop current stream | Control Role |
| `/nowplaying` | Show current stream | Control Role |
| `/search query:anime` | Search FMHY API | Everyone |
| `/random` | Get random resource | Everyone |
| `/stats` | Show API statistics | Everyone |

### Prefix Commands
| Command | Description | Permission |
|---------|-------------|------------|
| `!ping` | Check bot latency | Everyone |
| `!api` | Show API status | Everyone |
| `!setrole @Role` | Add control role | Admin |
| `!removerole @Role` | Remove control role | Admin |
| `!listroles` | List control roles | Admin |

## How to Watch Together

1. Join a voice channel
2. Use `/watch url:STREAM_URL`
3. Bot joins the voice channel
4. Click the voice channel → "Watch Together" or "Screen Share"
5. Open the stream URL in your browser
6. Share your screen in Discord!

## Example Usage

```
/watch query:anime           # Search for anime streaming sites
/watch url:https://site.com  # Play a specific URL
/search query:movies         # Search the API
/random category:Gaming      # Get random gaming resource
/stop                        # Stop the stream
```

## Troubleshooting

### Bot won't join voice channel
- Make sure you're in a voice channel
- Check bot has "Connect" permission

### Commands not working
- Re-sync commands: Restart the bot
- Check bot has "Use Slash Commands" permission

### API connection failed
- Check FMHY API is running
- Verify `FMHY_API_URL` environment variable

## Running as Service (Linux)

```bash
# Create service file
sudo nano /etc/systemd/system/fmhy-bot.service

# Add this content:
[Unit]
Description=FMHY Discord Bot
After=network.target

[Service]
User=root
WorkingDirectory=/path/to/discord-bot
Environment=DISCORD_TOKEN=your-token
Environment=FMHY_API_URL=https://fmhy-api.onrender.com
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable fmhy-bot
sudo systemctl start fmhy-bot
```
