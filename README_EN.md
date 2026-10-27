# MaiBot Discord Adapter Plugin

[![MaiBot Plugin SDK](https://img.shields.io/badge/MaiBot%20SDK-v2.0+-blue.svg)](https://docs.maibot.chat)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](https://www.python.org/)

Modern, reliable, and lightweight **Discord Duplex Message Gateway Adapter** for [MaiBot](https://github.com/Mai-with-u/MaiBot). Connect your MaiBot directly to Discord with official Bot APIs—no containers, no phone emulation, and zero risk control issues.

---

## ✨ Features

- **Official Native Integration**: Powered by Discord's official Gateway and REST APIs. Permanent online status with zero bans or risk controls.
- **Duplex MessageGateway**: Implements the official `@MessageGateway` SDK 2.x standard for seamless bidirectional routing.
- **Full Conversation Support**:
  - Direct Messages (DMs).
  - Server Guild Channels & Threads (with optional @mention requirement).
- **Rich Media & Interaction**:
  - Text, attachments, images, stickers, and reply quotes.
  - Automatic message splitting for Discord's 2000-character limit.
  - Realistic typing indicators (`typing...`).
- **Granular Permissions & Filtering**: Channel and user whitelists and blacklists.
- **Extremely Lightweight**: Built on `discord.py` async framework, consuming only tens of megabytes of memory.

---

## 🚀 Quick Start: Discord Bot Setup

1. **Create an Application & Get Token**:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications).
   - Click **New Application** and name your bot.
   - Navigate to the **Bot** tab, click **Reset Token**, and copy the generated Bot Token.
2. **Enable Privileged Gateway Intents**:
   - In the Bot tab, scroll down to **Privileged Gateway Intents**.
   - Enable:
     - `Presence Intent`
     - `Server Members Intent`
     - `Message Content Intent` (required to read messages).
3. **Invite the Bot**:
   - Navigate to **OAuth2** -> **URL Generator**.
   - Check `bot` under **Scopes**.
   - Check `Send Messages`, `Read Message History`, `Attach Files`, `Embed Links`, `View Channels` under **Bot Permissions**.
   - Copy the generated URL and open it in your browser to invite the bot to your server.

---

## ⚙️ Configuration

In WebUI or `config.toml`:

```toml
[WiseXin.discord-adapter]
token = "YOUR_DISCORD_BOT_TOKEN"
allow_dm = true
require_mention_in_guild = false
send_typing_indicator = true
channel_whitelist = []
channel_blacklist = []
user_blacklist = []
```

---

## 📄 License

This project is open-sourced under the [MIT License](LICENSE).
