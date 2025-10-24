"""
Test Bot Connection - Local Utility
Quick test to verify bot can connect
"""

import asyncio
import os
from pathlib import Path
import sys

# Add bot directory to path
bot_dir = Path(__file__).parent.parent / "bot"
sys.path.insert(0, str(bot_dir))

from dotenv import load_dotenv
load_dotenv(bot_dir / ".env")

async def test_connection():
    """Test bot connection"""
    import discord
    
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ No DISCORD_TOKEN in .env")
        return False
    
    print("🔄 Testing Discord connection...")
    
    try:
        intents = discord.Intents.default()
        client = discord.Client(intents=intents)
        
        @client.event
        async def on_ready():
            print(f"✅ Connected as {client.user}")
            print(f"📊 Serving {len(client.guilds)} servers")
            await client.close()
        
        await client.start(token)
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)