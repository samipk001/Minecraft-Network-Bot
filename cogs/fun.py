import discord
from discord.ext import commands
from discord.ui import Button, View
import random

class RockPaperScissors(View):
    def __init__(self, author):
        super().__init__()
        self.author = author
        self.result = None

    @discord.ui.button(label="🪨 Rock", style=discord.ButtonStyle.primary)
    async def rock(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.author:
            return await interaction.response.send_message("❌ This is not your game.", ephemeral=True)
        self.result = "rock"
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="📄 Paper", style=discord.ButtonStyle.primary)
    async def paper(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.author:
            return await interaction.response.send_message("❌ This is not your game.", ephemeral=True)
        self.result = "paper"
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="✂️ Scissors", style=discord.ButtonStyle.primary)
    async def scissors(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.author:
            return await interaction.response.send_message("❌ This is not your game.", ephemeral=True)
        self.result = "scissors"
        self.stop()
        await interaction.response.defer()

class Fun(commands.Cog):
    """Fun commands and games."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="rps")
    async def rock_paper_scissors(self, ctx):
        """🎮 Play rock, paper, scissors against the bot."""
        embed = discord.Embed(title="🎮 Rock, Paper, Scissors", description="Make your choice!", color=discord.Color.blurple())
        view = RockPaperScissors(ctx.author)
        
        await ctx.send(embed=embed, view=view)
        await view.wait()

        if not view.result:
            return

        bot_choice = random.choice(["rock", "paper", "scissors"])
        user_choice = view.result

        # Determine winner
        if user_choice == bot_choice:
            result = "🤝 It's a tie!"
            color = discord.Color.yellow()
        elif (user_choice == "rock" and bot_choice == "scissors") or \
             (user_choice == "paper" and bot_choice == "rock") or \
             (user_choice == "scissors" and bot_choice == "paper"):
            result = "🎉 You won!"
            color = discord.Color.green()
        else:
            result = "😢 You lost!"
            color = discord.Color.red()

        embed = discord.Embed(title=result, color=color)
        embed.add_field(name="Your Choice", value=user_choice.capitalize(), inline=True)
        embed.add_field(name="Bot's Choice", value=bot_choice.capitalize(), inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="8ball")
    async def magic_8ball(self, ctx, *, question: str = ""):
        """🔮 Ask the magic 8 ball a question."""
        if not question:
            return await ctx.send("❌ Please ask a question!")

        responses = [
            "✅ Yes, definitely",
            "✅ Absolutely",
            "✅ Without a doubt",
            "🤔 Ask again later",
            "🤔 Cannot predict now",
            "🤔 Maybe",
            "❌ No way",
            "❌ Don't count on it",
            "❌ Definitely not",
            "❓ Signs point to yes",
            "❓ The stars say maybe"
        ]

        answer = random.choice(responses)
        
        embed = discord.Embed(title="🔮 Magic 8 Ball", color=discord.Color.purple())
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=answer, inline=False)
        embed.set_footer(text=f"Asked by {ctx.author.name}")
        
        await ctx.send(embed=embed)

    @commands.command(name="coinflip")
    async def coinflip(self, ctx):
        """🪙 Flip a coin."""
        result = random.choice(["Heads", "Tails"])
        emoji = "🔴" if result == "Heads" else "⚪"
        
        embed = discord.Embed(title=f"{emoji} Coin Flip", color=discord.Color.gold())
        embed.add_field(name="Result", value=f"**{result}**", inline=False)
        embed.set_footer(text=f"Flipped by {ctx.author.name}")
        
        await ctx.send(embed=embed)

    @commands.command(name="roll")
    async def roll_dice(self, ctx, sides: int = 6):
        """🎲 Roll a die."""
        if sides < 2:
            return await ctx.send("❌ Dice must have at least 2 sides.")
        if sides > 1000:
            return await ctx.send("❌ Maximum 1000 sides.")

        result = random.randint(1, sides)
        
        embed = discord.Embed(title=f"🎲 Dice Roll (d{sides})", color=discord.Color.gold())
        embed.add_field(name="Result", value=f"**{result}**", inline=False)
        embed.set_footer(text=f"Rolled by {ctx.author.name}")
        
        await ctx.send(embed=embed)

    @commands.command(name="giveaway")
    @commands.has_permissions(administrator=True)
    async def giveaway(self, ctx, duration: int, *, prize: str):
        """🎁 Start a giveaway."""
        if duration < 1 or duration > 3600:
            return await ctx.send("❌ Duration must be between 1 and 3600 seconds.")

        embed = discord.Embed(title="🎁 GIVEAWAY", color=discord.Color.gold())
        embed.add_field(name="Prize", value=prize, inline=False)
        embed.add_field(name="Duration", value=f"{duration} seconds", inline=False)
        embed.set_footer(text="React with 🎉 to enter!")
        
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("🎉")

        await __import__("asyncio").sleep(duration)

        # Get all reactions
        reaction = discord.utils.get(msg.reactions, emoji="🎉")
        if reaction and reaction.count > 1:
            participants = await reaction.users().flatten()
            participants = [u for u in participants if u != self.bot.user]

            if participants:
                winner = random.choice(participants)
                embed.title = "🎉 GIVEAWAY WINNER"
                embed.add_field(name="Winner", value=winner.mention, inline=False)
                await ctx.send(embed=embed)
                
                try:
                    await winner.send(f"🎉 You won the giveaway!\n**Prize:** {prize}")
                except:
                    pass
            else:
                await ctx.send("❌ No valid participants.")
        else:
            await ctx.send("❌ Not enough participants for the giveaway.")

    @commands.command(name="poll")
    async def poll(self, ctx, *, question: str):
        """📊 Create a quick poll."""
        embed = discord.Embed(title="📊 Poll", description=question, color=discord.Color.blurple())
        embed.set_footer(text=f"Poll by {ctx.author.name}")
        
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await msg.add_reaction("🤷")

    @commands.command(name="trivia")
    async def trivia(self, ctx):
        """🧠 Answer a trivia question."""
        questions = [
            {
                "q": "What is the capital of France?",
                "options": ["Paris", "London", "Berlin", "Rome"],
                "answer": "Paris"
            },
            {
                "q": "What is 2 + 2?",
                "options": ["3", "4", "5", "6"],
                "answer": "4"
            },
            {
                "q": "What is the largest planet in our solar system?",
                "options": ["Saturn", "Mars", "Jupiter", "Neptune"],
                "answer": "Jupiter"
            },
            {
                "q": "Who wrote 'Hamlet'?",
                "options": ["Charles Dickens", "William Shakespeare", "Jane Austen", "Mark Twain"],
                "answer": "William Shakespeare"
            },
            {
                "q": "What is the smallest country in the world?",
                "options": ["Monaco", "Liechtenstein", "Vatican City", "San Marino"],
                "answer": "Vatican City"
            }
        ]

        q = random.choice(questions)
        options_str = "\n".join([f"{chr(65+i)}. {opt}" for i, opt in enumerate(q["options"])])

        embed = discord.Embed(title="🧠 Trivia Question", color=discord.Color.blurple())
        embed.add_field(name=q["q"], value=options_str, inline=False)
        embed.set_footer(text="React with the corresponding letter to answer")

        msg = await ctx.send(embed=embed)
        for i in range(len(q["options"])):
            await msg.add_reaction(chr(127462 + i))  # Regional indicator emojis

    @commands.command(name="joke")
    async def joke(self, ctx):
        """😄 Tell a joke."""
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "What do you call a fake noodle? An impasta!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
            "What's the best thing about Switzerland? I don't know, but their flag is a big plus.",
            "Did you hear about the claustrophobic astronaut? He just needed a little space!",
            "Why don't eggs tell jokes? They'd crack each other up!",
            "What do you call a boomerang that doesn't come back? A stick!",
            "Why did the coffee file a police report? It got mugged!"
        ]

        embed = discord.Embed(title="😄 Random Joke", color=discord.Color.gold())
        embed.add_field(name="Joke", value=random.choice(jokes), inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))
