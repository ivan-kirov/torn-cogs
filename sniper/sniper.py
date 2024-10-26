import discord
from redbot.core import commands, checks
import requests
import json
import logging
import os

class ItemMonitor(commands.Cog):
    """Cog for monitoring Torn API item market values."""

    def __init__(self, bot):
        self.bot = bot
        self.market_channel_id = None  # Channel ID to send market alerts
        self.api_key = self.load_api_key()  # Load API key from file

        # Initialize item data
        self.items = self.load_item_data()
        self._market_task = self.bot.loop.create_task(self.check_market_values())

    def load_api_key(self):
        """Load the API key from a JSON file or create it if it doesn't exist."""
        file_path = '/home/minecraft/redenv/config.json'
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                config = json.load(f)
            return config.get("api_key")
        else:
            # Create a new file if it doesn't exist
            with open(file_path, 'w') as f:
                json.dump({"api_key": ""}, f)
            return ""

    def save_api_key(self, api_key):
        """Save the API key to a JSON file."""
        file_path = '/home/minecraft/redenv/config.json'
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}

        config["api_key"] = api_key

        with open(file_path, 'w') as f:
            json.dump(config, f)

    def load_item_data(self):
        """Load item data from the JSON file or create it if it doesn't exist."""
        file_path = '/home/minecraft/redenv/item_data.json'
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
            return data.get("item_ids", [])
        else:
            # Create a new file if it doesn't exist
            with open(file_path, 'w') as f:
                json.dump({"item_ids": []}, f)
            return []

    async def fetch_market_value(self, item_id):
        """Fetches the average market value and first listing price for a given item ID."""
        url = f"https://api.torn.com/v2/market/?selections=itemmarket&key={self.api_key}&id={item_id}&offset=0"
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
        """Group command for Torn API item monitoring related commands.

        Available commands:
        - !item setmarketchannel <channel>: Sets the channel to send market alerts.
        - !item setitemids <item_id1> <item_id2> ...: Sets the item IDs to monitor.
        - !item setapikey <api_key>: Sets the API key for Torn API requests.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid item command passed...')

    @item.command(name='setmarketchannel')
    @checks.is_owner()
    async def set_market_channel(self, ctx, channel: discord.TextChannel):
        """Sets the channel to send market alerts."""
        self.market_channel_id = channel.id
        await ctx.send(f"Market alerts will be sent to channel: {channel.mention}")

    @item.command(name='setitemids')
    @checks.is_owner()
    async def set_item_ids(self, ctx, *item_ids: str):
        """Sets the item IDs to monitor."""
        # Load existing data
        file_path = '/home/minecraft/redenv/item_data.json'
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
        else:
            data = {}

        # Set the item IDs
        data["item_ids"] = list(item_ids)

        # Save the data back to the file
        with open(file_path, 'w') as f:
            json.dump(data, f)

        # Update the items attribute
        self.items = data.get("item_ids", [])
        
        await ctx.send(f"Item IDs set to: {', '.join(self.items)}")

    @item.command(name='setapikey')
    @checks.is_owner()
    async def set_api_key(self, ctx, api_key: str):
        """Sets the API key for Torn API requests."""
        self.api_key = api_key
        self.save_api_key(api_key)
        await ctx.send("API key has been set successfully.")

    def cog_unload(self):
        """Cancel the background tasks when the cog is unloaded."""
        self._market_task.cancel()
