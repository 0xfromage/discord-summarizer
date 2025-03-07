"""
Prompt Tester

This script allows testing different prompts with the extracted Discord data
without making any API calls to Discord. It uses the local data and only
makes LLM API calls to test your prompts.
"""

import os
import asyncio
import logging
import argparse
from datetime import datetime
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("prompt_tester")

# Import from the main project
from config.settings import load_config
from summarizers import create_summarizer
from clients.dummy_discord_reader import DummyDiscordReaderClient
from services.message_collector import MessageCollectorService
from services.summary_generator import SummaryGeneratorService
from models.message import DiscordMessage

# Directory for storing test results
RESULTS_DIR = "prompt_test_results"

async def test_prompts(channel_id: Optional[str] = None, prompt_type: Optional[str] = None, days: int = 4):
    """
    Test prompts with the extracted Discord data.
    
    Args:
        channel_id: Specific channel ID to test, or None for all channels
        prompt_type: Type of prompt to use (e.g., 'defi', 'crypto')
        days: Number of days of history to use (not actually used in dummy mode)
    """
    logger.info("Starting prompt testing with local data")
    
    # Ensure results directory exists
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Load configuration
    config = load_config()
    
    # Initialize components with dummy reader
    dummy_reader = DummyDiscordReaderClient()
    summarizer = create_summarizer(config.llm)
    message_collector = MessageCollectorService(dummy_reader, config.discord_reader)
    summary_generator = SummaryGeneratorService(message_collector, summarizer)
    
    # Create timestamp for result files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Test mode - single channel or all channels
    if channel_id:
        await test_single_channel(channel_id, prompt_type, summary_generator, timestamp)
    else:
        await test_all_channels(prompt_type, summary_generator, timestamp)
    
    # Test combined summary
    await test_combined_summary(prompt_type, summary_generator, timestamp)
    
    logger.info("Prompt testing completed. Results saved to the 'prompt_test_results' directory.")

async def test_single_channel(channel_id: str, prompt_type: Optional[str], summary_generator, timestamp: str):
    """
    Test prompts on a single channel.
    
    Args:
        channel_id: Channel ID to test
        prompt_type: Prompt type to use
        summary_generator: SummaryGeneratorService instance
        timestamp: Timestamp for result files
    """
    logger.info(f"Testing prompts on channel {channel_id}")
    
    # Generate summary for this channel
    summary = await summary_generator.generate_channel_summary(
        channel_id=channel_id,
        days=1,  # Not used in dummy mode
        prompt_type=prompt_type
    )
    
    if summary:
        # Save the result
        filename = f"{timestamp}_channel_{summary.channel_name.replace(' ', '_')}{'_' + prompt_type if prompt_type else ''}.md"
        filepath = os.path.join(RESULTS_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Summary for {summary.channel_name}\n\n")
            f.write(f"Generated using prompt type: {prompt_type or 'auto-detected'}\n\n")
            f.write(f"Provider: {summary.provider_name}\n\n")
            f.write(f"Message count: {summary.message_count}\n\n")
            f.write("## Summary Content\n\n")
            f.write(summary.content)
        
        logger.info(f"Saved channel summary to {filepath}")
    else:
        logger.error(f"Failed to generate summary for channel {channel_id}")

async def test_all_channels(prompt_type: Optional[str], summary_generator, timestamp: str):
    """
    Test prompts on all available channels.
    
    Args:
        prompt_type: Prompt type to use
        summary_generator: SummaryGeneratorService instance
        timestamp: Timestamp for result files
    """
    logger.info("Testing prompts on all channels")
    
    # Get all channel summaries
    channel_summaries = await summary_generator.generate_all_channel_summaries(days=1)  # Days not used in dummy mode
    
    for channel_id, summary in channel_summaries.items():
        if summary:
            # Save the result
            filename = f"{timestamp}_channel_{summary.channel_name.replace(' ', '_')}{'_' + prompt_type if prompt_type else ''}.md"
            filepath = os.path.join(RESULTS_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Summary for {summary.channel_name}\n\n")
                f.write(f"Generated using prompt type: {prompt_type or 'auto-detected'}\n\n")
                f.write(f"Provider: {summary.provider_name}\n\n")
                f.write(f"Message count: {summary.message_count}\n\n")
                f.write("## Summary Content\n\n")
                f.write(summary.content)
            
            logger.info(f"Saved channel summary to {filepath}")
        else:
            logger.error(f"Failed to generate summary for channel {channel_id}")

async def test_combined_summary(prompt_type: Optional[str], summary_generator, timestamp: str):
    """
    Test the combined summary.
    
    Args:
        prompt_type: Prompt type to use
        summary_generator: SummaryGeneratorService instance
        timestamp: Timestamp for result files
    """
    logger.info("Testing combined summary")
    
    # Generate combined summary
    combined_summary = await summary_generator.generate_combined_summary(days=1)  # Days not used in dummy mode
    
    if combined_summary:
        # Save the result
        filename = f"{timestamp}_combined_summary{'_' + prompt_type if prompt_type else ''}.md"
        filepath = os.path.join(RESULTS_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Combined Summary for All Channels\n\n")
            f.write(f"Generated using prompt type: {prompt_type or 'auto-detected'}\n\n")
            f.write(f"Provider: {combined_summary.provider_name}\n\n")
            f.write(f"Total message count: {combined_summary.message_count}\n\n")
            f.write("## Summary Content\n\n")
            f.write(combined_summary.content)
        
        logger.info(f"Saved combined summary to {filepath}")
    else:
        logger.error("Failed to generate combined summary")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test prompts with extracted Discord data")
    parser.add_argument("--channel", "-c", help="Specific channel ID to test")
    parser.add_argument("--prompt", "-p", help="Prompt type to use (e.g., 'defi', 'crypto')")
    parser.add_argument("--days", "-d", type=int, default=4, help="Number of days of history to use")
    
    args = parser.parse_args()
    
    # Run the tests
    asyncio.run(test_prompts(args.channel, args.prompt, args.days))