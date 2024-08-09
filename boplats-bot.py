import os
import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import asyncio

# Load environment variables from .env file
load_dotenv()

# Bot token and channel ID from .env file
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))

# Define intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the message content intent (necessary to read message contents)

# Create an instance of a bot with the specified intents
bot = commands.Bot(command_prefix='!', intents=intents)

# Boplats URL
LISTINGS_URL = "https://nya.boplats.se/sok"

# Seen listings
seen_listings = set()

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    bot.loop.create_task(background_task())  # Schedule the background task

async def check_for_new_listings():
    response = requests.get(LISTINGS_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Adjust this to target the specific elements of the website
    listings = soup.find_all('div', class_='listing-item')

    new_listings = []
    for listing in listings:
        listing_id = listing['data-id']  # Example of how you might identify a unique listing
        if listing_id not in seen_listings:
            seen_listings.add(listing_id)
            new_listings.append(listing)
    
    # If new listings were found, send a message
    if new_listings:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            for listing in new_listings:
                await channel.send(f"New listing found: {listing.find('a').get('href')}")
        else:
            print(f"Channel with ID {CHANNEL_ID} not found.")

@bot.event
async def on_message(message):
    if message.content.startswith('!check'):
        await check_for_new_listings()

# Schedule the bot to periodically check for new listings
async def background_task():
    await bot.wait_until_ready()
    while not bot.is_closed():
        await check_for_new_listings()
        await asyncio.sleep(60 * 10)  # Check every 10 minutes

if __name__ == "__main__":
    asyncio.run(bot.start(TOKEN))
