import discord
from redbot.core import commands, checks
import requests
import json
import logging
import asyncio

class ItemMonitor(commands.Cog):
    """Cog for monitoring Torn API item market values."""

    def __init__(self, bot):
        self.bot = bot
        self.market_channel_id = None  # Channel ID to send market alerts
        self.check_interval = 21600  # Default check interval in seconds (6 hours)
        self.api_key = None  # Initialize API key
        self.items = self.load_item_data()  # Load item data from JSON
        self._market_task = self.bot.loop.create_task(self.check_market_values())

    def load_item_data(self):
        """Load item data from the JSON file."""
        try:
            with open('/home/minecraft/redenv/item_data.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading item data: {e}")
            return []

    async def fetch_market_value(self, item_id):
        """Fetches the average market value and first listing price for a given item ID."""
        url = f"https://api.torn.com/v2/market/?selections=itemmarket&key={self.api_key}&id={item_id}&offset=0"
        try:
            response = requests.get(url)
            data = response.json()
            item = data["itemmarket"]["item"]
            listings = data["itemmarket"]["listings"]
            
            item_name = item.get("name", "Unknown Item")
            average_price = item.get("average_price")
            first_listing_price = listings[0]["price"] if listings else None

            return item_name, average_price, first_listing_price

        except Exception as e:
            logging.error(f"Error fetching data for item {item_id}: {e}")
            return None, None, None

    async def check_market_values(self):
        """Checks if the first listing price for each item is below the average market value."""
        await self.bot.wait_until_ready()
        while True:
            for item_id in self.items:
                item_name, average_price, first_listing_price = await self.fetch_market_value(item_id)

                if first_listing_price is not None and average_price is not None:
                    if first_listing_price < average_price and self.market_channel_id:
                        channel = discord.utils.get(self.bot.get_all_channels(), id=self.market_channel_id)
                        if channel:
                            formatted_average_price = f"{average_price:,.2f}"
                            formatted_first_listing_price = f"{first_listing_price:,.2f}"
                            message = (
                                f"Alert: The first listing price for **{item_name}** is **${formatted_first_listing_price}**, "
                                f"which is lower than the average market price of **${formatted_average_price}**."
                            )
                            await channel.send(message)
            await asyncio.sleep(self.check_interval)  # Use the set interval in seconds

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

    @item.command(name='setcheckinterval')
    @checks.is_owner()
    async def set_check_interval(self, ctx, seconds: int):
        """Sets the check interval in seconds."""
        self.check_interval = seconds
        await ctx.send(f"Check interval has been set to {seconds} seconds.")

    @item.command(name='setapikey')
    @checks.is_owner()
    async def set_api_key(self, ctx, api_key: str):
        """Sets the API key for Torn API."""
        self.api_key = api_key
        await ctx.send("API key has been set.")

    @item.command(name='additem')
    @checks.is_owner()
    async def add_item(self, ctx, item_id: str):
        """Adds an item ID to monitor."""
        if item_id not in self.items:
            self.items.append(item_id)
            await ctx.send(f"Item ID {item_id} has been added to monitoring.")
        else:
            await ctx.send(f"Item ID {item_id} is already being monitored.")

    @item.command(name='removeitem')
    @checks.is_owner()
    async def remove_item(self, ctx, item_id: str):
        """Removes an item ID from monitoring."""
        if item_id in self.items:
            self.items.remove(item_id)
            await ctx.send(f"Item ID {item_id} has been removed from monitoring.")
        else:
            await ctx.send(f"Item ID {item_id} is not being monitored.")

    @item.command(name='listitems')
    async def list_items(self, ctx):
        """Lists all monitored item IDs."""
        if self.items:
            await ctx.send("Currently monitored item IDs: " + ", ".join(self.items))
        else:
            await ctx.send("No items are being monitored.")

    def cog_unload(self):
        """Cancel the background tasks when the cog is unloaded."""
        self._market_task.cancel()
