# Discord Rules Bot (Resell Server Edition) 🌍

This Discord bot is specifically tailored for **resell servers**. It allows users to read the server safety and resell rules in multiple languages (**English, French, Spanish, German**) using an interactive dropdown selection menu.

## Features
- **Resell-specific rules**: Covers rules regarding legitimacy (no scams/counterfeits), posting formats (`#wts`, `#wtb`, `#wtt`), sniping prevention, and staff disclaimer.
- **Dropdown menu (`Select Menu`)** with flags for each country:
  - 🇬🇧 English
  - 🇫🇷 Français
  - 🇪🇸 Español
  - 🇩🇪 Deutsch
- **100% Private (Ephemeral replies)**: When a user selects their language, the rules are shown as an ephemeral message, meaning **only that user can see it** and no one else.
- **Persistent component**: The dropdown menu remains functional even if the bot restarts.
- **Clean admin command**: Installs the rules embed and deletes the initial command automatically.

## Prerequisites
- [Python 3.8+](https://www.python.org/)
- A Discord Bot Token from the [Discord Developer Portal](https://discord.com/developers/applications).

## Installation

1. Install the required package:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure your bot token in `bot.py` by replacing `"YOUR_TOKEN_HERE"` with your actual Discord token.

3. Make sure to enable the **Message Content Intent** under the "Bot" tab of your application page on the Discord Developer Portal.

## Running the Bot
Run the script:
```bash
python bot.py
```

## How to Use on Discord
1. Invite the bot to your server.
2. Go to your rules or terms channel.
3. Type the setup command (must have Administrator permissions):
   ```
   !setup_rules
   ```
4. The bot will send the Embed with the dropdown select menu, and delete your trigger message.
