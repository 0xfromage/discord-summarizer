"""
Discord Summary Model

This module defines the data model for generated summaries.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class DiscordSummary:
    """
    Represents a generated summary of Discord messages.
    
    This model contains the generated summary content along with
    metadata about the summarization process.
    """
    content: str
    title: str
    channel_id: str
    channel_name: str
    message_count: int
    provider_name: str
    generation_time: datetime = None
    date: str = None
    
    def __post_init__(self):
        """
        Initialize default values after initialization.
        """
        if self.generation_time is None:
            self.generation_time = datetime.now()
        
        if self.date is None:
            self.date = self.generation_time.strftime("%Y-%m-%d")
    
    @property
    def word_count(self) -> int:
        """
        Count the number of words in the summary.
        
        Returns:
            Number of words in the summary content
        """
        return len(self.content.split())
    
    @property
    def character_count(self) -> int:
        """
        Count the number of characters in the summary.
        
        Returns:
            Number of characters in the summary content
        """
        return len(self.content)
    
    def to_dict(self) -> dict:
        """
        Convert the summary to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the summary
        """
        return {
            "content": self.content,
            "title": self.title,
            "channel_id": self.channel_id,
            "channel_name": self.channel_name,
            "message_count": self.message_count,
            "provider_name": self.provider_name,
            "generation_time": self.generation_time.isoformat(),
            "date": self.date,
            "word_count": self.word_count,
            "character_count": self.character_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DiscordSummary':
        """
        Create a summary from a dictionary.
        
        Args:
            data: Dictionary representation of a summary
            
        Returns:
            DiscordSummary object
        """
        # Convert timestamp string to datetime
        if isinstance(data.get('generation_time'), str):
            generation_time = datetime.fromisoformat(data['generation_time'])
        else:
            generation_time = data.get('generation_time', datetime.now())
        
        return cls(
            content=data.get('content', ''),
            title=data.get('title', 'Discord Summary'),
            channel_id=data.get('channel_id', '0'),
            channel_name=data.get('channel_name', 'Unknown Channel'),
            message_count=data.get('message_count', 0),
            provider_name=data.get('provider_name', 'AI'),
            generation_time=generation_time,
            date=data.get('date')
        )