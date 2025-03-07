"""
Discord Writer Client with Enhanced Debugging

This is a modified version of the discord_writer.py file with additional
debugging to help identify connection issues.
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
        logger.debug(f"Initializing Discord writer client with token length: {len(bot_token)}")
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
        
        # Set up event handlers
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
                    logger.debug(f"Running on_ready callback: {callback.__name__ if hasattr(callback, '__name__') else 'unnamed'}")
                    await callback()
                except Exception as e:
                    logger.error(f"Error in on_ready callback: {str(e)}")
    
    def add_on_ready_callback(self, callback: Callable[[], Any]) -> None:
        """
        Add a callback to be executed when the Discord client is ready.
        
        Args:
            callback: Async function to call when the client is ready
        """
        logger.debug(f"Adding on_ready callback: {callback.__name__ if hasattr(callback, '__name__') else 'unnamed'}")
        self.on_ready_callbacks.append(callback)
    
    async def start(self) -> None:
        """
        Start the Discord client and set up event handlers.
        """
        logger.info("Starting Discord writer client")
        try:
            # Start the client - this is a blocking call that runs until the bot is closed
            logger.debug("About to start Discord client with token")
            
            # For one-time runs, we need a different approach
            if '--run-once' in asyncio.get_event_loop()._current_handles[0]._args[0]:
                logger.info("Detected --run-once mode, using run_until_complete")
                # In one-time mode, we need to login but not start the event loop
                await self.client.login(self.token)
                logger.info(f"Discord login successful as {self.client.user}")
                self.is_ready = True
                self.ready_event.set()
                
                # Process a few events to ensure Discord state is updated
                for _ in range(5):
                    await asyncio.sleep(0.5)  # Brief pause
                    self.client._connection.parse_presence_update = lambda *args, **kwargs: None
                    self.client._connection._dispatch_message = lambda *args, **kwargs: None
            else:
                # Normal mode - blocks until disconnect
                await self.client.start(self.token)
                
        except discord.errors.LoginFailure as e:
            logger.error(f"Discord login failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error starting Discord client: {str(e)}")
            raise
    
    async def wait_until_ready(self) -> None:
        """
        Wait until the Discord client is ready.
        """
        if not self.is_ready:
            logger.debug("Waiting for Discord client to be ready")
            try:
                # Wait with timeout to avoid hanging forever
                await asyncio.wait_for(self.ready_event.wait(), timeout=10.0)
                logger.debug("Discord client is now ready")
            except asyncio.TimeoutError:
                logger.error("Timed out waiting for Discord client to be ready")
                # Force ready state to try anyway
                self.is_ready = True
    
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
            
            # Wait until client is ready
            await self.wait_until_ready()
            logger.debug(f"Discord client is ready, accessing channel")
            
            # Direct way to post without using get_channel
            try:
                # Try REST API method directly
                logger.debug(f"Using REST API to send message")
                webhook = await self.client.create_webhook(channel_id, name="Summary Bot")
                
                # Create the embed
                embed = discord.Embed(
                    title=f"{summary.title} ({summary.date})",
                    description=summary.content,
                    color=0x3498db
                )
                
                # Add footer with metadata
                embed.set_footer(text=f"Summary by {summary.provider_name} • {summary.message_count} messages analyzed")
                
                # Send via webhook
                await webhook.send(embed=embed)
                logger.info(f"Successfully posted summary via webhook")
                await webhook.delete()
                return True
            except Exception as e1:
                logger.error(f"REST API approach failed: {str(e1)}")
                
                # Try the standard approach
                # Get the destination channel
                channel = self.client.get_channel(channel_id)
                logger.debug(f"get_channel result: {channel}")
                
                # If channel not found through get_channel, try fetch_channel
                if not channel:
                    try:
                        logger.debug(f"Channel not found with get_channel, trying fetch_channel")
                        channel = await self.client.fetch_channel(channel_id)
                        logger.debug(f"fetch_channel result: {channel}")
                    except Exception as e2:
                        logger.error(f"Failed to fetch channel {channel_id}: {str(e2)}")
                        
                        # Last resort - try to create a manual HTTP request
                        logger.debug("Trying manual HTTP request as last resort")
                        try:
                            import aiohttp
                            async with aiohttp.ClientSession() as session:
                                url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
                                headers = {
                                    "Authorization": f"Bot {self.token}",
                                    "Content-Type": "application/json"
                                }
                                embed_dict = {
                                    "title": f"{summary.title} ({summary.date})",
                                    "description": summary.content,
                                    "color": 0x3498db,
                                    "footer": {
                                        "text": f"Summary by {summary.provider_name} • {summary.message_count} messages analyzed"
                                    }
                                }
                                payload = {
                                    "content": f"Summary for {summary.channel_name}",
                                    "embeds": [embed_dict]
                                }
                                async with session.post(url, headers=headers, json=payload) as response:
                                    if response.status == 200:
                                        logger.info(f"Successfully posted summary via HTTP request")
                                        return True
                                    else:
                                        error_text = await response.text()
                                        logger.error(f"HTTP request failed: {response.status} - {error_text}")
                        except Exception as e3:
                            logger.error(f"Manual HTTP request failed: {str(e3)}")
                        return False
                
                if not channel:
                    logger.error(f"Discord channel {channel_id} not found after all attempts. Make sure the bot has access to this channel.")
                    return False
                
                # Create the embed
                embed = discord.Embed(
                    title=f"{summary.title} ({summary.date})",
                    description=summary.content,
                    color=0x3498db
                )
                
                # Add footer with metadata
                embed.set_footer(text=f"Summary by {summary.provider_name} • {summary.message_count} messages analyzed")
                
                # Send the message
                logger.debug("Sending message with embed")
                await channel.send(embed=embed)
                logger.info(f"Successfully posted summary '{summary.title}' to channel {channel_id}")
                return True
        
        except Exception as e:
            logger.error(f"Error posting summary to Discord: {str(e)}", exc_info=True)
            return False