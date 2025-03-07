"""
Discord Reader Client

This module provides a client for reading messages from Discord using a user token.
It handles API communication, rate limiting, and data extraction.
"""

import logging
import random
import time
from datetime import datetime, timedelta
import requests
from typing import List, Dict, Optional, Any, Tuple

from models.message import DiscordMessage

logger = logging.getLogger(__name__)

class DiscordReaderClient:
    """
    Client for interacting with Discord API to read messages.
    Uses a user token for authentication.
    """
    
    def __init__(self, user_token: str):
        """
        Initialize the Discord reader client.
        
        Args:
            user_token: Discord user token for authentication
        """
        self.base_url = "https://discord.com/api/v9"
        self.headers = {
            "Authorization": user_token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
        }
        
        # Rate limiting state
        self.rate_limit_remaining = 5
        self.rate_limit_reset = 0
    
    def _handle_rate_limit(self) -> None:
        """
        Handle Discord API rate limits by waiting if necessary.
        """
        if self.rate_limit_remaining <= 1:
            current_time = time.time()
            sleep_time = max(0, self.rate_limit_reset - current_time) + 0.5
            
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
    
    def _make_request(self, endpoint: str, method: str = "GET", payload: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        Make a request to the Discord API with rate limit handling.
        
        Args:
            endpoint: API endpoint to call
            method: HTTP method to use
            payload: Request payload for POST requests
            
        Returns:
            Response data if successful, None otherwise
        """
        self._handle_rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=payload)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            # Update rate limit information from headers
            self.rate_limit_remaining = int(response.headers.get("X-RateLimit-Remaining", 5))
            self.rate_limit_reset = float(response.headers.get("X-RateLimit-Reset", time.time() + 5))
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = response.json().get("retry_after", 1)
                logger.warning(f"Rate limited. Retrying after {retry_after} seconds")
                time.sleep(retry_after)
                return self._make_request(endpoint, method, payload)
            
            # Handle errors
            if response.status_code != 200:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return None
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return None
    
    def get_user_guilds(self) -> List[Dict[str, Any]]:
        """
        Get all guilds (servers) the user is a member of.
        
        Returns:
            List of guild objects
        """
        return self._make_request("/users/@me/guilds") or []
    
    def get_guild_channels(self, guild_id: str) -> List[Dict[str, Any]]:
        """
        Get all channels in a guild.
        
        Args:
            guild_id: ID of the guild
            
        Returns:
            List of channel objects
        """
        return self._make_request(f"/guilds/{guild_id}/channels") or []
    
    def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a channel.
        
        Args:
            channel_id: ID of the channel
            
        Returns:
            Channel information if successful, None otherwise
        """
        return self._make_request(f"/channels/{channel_id}")
    
    def get_messages(self, channel_id: str, limit: int = 100, before: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get messages from a channel with pagination.
        
        Args:
            channel_id: ID of the channel
            limit: Maximum number of messages to retrieve (max 100)
            before: Message ID to get messages before
            
        Returns:
            List of message objects
        """
        endpoint = f"/channels/{channel_id}/messages?limit={limit}"
        if before:
            endpoint += f"&before={before}"
        
        return self._make_request(endpoint) or []
    
    def collect_messages(self, channel_id: str, days: int = 1) -> Tuple[List[DiscordMessage], str]:
        """
        Collect messages from a channel for a specified time period.
        
        Args:
            channel_id: ID of the channel
            days: Number of days to look back
            
        Returns:
            Tuple of (list of message objects, channel name)
        """

        MAX_TOTAL_REQUESTS = 500
        total_requests = 0

        # Get channel information to include in the return value
        channel_info = self.get_channel_info(channel_id)
        channel_name = channel_info.get('name', f"Channel {channel_id}") if channel_info else f"Channel {channel_id}"
        
        # Calculate time threshold
        time_threshold = datetime.now() - timedelta(days=days)
        
        # Collect messages
        all_messages = []
        last_id = None
        
        try:
            while True:
                # Increment request counter
                total_requests += 1
                
                # Check if we've reached the request cap
                if total_requests >= MAX_TOTAL_REQUESTS:
                    logger.warning(f"Request cap reached ({MAX_TOTAL_REQUESTS}). Stopping further requests for channel {channel_id}.")
                    break
                
                # Get batch of messages
                messages = self.get_messages(channel_id, limit=100, before=last_id)
                
                # Stop if no messages returned
                if not messages or len(messages) == 0:
                    break
                
                # Check if we've reached messages older than our threshold
                # Convert ISO string to datetime and ensure timezone awareness is consistent
                oldest_msg_time = datetime.fromisoformat(messages[-1]['timestamp'].rstrip('Z')).replace(tzinfo=None)
                if oldest_msg_time < time_threshold:
                    # Process messages until we hit the threshold
                    for msg in messages:
                        msg_time = datetime.fromisoformat(msg['timestamp'].rstrip('Z')).replace(tzinfo=None)
                        if msg_time >= time_threshold:
                            message = self._convert_to_message_model(msg)
                            if message:
                                all_messages.append(message)
                    break
                
                # Process all messages in this batch
                for msg in messages:
                    message = self._convert_to_message_model(msg)
                    if message:
                        all_messages.append(message)
                
                # Update last_id for pagination
                last_id = messages[-1]['id']
                
                # Add a small delay to be gentle with the API
                time.sleep(0.5 + random.random())
            
            logger.info(f"Collected {len(all_messages)} messages from channel {channel_name}")
            return all_messages, channel_name
            
        except Exception as e:
            logger.error(f"Error collecting messages from channel {channel_id}: {str(e)}")
            return [], channel_name
    
    def _convert_to_message_model(self, raw_message: Dict[str, Any]) -> Optional[DiscordMessage]:
        """
        Convert a raw API message to a DiscordMessage model.
        
        Args:
            raw_message: Raw message data from the API
            
        Returns:
            DiscordMessage object or None if conversion fails
        """
        try:
            # Skip messages without content
            content = raw_message.get('content', '')
            if not content:
                return None
            
            # Get user info
            author = raw_message.get('author', {})
            username = author.get('username', 'Unknown')
            user_id = author.get('id', '0')
            
            # Get timestamp
            timestamp_str = raw_message.get('timestamp', '')
            if timestamp_str:
                # Ensure consistent timezone handling by removing the Z and any tzinfo
                timestamp = datetime.fromisoformat(timestamp_str.rstrip('Z')).replace(tzinfo=None)
            else:
                timestamp = datetime.now()
            
            # Create message object
            return DiscordMessage(
                id=raw_message.get('id', '0'),
                content=content,
                username=username,
                user_id=user_id,
                timestamp=timestamp,
                channel_id=raw_message.get('channel_id', '0'),
                attachments_count=len(raw_message.get('attachments', [])),
                embeds_count=len(raw_message.get('embeds', [])),
                mentions_count=len(raw_message.get('mentions', [])),
            )
            
        except Exception as e:
            logger.error(f"Error converting message: {str(e)}")
            return None