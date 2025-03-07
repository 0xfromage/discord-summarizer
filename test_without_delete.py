"""
Discord Permissions Test Script (Without Message Deletion)

This script tests if your bot has the necessary permissions to post in the destination channel.
It creates a test message and leaves it in the channel so you can verify it visually.
"""

import asyncio
import discord
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord_bot_test')

async def test_bot_posting():
    # Load .env file
    load_dotenv()
    
    # Get token and channel ID
    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    channel_id = int(os.getenv('DISCORD_DESTINATION_CHANNEL_ID'))
    
    if not bot_token:
        logger.error("No bot token found in .env file")
        return
    
    if not channel_id:
        logger.error("No destination channel ID found in .env file")
        return
    
    # Set up Discord client
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        logger.info(f"Logged in as {client.user}")
        
        try:
            # Try to get the channel
            channel = client.get_channel(channel_id)
            logger.info(f"get_channel result: {channel}")
            
            if not channel:
                try:
                    # Try fetch_channel instead
                    channel = await client.fetch_channel(channel_id)
                    logger.info(f"fetch_channel result: {channel}")
                except Exception as e:
                    logger.error(f"Failed to fetch channel {channel_id}: {str(e)}")
                    await client.close()
                    return
            
            if not channel:
                logger.error(f"Could not find channel with ID {channel_id}")
                await client.close()
                return
                
            # Create a test embed
            embed = discord.Embed(
                title="Test Message - DO NOT DELETE",
                description="This is a test message from the Discord Summary Bot. If you can see this message, the bot has permission to post in this channel.",
                color=0x00ff00
            )
            
            # Add current timestamp
            embed.timestamp = discord.utils.utcnow()
            
            # Send the message
            message = await channel.send(embed=embed)
            logger.info(f"Successfully sent message: {message.id}")
            logger.info(f"Message should now be visible in channel: {channel.name}")
            
        except Exception as e:
            logger.error(f"Error in on_ready: {str(e)}", exc_info=True)
        finally:
            # Wait a moment to ensure the message is sent before closing
            await asyncio.sleep(2)
            # Close the client after sending the test message
            await client.close()
    
    # Start the client
    try:
        await client.start(bot_token)
    except discord.errors.LoginFailure:
        logger.error("Invalid bot token - could not log in to Discord")
    except Exception as e:
        logger.error(f"Error starting Discord client: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_bot_posting())