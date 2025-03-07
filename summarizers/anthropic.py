"""
Anthropic Claude Summarizer

This module implements the summarizer interface using Anthropic's Claude API.
"""

import logging
from typing import List, Optional, Dict, Any

from anthropic import Anthropic
from models.message import DiscordMessage
from summarizers.base import BaseSummarizer
from utils.prompts import PromptTemplates

logger = logging.getLogger(__name__)

class AnthropicSummarizer(BaseSummarizer):
    """
    Summarizer implementation using Anthropic's Claude API.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the Claude summarizer.
        
        Args:
            api_key: Anthropic API key
        """
        super().__init__(api_key)
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-7-sonnet-20250219"  # Use the latest model by default
    
    def generate_summary(
        self,
        messages: List[DiscordMessage], 
        channel_name: str,
        prompt_type: Optional[str] = None, 
        override_system_prompt: Optional[str] = None, 
        override_user_prompt: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a summary using Claude.
        
        Args:
            messages: List of messages to summarize
            channel_name: Name of the channel
            prompt_type: Type of prompt to use
            override_system_prompt: Custom system prompt
            override_user_prompt: Custom user prompt
            
        Returns:
            Generated summary text or None if generation fails
        """
        try:
            if not messages:
                logger.warning(f"No messages to summarize for {channel_name}")
                return None
            
            # Format messages for the prompt
            formatted_messages = self._format_messages_for_prompt(messages)
            
            # Truncate if necessary for token limits
            formatted_messages = self._truncate_messages(formatted_messages, max_length=25000)
            
            # Get appropriate prompts
            prompts = PromptTemplates.get_prompts(
                channel_name=channel_name, 
                prompt_type=prompt_type,
                override_system_prompt=override_system_prompt,
                override_user_prompt=override_user_prompt
            )
            
            logger.info(f"Generating summary for {channel_name} with Claude ({len(messages)} messages)")
            
            # Make the API call
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=prompts['system_prompt'],
                messages=[
                    {
                        "role": "user",
                        "content": PromptTemplates.format_user_prompt(
                            formatted_messages, 
                            channel_name=channel_name,
                            prompt_type=prompt_type
                        )
                    }
                ]
            )
            
            summary_text = response.content[0].text
            logger.info(f"Successfully generated summary for {channel_name}")
            
            return summary_text
            
        except Exception as e:
            logger.error(f"Error generating summary with Claude: {str(e)}")
            return None