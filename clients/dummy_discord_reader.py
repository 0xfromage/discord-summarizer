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
from config.settings import DiscordReaderConfig

logger = logging.getLogger(__name__)

# Path to the stored data
DATA_DIR = "extracted_data"
PICKLE_FILE = os.path.join(DATA_DIR, "discord_messages.pkl")
THREAD_FILE = os.path.join(DATA_DIR, "discord_threads.pkl")

class DummyDiscordReaderClient:
    """
    Dummy client that mimics the DiscordReaderClient but uses local data.
    """
    
    def __init__(self, user_token: str = "dummy_token", config: Optional[DiscordReaderConfig] = None):
        """
        Initialize the dummy client.
        
        Args:
            user_token: Not used, but kept for API compatibility
            config: Configuration for the reader (optional)
        """
        self.data = self._load_data()
        self.thread_data = self._load_thread_data()
        self.user_token = "dummy_token"  # Not used, but kept for interface compatibility
        self.config = config
        logger.info(f"Initialized DummyDiscordReaderClient with {len(self.data)} channels of data and {len(self.thread_data)} threads")
    
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
    
    def _load_thread_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Load thread data from pickle file if it exists.
        
        Returns:
            Dictionary mapping thread IDs to thread data
        """
        try:
            if not os.path.exists(THREAD_FILE):
                logger.warning(f"Thread data file {THREAD_FILE} not found. Thread data will be empty.")
                return {}
            
            with open(THREAD_FILE, 'rb') as f:
                data = pickle.load(f)
            
            # Convert dictionaries back to DiscordMessage objects
            for thread_id, thread_data in data.items():
                thread_data["messages"] = [
                    DiscordMessage(**msg_dict) if isinstance(msg_dict, dict) else msg_dict
                    for msg_dict in thread_data["messages"]
                ]
            
            return data
        
        except Exception as e:
            logger.error(f"Error loading thread data from {THREAD_FILE}: {e}")
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
        elif channel_id in self.thread_data:
            return {
                "id": channel_id,
                "name": self.thread_data[channel_id]["thread_name"],
                "type": 11,  # Thread channel type
                "parent_id": self.thread_data[channel_id].get("parent_id", "unknown")
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
    
    def collect_messages(self, channel_id: str, days: int = 1) -> Tuple[List[DiscordMessage], str, List[Tuple[List[DiscordMessage], str]]]:
        """
        Get messages from the loaded data instead of from Discord.
        
        Args:
            channel_id: ID of the channel
            days: Number of days to look back (not used, returns all loaded data)
            
        Returns:
            Tuple of (list of messages, channel name, list of (thread messages, thread name) tuples)
        """
        if channel_id not in self.data:
            logger.warning(f"Channel {channel_id} not found in loaded data")
            return [], f"Unknown Channel {channel_id}", []
        
        channel_data = self.data[channel_id]
        messages = channel_data["messages"]
        channel_name = channel_data["channel_name"]
        
        # Check for thread data
        thread_data = []
        if self.config and hasattr(self.config, 'thread_ids') and self.config.thread_ids:
            for thread_id in self.config.thread_ids:
                if thread_id in self.thread_data and self.thread_data[thread_id].get("parent_id") == channel_id:
                    thread_messages = self.thread_data[thread_id]["messages"]
                    thread_name = self.thread_data[thread_id]["thread_name"]
                    thread_data.append((thread_messages, thread_name))
                    logger.info(f"Retrieved {len(thread_messages)} messages from thread {thread_name} (dummy mode)")
        
        logger.info(f"Retrieved {len(messages)} messages from {channel_name} (dummy mode) and {sum(len(t[0]) for t in thread_data)} thread messages")
        return messages, channel_name, thread_data