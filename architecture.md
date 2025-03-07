# Discord to Discord Summary Bot - Project Architecture

```
discord_summary_bot/
├── config/
│   ├── __init__.py
│   └── settings.py             # Configuration loader and validation
├── clients/
│   ├── __init__.py
│   ├── discord_reader.py       # Discord message extraction using user token
│   └── discord_writer.py       # Discord bot client for posting summaries
├── summarizers/
│   ├── __init__.py             # Factory method to create appropriate summarizer
│   ├── base.py                 # Abstract base class for summarizers
│   ├── anthropic.py            # Anthropic Claude implementation
│   └── deepseek.py             # DeepSeek implementation
├── models/
│   ├── __init__.py
│   ├── message.py              # Message data model
│   └── summary.py              # Summary data model
├── services/
│   ├── __init__.py
│   ├── message_collector.py    # Service to collect messages from channels
│   ├── summary_generator.py    # Service to generate summaries from messages
│   └── summary_scheduler.py    # Scheduling service for summary generation
├── utils/
│   ├── __init__.py
│   ├── logging_config.py       # Logging setup
│   ├── prompts.py              # LLM prompt templates
│   └── discord_explorer.py     # Utility to find guild/channel IDs
├── .env.example                # Example environment variables
├── .gitignore                  # Git ignore file
├── main.py                     # Application entry point
├── README.md                   # Project documentation
└── requirements.txt            # Dependencies
```

## Component Descriptions

### Config

- **settings.py**: Loads and validates environment variables, provides typed configuration objects for the rest of the application.

### Clients

- **discord_reader.py**: Responsible for reading messages from Discord using a user token. Handles rate limiting and Discord API interactions.
- **discord_writer.py**: Manages posting summaries to Discord using a bot token. Contains formatting logic for embeds.

### Summarizers

- ****init**.py**: Factory function to instantiate the correct summarizer based on configuration.
- **base.py**: Abstract base class defining the summarizer interface.
- **anthropic.py**: Implementation using Anthropic's Claude API.
- **deepseek.py**: Implementation using DeepSeek's API.

### Models

- **message.py**: Defines the structure for Discord messages with sender information, content, etc.
- **summary.py**: Represents a generated summary with metadata.

### Services

- **message_collector.py**: Orchestrates message collection from multiple channels.
- **summary_generator.py**: Handles the workflow of generating summaries from messages.
- **summary_scheduler.py**: Manages the scheduling of summary generation and posting.

### Utils

- **logging_config.py**: Configures application logging.
- **prompts.py**: Contains prompt templates for different LLM providers.
- **discord_explorer.py**: Utility tool to find Discord server and channel IDs.

## Data Flow

1. The scheduler triggers summary generation at configured times
2. Message collector retrieves messages from configured Discord channels
3. Summary generator processes messages and sends them to the selected LLM
4. Summaries are posted to the destination channel via the Discord writer

## Dependency Injection

The architecture uses dependency injection to:

- Make testing easier
- Allow for swapping implementations (e.g., different LLM providers)
- Maintain clear separation of concerns
