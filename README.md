# Discord to Discord Summary Bot

This bot automatically summarizes content from Discord channels and posts the summaries to a designated Discord channel using AI. It supports monitoring channels on one server and posting summaries to a different server.

## Features

- Monitors specified Discord channels for messages using your personal token
- Generates daily summaries using AI (DeepSeek or Claude)
- Posts formatted summaries to a Discord channel (can be on a different server)
- Configurable scheduling
- Modular architecture for easy maintenance
- Supports offline/dummy mode for testing and development

## Cross-Server Functionality

The bot supports a workflow where:

1. You monitor channels on Server A (using your personal user token)
2. The bot posts summaries to a channel on Server B (using a bot token)

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
python utils/discord_explorer.py
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

# It's recommended to provide both API keys for fallback functionality
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

### Standard Mode

Run the application in standard mode (scheduled):

```bash
python main.py
```

Or run it once without scheduling:

```bash
python main.py --run-once
```

### Dummy/Offline Mode

The bot provides a "dummy mode" that uses locally stored data instead of connecting to Discord for reading messages. This is useful for testing and development.

#### Extracting Data for Dummy Mode

Before using dummy mode, you need to extract Discord data:

```bash
python data_extractor.py [days]
```

Where `[days]` is the number of days of history to extract (default: 4).

This command will:

1. Connect to Discord using your user token
2. Extract messages from the configured channels
3. Save the data locally in the `extracted_data` directory

#### Running in Dummy Mode

Once data is extracted, run the bot in dummy mode:

```bash
python main_dummy.py
```

By default, this will:

1. Load messages from the local data
2. Generate summaries using the configured LLM provider
3. Post the summaries to your configured Discord channel

#### Testing Prompts

You can test different prompt configurations using the prompt tester:

```bash
python prompt_tester.py [--channel CHANNEL_ID] [--prompt PROMPT_TYPE] [--days DAYS]
```

Options:

- `--channel` or `-c`: Specify a channel ID to test (default: all channels)
- `--prompt` or `-p`: Specify a prompt type (e.g., 'defi', 'crypto')
- `--days` or `-d`: Number of days of history to use (default: 4)

This will save the generated summaries to the `prompt_test_results` directory.

## How It Works

1. The bot uses your Discord user token to collect messages from the configured channels
2. It extracts messages from the specified time period (default: last 24 hours)
3. The collected messages are sent to an AI service for summarization
   - The bot will automatically fall back to an alternative AI service if the primary one fails
4. The summary is posted to the configured Discord channel using a bot token

## Project Structure

- `main.py` - Main application entry point
- `main_dummy.py` - Entry point for dummy/offline mode
- `data_extractor.py` - Utility to extract Discord data for dummy mode
- `prompt_tester.py` - Utility to test different prompt configurations
- `config/` - Configuration management
- `clients/` - Discord reader and writer implementations
- `models/` - Data models for messages and summaries
- `services/` - Core services (message collection, summary generation, scheduling)
- `summarizers/` - AI summarization components
- `utils/` - Helper utilities

## Troubleshooting

Common issues:

1. **"Discord channel not found"**: Make sure the bot has been invited to the destination server and has permission to view and send messages in the destination channel.

2. **"Rate limit reached"**: The Discord API has rate limits. The bot includes rate limiting logic, but if you're monitoring many channels, you might need to adjust the code to add more delay between requests.

3. **"Error posting summary to Discord"**: Check that your bot token is correct and that the bot has the necessary permissions (Send Messages, Embed Links).

4. **Authentication issues**: If you change your Discord password, your user token will be invalidated. You'll need to obtain a new token.

5. **Dummy mode errors**: If experiencing SSL or connection errors in dummy mode, try adding a delay with `await asyncio.sleep(5)` before program exits to allow all operations to complete.

Check the `logs/discord_summary_bot.log` file for detailed logging information.

## Security Considerations

- Your Discord user token grants full access to your account. Never share it with anyone.
- Store the `.env` file securely and never commit it to version control.
- The bot respects rate limits to avoid getting your account flagged.
- This tool is for personal use only - mass scraping Discord data may violate Terms of Service.

## License

MIT
