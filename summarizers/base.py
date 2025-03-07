"""
Base Summarizer

This module defines the abstract base class for summarizers.
All LLM-specific summarizer implementations should inherit from this class.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from models.message import DiscordMessage
from models.summary import DiscordSummary

logger = logging.getLogger(__name__)

class BaseSummarizer(ABC):
    """
    Abstract base class for summarizers.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the summarizer with an API key.
        
        Args:
            api_key: API key for the LLM provider
        """
        self.api_key = api_key
    
    @property
    def provider_name(self) -> str:
        """
        Get the name of the LLM provider.
        
        Returns:
            Provider name
        """
        return self.__class__.__name__.replace('Summarizer', '')
    
    @abstractmethod
    def generate_summary(
        self,
        messages: List[DiscordMessage], 
        channel_name: str,  
        prompt_type: Optional[str] = None, 
        override_system_prompt: Optional[str] = None, 
        override_user_prompt: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a summary from Discord messages.
        
        Args:
            messages: List of messages to summarize
            channel_name: Name of the topic or channel
            prompt_type: Type of prompt to use (optional)
            override_system_prompt: Custom system prompt (optional)
            override_user_prompt: Custom user prompt (optional)
            
        Returns:
            Generated summary text or None if generation fails
        """
        pass
    

    def create_summary_object(
        self, 
        content: str, 
        messages: List[DiscordMessage], 
        channel_name: str,  # Change from channel_name to channel_name for consistency
        channel_id: str,
        provider_name: Optional[str] = None
    ) -> DiscordSummary:
        # Use the provided provider name or default to the class provider name
        actual_provider = provider_name or self.provider_name
        
        return DiscordSummary(
            content=content,
            title=f"Discord Summary: {channel_name}",  # Update this too
            channel_id=channel_id,
            channel_name=channel_name,  # And this
            message_count=len(messages),
            provider_name=actual_provider
        )
    
    def _format_messages_for_prompt(self, messages: List[DiscordMessage]) -> str:
        """
        Format messages for inclusion in the prompt.
        
        Args:
            messages: List of messages to format
            
        Returns:
            Formatted message text
        """
        # Sort messages by timestamp
        sorted_messages = sorted(messages, key=lambda m: m.timestamp)
        
        # Format each message and join with newlines
        return "\n".join(message.formatted_content for message in sorted_messages)
    
    def _truncate_messages(self, formatted_messages: str, max_length: int = 10000) -> str:
        """
        Truncate messages to fit within token limits.
        
        Args:
            formatted_messages: Formatted message text
            max_length: Maximum number of characters
            
        Returns:
            Truncated message text
        """
        if len(formatted_messages) <= max_length:
            return formatted_messages
        
        # Simple truncation - keep the most recent messages
        # In a real implementation, we might want a more sophisticated approach
        logger.warning(f"Truncating message text from {len(formatted_messages)} to {max_length} characters")
        return formatted_messages[-max_length:]