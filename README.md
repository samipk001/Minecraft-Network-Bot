# Minecraft Network Discord Bot 🎮

An all-in-one, feature-rich Discord bot for Minecraft server networks. Includes moderation, economy, player profiles, support tickets, fun commands, and much more.

## Features

### 🛡️ Moderation System
- **Warn**: Issue warnings to users with automatic logging
- **Mute**: Temporary mutes (duration: 1h, 24h, 7d, etc.)
- **Kick**: Remove users from the server
- **Ban**: Ban users with appeal system
- **Case History**: View all moderation actions per user
- **Appeals**: Users can appeal bans with staff review

### 💰 Economy System
- **Balances**: Track player coins/currency
- **Daily Rewards**: Claim daily coins (500 per day)
- **Transfers**: Pay coins to other players
- **Shop**: Buy items with currency
- **Leaderboards**: Top spenders/earners rankings
- **Persistent Storage**: All data saved in JSON

### 👤 Player Profiles & Stats
- **Profile System**: View player stats at a glance
- **Track Stats**: Kills, deaths, playtime, level, achievements
- **K/D Ratio**: Calculate and display kill-death ratios
- **Leaderboards**: Top killers, most active players
- **Achievements**: Unlock and display achievements
- **Join Tracking**: First seen, last seen timestamps

### 🎫 Support Tickets
- **Button Panel**: Clean ticket creation interface
- **Claim System**: Staff can claim tickets
- **User Notifications**: Ping + DM notifications
- **Auto-Close**: Fancy 5-second countdown on ticket deletion
- **HTML Transcripts**: Beautiful transcripts of all conversations
- **Auto-Delete Categories**: Empty ticket categories auto-delete

### 🎮 Fun Commands
- **Games**: Rock-paper-scissors, dice rolling, coin flips
- **Utilities**: Magic 8-ball, trivia, jokes
- **Giveaways**: Automated giveaway system with reactions
- **Polls**: Quick yes/no/maybe polls
- **Interactive**: Reaction-based games and voting

### 🔧 Server Management
- **Server Info**: Detailed server statistics
- **User Info**: Member profiles and join dates
- **Member Count**: Human vs bot breakdown
- **Bot Latency**: Check API response times
- **Help System**: Built-in command documentation

## Setup

