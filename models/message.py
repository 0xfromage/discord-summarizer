"""
Discord Message Model

This module defines the data model for Discord messages.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class DiscordMessage:
    """
    Represents a Discord message.
    
    This model contains essential information about a Discord message,
    including content, sender information, and metadata.
    """
    id: str
    content: str
    username: str
    user_id: str
    timestamp: datetime
    channel_id: str
    attachments_count: int = 0
    embeds_count: int = 0
    mentions_count: int = 0
    
    @property
    def formatted_time(self) -> str:
        """
        Get a formatted timestamp string.
        
        Returns:
            Formatted timestamp in the format "YYYY-MM-DD HH:MM:SS"
        """
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    @property
    def formatted_content(self) -> str:
        """
        Get a formatted string representation of the message.
        
        Returns:
            String in the format "[timestamp] username: content"
        """
        return f"[{self.formatted_time}] {self.username}: {self.content}"
    
    def to_dict(self) -> dict:
        """
        Convert the message to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the message
        """
        return {
            "id": self.id,
            "content": self.content,
            "username": self.username,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "channel_id": self.channel_id,
            "attachments_count": self.attachments_count,
            "embeds_count": self.embeds_count,
            "mentions_count": self.mentions_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DiscordMessage':
        """
        Create a message from a dictionary.
        
        Args:
            data: Dictionary representation of a message
            
        Returns:
            DiscordMessage object
        """
        # Convert timestamp string to datetime
        if isinstance(data.get('timestamp'), str):
            timestamp = datetime.fromisoformat(data['timestamp'])
        else:
            timestamp = data.get('timestamp', datetime.now())
        
        return cls(
            id=data.get('id', '0'),
            content=data.get('content', ''),
            username=data.get('username', 'Unknown'),
            user_id=data.get('user_id', '0'),
            timestamp=timestamp,
            channel_id=data.get('channel_id', '0'),
            attachments_count=data.get('attachments_count', 0),
            embeds_count=data.get('embeds_count', 0),
            mentions_count=data.get('mentions_count', 0)
        )