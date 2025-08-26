# 📹 Bober UA – Simple Telegram bot (Aiogram 3) for downloading videos from YouTube/Instagram/TikTok

[Українською](README.uk.md)

### 📌 Requirements
- Python 3.10+

### 🛠️ Setup
1. Copy `.env` from `.env.dist` and add your token:
```
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
```

2. Install dependencies (recommended in a virtual environment):
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. ▶️ Run the bot:
```
python bot.py
```

### 🐳 Setup with Docker
1. Create `.env` file with your token:
```
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
```
2. Build and start:
```
docker compose up -d --build
```
3. View logs:
```
docker compose logs -f
```
4. Update to latest code and rebuild:
```
git pull
docker compose up -d --build
```

### 📥 Usage
Send the bot a TikTok or Instagram Reels link. The bot will try to delete your link message and send the actual video. The caption will include your Telegram username (or your name if the username is missing)

### 👥 Use in groups
1. In BotFather, disable privacy mode for the bot:
   - Send `/setprivacy` → choose your bot → select `Disable`.
2. Add the bot to your group as an administrator to grant permissions to delete messages and send messages