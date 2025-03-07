"""
Summary Scheduler Service

This service manages the scheduling of summary generation and posting.
It coordinates all components to run on a schedule or on-demand.
"""

import logging
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.settings import AppConfig, SchedulerConfig
from services.summary_generator import SummaryGeneratorService
from clients.discord_writer import DiscordWriterClient

logger = logging.getLogger(__name__)

class SummarySchedulerService:
    """
    Service for scheduling summary generation and posting.
    """
    
    def __init__(
        self, 
        config: SchedulerConfig,
        summary_generator: SummaryGeneratorService,
        discord_writer: DiscordWriterClient,
        destination_channel_id: int
    ):
        """
        Initialize the scheduler service.
        
        Args:
            config: Scheduler configuration
            summary_generator: Service for generating summaries
            discord_writer: Client for posting to Discord
            destination_channel_id: ID of the destination channel
        """
        self.config = config
        self.summary_generator = summary_generator
        self.discord_writer = discord_writer
        self.destination_channel_id = destination_channel_id
        
        # Initialize scheduler
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    async def start(self) -> None:
        """
        Start the scheduler.
        """
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Add scheduled job
        self.scheduler.add_job(
            self.generate_and_post_summaries,
            'cron',
            hour=self.config.summary_hour,
            minute=self.config.summary_minute
        )
        
        logger.info(
            f"Scheduled daily summary at {self.config.summary_hour:02d}:{self.config.summary_minute:02d}"
        )
        
        # Start the scheduler
        self.scheduler.start()
        self.is_running = True
    
    async def stop(self) -> None:
        """
        Stop the scheduler.
        """
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        # Shut down the scheduler
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Scheduler stopped")
    
    async def generate_and_post_summaries(self) -> None:
        """
        Generate and post summaries for all configured channels.
        """
        try:
            logger.info("Starting scheduled summary generation")
            start_time = datetime.now()
            
            # Generate summaries for all channels
            channel_summaries = await self.summary_generator.generate_all_channel_summaries(
                days=self.config.days_to_collect
            )
            
            # Post each channel summary
            for channel_id, summary in channel_summaries.items():
                if summary:
                    await self.discord_writer.post_summary(
                        channel_id=self.destination_channel_id,
                        summary=summary
                    )
                    # Add a small delay between posts
                    await asyncio.sleep(1)
            
            # Generate and post combined summary if there are multiple channels
            if len(channel_summaries) > 1:
                combined_summary = await self.summary_generator.generate_combined_summary(
                    days=self.config.days_to_collect
                )
                
                if combined_summary:
                    await self.discord_writer.post_summary(
                        channel_id=self.destination_channel_id,
                        summary=combined_summary
                    )
            
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Completed scheduled summary generation in {elapsed_time:.2f} seconds")
            
        except Exception as e:
            error_message = f"Error in scheduled summary generation: {str(e)}"
            logger.error(error_message)
            
            # Post error message to Discord
            await self.discord_writer.post_error(
                channel_id=self.destination_channel_id,
                error_message=error_message
            )
    
    async def run_now(self) -> None:
        """
        Run the summary generation and posting immediately.
        """
        logger.info("Manually triggering summary generation")
        await self.generate_and_post_summaries()