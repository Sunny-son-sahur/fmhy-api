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

def has_control_role():
    async def predicate(interaction: discord.Interaction):
        user_roles = [str(role.id) for role in interaction.user.roles]
        user_roles.append(str(interaction.user.id))
        for role_id in CONTROL_ROLES:
            if role_id in user_roles:
                return True
        await interaction.response.send_message(
            "❌ No permission!",
            ephemeral=True
        )
        return False
    return discord.app_commands.check(predicate)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    init_db()
    print(f"Bot logged in as {bot.user.name}")
    print(f"API: {FMHY_API_URL}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Sync error: {e}")

@bot.tree.command(name="token", description="Save your Discord user token for selfbot")
@discord.app_commands.describe(token="Your Discord user token")
async def token_cmd(interaction: discord.Interaction, token: str):
    save_token(interaction.user.id, token, interaction.user.name)
    embed = discord.Embed(
        title="✅ Token Saved",
        description="Your user token has been saved securely.\nYou can now use `/join` and `/watch` to stream as yourself.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="removetoken", description="Remove your saved token")
async def removetoken_cmd(interaction: discord.Interaction):
    remove_token(interaction.user.id)
    embed = discord.Embed(
        title="✅ Token Removed",
        description="Your token has been deleted.",
        color=discord.Color.orange()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="join", description="Join voice channel as yourself")
@has_control_role()
async def join_cmd(interaction: discord.Interaction):
    user_token = get_token(interaction.user.id)
    if not user_token:
        await interaction.response.send_message(
            "❌ You need to save your token first! Use `/token`",
            ephemeral=True
        )
        return
    
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message(
            "❌ Join a voice channel first!",
            ephemeral=True
        )
        return
    
    channel = interaction.user.voice.channel
    
    await interaction.response.defer()
    
    # Clean the token
    user_token = user_token.strip().strip('"').strip("'")
    
    print(f"Attempting join with token: {user_token[:10]}...")
    
    try:
        selfbot = discord.Client(intents=discord.Intents.all())
        
        @selfbot.event
        async def on_ready():
            print(f"Selfbot joined as {selfbot.user.name}")
            try:
                vc = await channel.connect(self_mute=True, self_deaf=True)
                embed = discord.Embed(
                    title="✅ Joined Voice",
                    description=f"Joined **{channel.name}** as yourself.\nYou can now screen share from this PC.",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=embed)
            except Exception as e:
                await interaction.followup.send(f"❌ Failed: {e}")
            finally:
                await selfbot.close()
        
        asyncio.create_task(selfbot.start(user_token))
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}")

@bot.tree.command(name="search", description="Search FMHY for streaming sites")
async def search_cmd(
    interaction: discord.Interaction,
    query: str,
    category: Optional[str] = None
):
    await interaction.response.defer()
    
    async with aiohttp.ClientSession() as session:
        params = {"q": query, "limit": 10, "recommended": "true"}
        if category:
            params["category"] = category
        
        async with session.get(f"{FMHY_API_URL}/api/search", params=params) as resp:
            data = await resp.json()
    
    resources = data.get("resources", [])
    if not resources:
        await interaction.followup.send(f"❌ No results for **{query}**", ephemeral=True)
        return
    
    embed = discord.Embed(
        title=f"🔍 {query}",
        color=discord.Color.blue()
    )
    
    for i, r in enumerate(resources[:10], 1):
        name = r.get('name', 'Unknown')
        url = r.get('url', '#')
        desc = r.get('description', '')[:60]
        embed.add_field(
            name=f"{i}. {name}",
            value=f"{desc}\n[Open]({url})",
            inline=False
        )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="watch", description="Search for a movie/show and get links")
