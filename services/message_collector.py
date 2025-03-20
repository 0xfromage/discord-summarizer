"""
Message Collector Service

This service is responsible for collecting messages from Discord channels
using the DiscordReaderClient. It handles the orchestration of message collection
from multiple channels and provides processing of the collected messages.
"""

import logging
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

from clients.discord_reader import DiscordReaderClient
from models.message import DiscordMessage
from config.settings import DiscordReaderConfig

logger = logging.getLogger(__name__)

class MessageCollectorService:
    """
    Service for collecting messages from Discord channels.
    """
    
    def __init__(self, client: DiscordReaderClient, config: DiscordReaderConfig):
        """
        Initialize the message collector service.
        
        Args:
            client: Discord reader client
            config: Discord reader configuration
        """
        self.client = client
        self.config = config
    
    async def collect_from_channel(self, channel_id: str, days: int = 1) -> Tuple[List[DiscordMessage], str, List[Tuple[List[DiscordMessage], str]]]:
        """
        Collect messages from a single channel.
        
        Args:
            channel_id: ID of the channel to collect from
            days: Number of days to look back
            
        Returns:
            Tuple of (list of messages, channel name, list of (thread messages, thread name) tuples)
        """
        logger.info(f"Collecting messages from channel {channel_id} for the past {days} day(s)")
        return self.client.collect_messages(channel_id, days)
    
    async def collect_from_guild(self, guild_id: str, days: int = 1) -> List[Tuple[List[DiscordMessage], str]]:
        """
        Collect messages from all text channels in a guild.
        
        Args:
            guild_id: ID of the guild to collect from
            days: Number of days to look back
            
        Returns:
            List of tuples, each containing (list of messages, channel name)
        """
        logger.info(f"Collecting messages from all text channels in guild {guild_id}")
        
        # Get all channels in the guild
        channels = self.client.get_guild_channels(guild_id)
        
        # Filter for text channels only (type 0)
        text_channels = [channel for channel in channels if channel.get('type') == 0]
        
        if not text_channels:
            logger.warning(f"No text channels found in guild {guild_id}")
            return []
        
        logger.info(f"Found {len(text_channels)} text channels in guild {guild_id}")
        
        # Collect messages from each channel
        results = []
        for channel in text_channels:
            channel_id = channel.get('id')
            messages, channel_name, thread_data = await self.collect_from_channel(channel_id, days)
            results.append((messages, channel_name, thread_data))
        
        return results
    
    async def collect_from_config(self, days: Optional[int] = None) -> Dict[str, Tuple[List[DiscordMessage], str]]:
        """
        Collect messages based on the configuration.
        
        Args:
            days: Number of days to look back, defaults to config value
            
        Returns:
            Dictionary mapping channel IDs to tuples of (list of messages, channel name)
        """
        if days is None:
            days = 1  # Default to 1 day if not specified
        
        results = {}
        
        # If specific channel IDs are configured, collect from those
        if self.config.channel_ids:
            logger.info(f"Collecting messages from {len(self.config.channel_ids)} configured channels")
            
            for channel_id in self.config.channel_ids:
                messages, channel_name, thread_data = await self.collect_from_channel(channel_id, days)
                results[channel_id] = (messages, channel_name, thread_data)
        
        # If a guild ID is configured and we don't have specific channels, collect from the guild
        elif self.config.guild_id:
            logger.info(f"Collecting messages from all text channels in guild {self.config.guild_id}")
            
            guild_results = await self.collect_from_guild(self.config.guild_id, days)
            
            # Convert the list of results to a dictionary
            for messages, channel_name in guild_results:
                if messages:  # Only add channels with messages
                    # Use the first message's channel_id
                    channel_id = messages[0].channel_id if messages else "unknown"
                    results[channel_id] = (messages, channel_name)
        
        else:
            logger.warning("No channels or guild configured for message collection")
        
        return results