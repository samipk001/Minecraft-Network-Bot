import asyncio
import logging
import discord
from discord.ext import commands
from discord.ui import View, Button
from pathlib import Path
from datetime import datetime, timedelta
import json

BASE = Path(__file__).parent.parent
MODERATION_FILE = BASE / "data" / "moderation.json"
APPEALS_FILE = BASE / "data" / "appeals.json"

logger = logging.getLogger(__name__)

# Helper functions
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

# Appeal button view
class AppealView(View):
    def __init__(self, case_id: str):
        super().__init__(timeout=None)
        self.case_id = case_id

    @discord.ui.button(label="Appeal Ban", style=discord.ButtonStyle.primary, custom_id=f"appeal_btn")
    async def appeal_button(self, interaction: discord.Interaction, button: Button):
        """Open appeal form for banned user."""
        appeals = load_json(APPEALS_FILE)
        if str(interaction.user.id) in appeals:
            return await interaction.response.send_message("❌ You already have an active appeal.", ephemeral=True)
        
        # Create appeal in data
        appeals[str(interaction.user.id)] = {
            "case_id": self.case_id,
            "reason": "Pending",
            "status": "pending",
            "submitted_at": datetime.utcnow().isoformat(),
            "response": None
        }
        save_json(APPEALS_FILE, appeals)
        
        await interaction.response.send_message("✅ Your appeal has been submitted. Please wait for staff review.", ephemeral=True)


