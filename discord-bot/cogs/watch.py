import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
import subprocess
import os
import signal
import json
import yt_dlp
from typing import Optional

FMHY_API_URL = os.getenv("FMHY_API_URL", "https://fmhy-api.onrender.com")
CONFIG_FILE = "bot_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"control_roles": [], "allowed_users": []}

def has_control_role():
    async def predicate(interaction: discord.Interaction):
        config = load_config()
        allowed_roles = config.get("control_roles", [])
        
        if not allowed_roles:
            return True
        
        user_roles = [str(role.id) for role in interaction.user.roles]
        user_roles.append(str(interaction.user.id))
        
        for role_id in allowed_roles:
            if role_id in user_roles:
                return True
        
        await interaction.response.send_message(
            "❌ You don't have permission to use this command!",
            ephemeral=True
        )
        return False
    return app_commands.check(predicate)

def extract_video_url(url):
    """Extract direct video URL using yt-dlp"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best[height<=720]',
        'extract_flat': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'url' in info:
                return info['url'], info.get('title', 'Unknown')
            elif 'entries' in info:
                for entry in info['entries']:
                    if entry and 'url' in entry:
                        return entry['url'], entry.get('title', 'Unknown')
    except Exception as e:
        print(f"yt-dlp error: {e}")
        return None, None

class Watch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_streams = {}
    
    @app_commands.command(name="join", description="Join your voice channel")
    @has_control_role()
    async def join(self, interaction: discord.Interaction):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message(
                "❌ You need to be in a voice channel!",
                ephemeral=True
            )
            return
        
        voice_channel = interaction.user.voice.channel
        guild_id = interaction.guild_id
        
        if guild_id in self.active_streams:
            await interaction.response.send_message(
                "❌ Already in a voice channel!",
                ephemeral=True
            )
            return
        
        try:
            voice_client = await voice_channel.connect()
            self.active_streams[guild_id] = {
                "voice_client": voice_client,
                "channel": voice_channel,
                "url": None
            }
            
            embed = discord.Embed(
                title="🔊 Joined Voice Channel",
                description=f"Connected to **{voice_channel.name}**",
                color=discord.Color.green()
            )
            embed.set_footer(text="Use /watch to start streaming or /leave to disconnect")
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to join: {e}",
                ephemeral=True
            )
    
    @app_commands.command(name="leave", description="Leave the voice channel")
    @has_control_role()
    async def leave(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        
        if guild_id not in self.active_streams:
            await interaction.response.send_message(
                "❌ Not in any voice channel!",
                ephemeral=True
            )
            return
        
        stream = self.active_streams.pop(guild_id)
        voice_client = stream["voice_client"]
        
        if voice_client.is_connected():
            channel_name = voice_client.channel.name
            await voice_client.disconnect()
            
            embed = discord.Embed(
                title="🔊 Left Voice Channel",
                description=f"Disconnected from **{channel_name}**",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                "❌ Not connected!",
                ephemeral=True
            )
    
    @app_commands.command(name="play", description="Extract and play video from a URL")
    @app_commands.describe(url="Streaming site URL to play from")
    @has_control_role()
    async def play(self, interaction: discord.Interaction, url: str):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message(
                "❌ You need to be in a voice channel!",
                ephemeral=True
            )
            return
        
        voice_channel = interaction.user.voice.channel
        
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="🔍 Extracting video...",
            description=f"Trying to extract video from:\n{url}",
            color=discord.Color.yellow()
        )
        await interaction.followup.send(embed=embed)
        
        video_url, title = await asyncio.get_event_loop().run_in_executor(
            None, extract_video_url, url
        )
        
        if video_url:
            embed = discord.Embed(
                title=f"🎬 Playing: {title or 'Video'}",
                description=f"**Channel:** {voice_channel.name}",
                color=discord.Color.green()
            )
            await interaction.edit_original_response(embed=embed)
            await self._start_stream(interaction, voice_channel, video_url)
        else:
            embed = discord.Embed(
                title="❌ Couldn't extract video",
                description="This site might not be supported by yt-dlp.\n\nTry a different URL or use `/watch` to share your screen.",
                color=discord.Color.red()
            )
            await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="watch", description="Stream a movie/show in voice channel")
    @app_commands.describe(
        query="Search for a movie/show",
        url="Direct URL to stream (if you have one)"
    )
    @has_control_role()
    async def watch(
        self, 
        interaction: discord.Interaction, 
        query: Optional[str] = None,
        url: Optional[str] = None
    ):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message(
                "❌ You need to be in a voice channel!",
                ephemeral=True
            )
            return
        
        voice_channel = interaction.user.voice.channel
        
        await interaction.response.defer()
        
        if url:
            # Try to extract direct video URL
            video_url, title = await asyncio.get_event_loop().run_in_executor(
                None, extract_video_url, url
            )
            
            if video_url:
                embed = discord.Embed(
                    title=f"🎬 Playing: {title}",
                    description=f"**Channel:** {voice_channel.name}",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=embed)
                await self._start_stream(interaction, voice_channel, video_url)
            else:
                # If extraction fails, use screen share mode
                embed = discord.Embed(
                    title="📺 Screen Share Mode",
                    description=f"**URL:** {url}\n**Channel:** {voice_channel.name}",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="How to watch",
                    value="1. Bot joined the voice channel\n2. Open the URL in your browser\n3. Click 'Screen Share' in Discord\n4. Share your browser window",
                    inline=False
                )
                embed.set_footer(text="yt-dlp can't extract this site - screen share is the way to go")
                await interaction.followup.send(embed=embed)
                await self._start_stream(interaction, voice_channel, url)
            return
        
        if not query:
            await interaction.followup.send(
                "❌ Provide either `query` or `url`!",
                ephemeral=True
            )
            return
        
        async with aiohttp.ClientSession() as session:
            params = {
                "q": query,
                "limit": 5,
                "recommended": "true"
            }
            async with session.get(f"{FMHY_API_URL}/api/search", params=params) as resp:
                if resp.status != 200:
                    await interaction.followup.send("❌ API error!", ephemeral=True)
                    return
                data = await resp.json()
        
        resources = data.get("resources", [])
        if not resources:
            await interaction.followup.send(
                f"❌ No results for **{query}**",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🎬 Search Results",
            description=f"Found {len(resources)} results for **{query}**",
            color=discord.Color.blue()
        )
        
        for i, r in enumerate(resources[:5], 1):
            name = r.get('name', 'Unknown')
            url_r = r.get('url', '#')
            desc = r.get('description', '')[:100]
            category = r.get('category', '')
            embed.add_field(
                name=f"{i}. {name} ({category})",
                value=f"{desc}\n[Visit Site]({url_r})",
                inline=False
            )
        
        embed.set_footer(text="Use /watch url:URL to play a specific link")
        await interaction.followup.send(embed=embed)
    
    async def _start_stream(self, interaction, voice_channel, url):
        guild_id = interaction.guild_id
        
        if guild_id in self.active_streams:
            old = self.active_streams.pop(guild_id)
            try:
                if old["voice_client"].is_connected():
                    await old["voice_client"].disconnect()
            except:
                pass
        
        try:
            voice_client = await voice_channel.connect()
            
            embed = discord.Embed(
                title="🔴 Live Now",
                description=f"Streaming in **{voice_channel.name}**\n[Watch URL]({url})",
                color=discord.Color.red()
            )
            embed.add_field(
                name="How to Watch",
                value="1. Click the voice channel\n2. Click 'Watch Together' or screen share\n3. Open the URL above in your browser",
                inline=False
            )
            await interaction.followup.send(embed=embed)
            
            self.active_streams[guild_id] = {
                "voice_client": voice_client,
                "channel": voice_channel,
                "url": url
            }
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Failed to join voice channel: {e}",
                ephemeral=True
            )
    
    @app_commands.command(name="stop", description="Stop the current stream")
    @has_control_role()
    async def stop(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        
        if guild_id not in self.active_streams:
            await interaction.response.send_message(
                "❌ Nothing is streaming!",
                ephemeral=True
            )
            return
        
        stream = self.active_streams.pop(guild_id)
        voice_client = stream["voice_client"]
        
        if voice_client.is_connected():
            await voice_client.disconnect()
        
        embed = discord.Embed(
            title="⏹️ Stream Stopped",
            description="Thanks for watching!",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="nowplaying", description="Show current stream info")
    @has_control_role()
    async def nowplaying(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        
        if guild_id not in self.active_streams:
            await interaction.response.send_message(
                "❌ Nothing is streaming!",
                ephemeral=True
            )
            return
        
        stream = self.active_streams[guild_id]
        embed = discord.Embed(
            title="🔴 Currently Streaming",
            description=f"**URL:** {stream['url']}\n**Channel:** {stream['channel'].name}",
            color=discord.Color.red()
        )
        embed.set_footer(text="Use /stop to end the stream")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="search", description="Search FMHY API for movies/shows")
    @app_commands.describe(
        query="What to search for",
        category="Filter by category (Streaming, Gaming, etc.)"
    )
    async def search(
        self,
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
                if resp.status != 200:
                    await interaction.followup.send("❌ API error!", ephemeral=True)
                    return
                data = await resp.json()
        
        resources = data.get("resources", [])
        if not resources:
            await interaction.followup.send(
                f"❌ No results for **{query}**",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f"🔍 Search: {query}",
            color=discord.Color.blue()
        )
        
        for i, r in enumerate(resources[:10], 1):
            name = r.get('name', 'Unknown')
            url = r.get('url', '#')
            desc = r.get('description', '')[:80]
            discord_link = r.get('discord')
            
            value = f"{desc}\n[Visit]({url})"
            if discord_link:
                value += f" | [Discord]({discord_link})"
            
            embed.add_field(
                name=f"{i}. {name}",
                value=value,
                inline=False
            )
        
        embed.set_footer(text=f"Page 1 • {data.get('total', 0)} total results")
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="random", description="Get a random resource from FMHY")
    @app_commands.describe(category="Filter by category")
    async def random(
        self,
        interaction: discord.Interaction,
        category: Optional[str] = None
    ):
        await interaction.response.defer()
        
        async with aiohttp.ClientSession() as session:
            params = {}
            if category:
                params["category"] = category
            
            async with session.get(f"{FMHY_API_URL}/api/random", params=params) as resp:
                if resp.status != 200:
                    await interaction.followup.send("❌ API error!", ephemeral=True)
                    return
                resource = await resp.json()
        
        embed = discord.Embed(
            title=f"🎲 Random {category or 'Resource'}",
            color=discord.Color.purple()
        )
        
        name = resource.get('name', 'Unknown')
        url = resource.get('url', '#')
        desc = resource.get('description', '')
        cat = resource.get('category', '')
        subcat = resource.get('subcategory', '')
        discord_link = resource.get('discord')
        
        embed.add_field(name="Name", value=name, inline=True)
        embed.add_field(name="Category", value=f"{cat} / {subcat}", inline=True)
        embed.add_field(name="Description", value=desc[:200] or "No description", inline=False)
        embed.add_field(name="Link", value=f"[Visit Site]({url})", inline=False)
        
        if discord_link:
            embed.add_field(name="Discord", value=f"[Join]({discord_link})", inline=True)
        
        embed.set_footer(text="Use /watch url:URL to play this")
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="stats", description="Show FMHY API statistics")
    async def stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{FMHY_API_URL}/api/stats") as resp:
                if resp.status != 200:
                    await interaction.followup.send("❌ API error!", ephemeral=True)
                    return
                data = await resp.json()
        
        embed = discord.Embed(
            title="📊 FMHY API Stats",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Total Resources", value=str(data['total_resources']), inline=True)
        embed.add_field(name="Recommended", value=str(data['recommended_resources']), inline=True)
        embed.add_field(name="Categories", value=str(data['categories']), inline=True)
        embed.add_field(name="Subcategories", value=str(data['subcategories']), inline=True)
        embed.add_field(name="Unique Tags", value=str(data['unique_tags']), inline=True)
        embed.add_field(name="With Discord", value=str(data['with_discord']), inline=True)
        embed.add_field(name="With GitHub", value=str(data['with_github']), inline=True)
        embed.add_field(name="With Telegram", value=str(data['with_telegram']), inline=True)
        
        embed.set_footer(text=f"API: {FMHY_API_URL}")
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Watch(bot))
