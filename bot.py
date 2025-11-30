import os
import json
from pathlib import Path
from dotenv import load_dotenv
import logging
import discord
from discord.ext import commands

# basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ticketbot")

# Load .env (optional)
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# Load config
CONFIG_PATH = Path(__file__).parent / "config.json"
if not CONFIG_PATH.exists():
    logger.error("Missing config.json in project root.")
    raise RuntimeError("Missing config.json")
with open(CONFIG_PATH) as f:
    config = json.load(f)

# Token may come from environment or config.json (config takes second priority)
TOKEN = os.getenv("TOKEN") or config.get("token")
if not TOKEN:
    logger.error("Bot token not found. Set TOKEN in .env or add \"token\" to config.json")
    raise RuntimeError("TOKEN missing; add it to .env or config.json")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=config.get("prefix", "!"), intents=intents)


@bot.event
async def setup_hook():
    # Load cogs
    try:
        await bot.load_extension("cogs.tickets")
        logger.info("Loaded cog: cogs.tickets")
    except Exception:
        logger.exception("Failed to load cog cogs.tickets")

    logger.info("Setup hook complete.")


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")


if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception:
        logger.exception("Bot terminated with an exception")
