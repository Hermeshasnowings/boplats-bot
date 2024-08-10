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
            
            #get more details
            price_div = listing.find('div', class_='search-result-price')
            size_div = listing.find('div', class_='pure-u-2-5')
            room_div = listing.find('div', class_='pure-u-1-2.right-align')
            link_a = listing.find('a', class_='search-result-link')
            #more deets here please
            
            # Extract the actual link from the 'href' attribute
            link_url = link_a['href'] if link_a else 'N/A'
            
            details = (
                    f"**Address:** {listing_id}\n"
                    f"**Price:** {price_div.text.strip() if price_div else 'N/A'}\n"
                    f"**Size:** {size_div.text.strip() if size_div else 'N/A'}\n"
                    f"**Rooms:** {room_div.text.strip() if room_div else 'N/A'}\n"
                    f"**Link:** [View Listing]({link_url})\n"
                )
            
            # Send to the channel
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                    await channel.send("***New listing!***")
                    await channel.send(details)
    
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
    print('saving seen listings...')
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
