import discord
from discord.ext import commands
from datetime import datetime

class Utilities(commands.Cog):
    """Utility commands for server management."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="serverinfo")
    async def serverinfo(self, ctx):
        """ℹ️ Get server information."""
        guild = ctx.guild
        
        embed = discord.Embed(title=f"ℹ️ {guild.name}", color=discord.Color.blurple())
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Members", value=f"**{guild.member_count}**", inline=True)
        embed.add_field(name="Created", value=f"<t:{int(guild.created_at.timestamp())}:d>", inline=True)
        
        embed.add_field(name="Channels", value=f"Text: {len(guild.text_channels)} | Voice: {len(guild.voice_channels)}", inline=True)
        embed.add_field(name="Roles", value=f"**{len(guild.roles)}**", inline=True)
        embed.add_field(name="Boosts", value=f"**{guild.premium_subscription_count}**", inline=True)
        
        embed.set_footer(text=f"Guild ID: {guild.id}")
        
        await ctx.send(embed=embed)

    @commands.command(name="userinfo")
    async def userinfo(self, ctx, member: discord.Member = None):
        """👤 Get user information."""
        member = member or ctx.author
        
        embed = discord.Embed(title=f"👤 {member.name}", color=member.color)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        
        embed.add_field(name="Username", value=f"**{member}**", inline=True)
        embed.add_field(name="ID", value=f"**{member.id}**", inline=True)
        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:d>", inline=True)
        
        embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:d>", inline=True)
        embed.add_field(name="Bot", value="✅ Yes" if member.bot else "❌ No", inline=True)
        
        if member.roles[1:]:  # Skip @everyone role
            roles_str = ", ".join([r.mention for r in member.roles[1:][:10]])
            embed.add_field(name="Roles", value=roles_str, inline=False)
        
        embed.set_footer(text=f"User ID: {member.id}")
        
        await ctx.send(embed=embed)

    @commands.command(name="membercount")
    async def membercount(self, ctx):
        """👥 Get member count."""
        guild = ctx.guild
        
        embed = discord.Embed(title="👥 Member Count", color=discord.Color.blurple())
        embed.add_field(name="Total Members", value=f"**{guild.member_count}**", inline=True)
        embed.add_field(name="Humans", value=f"**{sum(1 for m in guild.members if not m.bot)}**", inline=True)
        embed.add_field(name="Bots", value=f"**{sum(1 for m in guild.members if m.bot)}**", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="ping")
    async def ping(self, ctx):
        """🏓 Check bot latency."""
        latency = round(self.bot.latency * 1000)
        
        embed = discord.Embed(title="🏓 Pong!", color=discord.Color.green())
        embed.add_field(name="Latency", value=f"**{latency}ms**", inline=False)
        embed.set_footer(text="Discord API Latency")
        
        await ctx.send(embed=embed)

    @commands.command(name="help_minecraft")
    async def help_minecraft(self, ctx):
        """❓ Get list of all commands."""
        embed = discord.Embed(title="❓ Minecraft Network Bot - Commands", color=discord.Color.gold())
        
        # Moderation
        embed.add_field(
            name="🛡️ Moderation",
            value="`warn` `mute` `kick` `ban` `cases` `appeal`",
            inline=False
        )
        
        # Economy
        embed.add_field(
            name="💰 Economy",
            value="`balance` `daily` `pay` `leaderboard` `shop` `buy`",
            inline=False
        )
        
        # Profiles
        embed.add_field(
            name="👤 Profiles",
            value="`profile` `stats` `leaderboard_kills` `leaderboard_playtime` `achievement`",
            inline=False
        )
        
        # Fun
        embed.add_field(
            name="🎮 Fun",
            value="`rps` `8ball` `coinflip` `roll` `giveaway` `poll` `trivia` `joke`",
            inline=False
        )
        
        # Utilities
        embed.add_field(
            name="🔧 Utilities",
            value="`serverinfo` `userinfo` `membercount` `ping` `help_minecraft`",
            inline=False
        )
        
        embed.set_footer(text="Use /command for slash commands or !command for prefix commands")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utilities(bot))
