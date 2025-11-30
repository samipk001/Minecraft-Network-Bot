import asyncio
import logging
import discord
from discord.ext import commands
from discord.ui import View, Button
import json
import os
from pathlib import Path
from datetime import datetime
import io

BASE = Path(__file__).parent.parent
TICKETS_FILE = BASE / "tickets.json"
BLACKLIST_FILE = BASE / "blacklist.json"
CONFIG_FILE = BASE / "config.json"

# logger
logger = logging.getLogger(__name__)

# -------------------------
# Helper: JSON persistence
# -------------------------
def load_json(path: Path):
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


async def generate_transcript(channel: discord.TextChannel, format: str = "html") -> str:
    """Generate a transcript (HTML or TXT). format='html' (default) or 'txt'. Returns file path."""
    transcripts_dir = BASE / "transcripts"
    transcripts_dir.mkdir(exist_ok=True)

    ext = "html" if format == "html" else "txt"
    filename = f"transcript_{channel.guild.id}_{channel.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
    path = transcripts_dir / filename

    messages = []
    async for msg in channel.history(limit=None, oldest_first=True):
        messages.append((msg.created_at, msg.author, msg.content or "", msg.attachments))

    try:
        if format == "html":
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #2c2f33; color: #dcddde; margin: 0; padding: 20px; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header {{ background: #23272a; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #7289da; }}
        .header h2 {{ margin: 0 0 10px 0; color: #fff; }}
        .header p {{ margin: 5px 0; color: #b9bbbe; }}
        .message {{ background: #36393f; padding: 12px 15px; margin: 10px 0; border-radius: 5px; border-left: 3px solid #7289da; }}
        .message:nth-child(odd) {{ background: #35393e; }}
        .author {{ font-weight: bold; color: #7289da; font-size: 0.95em; }}
        .timestamp {{ color: #99aab5; font-size: 0.85em; margin-left: 10px; }}
        .content {{ margin-top: 8px; word-wrap: break-word; }}
        .attachment {{ color: #43b581; margin-top: 5px; font-size: 0.9em; }}
        a {{ color: #00b0f4; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class=\"container\">
        <div class=\"header\">
            <h2>📋 Ticket Transcript</h2>
            <p><strong>Channel:</strong> {channel.name}</p>
            <p><strong>Guild:</strong> {channel.guild.name}</p>
            <p><strong>Generated:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>
"""
            for ts, author, content, attachments in messages:
                html_content += f"""        <div class="message">
            <span class="author">{author}</span> <span class="timestamp">{ts.strftime('%H:%M:%S')}</span>
            <div class="content">{content}</div>"""
                if attachments:
                    for att in attachments:
                        html_content += f'<div class="attachment">📎 <a href="{att.url}" target="_blank">{att.filename}</a></div>'
                html_content += "        </div>\n"
            html_content += """    </div>
</body>
</html>"""
            with open(path, "w", encoding="utf-8") as f:
                f.write(html_content)
        else:
            lines = []
            for ts, author, content, attachments in messages:
                lines.append(f"[{ts.isoformat()}] {author}: {content}\n")
                if attachments:
                    att_urls = " ".join(a.url for a in attachments)
                    lines.append(f"  📎 Attachments: {att_urls}\n")
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(lines)
    except Exception:
        logger.exception("Failed to write transcript file %s", path)
        raise

    return str(path)

# -------------------------
# Load config (used by cog)
# -------------------------
CONFIG = load_json(CONFIG_FILE)
PANEL_CHANNEL_ID = CONFIG.get("panel_channel_id", 0)
TICKET_CATEGORY_NAME = CONFIG.get("ticket_category_name", "Tickets")
STAFF_ROLES = CONFIG.get("staff_roles", ["Staff"])
TICKET_OPTIONS = CONFIG.get("ticket_options", [
    {"label": "General Support", "value": "general"},
    {"label": "Billing Support", "value": "billing"},
    {"label": "Staff Application", "value": "staff"}
])
LOG_CHANNEL_ID = CONFIG.get("log_channel_id", 0)

# -------------------------
# Views / UI
# -------------------------
class TicketCloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.primary, custom_id="ticket_claim_v1")
    async def claim_ticket(self, interaction: discord.Interaction, button: Button):
        """Allow staff to claim the ticket so other staff know who is handling it."""
        channel = interaction.channel
        guild = interaction.guild
        user = interaction.user
        tickets = load_json(TICKETS_FILE)

        cid = str(channel.id)
        if cid not in tickets:
            return await interaction.response.send_message("❌ This channel is not a registered ticket.", ephemeral=True)

        # Check staff permission by role name
        is_staff = any(r.name in STAFF_ROLES for r in user.roles)
        if not is_staff and not user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You don't have permission to claim tickets.", ephemeral=True)

        # Record claimer
        tickets[cid]["claimer_id"] = user.id
        save_json(TICKETS_FILE, tickets)

        # Disable claim button on the view and update message so it's clear
        for child in list(self.children):
            if getattr(child, 'custom_id', None) == 'ticket_claim_v1':
                child.disabled = True
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass

        await interaction.response.send_message(f"✅ {user.mention} has claimed this ticket.", ephemeral=False)

        # Send DM to ticket creator to notify them their ticket was claimed
        ticket_user_id = tickets[cid].get("user_id")
        if ticket_user_id:
            try:
                ticket_user = await guild.fetch_member(ticket_user_id)
                await ticket_user.send(f"📨 **Ticket Claimed!**\n\n{user.mention} from **{guild.name}** has claimed your ticket: {channel.name}\n\nThey will help you shortly! 🎯")
            except Exception:
                logger.exception("Failed to send DM to ticket creator %s", ticket_user_id)

    @discord.ui.button(label="Transcript", style=discord.ButtonStyle.secondary, custom_id="ticket_transcript_v1")
    async def transcript_ticket(self, interaction: discord.Interaction, button: Button):
        """Generate a transcript and post to the configured log channel (if any)."""
        channel = interaction.channel
        guild = interaction.guild
        user = interaction.user

        # permission check
        is_staff = any(r.name in STAFF_ROLES for r in user.roles)
        if not is_staff and not user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You don't have permission to create transcripts.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        try:
            path = await generate_transcript(channel, format="html")
        except Exception:
            logger.exception("Transcript generation failed for channel %s", getattr(channel, 'id', None))
            return await interaction.followup.send("❌ Failed to generate transcript.", ephemeral=True)

        # Send to configured log channel if available
        if LOG_CHANNEL_ID:
            log_chan = guild.get_channel(LOG_CHANNEL_ID)
            if log_chan:
                try:
                    await log_chan.send(content=f"Transcript for {channel.name} (closed by {user.mention}):", file=discord.File(path))
                except Exception:
                    logger.exception("Failed to send transcript to log channel %s", LOG_CHANNEL_ID)
                    await interaction.followup.send("⚠️ Transcript generated but failed to post to log channel.", ephemeral=True)
                else:
                    await interaction.followup.send("✅ Transcript generated and posted to log channel.", ephemeral=True)
                    return

        # If no log channel, offer the file to the caller (ephemeral not possible for files), so send in channel but mention staff
        try:
            await channel.send(file=discord.File(path), content=f"Transcript generated by {user.mention}")
            await interaction.followup.send("✅ Transcript attached in this channel.", ephemeral=True)
        except Exception:
            logger.exception("Failed to deliver transcript file for channel %s", getattr(channel, 'id', None))
            await interaction.followup.send("❌ Transcript generated but failed to deliver.", ephemeral=True)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="ticket_close_btn_v1")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        channel = interaction.channel
        tickets = load_json(TICKETS_FILE)

        # tickets keyed by channel_id (string)
        cid = str(channel.id)
        if cid not in tickets:
            return await interaction.response.send_message("❌ This channel is not a registered ticket.", ephemeral=True)

        # Acknowledge interaction quickly
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            # If the interaction has already been acknowledged, ignore
            pass

        # Remove record first
        info = tickets.pop(cid, None)
        save_json(TICKETS_FILE, tickets)

        # Auto-generate transcript in HTML format before deletion
        try:
            await generate_transcript(channel, format="html")
        except Exception:
            logger.exception("Failed to auto-generate transcript before closing channel %s", getattr(channel, 'id', None))

        # Remember the category so we can remove it if empty after deletion
        category = channel.category

        # Send fancy countdown embed with animation
        countdown_embed = discord.Embed(
            title="🔒 Ticket Closing",
            description="This ticket will be deleted in...",
            color=discord.Color.red()
        )
        countdown_embed.add_field(name="Status", value="⏳ Countdown started", inline=False)
        countdown_msg = await channel.send(embed=countdown_embed)

        # Animated countdown: 5, 4, 3, 2, 1 with visual effects
        for remaining in [5, 4, 3, 2, 1]:
            countdown_embed.title = f"🔒 Ticket Closing — {remaining}"
            countdown_embed.description = "This ticket will be deleted in..."
            
            # Visual feedback based on remaining time
            if remaining > 3:
                countdown_embed.color = discord.Color.orange()
                status_text = "⏳ Closing..."
            elif remaining > 1:
                countdown_embed.color = discord.Color.red()
                status_text = "⚠️ Final moments..."
            else:
                countdown_embed.color = discord.Color.dark_red()
                status_text = "🚨 Deleting NOW!"
            
            countdown_embed.set_field_at(0, name="Status", value=status_text, inline=False)
            countdown_embed.add_field(name="Time Remaining", value=f"**{remaining}** second{'s' if remaining != 1 else ''}", inline=True)
            
            try:
                await countdown_msg.edit(embed=countdown_embed)
            except Exception:
                pass
            await asyncio.sleep(1)
        
        # Final deletion message
        countdown_embed.title = "✅ Deleted"
        countdown_embed.color = discord.Color.green()
        countdown_embed.description = "This ticket channel has been closed and deleted."
        try:
            await countdown_msg.edit(embed=countdown_embed)
        except Exception:
            pass

        try:
            await channel.delete()
        except Exception:
            logger.exception("Failed to delete ticket channel %s", getattr(channel, 'id', None))
        else:
            # If the category matches our ticket category and is empty now, delete it to keep the server tidy
            try:
                if category and category.name and category.name.lower() == TICKET_CATEGORY_NAME.lower():
                    if len(category.channels) == 0:
                        await category.delete()
                        logger.info("Deleted empty ticket category %s", category.name)
            except Exception:
                logger.exception("Failed to delete empty category %s", getattr(category, 'id', None))


# Note: dropdown/select removed - using buttons only for a cleaner UX


class TicketTypeButton(Button):
    def __init__(self, label: str, value: str, style=discord.ButtonStyle.secondary, emoji: str | None = None):
        super().__init__(label=label, style=style, custom_id=f"ticket_btn_{value}", emoji=emoji)
        self.value = value

    async def callback(self, interaction: discord.Interaction):
        await open_ticket(interaction, self.value)


async def open_ticket(interaction: discord.Interaction, ticket_type: str):
    """Shared helper to open a ticket for an interaction and ticket_type."""
    user = interaction.user
    guild = interaction.guild
    if guild is None:
        return await interaction.response.send_message("This command must be used in a server.", ephemeral=True)

    tickets = load_json(TICKETS_FILE)
    blacklist = load_json(BLACKLIST_FILE)

    # Blacklist check
    if str(user.id) in blacklist:
        reason = blacklist[str(user.id)].get("reason", "No reason provided")
        return await interaction.response.send_message(f"⛔ You are blacklisted from creating tickets.\nReason: {reason}", ephemeral=True)

    # Single ticket per user check
    existing_channel = None
    orphaned = []
    for cid, info in list(tickets.items()):
        if info.get("user_id") == user.id:
            ch = guild.get_channel(int(cid))
            if ch:
                existing_channel = ch
                break
            else:
                orphaned.append(cid)

    if orphaned:
        for cid in orphaned:
            tickets.pop(cid, None)
        save_json(TICKETS_FILE, tickets)

    if existing_channel:
        return await interaction.response.send_message(f"❗ You already have an open ticket: {existing_channel.mention}", ephemeral=True)

    # Get/create category
    category = next((c for c in guild.categories if c.name.lower() == TICKET_CATEGORY_NAME.lower()), None)
    if category is None:
        try:
            category = await guild.create_category(TICKET_CATEGORY_NAME)
        except Exception:
            logger.exception("Failed to create category '%s'", TICKET_CATEGORY_NAME)
            return await interaction.response.send_message("❌ Failed to create ticket category. Contact an admin.", ephemeral=True)

    # Short, premium-looking channel name: ticket-{type}-{xxxx}
    short_suffix = datetime.utcnow().strftime("%H%M%S") + str(user.id)[-3:]
    short_type = ''.join(ch for ch in ticket_type if ch.isalnum())[:10]
    channel_name = f"ticket-{short_type}-{short_suffix}"[:90]

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True),
        guild.me: discord.PermissionOverwrite(view_channel=True)
    }

    try:
        for role_name in STAFF_ROLES:
            role = discord.utils.find(lambda r: r.name == role_name, guild.roles)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True)
    except Exception:
        logger.exception("Error while applying staff role overwrites")

    try:
        channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)
    except Exception:
        logger.exception("Failed to create ticket channel in guild %s", getattr(guild, 'id', None))
        return await interaction.response.send_message("❌ Failed to create ticket channel. Contact an admin.", ephemeral=True)

    tickets[str(channel.id)] = {
        "user_id": user.id,
        "type": ticket_type,
        "created_at": datetime.utcnow().isoformat()
    }
    save_json(TICKETS_FILE, tickets)

    # Respond to the user first
    try:
        await interaction.response.send_message(f"✅ Your ticket has been created: {channel.mention}", ephemeral=True)
    except Exception:
        try:
            await interaction.followup.send(f"✅ Your ticket has been created: {channel.mention}", ephemeral=True)
        except Exception:
            logger.exception("Failed to send ticket creation confirmation to user %s", user.id)

    # Send a premium embed inside the ticket with a close button
    try:
        embed = discord.Embed(
            title=f"🎫 Ticket — {ticket_type.title()}",
            description=f"Hello {user.mention}, a member of our team will be with you shortly. Use the buttons below to manage this ticket.",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"{guild.name} Support Team", icon_url=guild.icon.url if guild.icon else None)
        embed.add_field(name="User", value=user.mention, inline=True)
        embed.add_field(name="Type", value=ticket_type.title(), inline=True)
        await channel.send(embed=embed, view=TicketCloseView())
    except Exception:
        logger.exception("Failed to send ticket opening message in channel %s", getattr(channel, 'id', None))


class TicketPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
        # Quick buttons for top options
        for opt in TICKET_OPTIONS[:3]:
            emoji = None
            if opt.get("value") == "report":
                emoji = "🚨"
            elif opt.get("value") == "billing":
                emoji = "💳"
            elif opt.get("value") == "general":
                emoji = "❓"
            self.add_item(TicketTypeButton(label=opt.get("label"), value=opt.get("value"), emoji=emoji))

        # (Select removed) Buttons-only UI for a cleaner experience


# -------------------------
# Cog with commands
# -------------------------
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Admin: post the ticket panel (in current channel or configured panel channel)
    @commands.command(name="ticketpanel")
    @commands.has_permissions(administrator=True)
    async def ticketpanel(self, ctx):
        embed = discord.Embed(
            title="🎫 Create a Ticket",
            description="Select a reason below to open a ticket.",
            color=discord.Color.blue()
        )
        view = TicketPanelView()

        if PANEL_CHANNEL_ID and PANEL_CHANNEL_ID != 0:
            panel_chan = ctx.guild.get_channel(PANEL_CHANNEL_ID)
            if panel_chan:
                await panel_chan.send(embed=embed, view=view)
                return await ctx.send(f"✅ Ticket panel posted in {panel_chan.mention}")
            # if config channel id invalid, fall back to current channel

        await ctx.send(embed=embed, view=view)

    # STAFF: force-close ticket by command
    @commands.command(name="closeticket")
    @commands.has_any_role(*STAFF_ROLES)
    async def closeticket(self, ctx):
        tickets = load_json(TICKETS_FILE)
        cid = str(ctx.channel.id)
        if cid not in tickets:
            return await ctx.send("❌ This is not a registered ticket channel.")
        # Remove record
        tickets.pop(cid, None)
        save_json(TICKETS_FILE, tickets)
        await ctx.send("Ticket closed by staff. Deleting channel...")
        await ctx.channel.delete()

    # INFO: show ticket info
    @commands.command(name="ticketinfo")
    async def ticketinfo(self, ctx):
        tickets = load_json(TICKETS_FILE)
        cid = str(ctx.channel.id)
        if cid not in tickets:
            return await ctx.send("This is not a ticket channel.")
        info = tickets[cid]
        user = ctx.guild.get_member(info["user_id"])
        embed = discord.Embed(title="Ticket Info", color=discord.Color.green())
        embed.add_field(name="User", value=user.mention if user else f"<@{info['user_id']}>")
        embed.add_field(name="Type", value=info["type"])
        embed.add_field(name="Created At", value=info.get("created_at", "unknown"))
        await ctx.send(embed=embed)

    # BLACKLIST: add user to blacklist
    @commands.command(name="blacklist")
    @commands.has_permissions(administrator=True)
    async def blacklist(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        bl = load_json(BLACKLIST_FILE)
        bl[str(member.id)] = {"by": ctx.author.id, "reason": reason, "time": datetime.utcnow().isoformat()}
        save_json(BLACKLIST_FILE, bl)
        await ctx.send(f"✅ {member.mention} has been blacklisted from creating tickets.\nReason: {reason}")

    # UNBLACKLIST
    @commands.command(name="unblacklist")
    @commands.has_permissions(administrator=True)
    async def unblacklist(self, ctx, member: discord.Member):
        bl = load_json(BLACKLIST_FILE)
        if str(member.id) in bl:
            bl.pop(str(member.id))
            save_json(BLACKLIST_FILE, bl)
            return await ctx.send(f"✅ {member.mention} has been removed from the blacklist.")
        await ctx.send("That user is not blacklisted.")

    # LIST BLACKLIST
    @commands.command(name="blacklistlist")
    @commands.has_permissions(administrator=True)
    async def blacklistlist(self, ctx):
        bl = load_json(BLACKLIST_FILE)
        if not bl:
            return await ctx.send("Blacklist is empty.")
        lines = []
        for uid, info in bl.items():
            lines.append(f"<@{uid}> — {info.get('reason','')}")
        # send in chunks if large
        await ctx.send("\n".join(lines))

    # Admin utility: reload views (if you change code/config)
    @commands.command(name="reloadviews")
    @commands.has_permissions(administrator=True)
    async def reloadviews(self, ctx):
        self.bot.add_view(TicketPanelView())
        self.bot.add_view(TicketCloseView())
        await ctx.send("✅ Views reloaded.")

    # --- Slash Commands ---

    @discord.app_commands.command(name="ticket_panel", description="Post the ticket creation panel to this channel")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def ticket_panel_slash(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎫 Create a Ticket",
            description="Click a button below to open a support ticket.",
            color=discord.Color.blurple()
        )
        view = TicketPanelView()
        await interaction.response.send_message(embed=embed, view=view)
        await interaction.followup.send("✅ Ticket panel posted!", ephemeral=True)

    @discord.app_commands.command(name="ticket_info", description="Show info about the current ticket")
    async def ticket_info_slash(self, interaction: discord.Interaction):
        tickets = load_json(TICKETS_FILE)
        cid = str(interaction.channel_id)
        if cid not in tickets:
            return await interaction.response.send_message("❌ This is not a ticket channel.", ephemeral=True)
        
        info = tickets[cid]
        user = interaction.guild.get_member(info["user_id"])
        claimer_id = info.get("claimer_id")
        claimer = interaction.guild.get_member(claimer_id) if claimer_id else None
        
        embed = discord.Embed(title="🎫 Ticket Info", color=discord.Color.green())
        embed.add_field(name="User", value=user.mention if user else f"<@{info['user_id']}>", inline=True)
        embed.add_field(name="Type", value=info["type"], inline=True)
        embed.add_field(name="Created", value=info.get("created_at", "unknown"), inline=False)
        if claimer:
            embed.add_field(name="Claimed by", value=claimer.mention, inline=True)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="blacklist_user", description="Blacklist a user from creating tickets")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def blacklist_user_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        bl = load_json(BLACKLIST_FILE)
        bl[str(member.id)] = {"by": interaction.user.id, "reason": reason, "time": datetime.utcnow().isoformat()}
        save_json(BLACKLIST_FILE, bl)
        embed = discord.Embed(title="✅ User Blacklisted", color=discord.Color.red())
        embed.add_field(name="User", value=member.mention)
        embed.add_field(name="Reason", value=reason)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.app_commands.command(name="unblacklist_user", description="Remove a user from the blacklist")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def unblacklist_user_slash(self, interaction: discord.Interaction, member: discord.Member):
        bl = load_json(BLACKLIST_FILE)
        if str(member.id) in bl:
            bl.pop(str(member.id))
            save_json(BLACKLIST_FILE, bl)
            await interaction.response.send_message(f"✅ {member.mention} has been removed from the blacklist.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {member.mention} is not blacklisted.", ephemeral=True)

    @discord.app_commands.command(name="blacklist_view", description="View the current blacklist")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def blacklist_view_slash(self, interaction: discord.Interaction):
        bl = load_json(BLACKLIST_FILE)
        if not bl:
            return await interaction.response.send_message("✅ Blacklist is empty.", ephemeral=True)
        
        embed = discord.Embed(title="🚫 Blacklist", color=discord.Color.red())
        for uid, info in list(bl.items())[:25]:
            embed.add_field(name=f"<@{uid}>", value=f"Reason: {info.get('reason', 'N/A')}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    cog = Tickets(bot)
    await bot.add_cog(cog)

    # Register persistent views so buttons/select keep working after restart
    bot.add_view(TicketPanelView())
    bot.add_view(TicketCloseView())
    
    # Sync slash commands
    try:
        await bot.tree.sync()
        logger.info("Slash commands synced successfully")
    except Exception:
        logger.exception("Failed to sync slash commands")