@has_control_role()
async def watch_cmd(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    
    async with aiohttp.ClientSession() as session:
        params = {"q": query, "limit": 5, "recommended": "true"}
        async with session.get(f"{FMHY_API_URL}/api/search", params=params) as resp:
            data = await resp.json()
    
    resources = data.get("resources", [])
    if not resources:
        await interaction.followup.send(f"❌ No results for **{query}**", ephemeral=True)
        return
    
    embed = discord.Embed(
        title=f"🎬 {query}",
        description="Pick a site, find your movie, screen share in Discord!",
        color=discord.Color.blue()
    )
    
    for i, r in enumerate(resources[:5], 1):
        name = r.get('name', 'Unknown')
        url = r.get('url', '#')
        desc = r.get('description', '')[:60]
        embed.add_field(
            name=f"{i}. {name}",
            value=f"{desc}\n[Open]({url})",
            inline=False
        )
    
    embed.set_footer(text="Use /join first, then screen share from your PC")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="random", description="Get a random streaming site")
async def random_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{FMHY_API_URL}/api/random") as resp:
            resource = await resp.json()
    
    embed = discord.Embed(
        title="🎲 Random Site",
        color=discord.Color.purple()
    )
    
    embed.add_field(name="Name", value=resource.get('name', 'Unknown'), inline=True)
    embed.add_field(name="URL", value=f"[Open]({resource.get('url', '#')})", inline=True)
    embed.add_field(name="Description", value=resource.get('description', '')[:200], inline=False)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="stats", description="Show API stats")
async def stats_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{FMHY_API_URL}/api/stats") as resp:
            data = await resp.json()
    
    embed = discord.Embed(title="📊 API Stats", color=discord.Color.green())
    embed.add_field(name="Resources", value=str(data['total_resources']), inline=True)
    embed.add_field(name="With Discord", value=str(data['with_discord']), inline=True)
    embed.add_field(name="With GitHub", value=str(data['with_github']), inline=True)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="checktoken", description="Check if your token is saved correctly")
async def checktoken_cmd(interaction: discord.Interaction):
    user_token = get_token(interaction.user.id)
    if not user_token:
        await interaction.response.send_message("❌ No token saved. Use `/token`", ephemeral=True)
        return
    
    # Show first and last 5 chars only for security
    masked = user_token[:5] + "..." + user_token[-5:]
    token_len = len(user_token)
    
    embed = discord.Embed(
        title="🔑 Token Info",
        description=f"**Length:** {token_len} chars\n**Preview:** `{masked}`\n**Starts with:** `{user_token[:8]}`",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="help", description="Show all commands")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎬 FMHY Selfbot Commands",
        description="Commands for streaming movies with friends",
        color=discord.Color.blue()
    )
    
    commands_list = [
        ("`/token`", "Save your Discord user token"),
        ("`/removetoken`", "Remove your saved token"),
        ("`/join`", "Join voice as yourself (for screen sharing)"),
        ("`/watch <movie>`", "Find streaming sites for a movie"),
        ("`/search <query>`", "Search FMHY database"),
        ("`/random`", "Get random streaming site"),
        ("`/stats`", "Show API statistics"),
        ("`/tokens`", "View all saved tokens (admin)"),
        ("`/help`", "Show this message"),
    ]
    
    for name, desc in commands_list:
        embed.add_field(name=name, value=desc, inline=False)
    
    embed.set_footer(text="Setup: 1. /token  2. /join  3. /watch movie_name  4. Screen share")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="tokens", description="View all saved tokens (admin only)")
@has_control_role()
async def tokens_cmd(interaction: discord.Interaction):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT user_id, username, created_at FROM user_tokens").fetchall()
    conn.close()
    
    if not rows:
        await interaction.response.send_message("No tokens saved yet.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title=f"🔑 Saved Tokens ({len(rows)} users)",
        color=discord.Color.blue()
    )
    
    for user_id, username, created_at in rows:
        embed.add_field(
            name=f"{username or 'Unknown'} ({user_id})",
            value=f"Saved: {created_at}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("ERROR: Set DISCORD_TOKEN env var")
        exit(1)
    bot.run(BOT_TOKEN)
