import discord
from redbot.core import commands, checks
import requests
import json
import logging
import os
import asyncio

class ItemMonitor(commands.Cog):
    """Cog for monitoring Torn API item market values."""

    def __init__(self, bot):
        self.bot = bot
        self.market_channel_id = None  # Channel ID to send market alerts
        self.items = self.load_item_data() or []  # Initialize item data
        self.check_interval = 5  # Default check interval set to 6 hours (21600 seconds)
        self.api_key = None  # API key placeholder

        # Set up logging
        self.log_file_path = 'torn_item_monitor.log'
        self.setup_logging()

        # Start the market checking task
        self._market_task = self.bot.loop.create_task(self.check_market_values())

    def setup_logging(self):
        """Sets up the logging configuration."""
        logging.basicConfig(
            filename=self.log_file_path,
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s'
        )
        logging.info("ItemMonitor initialized.")

    def load_item_data(self):
        """Load item data from the JSON file."""
        try:
            with open('/home/minecraft/redenv/item_data.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error("item_data.json file not found. Starting with an empty item list.")
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

            logging.info(f"Fetched data for item {item_id}: avg_price={average_price}, first_listing_price={first_listing_price}")
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
                            item_name = await self.get_item_name(item_id)  # Fetch the item name
                            message = (
                                f"Alert: The first listing price for **{item_name}** (ID: {item_id}) is **{first_listing_price:,}**, "
                                f"which is lower than the average market price of **{average_price:,}**."
                            )
                            await channel.send(message)
                            logging.info(f"Alert sent for item {item_id}: {message}")
            await asyncio.sleep(self.check_interval)  # Use the configured check interval

    async def get_item_name(self, item_id):
        """Fetch the item name for a given item ID."""
        # This would be replaced by an actual API call or a lookup method
        return f"Item Name for ID {item_id}"  # Placeholder for item name

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
        logging.info(f"Market channel set to: {channel.mention}")

    @item.command(name='setapi')
    @checks.is_owner()
    async def set_api(self, ctx, api_key: str):
        """Sets the Torn API key."""
        self.api_key = api_key
        await ctx.send("API key has been set.")
        logging.info("API key has been set.")

    @item.command(name='additem')
    @checks.is_owner()
    async def add_item(self, ctx, item_id: str):
        """Adds an item ID to monitor."""
        logging.info(f"Trying to add item ID: {item_id}")

        if item_id not in self.items:
            self.items.append(item_id)
            await ctx.send(f"Item ID **{item_id}** has been added to monitoring.")
            logging.info(f"Item ID {item_id} added. New monitored items: {self.items}")
        else:
            await ctx.send(f"Item ID **{item_id}** is already being monitored.")

    @item.command(name='removeitem')
    @checks.is_owner()
    async def remove_item(self, ctx, item_id: str):
        """Removes an item ID from monitoring."""
        logging.info(f"Trying to remove item ID: {item_id}")

        if item_id in self.items:
            self.items.remove(item_id)
            await ctx.send(f"Item ID **{item_id}** has been removed from monitoring.")
            logging.info(f"Item ID {item_id} removed. Remaining monitored items: {self.items}")
        else:
            await ctx.send(f"Item ID **{item_id}** is not being monitored.")

    @item.command(name='listitems')
    async def list_items(self, ctx):
        """Lists all monitored item IDs."""
         if self.items:
            item_ids = list(self.items.keys())
            logger.info(f"Currently monitoring item IDs: {item_ids}")
            await ctx.send(f"Currently monitoring the following item IDs: {', '.join(item_ids)}")
        else:
            await ctx.send("No items are being monitored.")

    @item.command(name='setcheckinterval')
    @checks.is_owner()
    async def set_check_interval(self, ctx, interval: int):
        """Sets the check interval in seconds."""
        self.check_interval = interval
        await ctx.send(f"Check interval set to **{interval} seconds**.")
        logging.info(f"Check interval set to {interval} seconds.")

    def cog_unload(self):
        """Cancel the background tasks when the cog is unloaded."""
        self._market_task.cancel()
        logging.info("ItemMonitor cog unloaded.")
