# GitHub Push Instructions

## Summary
Your local repo is ready to push. Follow these steps to create a **private** GitHub repository:

### Step 1: Create a Public Repository on GitHub
1. Go to [github.com/new](https://github.com/new)
2. Enter repository name: `ticketbot` (or your preferred name)
3. Set to **Public** (everyone can see the code)
4. **Do NOT** initialize with README, .gitignore, or license (we already have these)
5. Click "Create repository"

### Step 2: Add Remote and Push
After creating the repo, GitHub will show commands. Run these in your terminal:

```bash
cd /home/linux-mint/Desktop/ticketbot
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ticketbot.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

### Step 3: Verify
- Go to your repo on GitHub
- Confirm it's **Public** (check Settings → Visibility)
- Verify `.env` and data files are NOT in the repo (only `.env.example` should be there)

### What's Included (Safe to Share)
- `bot.py` — Main bot code
- `cogs/tickets.py` — Ticket system
- `config.json` — Configuration template
- `requirements.txt` — Dependencies
- `README.md` — Documentation
- `.env.example` — Example environment variables
- `requirements.txt` — Python packages

### What's Excluded (Secrets Protected)
- `.env` — **NOT uploaded** (your actual token)
- `tickets.json` — **NOT uploaded** (user data)
- `blacklist.json` — **NOT uploaded** (user data)
- `transcripts/` — **NOT uploaded** (chat logs)
- `venv/` — **NOT uploaded** (virtual environment)
- `__pycache__/` — **NOT uploaded** (compiled files)

### Future Pushes
After the initial push, you can use:
```bash
git add .
git commit -m "Your commit message"
git push
```

### Cloning to Another Machine
If you want to use this on another machine:
1. Clone: `git clone https://github.com/YOUR_USERNAME/ticketbot.git`
2. Create virtual env: `python3 -m venv venv && source venv/bin/activate`
3. Install deps: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill in your token
5. Run: `python3 bot.py`

---

**Current Git Status**
- ✅ Local repo initialized
- ✅ All safe files staged and committed
- ⏳ Ready to push (just add remote and push)
