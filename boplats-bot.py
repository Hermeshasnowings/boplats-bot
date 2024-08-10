import os
import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import asyncio
import json

# Load environment variables from .env file
load_dotenv()

# Get bot token and channel ID from environment variables
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')

if not TOKEN or not CHANNEL_ID:
    raise ValueError("Missing DISCORD_TOKEN or DISCORD_CHANNEL_ID in environment variables")

# Convert CHANNEL_ID to integer
CHANNEL_ID = int(CHANNEL_ID)

# Define intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the message content intent

# Create an instance of a bot with the specified intents
bot = commands.Bot(command_prefix='!', intents=intents)

# Boplats URL
LISTINGS_URL = "https://nya.boplats.se/sok?types=1hand&area=508A8CB4FBDC002E000345E7"

# Load seen listings from a file
def load_seen_listings():
    try:
        with open('seen_listings.json', 'r') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

# Save seen listings to a file
def save_seen_listings(seen_listings):
    with open('seen_listings.json', 'w') as f:
        json.dump(list(seen_listings), f)
        
# Seen listings
#seen_listings = set()


# Load seen listings at startup
seen_listings = load_seen_listings()


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user.name}')
    bot.loop.create_task(background_task())  # Schedule the background task

channel = bot.get_channel(CHANNEL_ID)


async def check_for_new_listings():
    response = requests.get(LISTINGS_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Adjust this to target the specific elements of the website
    listings = soup.find_all('div', class_='mob-info-container')
    print(listings)

    new_listings = []
    for listing in listings:
        #find address div and extract the text
        address_div = listing.find('div', class_='search-result-address')
        listing_id = address_div.text.strip()  # Need to use text as identifier as there is no int id
        print(listing_id)
        if listing_id and listing_id not in seen_listings:
            seen_listings.add(listing_id)
            new_listings.append(listing)
    
    # If new listings were found, send a message
    if new_listings:
        if channel:
            for listing in new_listings:
                link = listing.find('a')['href']
                await channel.send(f"New listing found: {link}")
        else:
            print(f"Channel with ID {CHANNEL_ID} not found.")
            
    save_seen_listings(seen_listings)
            
# Save seen listings before the bot shuts down
@bot.event
async def on_disconnect():
    save_seen_listings(seen_listings)

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
    bot.run(TOKEN)
