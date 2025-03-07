"""
Discord Explorer Utility

This utility allows users to explore their Discord servers and channels
to find the IDs needed for configuration.
"""

import os
import sys
import requests
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

def get_headers(user_token: str) -> Dict[str, str]:
    """
    Create headers for Discord API requests.
    
    Args:
        user_token: Discord user token
        
    Returns:
        Headers dictionary
    """
    return {
        "Authorization": user_token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
    }

def make_request(endpoint: str, headers: Dict[str, str]) -> Optional[Any]:
    """
    Make a request to the Discord API.
    
    Args:
        endpoint: API endpoint
        headers: Request headers
        
    Returns:
        Response data if successful, None otherwise
    """
    base_url = "https://discord.com/api/v9"
    url = f"{base_url}{endpoint}"
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            return None
        
        return response.json()
    
    except Exception as e:
        print(f"Request error: {e}")
        return None

def list_guilds(headers: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    List all guilds (servers) the user is in.
    
    Args:
        headers: Request headers
        
    Returns:
        List of guild objects
    """
    return make_request("/users/@me/guilds", headers) or []

def list_channels(guild_id: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    List all channels in a guild.
    
    Args:
        guild_id: ID of the guild
        headers: Request headers
        
    Returns:
        List of channel objects
    """
    return make_request(f"/guilds/{guild_id}/channels", headers) or []

def explore_discord_servers() -> None:
    """
    Interactive utility to explore Discord servers and channels.
    """
    # Load environment variables
    load_dotenv()
    
    # Get Discord user token
    user_token = os.getenv('DISCORD_USER_TOKEN')
    if not user_token:
        user_token = input("Enter your Discord user token: ").strip()
        
        if not user_token:
            print("No token provided. Exiting.")
            return
    
    headers = get_headers(user_token)
    
    # Get list of guilds
    print("Fetching your Discord servers...")
    guilds = list_guilds(headers)
    
    if not guilds:
        print("Error fetching servers or no servers found.")
        return
    
    print("\n=== YOUR DISCORD SERVERS ===")
    print("ID | Name")
    print("-" * 50)
    
    for i, guild in enumerate(guilds):
        guild_id = guild.get("id", "Unknown")
        guild_name = guild.get("name", "Unknown")
        print(f"{i+1}. {guild_id} | {guild_name}")
    
    # Ask which guild to explore
    selection = input("\nEnter the number of the server to explore (or press Enter to exit): ").strip()
    
    if not selection.isdigit() or int(selection) < 1 or int(selection) > len(guilds):
        print("Invalid selection or exiting.")
        return
    
    selected_guild = guilds[int(selection) - 1]
    guild_id = selected_guild.get("id")
    guild_name = selected_guild.get("name")
    
    print(f"\nExploring server: {guild_name} ({guild_id})")
    
    # Get channels for the selected guild
    print("Fetching channels...")
    channels = list_channels(guild_id, headers)
    
    if not channels:
        print("Error fetching channels or no channels found.")
        return
    
    # Create a map of category IDs to names
    categories = {c["id"]: c["name"] for c in channels if c.get("type") == 4}  # 4 = CATEGORY
    
    # Filter and display text channels
    text_channels = [c for c in channels if c.get("type") == 0]  # 0 = TEXT channel
    voice_channels = [c for c in channels if c.get("type") == 2]  # 2 = VOICE channel
    
    if text_channels:
        print("\n=== TEXT CHANNELS ===")
        print("ID | Name | Category")
        print("-" * 50)
        
        for i, channel in enumerate(text_channels):
            channel_id = channel.get("id", "Unknown")
            channel_name = channel.get("name", "Unknown")
            category_id = channel.get("parent_id")
            category_name = categories.get(category_id, "None") if category_id else "None"
            
            print(f"{i+1}. {channel_id} | {channel_name} | {category_name}")
    
    if voice_channels:
        print("\n=== VOICE CHANNELS ===")
        print("ID | Name | Category")
        print("-" * 50)
        
        for i, channel in enumerate(voice_channels):
            channel_id = channel.get("id", "Unknown")
            channel_name = channel.get("name", "Unknown")
            category_id = channel.get("parent_id")
            category_name = categories.get(category_id, "None") if category_id else "None"
            
            print(f"{i+1}. {channel_id} | {channel_name} | {category_name}")
    
    # Prompt for .env configuration
    print("\n=== CONFIGURATION ===")
    print("Add the following to your .env file:")
    print(f"DISCORD_SOURCE_GUILD_ID={guild_id}")
    print("To monitor specific channels, add their IDs:")
    print("DISCORD_SOURCE_CHANNEL_IDS=CHANNEL_ID_1,CHANNEL_ID_2,...")
    print("Or leave DISCORD_SOURCE_CHANNEL_IDS empty to monitor all text channels in the guild")

if __name__ == "__main__":
    explore_discord_servers()