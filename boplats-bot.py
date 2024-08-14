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

channel = bot.get_channel(CHANNEL_ID)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user.name}')
    bot.loop.create_task(background_task())  # Schedule the background task
    await language_select();


async def check_for_new_listings():
    response = requests.get(LISTINGS_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Adjust this to target the specific elements of the website
    listings = soup.find_all('div', class_='search-result-item')
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
            area_div = listing.find('div', class_='search-result-area-name')
            price_div = listing.find('div', class_='search-result-price')
            size_div = listing.find('div', class_='pure-u-2-5')
            room_div = listing.find('div', {'class': lambda x: x and 'pure-u-1-2' in x})
            publ_div = listing.find('div', class_='publ-date')
            img_tag = listing.find('img')
            
            # Extract image URL
            img_url = img_tag['src'] if img_tag else 'N/A'  # Use 'src' to get the image URL
            
            # create the embed
            embed = discord.Embed(
                title=area_div.text.strip() if area_div else 'N/A',  # Area
                description=listing_id,  # Description of the listing
                color=discord.Color.blue()  # You can set a color for the embed
            )
            
            #embed details                
            embed.add_field(name="Price", value=price_div.text.strip() if price_div else 'N/A', inline=False)
            embed.add_field(name="Rooms", value=room_div.text.strip() if room_div else 'N/A', inline=False)
            embed.add_field(name="Size", value=size_div.text.strip() if size_div else 'N/A', inline=False)
            embed.add_field(name="Published", value=publ_div.text.strip() if publ_div else 'N/A', inline=False)
            link = listing.find('a')['href']
            embed.add_field(name="Link", value=link, inline=False)
            
            #embed image
            embed.set_image(url=img_tag['src']),
            
            # Send to the channel
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                    await channel.send("***New listing!***")
                    await channel.send(embed=embed)
    
    # If new listings were found, send a message
    if new_listings:
        if channel:
            for listing in new_listings:
                link = listing.find('a')['href']
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
        
async def language_select():
    channel = bot.get_channel(CHANNEL_ID)
    message = await channel.send("Please Select a Language:")

    flag_se = "🇸🇪"  # Sweden Flag Unicode Emoji
    flag_gb = "🇬🇧"  # United Kingdom Flag Unicode Emoji

    await message.add_reaction(flag_se) # send se flag emoji
    await message.add_reaction(flag_gb) # send gb flag emoji
    
    #wait for reaction

    reaction = await bot.wait_for("reaction_add")  # Wait for a reaction
    await channel.send(f"Language set to: {reaction[0]}")  # [0] only display the emoji
    print(reaction[0])
    choice = str(reaction[0])
    
    #if flag is gb proceed in english, else swedish
    
    if choice == "'🇬🇧'" or choice == ":flag_gb:":
        await channel.send("Language set to English")
        language = "en"
        with open('language.json', 'w') as f:
            json.dump(language, f)
    elif choice == "🇸🇪" or  choice == ":flag_se:":
        await channel.send("Språk satt till Svenska")
        language = "'se'"
        with open('language.json', 'w') as f:
            json.dump(language, f)
            

        

if __name__ == "__main__":
    bot.run(TOKEN)
