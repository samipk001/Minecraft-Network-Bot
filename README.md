# TicketBot

Simple Discord ticket bot using `discord.py` v2+ with GUI elements (buttons/selects).

Setup

1. Create a virtual environment (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Provide a bot token either in a `.env` file at the project root with:

```text
TOKEN=your_bot_token_here
```

Or add a `"token": "..."` field to `config.json` (less recommended).

4. Run the bot:

```bash
python bot.py
```

Notes

- Configure `config.json` to set `prefix`, `panel_channel_id`, `ticket_category_name`, and `staff_roles`.
- Use `!ticketpanel` (admin) in a channel to post the ticket creation panel.
