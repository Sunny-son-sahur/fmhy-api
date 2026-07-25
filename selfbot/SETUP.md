# Selfbot Setup Guide

## Prerequisites

1. **Discord Bot Token** (from Developer Portal - your existing bot)
2. **FMHY API** running (yours is at https://fmhy-api.onrender.com)
3. **Fedora Server** PC

## Step 1: Setup on Fedora Server

SSH into your server:
```bash
ssh root@192.168.4.159
```

Install dependencies:
```bash
sudo dnf install python3 python3-pip git -y
```

Clone and setup:
```bash
git clone https://github.com/Sunny-son-sahur/fmhy-api.git
cd fmhy-api/selfbot
pip3 install -r requirements.txt
```

## Step 2: Set Environment Variables

```bash
export DISCORD_TOKEN="your-bot-token-here"
export FMHY_API_URL="https://fmhy-api.onrender.com"
```

To make permanent:
```bash
echo 'export DISCORD_TOKEN="your-token"' >> ~/.bashrc
echo 'export FMHY_API_URL="https://fmhy-api.onrender.com"' >> ~/.bashrc
source ~/.bashrc
```

## Step 3: Run the Bot

```bash
python3 bot.py
```

## Step 4: Keep Running 24/7

Using screen:
```bash
sudo dnf install screen -y
screen -S bot
python3 bot.py
# Press Ctrl+A then D to detach
# screen -r bot to reattach
```

Or using systemd (auto-start on boot):
```bash
sudo nano /etc/systemd/system/fmhy-bot.service
```

Paste:
```ini
[Unit]
Description=FMHY Selfbot
After=network.target

[Service]
User=root
WorkingDirectory=/root/fmhy-api/selfbot
Environment=DISCORD_TOKEN=your-token
Environment=FMHY_API_URL=https://fmhy-api.onrender.com
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable fmhy-bot
sudo systemctl start fmhy-bot
```

## How to Use

### First Time Setup
1. Type `/token` in Discord
2. Paste your Discord user token
3. Done! Token is saved.

### Get Your User Token
1. Open Discord in browser
2. Press F12 (Developer Tools)
3. Go to Network tab
4. Click any request
5. Find "Authorization" header
6. Copy the token value

### Watch Movies
1. Join a voice channel in Discord
2. Type `/join` - bot joins as you
3. Type `/watch movie_name` - get streaming links
4. Open a link in your browser
5. Screen share your browser in Discord

## Commands

| Command | Description |
|---------|-------------|
| `/token` | Save your user token |
| `/removetoken` | Remove your token |
| `/join` | Join voice as yourself |
| `/watch <movie>` | Find streaming links |
| `/search <query>` | Search FMHY |
| `/random` | Random streaming site |
| `/stats` | API stats |
| `/help` | Show commands |

## Multiple Users

Anyone can use `/token` to save their own token. Each user controls their own selfbot instance. The bot supports multiple users simultaneously.
