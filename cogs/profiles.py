import discord
from discord.ext import commands
from pathlib import Path
from datetime import datetime
import json

BASE = Path(__file__).parent.parent
PROFILES_FILE = BASE / "data" / "profiles.json"

logger = __import__("logging").getLogger(__name__)

def load_json(path: Path):
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

class Profiles(commands.Cog):
    """Player profiles and stats tracking."""
    
    def __init__(self, bot):
        self.bot = bot
        PROFILES_FILE.parent.mkdir(parents=True, exist_ok=True)

    def get_profile(self, user_id: int) -> dict:
        """Get or create player profile."""
        data = load_json(PROFILES_FILE)
        uid = str(user_id)
        if uid not in data:
            data[uid] = {
                "username": "",
                "minecraft_uuid": "",
                "kills": 0,
                "deaths": 0,
                "playtime_hours": 0,
                "level": 1,
                "achievements": [],
                "first_seen": datetime.utcnow().isoformat(),
                "last_seen": datetime.utcnow().isoformat()
            }
            save_json(PROFILES_FILE, data)
        return data[uid]

    def update_stat(self, user_id: int, stat: str, amount: int):
        """Update a player stat."""
        data = load_json(PROFILES_FILE)
        uid = str(user_id)
        if uid not in data:
            self.get_profile(user_id)
            data = load_json(PROFILES_FILE)
        data[uid][stat] = data[uid].get(stat, 0) + amount
        data[uid]["last_seen"] = datetime.utcnow().isoformat()
        save_json(PROFILES_FILE, data)

    @commands.command(name="profile")
    async def profile(self, ctx, member: discord.Member = None):
        """👤 View player profile."""
        member = member or ctx.author
        prof = self.get_profile(member.id)

        # Calculate K/D ratio
        kd_ratio = prof["kills"] / max(1, prof["deaths"])

        embed = discord.Embed(title=f"👤 {member.name}'s Profile", color=discord.Color.blurple())
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        
        embed.add_field(name="Level", value=f"**{prof['level']}**", inline=True)
        embed.add_field(name="Playtime", value=f"**{prof['playtime_hours']}h**", inline=True)
        embed.add_field(name="Joined", value=f"<t:{int(datetime.fromisoformat(prof['first_seen']).timestamp())}:d>", inline=True)
        
        embed.add_field(name="Kills", value=f"**{prof['kills']}**", inline=True)
        embed.add_field(name="Deaths", value=f"**{prof['deaths']}**", inline=True)
        embed.add_field(name="K/D Ratio", value=f"**{kd_ratio:.2f}**", inline=True)

        if prof.get("achievements"):
            achievements_str = ", ".join(prof["achievements"][:5])
            embed.add_field(name="Achievements", value=achievements_str, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="stats")
    async def stats(self, ctx, member: discord.Member = None):
        """📊 View detailed player stats."""
        member = member or ctx.author
        prof = self.get_profile(member.id)

        embed = discord.Embed(title=f"📊 Stats - {member.name}", color=discord.Color.gold())
        embed.add_field(name="💀 Kills", value=f"**{prof['kills']:,}**", inline=True)
        embed.add_field(name="⚰️ Deaths", value=f"**{prof['deaths']:,}**", inline=True)
        embed.add_field(name="📈 K/D", value=f"**{prof['kills'] / max(1, prof['deaths']):.2f}**", inline=True)
        
        embed.add_field(name="⏱️ Playtime", value=f"**{prof['playtime_hours']:,}** hours", inline=True)
        embed.add_field(name="⭐ Level", value=f"**{prof['level']}**", inline=True)
        embed.add_field(name="🏅 Achievements", value=f"**{len(prof.get('achievements', []))}**", inline=True)

        await ctx.send(embed=embed)

    @commands.command(name="leaderboard_kills")
    async def leaderboard_kills(self, ctx):
        """🏆 Top killers."""
        data = load_json(PROFILES_FILE)
        sorted_players = sorted(
            data.items(),
            key=lambda x: x[1].get("kills", 0),
            reverse=True
        )[:10]

        embed = discord.Embed(title="🏆 Top Killers", color=discord.Color.dark_red())
        for rank, (uid, prof) in enumerate(sorted_players, 1):
            member = ctx.guild.get_member(int(uid))
            name = member.mention if member else f"<@{uid}>"
            emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."
            embed.add_field(name=f"{emoji} {name}", value=f"**{prof['kills']:,}** kills", inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="leaderboard_playtime")
    async def leaderboard_playtime(self, ctx):
        """⏱️ Most active players."""
        data = load_json(PROFILES_FILE)
        sorted_players = sorted(
            data.items(),
            key=lambda x: x[1].get("playtime_hours", 0),
            reverse=True
        )[:10]

        embed = discord.Embed(title="⏱️ Most Active Players", color=discord.Color.green())
        for rank, (uid, prof) in enumerate(sorted_players, 1):
            member = ctx.guild.get_member(int(uid))
            name = member.mention if member else f"<@{uid}>"
            emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."
            embed.add_field(name=f"{emoji} {name}", value=f"**{prof['playtime_hours']:,}h** playtime", inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="achievement")
    @commands.has_permissions(administrator=True)
    async def achievement(self, ctx, member: discord.Member, *, achievement: str):
        """🏅 Give an achievement to a player."""
        data = load_json(PROFILES_FILE)
        uid = str(member.id)
        if uid not in data:
            self.get_profile(member.id)
            data = load_json(PROFILES_FILE)
        
        if achievement not in data[uid]["achievements"]:
            data[uid]["achievements"].append(achievement)
            save_json(PROFILES_FILE, data)

            embed = discord.Embed(title="🏅 Achievement Unlocked!", color=discord.Color.gold())
            embed.add_field(name="Player", value=member.mention)
            embed.add_field(name="Achievement", value=achievement, inline=False)
            await ctx.send(embed=embed)
            
            try:
                await member.send(f"🏅 **Achievement Unlocked:** {achievement}")
            except:
                pass
        else:
            await ctx.send(f"ℹ️ {member.mention} already has this achievement.")

async def setup(bot):
    await bot.add_cog(Profiles(bot))