### Prerequisites
- Python 3.8+
- Discord bot token from [Discord Developer Portal](https://discord.com/developers/applications)

### Installation

1. **Clone & Setup Environment**:
```bash
cd /path/to/ticketbot
python3 -m venv .venv
source .venv/bin/activate
```

2. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure Bot Token**:
Create `.env` file (or copy from `.env.example`):
```text
TOKEN=your_discord_bot_token_here
```

4. **Configure Server Settings**:
Edit `config.json`:
```json
{
  "prefix": "!",
  "panel_channel_id": 0,
  "log_channel_id": 0,
  "ticket_category_name": "Tickets",
  "staff_roles": ["Staff", "Moderator"],
  "ticket_options": [
    { "label": "General Support", "value": "general" },
    { "label": "Report User", "value": "report" },
    { "label": "Bug Report", "value": "bug" }
  ]
}
```

5. **Run the Bot**:
```bash
python3 bot.py
```

## Commands

### 🛡️ Moderation
```
!warn <member> [reason]          — Warn a user
!mute <member> <duration> [reason] — Mute for 1h/24h/7d/etc
!kick <member> [reason]          — Kick from server
!ban <member> [reason]           — Ban from server
!cases <member>                  — View user's cases
!appeal                          — Check your appeal status
```

### 💰 Economy
```
!balance [member]                — View balance
!daily                           — Claim daily reward
!pay <member> <amount>           — Send coins
!leaderboard                     — Top earners
!shop                            — View shop items
!buy <item_id>                   — Purchase item
```

### 👤 Profiles
```
!profile [member]                — View player profile
!stats [member]                  — Detailed statistics
!leaderboard_kills               — Top killers
!leaderboard_playtime            — Most active players
!achievement <member> <name>     — Award achievement
```

### 🎮 Fun
```
!rps                             — Rock-paper-scissors game
!8ball <question>                — Magic 8-ball
!coinflip                        — Flip a coin
!roll [sides]                    — Roll dice (default d6)
!giveaway <duration> <prize>     — Start giveaway
!poll <question>                 — Create reaction poll
!trivia                          — Answer trivia question
!joke                            — Random joke
```

### 🔧 Utilities
```
!serverinfo                      — Server statistics
!userinfo [member]               — Member information
!membercount                     — Show member breakdown
!ping                            — Bot latency
!help_minecraft                  — Command reference
```

## Slash Commands

All commands are also available as slash commands (`/command`) for convenience:
- `/ticket_panel` — Post support ticket panel
- `/ticket_info` — Ticket details
- `/blacklist_user` — Manage blacklist
- `/blacklist_view` — View blacklist

## File Structure

```
ticketbot/
├── bot.py                 # Main bot entry point
├── config.json           # Server configuration
├── requirements.txt      # Python dependencies
├── .env                  # Bot token (don't commit!)
├── .env.example          # Token template
├── .gitignore            # Git ignore rules
├── README.md             # This file
└── cogs/
    ├── tickets.py        # Support ticket system
    ├── moderation.py     # Moderation & case management
    ├── economy.py        # Currency & shop system
    ├── profiles.py       # Player profiles & stats
    ├── fun.py            # Games & entertainment
    └── utilities.py      # Server info & utilities
└── data/ (auto-created)
    ├── moderation.json   # Mod cases & appeals
    ├── economy.json      # Player balances
    ├── profiles.json     # Player stats
    ├── shop.json         # Shop items
    ├── tickets.json      # Open tickets
    └── transcripts/      # Chat transcripts (HTML)
```

## Configuration

### `config.json` Settings

| Setting | Type | Description |
|---------|------|-------------|
| `prefix` | string | Command prefix (default: `!`) |
| `panel_channel_id` | number | Channel for auto-posting ticket panel |
| `log_channel_id` | number | Channel for moderation/transaction logs |
| `ticket_category_name` | string | Category for tickets |
| `staff_roles` | array | Roles that can moderate/claim tickets |
| `ticket_options` | array | Ticket type buttons |

## Features In Depth

### Ticket System
- **User Creates Ticket**: Clicks button in panel
- **User is Notified**: Gets ping + embed in ticket channel
- **Staff Claims**: Button marks ticket as claimed, user gets DM
- **Conversation**: Full conversation in dedicated channel
- **Transcripts**: HTML transcripts with styling (Discord theme)
- **Auto-Close**: 5-second countdown with animation
- **Auto-Cleanup**: Empty category deleted after last ticket closes

### Economy System
- **Persistent Storage**: All balances saved to JSON
- **Daily Rewards**: One per user per 24 hours
- **Leaderboards**: Top 10 ranked players
- **Shops**: Customizable items with prices
- **Transactions**: Full audit trail in JSON

### Moderation
- **Multi-Action**: Warn, mute, kick, ban in one system
- **Case Logging**: Every action tracked with ID
- **Appeals**: Users can appeal bans (staff review)
- **Duration Parsing**: Flexible mute durations (1h, 24h, 7d, etc)
- **Auto-Unmute**: Automatic role removal after mute expires

### Profiles
- **Real-Time Tracking**: Update stats with commands
- **Multi-Leaderboards**: Kills, playtime, level, etc
- **Achievements**: Award badges/achievements to players
- **Stats Display**: K/D ratio, total kills, total playtime

## Permissions Required

Ensure your bot has these permissions in Discord:
- ✅ Send Messages
- ✅ Embed Links
- ✅ Manage Messages (for reactions, polls)
- ✅ Manage Roles (for mutes)
- ✅ Kick Members
- ✅ Ban Members
- ✅ Manage Channels (for ticket channels)

## Data Storage

All data is stored in JSON files (no database required):
- **Moderation Cases**: `data/moderation.json`
- **Economy**: `data/economy.json`
- **Profiles**: `data/profiles.json`
- **Shop Items**: `data/shop.json`
- **Tickets**: `data/tickets.json`
- **Appeals**: `data/appeals.json`
- **Transcripts**: `data/transcripts/` (HTML files)

## Security

🔒 **Sensitive Data Protection**:
- `.env` file excluded via `.gitignore`
- Bot token never logged or exposed
- User data stored locally (no external APIs)
- Appeals & moderation actions logged

## Roadmap

Future features:
- [ ] Auction system for economy
- [ ] Mini-games with rewards
- [ ] Database integration (SQLite/PostgreSQL)
- [ ] Web dashboard
- [ ] API for external stats
- [ ] Custom commands builder
- [ ] Raid protection
- [ ] Auto-moderation (spam, profanity)

## Troubleshooting

**Bot won't start?**
- Check `.env` file has valid token
- Verify `config.json` is valid JSON
- Check Python 3.8+ installed

**Commands not working?**
- Verify bot has permissions
- Check bot role is above muted role
- Try `!help_minecraft` for command list

**Data lost?**
- Check `data/` folder exists
- Verify file permissions (readable/writable)
- Backups of JSON files in use

## Support & Contributing

For issues, questions, or features:
- Check existing GitHub issues
- Create new issue with details
- Submit pull requests for improvements

## License

This project is open-source and available for modification and distribution.

---

**Built with** ❤️ **using discord.py v2+**
