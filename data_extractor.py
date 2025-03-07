"""
Discord Data Extractor

This standalone script extracts message data from Discord channels
and saves it locally for offline testing and prompt development.
"""

import os
import json
import asyncio
import logging
from datetime import datetime
import pickle
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("discord_data_extractor")

# Import from the main project
from config.settings import load_config
from clients.discord_reader import DiscordReaderClient
from models.message import DiscordMessage

# Directory for storing extracted data
DATA_DIR = "extracted_data"
PICKLE_FILE = os.path.join(DATA_DIR, "discord_messages.pkl")
JSON_FILE = os.path.join(DATA_DIR, "discord_messages.json")

async def extract_messages(days: int = 4):
    """
    Extract messages from Discord channels and save them locally.
    
    Args:
        days: Number of days of history to extract
    """
    logger.info(f"Starting Discord message extraction (past {days} days)")
    
    # Load configuration
    config = load_config()
    
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Initialize Discord reader client
    discord_reader = DiscordReaderClient(config.discord_reader.user_token)
    
    # Store all extracted data
    all_data = {}
    
    # Check if we have specific channel IDs configured
    channel_ids = config.discord_reader.channel_ids
    
    if not channel_ids and config.discord_reader.guild_id:
        # Get all channels in the guild
        logger.info(f"Getting all channels in guild {config.discord_reader.guild_id}")
        guild_channels = discord_reader.get_guild_channels(config.discord_reader.guild_id)
        
        # Filter for text channels (type 0)
        channel_ids = [channel['id'] for channel in guild_channels if channel.get('type') == 0]
        logger.info(f"Found {len(channel_ids)} text channels in guild")
    
    # Extract messages from each channel
    for channel_id in channel_ids:
        logger.info(f"Collecting messages from channel {channel_id} for the past {days} day(s)")
        
        # Get channel info
        channel_info = discord_reader.get_channel_info(channel_id)
        channel_name = channel_info.get('name', f"Channel {channel_id}") if channel_info else f"Channel {channel_id}"
        
        # Collect messages
        messages, _ = discord_reader.collect_messages(channel_id, days=days)
        
        logger.info(f"Collected {len(messages)} messages from {channel_name}")
        
        # Store messages for this channel
        all_data[channel_id] = {
            "channel_name": channel_name,
            "messages": [message.__dict__ for message in messages]  # Convert to dict for serialization
        }
        
        # Add a small delay to avoid rate limiting
        await asyncio.sleep(1)
    
    # Save data in pickle format (preserves DiscordMessage objects)
    with open(PICKLE_FILE, 'wb') as f:
        pickle.dump(all_data, f)
    
    # Save data in JSON format (for human readability)
    json_data = {}
    for channel_id, channel_data in all_data.items():
        # Convert datetime objects to ISO format strings for JSON serialization
        json_data[channel_id] = {
            "channel_name": channel_data["channel_name"],
            "messages": []
        }
        
        for msg_dict in channel_data["messages"]:
            msg_copy = msg_dict.copy()
            # Convert datetime to string
            if isinstance(msg_copy.get('timestamp'), datetime):
                msg_copy['timestamp'] = msg_copy['timestamp'].isoformat()
            json_data[channel_id]["messages"].append(msg_copy)
    
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Successfully extracted and saved data from {len(all_data)} channels")
    logger.info(f"Data saved to {PICKLE_FILE} (for program use) and {JSON_FILE} (for review)")

    # Print summary of extracted data
    print("\nExtraction Summary:")
    print("-------------------")
    total_messages = sum(len(data["messages"]) for data in all_data.values())
    print(f"Total channels: {len(all_data)}")
    print(f"Total messages: {total_messages}")
    print("\nChannel breakdown:")
    for channel_id, data in all_data.items():
        print(f"- {data['channel_name']}: {len(data['messages'])} messages")

if __name__ == "__main__":
    # Default to 4 days of history
    days = 4
    
    # Check if days argument is provided
    import sys
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        days = int(sys.argv[1])
    
    # Run the extraction
    asyncio.run(extract_messages(days))