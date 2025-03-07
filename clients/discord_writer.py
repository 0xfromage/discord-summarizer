"""
Discord Writer Client

This module provides a client for posting messages to Discord using a bot token.
It handles formatting summaries and posting them as embeds.
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional, List, Callable, Any
import discord

from models.summary import DiscordSummary

logger = logging.getLogger(__name__)

class DiscordWriterClient:
    """
    Client for posting summaries to Discord channels using a bot token.
    Wraps the discord.py library to provide a simpler interface.
    """
    
    def __init__(self, bot_token: str):
        """
        Initialize the Discord writer client.
        
        Args:
            bot_token: Discord bot token for authentication
        """
        # Initialize discord.py client
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        self.token = bot_token
        
        # Store callbacks for when the client is ready
        self.on_ready_callbacks = []
        
        # Track client ready state
        self.is_ready = False
        self.ready_event = asyncio.Event()
    
    def add_on_ready_callback(self, callback: Callable[[], Any]) -> None:
        """
        Add a callback to be executed when the Discord client is ready.
        
        Args:
            callback: Async function to call when the client is ready
        """
        self.on_ready_callbacks.append(callback)
    
    async def start(self) -> None:
        """
        Start the Discord client and set up event handlers.
        """
        @self.client.event
        async def on_ready():
            """
            Triggered when the Discord client is connected and ready.
            """
            self.is_ready = True
            logger.info(f'Discord writer client logged in as {self.client.user}')
            
            # Set the ready event
            self.ready_event.set()
            
            # Execute all registered callbacks
            for callback in self.on_ready_callbacks:
                try:
                    await callback()
                except Exception as e:
                    logger.error(f"Error in on_ready callback: {str(e)}")
        
        # Start the client
        await self.client.start(self.token)
    
    async def wait_until_ready(self) -> None:
        """
        Wait until the Discord client is ready.
        """
        if not self.is_ready:
            await self.ready_event.wait()
    
    async def post_summary(self, channel_id: int, summary: DiscordSummary) -> bool:
        """
        Post a summary to a Discord channel.
        
        Args:
            channel_id: ID of the channel to post to
            summary: Summary information to post
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.debug(f"Attempting to post summary to channel ID: {channel_id}")
            await self.wait_until_ready()
            logger.debug(f"Discord client is ready, getting channel")

            # Get the destination channel - first check through get_channel (same server)
            channel = self.client.get_channel(channel_id)
            logger.debug(f"get_channel result: {channel}")

            # If channel not found through get_channel, try fetch_channel (works for channels across servers)
            if not channel:
                try:
                    logger.debug(f"Channel not found with get_channel, trying fetch_channel")
                    channel = await self.client.fetch_channel(channel_id)
                    logger.debug(f"fetch_channel result: {channel}")
                except Exception as e:
                    logger.error(f"Failed to fetch channel {channel_id}: {str(e)}")
                    return False
            # Wait until client is ready
            await self.wait_until_ready()
            
            # Get the destination channel - first check through get_channel (same server)
            channel = self.client.get_channel(channel_id)
            
            # If channel not found through get_channel, try fetch_channel (works for channels across servers)
            if not channel:
                try:
                    channel = await self.client.fetch_channel(channel_id)
                except Exception as e:
                    logger.error(f"Failed to fetch channel {channel_id}: {str(e)}")
                    return False
            
            if not channel:
                logger.error(f"Discord channel {channel_id} not found. Make sure the bot has access to this channel.")
                return False
            
            # Create the embed
            embed = discord.Embed(
                title=f"{summary.title} ({summary.date})",
                description=summary.content,
                color=self._get_color_for_summary(summary)
            )
            
            # Add footer with metadata
            embed.set_footer(text=f"Summary by {summary.provider_name} • {summary.message_count} messages analyzed")
            
            # Send the message
            await channel.send(embed=embed)
            logger.info(f"Successfully posted summary '{summary.title}' to channel {channel_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error posting summary to Discord: {str(e)}")
            return False
    
    async def post_error(self, channel_id: int, error_message: str, title: str = "Error Generating Summary") -> bool:
        """
        Post an error message to a Discord channel.
        
        Args:
            channel_id: ID of the channel to post to
            error_message: Error message to post
            title: Title for the error message
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Wait until client is ready
            await self.wait_until_ready()
            
            # Get the destination channel - first check through get_channel (same server)
            channel = self.client.get_channel(channel_id)
            
            # If channel not found through get_channel, try fetch_channel (works for channels across servers)
            if not channel:
                try:
                    channel = await self.client.fetch_channel(channel_id)
                except Exception as e:
                    logger.error(f"Failed to fetch channel {channel_id}: {str(e)}")
                    return False
            
            if not channel:
                logger.error(f"Discord channel {channel_id} not found. Make sure the bot has access to this channel.")
                return False
            
            # Create the embed
            embed = discord.Embed(
                title=title,
                description=error_message,
                color=discord.Color.red()
            )
            
            # Add timestamp
            embed.timestamp = datetime.now()
            
            # Send the message
            await channel.send(embed=embed)
            logger.info(f"Posted error message to channel {channel_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error posting error message to Discord: {str(e)}")
            return False
    
    def _get_color_for_summary(self, summary: DiscordSummary) -> discord.Color:
        """
        Get a color for the summary embed based on the summary type or content.
        
        Args:
            summary: Summary to get a color for
            
        Returns:
            Discord color object
        """
        # Use a blue color by default
        return discord.Color.blue()