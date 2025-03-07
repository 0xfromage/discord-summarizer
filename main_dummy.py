"""
Discord Summary Bot (Dummy Mode)

This is an alternative entry point that uses locally stored data
instead of connecting to Discord API.
"""

import asyncio
import logging
import sys
from typing import Dict, Any, Optional

from config.settings import load_config
from utils.logging_config import setup_logging
from clients.dummy_discord_reader import DummyDiscordReaderClient  # Use dummy client
from clients.discord_writer import DiscordWriterClient
from summarizers import create_summarizer
from services.message_collector import MessageCollectorService
from services.summary_generator import SummaryGeneratorService
from services.summary_scheduler import SummarySchedulerService

# Set to True to actually post to Discord, False for test only (no Discord posting)
POST_TO_DISCORD = True

logger = logging.getLogger(__name__)

async def initialize_components() -> Dict[str, Any]:
    """
    Initialize all application components with dummy Discord reader.
    
    Returns:
        Dictionary of initialized components
    """
    # Load configuration
    config = load_config()
    
    # Configure logging
    logger = setup_logging(debug=config.debug_mode)
    logger.info("Starting Discord Summary Bot (DUMMY MODE)")
    
    # Initialize clients - use dummy client for reading
    discord_reader = DummyDiscordReaderClient(config.discord_reader.user_token)
    
    if POST_TO_DISCORD:
        # Initialize real Discord writer if posting enabled
        discord_writer = DiscordWriterClient(config.discord_writer.bot_token)
    else:
        
        # Use a dummy writer that just logs instead of posting
        class DummyWriter:
            async def start(self):
                logger.info("Dummy Discord writer started")
                self.is_ready = True
                self.ready_event = asyncio.Event()
                self.ready_event.set()
            
            async def wait_until_ready(self):
                logger.info("Dummy Discord writer ready")
            
            async def post_summary(self, channel_id, summary):
                logger.info(f"DUMMY: Would post summary to channel {channel_id}")
                logger.info(f"Summary title: {summary.title}")
                logger.info(f"Content length: {len(summary.content)} characters")
                return True
            
            # Add this method
            async def post_error(self, channel_id, error_message, title="Error"):
                logger.info(f"DUMMY: Would post error to channel {channel_id}")
                logger.info(f"Error title: {title}")
                logger.info(f"Error message: {error_message}")
                return True
        
        discord_writer = DummyWriter()
        
    # Initialize summarizer
    summarizer = create_summarizer(config.llm)
    
    # Initialize services
    message_collector = MessageCollectorService(discord_reader, config.discord_reader)
    summary_generator = SummaryGeneratorService(message_collector, summarizer)
    summary_scheduler = SummarySchedulerService(
        config=config.scheduler,
        summary_generator=summary_generator,
        discord_writer=discord_writer,
        destination_channel_id=config.discord_writer.destination_channel_id
    )
    
    # Store components
    components = {
        'config': config,
        'logger': logger,
        'discord_reader': discord_reader,
        'discord_writer': discord_writer,
        'summarizer': summarizer,
        'message_collector': message_collector,
        'summary_generator': summary_generator,
        'summary_scheduler': summary_scheduler
    }
    
    return components

async def run_once(components: Dict[str, Any]) -> None:
    """
    Run the summary generation once.
    
    Args:
        components: Dictionary of application components
    """
    logger = components['logger']
    discord_writer = components['discord_writer']
    summary_scheduler = components['summary_scheduler']
    
    logger.info("Running summary generation once (DUMMY MODE)")
    
    # Only log in but don't start the full client (non-blocking)
    if hasattr(discord_writer, 'client'):  # Check if real client
        await discord_writer.client.login(discord_writer.token)
        discord_writer.is_ready = True
        discord_writer.ready_event.set()
    else:
        # Handle dummy writer
        await discord_writer.start()
    
    await discord_writer.wait_until_ready()
    
    # Generate and post summaries
    await summary_scheduler.run_now()
    
    # Allow time for API calls to complete
    await asyncio.sleep(5)
    
    logger.info("One-time summary generation completed (DUMMY MODE)")
async def main() -> None:
    """
    Main application entry point for dummy mode.
    """
    try:
        # Initialize components
        components = await initialize_components()
        logger = components['logger']
        
        # Run once
        await run_once(components)
        
    except Exception as e:
        logger = logging.getLogger()
        logger.error(f"Unhandled exception: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())