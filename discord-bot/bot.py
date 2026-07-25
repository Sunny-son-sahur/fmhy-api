import discord
from discord.ext import commands
import asyncio
import aiohttp
import json
import os
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

FMHY_API_URL = os.getenv("FMHY_API_URL", "https://fmhy-api.onrender.com")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CONTROL_ROLES = os.getenv("CONTROL_ROLES", "1530632553021837372").split(",") if os.getenv("CONTROL_ROLES") else ["1530632553021837372"]
CONFIG_FILE = "bot_config.json"

if not DISCORD_TOKEN:
    print("ERROR: Set DISCORD_TOKEN environment variable")
    exit(1)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"control_roles": CONTROL_ROLES, "allowed_users": []}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

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
    return discord.app_commands.check(predicate)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")
    print(f"FMHY API: {FMHY_API_URL}")
    print(f"Control Roles: {CONTROL_ROLES}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")

@bot.command(name="setrole")
@commands.has_permissions(administrator=True)
async def set_role(ctx, role: discord.Role):
    config = load_config()
    if str(role.id) not in config.get("control_roles", []):
        config.setdefault("control_roles", []).append(str(role.id))
        save_config(config)
        await ctx.send(f"✅ Added {role.mention} as a control role")
    else:
        await ctx.send("❌ Role already has control")

@bot.command(name="removerole")
@commands.has_permissions(administrator=True)
async def remove_role(ctx, role: discord.Role):
    config = load_config()
    roles = config.get("control_roles", [])
    if str(role.id) in roles:
        roles.remove(str(role.id))
        config["control_roles"] = roles
        save_config(config)
        await ctx.send(f"✅ Removed {role.mention} from control roles")
    else:
        await ctx.send("❌ Role doesn't have control")

@bot.command(name="listroles")
@commands.has_permissions(administrator=True)
async def list_roles(ctx):
    config = load_config()
    roles = config.get("control_roles", [])
    if not roles:
        await ctx.send("No control roles set. Everyone has access.")
        return
    
    mentions = []
    for role_id in roles:
        role = ctx.guild.get_role(int(role_id))
        if role:
            mentions.append(role.mention)
    
    embed = discord.Embed(
        title="Control Roles",
        description="\n".join(mentions) if mentions else "None found",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command(name="api")
async def api_status(ctx):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{FMHY_API_URL}/api/stats") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    embed = discord.Embed(
                        title="FMHY API Status",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Total Resources", value=str(data['total_resources']), inline=True)
                    embed.add_field(name="Categories", value=str(data['categories']), inline=True)
                    embed.add_field(name="With Discord", value=str(data['with_discord']), inline=True)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("API is down!")
        except Exception as e:
            await ctx.send(f"API connection failed: {e}")

async def setup():
    await bot.load_extension("cogs.watch")

if __name__ == "__main__":
    keep_alive()
    async def main():
        async with bot:
            await setup()
            await bot.start(DISCORD_TOKEN)
    asyncio.run(main())
