import asyncio
import logging
import signal
import sys
from typing import Dict, Any, Optional

from config.settings import load_config
from utils.logging_config import setup_logging
from clients.discord_reader import DiscordReaderClient
from clients.discord_writer import DiscordWriterClient
from summarizers import create_summarizer
from services.message_collector import MessageCollectorService
from services.summary_generator import SummaryGeneratorService
from services.summary_scheduler import SummarySchedulerService

# Global variables for shutdown handling
shutdown_event = asyncio.Event()
app_components = {}  # Store components that need to be shut down

async def initialize_components() -> Dict[str, Any]:
    """
    Initialize all application components.
    
    Returns:
        Dictionary of initialized components
    """
    # Load configuration
    config = load_config()
    
    # Configure logging
    logger = setup_logging(debug=config.debug_mode)
    logger.info("Starting Discord Summary Bot")
    
    # Initialize clients
    discord_reader = DiscordReaderClient(config.discord_reader.user_token)
    discord_writer = DiscordWriterClient(config.discord_writer.bot_token)
    
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
    Run the summary generation and posting once.
    
    Args:
        components: Dictionary of application components
    """
    logger = components['logger']
    discord_writer = components['discord_writer']
    summary_scheduler = components['summary_scheduler']
    
    logger.info("Running summary generation once")
    
    # Initialize Discord writer first
    logger.info("Initializing Discord writer for one-time run")
    try:
        await discord_writer.start()
        
        # Wait for the Discord client to be ready
        await discord_writer.wait_until_ready()
        logger.info("Discord writer ready, generating summary")
        
        # Run summary generation
        await summary_scheduler.run_now()
        
        # Give Discord operations time to complete
        logger.info("Waiting for Discord operations to complete...")
        await asyncio.sleep(10)  # Wait 10 seconds to ensure message posting completes
        
        logger.info("One-time summary generation completed")
    except Exception as e:
        logger.error(f"Error in run_once: {e}")

async def run_scheduled(components: Dict[str, Any]) -> None:
    """
    Run the summary generation and posting on a schedule.
    
    Args:
        components: Dictionary of application components
    """
    logger = components['logger']
    discord_writer = components['discord_writer']
    summary_scheduler = components['summary_scheduler']
    config = components['config']
    
    logger.info("Starting Discord writer client")
    
    # Set up ready callback
    async def on_ready():
        logger.info("Discord writer client ready, starting scheduler")
        await summary_scheduler.start()
        
        # Run once immediately if in debug mode
        if config.debug_mode:
            logger.info("Debug mode enabled, running summary generation immediately")
            asyncio.create_task(summary_scheduler.run_now())
    
    # Add ready callback and start discord client
    discord_writer.add_on_ready_callback(on_ready)
    
    # Wait for shutdown signal
    try:
        await discord_writer.start()
    except Exception as e:
        logger.error(f"Error starting Discord writer client: {e}")
        shutdown_event.set()

def setup_signal_handlers() -> None:
    """
    Set up signal handlers for graceful shutdown.
    """
    try:
        loop = asyncio.get_running_loop()
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
    except NotImplementedError:
        # Windows doesn't support add_signal_handler
        pass
    except Exception as e:
        print(f"Failed to set up signal handlers: {e}")

async def shutdown() -> None:
    """
    Perform graceful shutdown of all components.
    """
    logger = app_components.get('logger', logging.getLogger())
    logger.info("Shutting down...")
    
    # Stop scheduler
    scheduler = app_components.get('summary_scheduler')
    if scheduler:
        await scheduler.stop()
    
    # Set shutdown event
    shutdown_event.set()
    logger.info("Shutdown complete")

async def main() -> None:
    """
    Main application entry point.
    """
    global app_components
    
    try:
        # Initialize components
        app_components = await initialize_components()
        logger = app_components['logger']
        
        # Set up signal handlers
        setup_signal_handlers()
        
        # Parse command line arguments
        run_once_flag = '--run-once' in sys.argv
        
        # Run either once or scheduled
        if run_once_flag:
            await run_once(app_components)
        else:
            await run_scheduled(app_components)
            
            # Wait for shutdown event
            await shutdown_event.wait()
    
    except Exception as e:
        try:
            logger = app_components.get('logger', logging.getLogger())
            logger.error(f"Unhandled exception: {e}", exc_info=True)
        except:
            print(f"Fatal error: {e}")
        
        # Ensure clean shutdown
        if not shutdown_event.is_set():
            await shutdown()

if __name__ == "__main__":
    asyncio.run(main())