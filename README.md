# Discord to Discord Summary Bot

This bot automatically summarizes content from Discord channels and posts the summaries to a designated Discord channel using AI. It supports monitoring channels on one server and posting summaries to a different server.

## Features

- Monitors specified Discord channels for messages using your personal token
- Generates daily summaries using AI (DeepSeek or Claude)
- Posts formatted summaries to a Discord channel (can be on a different server)
- Configurable scheduling
- Modular architecture for easy maintenance

## Cross-Server Functionality

The bot supports a workflow where:

1. You monitor channels on Server A (using your personal user token)
2. The bot posts summaries to a channel on Server B (using a bot token)

To set this up correctly:

1. Make sure your personal token has access to read the source channels
2. Ensure your bot is invited to the destination server with proper permissions
3. Configure your `.env` file with the correct channel IDs

### Bot Permissions Required

When inviting your bot to the destination server, it needs these permissions:

- Read Messages/View Channels
- Send Messages
- Embed Links

## Setup

### Prerequisites

- Python 3.8 or higher
- Your Discord user token (for reading messages)
- Discord bot token (for posting summaries)
- AI API key (DeepSeek or Anthropic)

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure the `.env` file with your credentials (see `.env` section below)

### Finding Your Discord User Token

⚠️ **IMPORTANT**: Never share your user token with anyone or post it publicly. The token provides full access to your Discord account.

To find your Discord user token:

1. Open Discord in your browser (or open the developer tools in the desktop app with Ctrl+Shift+I)
2. Press F12 to open DevTools
3. Go to the Network tab
4. Look for requests to discord.com
5. Find your token in the request headers under "Authorization"

### Finding Server and Channel IDs

Use the included utility to find server and channel IDs:

```bash
python -m utils.discord_explorer
```

Follow the prompts to select a server and view all available text channels.

### Creating a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a New Application
3. Go to the "Bot" tab and click "Add Bot"
4. Under the Token section, click "Copy" (this is your DISCORD_BOT_TOKEN)
5. Enable the "Message Content Intent" under Privileged Gateway Intents
6. Go to OAuth2 > URL Generator
   - Select "bot" scope
   - Select permissions: "Read Messages/View Channels", "Send Messages", "Embed Links"
7. Copy the generated URL and open it in your browser to invite the bot to your destination server

### Configuration

Create a `.env` file in the project root with the following properties:

```
# Discord credentials for reading messages (your personal token)
DISCORD_USER_TOKEN=your_user_token_here

# Discord server and channel configuration (source)
DISCORD_SOURCE_GUILD_ID=123456789012345678
# Leave empty to monitor all text channels in the guild,
# or specify comma-separated channel IDs:
DISCORD_SOURCE_CHANNEL_IDS=123456789012345678,234567890123456789

# Discord bot credentials for posting summaries (destination)
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_DESTINATION_CHANNEL_ID=345678901234567890

# LLM Provider (options: 'deepseek' or 'anthropic')
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here

# Time for daily summary (24-hour format)
SUMMARY_HOUR=23
SUMMARY_MINUTE=0
DAYS_TO_COLLECT=1

# Debug mode (true or false)
DEBUG=false
```

## Usage

Run the application:

```bash
python main.py
```

The bot will run according to your configured schedule, collecting messages from the specified Discord channels, summarizing them, and posting the summaries to your destination channel.

For a one-time run without scheduling:

```bash
python main.py --run-once
```

## Troubleshooting

Common issues:

1. **"Discord channel not found"**: Make sure the bot has been invited to the destination server and has permission to view and send messages in the destination channel.

2. **"Rate limit reached"**: The Discord API has rate limits. The bot includes rate limiting logic, but if you're monitoring many channels, you might need to adjust the code to add more delay between requests.

3. **"Error posting summary to Discord"**: Check that your bot token is correct and that the bot has the necessary permissions (Send Messages, Embed Links).

Check the `logs/discord_summary_bot.log` file for detailed logging information if you encounter issues.
