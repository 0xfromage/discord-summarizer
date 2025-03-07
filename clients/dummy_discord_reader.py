"""
Dummy Discord Reader Client

This module provides a drop-in replacement for the real DiscordReaderClient
that reads messages from a local file instead of calling Discord's API.
"""

import os
import pickle
import logging
from typing import List, Dict, Tuple, Optional, Any

from models.message import DiscordMessage

logger = logging.getLogger(__name__)

# Path to the stored data
DATA_DIR = "extracted_data"
PICKLE_FILE = os.path.join(DATA_DIR, "discord_messages.pkl")

class DummyDiscordReaderClient:
    """
    Dummy client that mimics the DiscordReaderClient but uses local data.
    """
    
    def __init__(self, user_token: str = "dummy_token"):
        """
        Initialize the dummy client.
        
        Args:
            user_token: Not used, but kept for API compatibility
        """
        self.data = self._load_data()
        self.user_token = "dummy_token"  # Not used, but kept for interface compatibility
        logger.info(f"Initialized DummyDiscordReaderClient with {len(self.data)} channels of data")
    
    def _load_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Load the stored data from the pickle file.
        
        Returns:
            Dictionary mapping channel IDs to channel data
        """
        try:
            if not os.path.exists(PICKLE_FILE):
                logger.error(f"Data file {PICKLE_FILE} not found. Run data_extractor.py first.")
                return {}
            
            with open(PICKLE_FILE, 'rb') as f:
                data = pickle.load(f)
            
            # Convert dictionaries back to DiscordMessage objects
            for channel_id, channel_data in data.items():
                channel_data["messages"] = [
                    DiscordMessage(**msg_dict) if isinstance(msg_dict, dict) else msg_dict
                    for msg_dict in channel_data["messages"]
                ]
            
            return data
        
        except Exception as e:
            logger.error(f"Error loading data from {PICKLE_FILE}: {e}")
            return {}
    
    def get_my_guilds(self) -> List[Dict[str, Any]]:
        """
        Simulate getting all guilds (servers) the user is in.
        
        Returns:
            List of dummy guild objects
        """
        return [{"id": "dummy_guild_id", "name": "Dummy Guild"}]
    
    def get_guild_channels(self, guild_id: str) -> List[Dict[str, Any]]:
        """
        Simulate getting all channels in a guild.
        
        Args:
            guild_id: ID of the guild (not used)
            
        Returns:
            List of channel objects based on the loaded data
        """
        channels = []
        for channel_id, channel_data in self.data.items():
            channels.append({
                "id": channel_id,
                "name": channel_data["channel_name"],
                "type": 0  # Text channel
            })
        return channels
    
    def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Simulate getting information about a channel.
        
        Args:
            channel_id: ID of the channel
            
        Returns:
            Channel information if the channel exists in the loaded data, None otherwise
        """
        if channel_id in self.data:
            return {
                "id": channel_id,
                "name": self.data[channel_id]["channel_name"],
                "type": 0  # Text channel
            }
        return None
    
    def get_messages(self, channel_id: str, limit: int = 100, before: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Simulate getting messages from a channel.
        
        Args:
            channel_id: ID of the channel
            limit: Maximum number of messages to retrieve (not used)
            before: Message ID to get messages before (not used)
            
        Returns:
            Empty list - this method isn't used by collect_messages in dummy mode
        """
        return []
    
    def collect_messages(self, channel_id: str, days: int = 1) -> Tuple[List[DiscordMessage], str]:
        """
        Get messages from the loaded data instead of from Discord.
        
        Args:
            channel_id: ID of the channel
            days: Number of days to look back (not used, returns all loaded data)
            
        Returns:
            Tuple of (list of messages, channel name)
        """
        if channel_id not in self.data:
            logger.warning(f"Channel {channel_id} not found in loaded data")
            return [], f"Unknown Channel {channel_id}"
        
        channel_data = self.data[channel_id]
        messages = channel_data["messages"]
        channel_name = channel_data["channel_name"]
        
        logger.info(f"Retrieved {len(messages)} messages from {channel_name} (dummy mode)")
        return messages, channel_name