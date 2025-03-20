"""
Summary Generator Service

This service orchestrates the generation of summaries from collected messages.
It coordinates between the message collector and summarizer components.
"""

import logging
import os  # Add this import at the top
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from models.message import DiscordMessage
from models.summary import DiscordSummary
from summarizers.base import BaseSummarizer
from services.message_collector import MessageCollectorService

logger = logging.getLogger(__name__)

class SummaryGeneratorService:
    """
    Service for generating summaries from collected messages.
    """
    
    def __init__(self, message_collector: MessageCollectorService, summarizer: BaseSummarizer):
        """
        Initialize the summary generator service.
        
        Args:
            message_collector: Service for collecting messages
            summarizer: Summarizer implementation
        """
        self.message_collector = message_collector
        self.summarizer = summarizer
    
    async def generate_channel_summary(
        self, 
        channel_id: str, 
        days: int = 1,
        prompt_type: Optional[str] = None
    ) -> Optional[DiscordSummary]:
        """
        Generate a summary for a single channel.
        
        Args:
            channel_id: ID of the channel to summarize
            days: Number of days to look back
            prompt_type: Type of prompt to use
            
        Returns:
            DiscordSummary object if successful, None otherwise
        """
        start_time = datetime.now()
        logger.info(f"Generating summary for channel {channel_id}")
        
        try:
            # Collect messages from the channel including threads
            messages, channel_name, thread_data = await self.message_collector.collect_from_channel(channel_id, days)
            
            if not messages and not any(thread_msgs for thread_msgs, _ in thread_data):
                logger.warning(f"No messages found in channel {channel_name} or its threads for the past {days} day(s)")
                return None
            
            logger.info(f"Collected {len(messages)} messages from {channel_name} and {sum(len(t[0]) for t in thread_data)} messages from threads")
            
            # Generate summary for main channel
            main_summary = None
            if messages:
                summary_text, provider_name = await self._generate_summary_with_fallback(
                    messages=messages,
                    channel_name=channel_name,
                    prompt_type=prompt_type
                )
                
                if not summary_text:
                    logger.error(f"Failed to generate summary for {channel_name}")
                    main_summary = None
                else:
                    main_summary = summary_text
            else:
                main_summary = "No messages in main channel during this period."
                provider_name = self.summarizer.provider_name
            
            # Process thread data if available
            thread_summaries = []
            for thread_messages, thread_name in thread_data:
                if thread_messages:
                    thread_summary_text, thread_provider = await self._generate_summary_with_fallback(
                        messages=thread_messages,
                        channel_name=f"{channel_name} > {thread_name}",
                        prompt_type=prompt_type
                    )
                    
                    if thread_summary_text:
                        thread_summaries.append((thread_name, thread_summary_text))
                        if not main_summary:  # If main channel had no summary but thread does
                            provider_name = thread_provider
            
            # Combine main summary with thread summaries
            combined_summary = ""
            if main_summary:
                combined_summary = main_summary
            
            if thread_summaries:
                if combined_summary:
                    combined_summary += "\n\n## Thread Summaries\n"
                else:
                    combined_summary = "## Thread Summaries\n"
                    
                for thread_name, thread_content in thread_summaries:
                    combined_summary += f"\n### {thread_name}\n{thread_content}\n"
            
            if not combined_summary:
                logger.error(f"Failed to generate any summaries for {channel_name} or its threads")
                return None
            
            # Create summary object
            summary = self.summarizer.create_summary_object(
                content=combined_summary,
                messages=messages + [msg for thread_msgs, _ in thread_data for msg in thread_msgs],
                channel_name=channel_name,
                channel_id=channel_id,
                provider_name=provider_name
            )
                        
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Summary generated for {channel_name} in {elapsed_time:.2f} seconds")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary for channel {channel_id}: {str(e)}")
            return None


    async def _generate_summary_with_fallback(
        self, 
        messages, 
        channel_name=None,  # Parameter should match what's expected in summarizers
        prompt_type=None
    ):
        """
        Generate a summary with fallback to an alternative LLM provider if the primary one fails.
        
        Args:
            messages: List of messages to summarize
            channel_name: Name of the channel
            prompt_type: Type of prompt to use
            
        Returns:
            Tuple of (summary text, provider name) if successful, (None, None) if all providers fail
        """
        try:
            # Try with the primary summarizer
            summary_text = self.summarizer.generate_summary(
                messages=messages,
                channel_name=channel_name,  # Must match parameter name in summarizer
                prompt_type=prompt_type
            )
            
            if summary_text:
                return summary_text, self.summarizer.provider_name
                
            # If primary summarizer failed, create and try a fallback summarizer
            logger.warning("Primary summarizer failed, trying fallback...")
            
            # Determine current provider and create a fallback
            import os
            from config.settings import LLMProvider
            from summarizers import create_summarizer
            
            # If current is Anthropic, fall back to DeepSeek, and vice versa
            current_provider = self.summarizer.__class__.__name__
            
            if "Anthropic" in current_provider:
                from config.settings import LLMConfig
                fallback_config = LLMConfig(
                    provider=LLMProvider.DEEPSEEK,
                    api_key=os.getenv('DEEPSEEK_API_KEY')
                )
            else:
                from config.settings import LLMConfig
                fallback_config = LLMConfig(
                    provider=LLMProvider.ANTHROPIC,
                    api_key=os.getenv('ANTHROPIC_API_KEY')
                )
            
            # Check if we have the API key for fallback
            if not fallback_config.api_key:
                logger.error("No API key available for fallback LLM provider")
                return None, None
                
            # Create fallback summarizer
            fallback_summarizer = create_summarizer(fallback_config)
            
            # Try with fallback summarizer
            fallback_summary = fallback_summarizer.generate_summary(
                messages=messages,
                channel_name=channel_name,  # Must match parameter name in summarizer
                prompt_type=prompt_type
            )
            
            if fallback_summary:
                logger.info(f"Successfully generated summary using fallback provider {fallback_summarizer.provider_name}")
                return fallback_summary, fallback_summarizer.provider_name
                
            # If we get here, both summarizers failed
            logger.error("All summarizer providers failed")
            return None, None
            
        except Exception as e:
            logger.error(f"Error in fallback summarization: {str(e)}")
            return None, None
    
    async def generate_all_channel_summaries(self, days: int = 1) -> Dict[str, Optional[DiscordSummary]]:
        """
        Generate summaries for all configured channels.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary mapping channel IDs to summary objects
        """
        logger.info("Generating summaries for all configured channels")
        
        # Collect messages from all configured channels
        channel_messages = await self.message_collector.collect_from_config(days)
        
        results = {}
        
        # Generate a summary for each channel
        for channel_id, (messages, channel_name) in channel_messages.items():
            if not messages:
                logger.warning(f"No messages found in channel {channel_name}")
                results[channel_id] = None
                continue
            
            logger.info(f"Generating summary for {channel_name} ({len(messages)} messages)")
            
            # Determine prompt type based on channel name
            prompt_type = self._detect_prompt_type(channel_name)
            
            # Generate summary with fallback
            summary_text, provider_name = await self._generate_summary_with_fallback(
                messages=messages,
                channel_name=channel_name,
                prompt_type=prompt_type
            )
            
            if not summary_text:
                logger.error(f"Failed to generate summary for {channel_name}")
                results[channel_id] = None
                continue
            
            # Create summary object
            summary = self.summarizer.create_summary_object(
            content=summary_text,
            messages=messages,
            channel_name=channel_name,  # This needs to be changed to channel_name
            channel_id=channel_id,
            provider_name=provider_name
        )
            
            results[channel_id] = summary
        
        logger.info(f"Generated summaries for {sum(1 for s in results.values() if s)} out of {len(results)} channels")
        return results
    
    async def generate_combined_summary(self, days: int = 1) -> Optional[DiscordSummary]:
        """
        Generate a combined summary for all channels.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Combined summary object if successful, None otherwise
        """
        logger.info("Generating combined summary for all channels")
        
        # Collect messages from all configured channels
        channel_messages = await self.message_collector.collect_from_config(days)
        
        # Combine all messages
        all_messages = []
        for channel_id, (messages, _) in channel_messages.items():
            all_messages.extend(messages)
        
        if not all_messages:
            logger.warning("No messages found in any channel")
            return None
        
        # Sort messages by timestamp
        all_messages.sort(key=lambda m: m.timestamp)
        
        logger.info(f"Generating combined summary for {len(all_messages)} messages from all channels")
        
        # Generate combined summary with fallback
        summary_text, provider_name = await self._generate_summary_with_fallback(
            messages=all_messages,
            channel_name="All Channels",
            prompt_type="general"
        )
        
        if not summary_text:
            logger.error("Failed to generate combined summary")
            return None
        
        # Create summary object
        summary = self.summarizer.create_summary_object(
            content=summary_text,
            messages=all_messages,
            channel_name="All Channels",  # This needs to be changed to channel_name
            channel_id="combined",
            provider_name=provider_name
        )
        
        return summary
    
    def _detect_prompt_type(self, channel_name: str) -> Optional[str]:
        """
        Detect the appropriate prompt type based on the channel name.
        
        Args:
            channel_name: Name of the channel
            
        Returns:
            Prompt type if a match is found, None otherwise
        """
        channel_lower = channel_name.lower()
        
        if any(tech in channel_lower for tech in ['dev', 'code', 'programming', 'tech', 'engineering']):
            return 'technical'
        elif any(game in channel_lower for game in ['game', 'gaming', 'play', 'stream']):
            return 'gaming'
        
        return None