class Moderation(commands.Cog):
    """Moderation commands for Minecraft network."""
    
    def __init__(self, bot):
        self.bot = bot
        MODERATION_FILE.parent.mkdir(parents=True, exist_ok=True)

    @commands.command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """⚠️ Warn a user."""
        if member == ctx.author:
            return await ctx.send("❌ You can't warn yourself.")
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("❌ You can't warn someone with equal or higher role.")

        mod_data = load_json(MODERATION_FILE)
        case_id = str(len(mod_data) + 1)
        
        mod_data[case_id] = {
            "type": "warn",
            "user_id": member.id,
            "moderator_id": ctx.author.id,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
        save_json(MODERATION_FILE, mod_data)

        embed = discord.Embed(title="⚠️ User Warned", color=discord.Color.orange())
        embed.add_field(name="User", value=member.mention)
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Case ID", value=f"#{case_id}")
        embed.set_footer(text=f"Warned by {ctx.author}")
        
        await ctx.send(embed=embed)
        try:
            await member.send(f"⚠️ You were warned in {ctx.guild.name}.\n**Reason:** {reason}")
        except:
            pass

    @commands.command(name="mute")
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, duration: str = "1h", *, reason: str = "No reason provided"):
        """🔇 Mute a user for a duration (1h, 24h, 7d, etc.)."""
        if member == ctx.author:
            return await ctx.send("❌ You can't mute yourself.")
        
        # Parse duration
        duration_map = {"m": 60, "h": 3600, "d": 86400, "w": 604800}
        try:
            unit = duration[-1].lower()
            amount = int(duration[:-1])
            if unit not in duration_map:
                raise ValueError
            seconds = amount * duration_map[unit]
        except:
            return await ctx.send("❌ Invalid duration format. Use: 1h, 24h, 7d, etc.")

        # Create/use muted role
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            try:
                muted_role = await ctx.guild.create_role(name="Muted", color=discord.Color.darker_gray())
                for channel in ctx.guild.channels:
                    await channel.set_permissions(muted_role, send_messages=False, speak=False)
            except:
                return await ctx.send("❌ Failed to create muted role.")

        await member.add_roles(muted_role)
        
        mod_data = load_json(MODERATION_FILE)
        case_id = str(len(mod_data) + 1)
        mod_data[case_id] = {
            "type": "mute",
            "user_id": member.id,
            "moderator_id": ctx.author.id,
            "reason": reason,
            "duration": seconds,
            "timestamp": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(seconds=seconds)).isoformat()
        }
        save_json(MODERATION_FILE, mod_data)

        embed = discord.Embed(title="🔇 User Muted", color=discord.Color.red())
        embed.add_field(name="User", value=member.mention)
        embed.add_field(name="Duration", value=duration)
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Case ID", value=f"#{case_id}")
        await ctx.send(embed=embed)

        # Schedule unmute
        await asyncio.sleep(seconds)
        try:
            await member.remove_roles(muted_role)
            logger.info(f"Auto-unmuted {member.id}")
        except:
            pass

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """🚫 Ban a user from the server."""
        if member == ctx.author:
            return await ctx.send("❌ You can't ban yourself.")
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("❌ You can't ban someone with equal or higher role.")

        mod_data = load_json(MODERATION_FILE)
        case_id = str(len(mod_data) + 1)
        
        mod_data[case_id] = {
            "type": "ban",
            "user_id": member.id,
            "moderator_id": ctx.author.id,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
        save_json(MODERATION_FILE, mod_data)

        # Send appeal embed before banning
        embed = discord.Embed(
            title="🚫 You Have Been Banned",
            description=f"You were banned from **{ctx.guild.name}**",
            color=discord.Color.dark_red()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Case ID", value=f"#{case_id}", inline=True)
        embed.set_footer(text="You can appeal this ban using the button below.")
        
        try:
            await member.send(embed=embed, view=AppealView(case_id))
        except:
            pass

        await ctx.guild.ban(member, reason=reason)
        
        embed.title = "✅ User Banned"
        embed.color = discord.Color.green()
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """👢 Kick a user from the server."""
        if member == ctx.author:
            return await ctx.send("❌ You can't kick yourself.")
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("❌ You can't kick someone with equal or higher role.")

        mod_data = load_json(MODERATION_FILE)
        case_id = str(len(mod_data) + 1)
        
        mod_data[case_id] = {
            "type": "kick",
            "user_id": member.id,
            "moderator_id": ctx.author.id,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
        save_json(MODERATION_FILE, mod_data)

        await ctx.guild.kick(member, reason=reason)
        
        embed = discord.Embed(title="👢 User Kicked", color=discord.Color.gold())
        embed.add_field(name="User", value=member.mention)
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Case ID", value=f"#{case_id}")
        embed.set_footer(text=f"Kicked by {ctx.author}")
        
        await ctx.send(embed=embed)

    @commands.command(name="cases")
    @commands.has_permissions(manage_messages=True)
    async def cases(self, ctx, member: discord.Member):
        """📋 View moderation cases for a user."""
        mod_data = load_json(MODERATION_FILE)
        user_cases = [
            (cid, case) for cid, case in mod_data.items()
            if case.get("user_id") == member.id
        ]

        if not user_cases:
            return await ctx.send(f"✅ {member.mention} has no cases.")

        embed = discord.Embed(title=f"📋 Cases for {member}", color=discord.Color.blurple())
        for cid, case in user_cases[:10]:
            mod = ctx.guild.get_member(case.get("moderator_id"))
            mod_name = mod.mention if mod else "Unknown"
            embed.add_field(
                name=f"#{cid} - {case['type'].upper()}",
                value=f"**Reason:** {case['reason']}\n**Mod:** {mod_name}\n**Date:** {case['timestamp'][:10]}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command(name="appeal")
    async def appeal(self, ctx):
        """📝 Check your ban appeal status."""
        appeals = load_json(APPEALS_FILE)
        if str(ctx.author.id) not in appeals:
            return await ctx.send("❌ You don't have any active appeals.")

        appeal = appeals[str(ctx.author.id)]
        embed = discord.Embed(title="📝 Your Appeal", color=discord.Color.blurple())
        embed.add_field(name="Status", value=appeal["status"].upper(), inline=False)
        embed.add_field(name="Case ID", value=appeal["case_id"], inline=True)
        if appeal.get("response"):
            embed.add_field(name="Response", value=appeal["response"], inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
