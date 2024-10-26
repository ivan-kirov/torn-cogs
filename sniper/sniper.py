import discord
from redbot.core import commands, checks
import requests
import json
import logging
import os
import asyncio  # Make sure to import asyncio

class ItemMonitor(commands.Cog):
    """Cog for monitoring Torn API item market values."""

    def __init__(self, bot):
        self.bot = bot
        self.market_channel_id = None  # Channel ID to send market alerts

        # Initialize item data
        self.items = self.load_item_data()
        self._market_task = self.bot.loop.create_task(self.check_market_values())

    def load_item_data(self):
        """Load item data from the JSON file or create it if it doesn't exist."""
        file_path = '/home/minecraft/redenv/item_data.json'
        
        # Check if the file exists
        if not os.path.exists(file_path):
            # Create a new file with default content
            default_data = {}
            with open(file_path, 'w') as f:
                json.dump(default_data, f)
            logging.info("item_data.json created with default content.")
        
        # Load the data from the file
        with open(file_path, 'r') as f:
            return json.load(f)

    async def fetch_market_value(self, item_id):
        """Fetches the average market value and first listing price for a given item ID."""
        url = f"https://api.torn.com/v2/market/?selections=itemmarket&key=YOUR_API_KEY&id={item_id}&offset=0"
        try:
            response = requests.get(url)
            data = response.json()
            item = data["itemmarket"]["item"]
            listings = data["itemmarket"]["listings"]
            
            average_price = item.get("average_price")
            first_listing_price = listings[0]["price"] if listings else None

            return average_price, first_listing_price

        except Exception as e:
            logging.error(f"Error fetching data for item {item_id}: {e}")
            return None, None

    async def check_market_values(self):
        """Checks if the first listing price for each item is below the average market value."""
        await self.bot.wait_until_ready()
        while True:
            for item_id in self.items:
                average_price, first_listing_price = await self.fetch_market_value(item_id)

                if first_listing_price is not None and average_price is not None:
                    if first_listing_price < average_price and self.market_channel_id:
                        channel = discord.utils.get(self.bot.get_all_channels(), id=self.market_channel_id)
                        if channel:
                            message = (
                                f"Alert: The first listing price for item ID {item_id} is {first_listing_price}, "
                                f"which is lower than the average market price of {average_price}."
                            )
                            await channel.send(message)
            await asyncio.sleep(21600)  # Run every 6 hours

    @commands.group()
    async def item(self, ctx):
        """Group command for Torn API item monitoring related commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid item command passed...')

    @item.command(name='setmarketchannel')
    @checks.is_owner()
    async def set_market_channel(self, ctx, channel: discord.TextChannel):
        """Sets the channel to send market alerts."""
        self.market_channel_id = channel.id
        await ctx.send(f"Market alerts will be sent to channel: {channel.mention}")

    def cog_unload(self):
        """Cancel the background tasks when the cog is unloaded."""
        self._market_task.cancel()
