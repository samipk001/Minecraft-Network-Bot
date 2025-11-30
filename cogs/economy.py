import discord
from discord.ext import commands
from pathlib import Path
from datetime import datetime
import json

BASE = Path(__file__).parent.parent
ECONOMY_FILE = BASE / "data" / "economy.json"
SHOP_FILE = BASE / "data" / "shop.json"

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

class Economy(commands.Cog):
    """Economy system for Minecraft network."""
    
    def __init__(self, bot):
        self.bot = bot
        ECONOMY_FILE.parent.mkdir(parents=True, exist_ok=True)

    def get_balance(self, user_id: int) -> int:
        """Get user's balance."""
        data = load_json(ECONOMY_FILE)
        return data.get(str(user_id), {}).get("balance", 0)

    def add_balance(self, user_id: int, amount: int, reason: str = ""):
        """Add coins to user."""
        data = load_json(ECONOMY_FILE)
        uid = str(user_id)
        if uid not in data:
            data[uid] = {"balance": 0, "transactions": []}
        data[uid]["balance"] = max(0, data[uid]["balance"] + amount)
        data[uid]["transactions"].append({
            "type": "add" if amount > 0 else "remove",
            "amount": abs(amount),
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })
        save_json(ECONOMY_FILE, data)

    @commands.command(name="balance")
    async def balance(self, ctx, member: discord.Member = None):
        """💰 Check player balance."""
        member = member or ctx.author
        bal = self.get_balance(member.id)
        
        embed = discord.Embed(title="💰 Balance", color=discord.Color.gold())
        embed.add_field(name="Player", value=member.mention)
        embed.add_field(name="Coins", value=f"**{bal:,}**", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="daily")
    async def daily(self, ctx):
        """🎁 Claim your daily reward."""
        data = load_json(ECONOMY_FILE)
        uid = str(ctx.author.id)
        
        if uid not in data:
            data[uid] = {"balance": 0, "transactions": [], "last_daily": None}
        
        last_daily = data[uid].get("last_daily")
        if last_daily:
            last_time = datetime.fromisoformat(last_daily)
            if (datetime.utcnow() - last_time).total_seconds() < 86400:
                return await ctx.send("❌ You already claimed your daily reward. Come back tomorrow!")

        reward = 500
        self.add_balance(ctx.author.id, reward, "Daily reward")
        data[uid]["last_daily"] = datetime.utcnow().isoformat()
        save_json(ECONOMY_FILE, data)

        embed = discord.Embed(title="🎁 Daily Reward", color=discord.Color.green())
        embed.add_field(name="Claimed", value=f"+{reward:,} coins")
        embed.set_footer(text="Come back tomorrow for your next reward!")
        
        await ctx.send(embed=embed)

    @commands.command(name="pay")
    async def pay(self, ctx, member: discord.Member, amount: int):
        """💸 Send coins to another player."""
        if amount <= 0:
            return await ctx.send("❌ Amount must be positive.")
        if member == ctx.author:
            return await ctx.send("❌ You can't pay yourself.")

        balance = self.get_balance(ctx.author.id)
        if balance < amount:
            return await ctx.send(f"❌ Insufficient balance. You have **{balance:,}** coins.")

        self.add_balance(ctx.author.id, -amount, f"Paid to {member}")
        self.add_balance(member.id, amount, f"Received from {ctx.author}")

        embed = discord.Embed(title="💸 Payment Sent", color=discord.Color.green())
        embed.add_field(name="From", value=ctx.author.mention)
        embed.add_field(name="To", value=member.mention)
        embed.add_field(name="Amount", value=f"**{amount:,}** coins", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="leaderboard")
    async def leaderboard(self, ctx):
        """🏆 Top players by coins."""
        data = load_json(ECONOMY_FILE)
        sorted_users = sorted(
            data.items(),
            key=lambda x: x[1].get("balance", 0),
            reverse=True
        )[:10]

        embed = discord.Embed(title="🏆 Economy Leaderboard", color=discord.Color.gold())
        for rank, (uid, info) in enumerate(sorted_users, 1):
            member = ctx.guild.get_member(int(uid))
            name = member.mention if member else f"<@{uid}>"
            balance = info.get("balance", 0)
            emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."
            embed.add_field(name=f"{emoji} {name}", value=f"**{balance:,}**", inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="shop")
    async def shop(self, ctx):
        """🛍️ View the shop."""
        shop_data = load_json(SHOP_FILE)
        if not shop_data:
            return await ctx.send("❌ Shop is empty.")

        embed = discord.Embed(title="🛍️ Shop", color=discord.Color.blurple())
        for item_id, item in shop_data.items():
            embed.add_field(name=f"{item['name']} (ID: {item_id})", value=f"**Cost:** {item['price']:,} coins", inline=False)

        embed.set_footer(text="Use /buy <item_id> to purchase")
        await ctx.send(embed=embed)

    @commands.command(name="buy")
    async def buy(self, ctx, item_id: str):
        """🛒 Buy an item from the shop."""
        shop_data = load_json(SHOP_FILE)
        if item_id not in shop_data:
            return await ctx.send("❌ Item not found.")

        item = shop_data[item_id]
        balance = self.get_balance(ctx.author.id)
        
        if balance < item["price"]:
            return await ctx.send(f"❌ Insufficient balance. Cost: **{item['price']:,}** coins")

        self.add_balance(ctx.author.id, -item["price"], f"Bought {item['name']}")

        embed = discord.Embed(title="✅ Purchase Successful", color=discord.Color.green())
        embed.add_field(name="Item", value=item["name"])
        embed.add_field(name="Cost", value=f"-{item['price']:,} coins")
        
        await ctx.send(embed=embed)
        try:
            await ctx.author.send(f"🎉 You purchased **{item['name']}** for **{item['price']:,}** coins!")
        except:
            pass

async def setup(bot):
    await bot.add_cog(Economy(bot))
