# Replit Setup

## Steps

1. Go to [replit.com](https://replit.com)
2. Click **"Create Repl"**
3. Select **Python** template
4. Name it `fmhy-bot`
5. Upload all files from `discord-bot/` folder:
   - `bot.py`
   - `cogs/watch.py`
   - `keep_alive.py`
   - `.replit`
   - `requirements.txt`

## Add Secrets

1. Click the **🔒 Secrets** tab (lock icon)
2. Add these secrets:
   - Key: `DISCORD_TOKEN` → Value: `your-bot-token`
   - Key: `CONTROL_ROLES` → Value: `1530632553021837372`

## Run

1. Click **▶ Run** button
2. Bot will start and show "Logged in as..."
3. Keep tab open to keep bot running

## Keep Bot Always On

1. Go to [uptimerobot.com](https://uptimerobot.com)
2. Create free account
3. Add new monitor:
   - Type: HTTP(s)
   - URL: Your Repl's web URL (shown in Replit)
   - Interval: 5 minutes
4. This pings your bot every 5 min to prevent sleep

## Files to Upload

```
discord-bot/
├── bot.py              # Main bot
├── cogs/
│   └── watch.py        # Commands
├── keep_alive.py       # Keeps Replit awake
├── .replit             # Replit config
└── requirements.txt    # Dependencies
```

## Bot Commands

- `/join` - Join voice channel
- `/leave` - Leave voice channel
- `/watch query:anime` - Search movies
- `/watch url:URL` - Play specific URL
- `/stop` - Stop stream
- `/search query:movies` - Search API
- `/random` - Random resource
- `/stats` - API stats

## Permissions

Only role `1530632553021837372` can use:
- `/join`
- `/leave`
- `/watch`
- `/stop`
- `/nowplaying`

Everyone can use:
- `/search`
- `/random`
- `/stats`
