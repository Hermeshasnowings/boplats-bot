import discord
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

#Bot token from discord
TOKEN = 'token.env'

#init client
discord.Client()

#boplats scrape

_URL = "https://nya.boplats.se/sok"

#seen listings

seen_listings = set()

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    
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
        channel = client.get_channel(chan.env)
        for listing in new_listings:
            await channel.send(f"New listing found: {listing.find('a').get('href')}")

@client.event
async def on_message(message):
    if message.content.startswith('!check'):
        await check_for_new_listings()

# Schedule the bot to periodically check for new listings
import asyncio

async def background_task():
    await client.wait_until_ready()
    while not client.is_closed():
        await check_for_new_listings()
        await asyncio.sleep(60 * 10)  # Check every 10 minutes

client.loop.create_task(background_task())
client.run(TOKEN)