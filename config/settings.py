"""
Configuration Management Module

This module is responsible for loading and validating the application configuration
from environment variables, providing typed and validated configuration objects
to the rest of the application.
"""

import os
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

class LLMProvider(Enum):
    """
    Supported LLM providers for summarization.
    """
    DEEPSEEK = "deepseek"
    ANTHROPIC = "anthropic"

@dataclass
class DiscordReaderConfig:
    """
    Configuration for the Discord reader client.
    """
    user_token: str
    guild_id: Optional[str]
    channel_ids: List[str]
    
@dataclass
class DiscordWriterConfig:
    """
    Configuration for the Discord writer client.
    """
    bot_token: str
    destination_channel_id: int

@dataclass
class LLMConfig:
    """
    Configuration for the LLM provider.
    """
    provider: LLMProvider
    api_key: str

@dataclass
class SchedulerConfig:
    """
    Configuration for the scheduler.
    """
    summary_hour: int
    summary_minute: int
    days_to_collect: int = 1  # Default to 1 day

@dataclass
class AppConfig:
    """
    Complete application configuration.
    """
    discord_reader: DiscordReaderConfig
    discord_writer: DiscordWriterConfig
    llm: LLMConfig
    scheduler: SchedulerConfig
    debug_mode: bool = False

def _parse_channel_ids(channel_ids_str: str) -> List[str]:
    """
    Parse a comma-separated list of channel IDs into a list.
    
    Args:
        channel_ids_str: Comma-separated list of channel IDs
        
    Returns:
        List of channel IDs
    """
    if not channel_ids_str:
        return []
    
    return [channel_id.strip() for channel_id in channel_ids_str.split(',') if channel_id.strip()]

def _get_llm_api_key(provider: LLMProvider) -> str:
    """
    Get the API key for the specified LLM provider.
    
    Args:
        provider: LLM provider enum
        
    Returns:
        API key for the provider
        
    Raises:
        ValueError: If no API key is found for the provider
    """
    if provider == LLMProvider.ANTHROPIC:
        api_key = os.getenv('ANTHROPIC_API_KEY')
    elif provider == LLMProvider.DEEPSEEK:
        api_key = os.getenv('DEEPSEEK_API_KEY')
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
    
    if not api_key:
        raise ValueError(f"No API key found for {provider.value} provider")
    
    return api_key

def load_config() -> AppConfig:
    """
    Load and validate configuration from environment variables.
    
    Returns:
        Complete application configuration
        
    Raises:
        ValueError: If required configuration values are missing or invalid
    """
    # Load environment variables from .env file
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(dotenv_path, override=True)
    
    # Get Discord reader configuration
    discord_user_token = os.getenv('DISCORD_USER_TOKEN')
    if not discord_user_token:
        raise ValueError("DISCORD_USER_TOKEN is required")
    
    discord_guild_id = os.getenv('DISCORD_SOURCE_GUILD_ID')
    discord_channel_ids = _parse_channel_ids(os.getenv('DISCORD_SOURCE_CHANNEL_IDS', ''))
    
    # If no guild ID and no channel IDs, we can't know what to monitor
    if not discord_guild_id and not discord_channel_ids:
        raise ValueError("Either DISCORD_SOURCE_GUILD_ID or DISCORD_SOURCE_CHANNEL_IDS must be provided")
    
    # Get Discord writer configuration
    discord_bot_token = os.getenv('DISCORD_BOT_TOKEN')
    if not discord_bot_token:
        raise ValueError("DISCORD_BOT_TOKEN is required")
    
    discord_destination_channel_id = os.getenv('DISCORD_DESTINATION_CHANNEL_ID')
    if not discord_destination_channel_id:
        raise ValueError("DISCORD_DESTINATION_CHANNEL_ID is required")
    
    # Determine LLM provider
    llm_provider_str = os.getenv('LLM_PROVIDER', 'anthropic').strip().lower()
    try:
        llm_provider = LLMProvider(llm_provider_str)
    except ValueError:
        print(f"WARNING: Invalid LLM provider '{llm_provider_str}'. Defaulting to Anthropic.")
        llm_provider = LLMProvider.ANTHROPIC
    
    # Get LLM API key
    llm_api_key = _get_llm_api_key(llm_provider)
    
    # Get scheduler configuration
    summary_hour = int(os.getenv('SUMMARY_HOUR', '23'))
    summary_minute = int(os.getenv('SUMMARY_MINUTE', '0'))
    days_to_collect = int(os.getenv('DAYS_TO_COLLECT', '1'))
    
    # Debug mode
    debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # Create and return configuration
    return AppConfig(
        discord_reader=DiscordReaderConfig(
            user_token=discord_user_token,
            guild_id=discord_guild_id,
            channel_ids=discord_channel_ids
        ),
        discord_writer=DiscordWriterConfig(
            bot_token=discord_bot_token,
            destination_channel_id=int(discord_destination_channel_id)
        ),
        llm=LLMConfig(
            provider=llm_provider,
            api_key=llm_api_key
        ),
        scheduler=SchedulerConfig(
            summary_hour=summary_hour,
            summary_minute=summary_minute,
            days_to_collect=days_to_collect
        ),
        debug_mode=debug_mode
    )