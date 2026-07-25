import discord
from discord.ext import commands
import asyncio
import aiohttp
import json
import os
import sqlite3
from typing import Optional

FMHY_API_URL = os.getenv("FMHY_API_URL", "https://fmhy-api.onrender.com")
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
CONTROL_ROLES = ["1530632553021837372"]
DB_PATH = "tokens.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_tokens (
            user_id TEXT PRIMARY KEY,
            token TEXT NOT NULL,
            username TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_token(user_id, token, username=None):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO user_tokens (user_id, token, username) VALUES (?, ?, ?)",
        (str(user_id), token, username)
    )
    conn.commit()
    conn.close()

def get_token(user_id):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT token FROM user_tokens WHERE user_id = ?", (str(user_id),)).fetchone()
    conn.close()
    return row[0] if row else None

def remove_token(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM user_tokens WHERE user_id = ?", (str(user_id),))
    conn.commit()
    conn.close()

bot = commands.Bot(command_prefix="!", self_bot=True)

@bot.event
async def on_ready():
    init_db()
    print(f"Logged in as {bot.user.name} ({bot.user.id})")
    print(f"API: {FMHY_API_URL}")

def is_control():
    async def predicate(ctx):
        if str(ctx.author.id) in CONTROL_ROLES:
            return True
        user_roles = [str(role.id) for role in ctx.author.roles]
        for role_id in CONTROL_ROLES:
            if role_id in user_roles:
                return True
        await ctx.send("❌ No permission!")
        return False
    return commands.check(predicate)

@bot.command(name="token")
async def token_cmd(ctx, token: str):
    save_token(ctx.author.id, token, ctx.author.name)
    await ctx.send("✅ Token saved!")

@bot.command(name="removetoken")
async def removetoken_cmd(ctx):
    remove_token(ctx.author.id)
    await ctx.send("✅ Token removed!")

@bot.command(name="checktoken")
async def checktoken_cmd(ctx):
    user_token = get_token(ctx.author.id)
    if not user_token:
        await ctx.send("❌ No token saved. Use `!token YOUR_TOKEN`")
        return
    masked = user_token[:8] + "..." + user_token[-5:]
    await ctx.send(f"🔑 Token: `{masked}` (length: {len(user_token)})")

@bot.command(name="join")
@is_control()
async def join_cmd(ctx):
    user_token = get_token(ctx.author.id)
    if not user_token:
        await ctx.send("❌ Save your token first! Use `!token YOUR_TOKEN`")
        return
    
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ Join a voice channel first!")
        return
    
    channel = ctx.author.voice.channel
    await ctx.send(f"🔄 Joining **{channel.name}**...")
    
    try:
        user_bot = commands.Bot(command_prefix="!", self_bot=True)
        
        @user_bot.event
        async def on_ready():
            print(f"Selfbot joined as {user_bot.user.name}")
            try:
                vc = await channel.connect(self_mute=True, self_deaf=True)
                await ctx.send(f"✅ Joined **{channel.name}** as yourself!")
            except Exception as e:
                await ctx.send(f"❌ Failed: {e}")
            finally:
                await user_bot.close()
        
        await user_bot.start(user_token)
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="leave")
@is_control()
async def leave_cmd(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("✅ Left voice channel!")
    else:
        await ctx.send("❌ Not in a voice channel!")

@bot.command(name="watch")
@is_control()
async def watch_cmd(ctx, *, query: str):
    async with aiohttp.ClientSession() as session:
        params = {"q": query, "limit": 5, "recommended": "true"}
        async with session.get(f"{FMHY_API_URL}/api/search", params=params) as resp:
            data = await resp.json()
    
    resources = data.get("resources", [])
    if not resources:
        await ctx.send(f"❌ No results for **{query}**")
        return
    
    msg = f"🎬 **{query}** - Pick a site:\n\n"
    for i, r in enumerate(resources[:5], 1):
        name = r.get('name', 'Unknown')
        url = r.get('url', '#')
        desc = r.get('description', '')[:50]
        msg += f"**{i}. {name}**\n{desc}\n<{url}>\n\n"
    
    msg += "Open a link → Find your movie → Screen share in Discord!"
    await ctx.send(msg)

@bot.command(name="search")
async def search_cmd(ctx, *, query: str):
    async with aiohttp.ClientSession() as session:
        params = {"q": query, "limit": 10, "recommended": "true"}
        async with session.get(f"{FMHY_API_URL}/api/search", params=params) as resp:
            data = await resp.json()
    
    resources = data.get("resources", [])
    if not resources:
        await ctx.send(f"❌ No results for **{query}**")
        return
    
    msg = f"🔍 **{query}**\n\n"
    for i, r in enumerate(resources[:5], 1):
        name = r.get('name', 'Unknown')
        url = r.get('url', '#')
        desc = r.get('description', '')[:50]
        msg += f"**{i}. {name}** - {desc}\n<{url}>\n\n"
    
    await ctx.send(msg)

@bot.command(name="random")
async def random_cmd(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{FMHY_API_URL}/api/random") as resp:
            resource = await resp.json()
    
    name = resource.get('name', 'Unknown')
    url = resource.get('url', '#')
    desc = resource.get('description', '')[:100]
    
    await ctx.send(f"🎲 **{name}**\n{desc}\n<{url}>")

@bot.command(name="stats")
async def stats_cmd(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{FMHY_API_URL}/api/stats") as resp:
            data = await resp.json()
    
    await ctx.send(
        f"📊 **API Stats**\n"
        f"Resources: {data['total_resources']}\n"
        f"With Discord: {data['with_discord']}\n"
        f"With GitHub: {data['with_github']}"
    )

@bot.command(name="tokens")
@is_control()
async def tokens_cmd(ctx):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT user_id, username, created_at FROM user_tokens").fetchall()
    conn.close()
    
    if not rows:
        await ctx.send("No tokens saved yet.")
        return
    
    msg = f"🔑 **Saved Tokens** ({len(rows)} users)\n\n"
    for user_id, username, created_at in rows:
        msg += f"**{username or 'Unknown'}** ({user_id}) - {created_at}\n"
    
    await ctx.send(msg)

@bot.command(name="help")
async def help_cmd(ctx):
    await ctx.send(
        "🎬 **FMHY Selfbot Commands**\n\n"
        "**Setup:**\n"
        "`!token YOUR_TOKEN` - Save your user token\n"
        "`!removetoken` - Remove your token\n"
        "`!checktoken` - Check saved token\n\n"
        "**Streaming:**\n"
        "`!join` - Join voice as yourself\n"
        "`!leave` - Leave voice\n"
        "`!watch movie_name` - Find streaming links\n"
        "`!search query` - Search FMHY\n"
        "`!random` - Random streaming site\n\n"
        "**Info:**\n"
        "`!stats` - API stats\n"
        "`!tokens` - View all tokens (admin)\n"
        "`!help` - Show this message"
    )

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("ERROR: Set DISCORD_TOKEN env var")
        exit(1)
    bot.run(BOT_TOKEN)
