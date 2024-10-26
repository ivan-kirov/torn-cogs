import discord
from redbot.core import commands, checks
import requests
import json
import logging
import asyncio
import locale

class ItemMonitor(commands.Cog):
    """Cog for monitoring Torn API item market values."""

    def __init__(self, bot):
        self.bot = bot
        self.market_channel_id = None  # Channel ID to send market alerts
        self.check_interval = 21600  # Default to 6 hours in seconds

        # Set locale for number formatting
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

        # Initialize item data
        self.items = self.load_item_data()
        self._market_task = self.bot.loop.create_task(self.check_market_values())

    def load_item_data(self):
        """Load item data from the JSON file."""
        try:
            with open('/home/minecraft/redenv/item_data.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Failed to load item data: {e}")
            return []

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
                    # Format the prices for readability
                    formatted_first_listing_price = locale.format_string("%d", first_listing_price, grouping=True)
                    formatted_average_price = locale.format_string("%d", average_price, grouping=True)

                    if first_listing_price < average_price and self.market_channel_id:
                        channel = discord.utils.get(self.bot.get_all_channels(), id=self.market_channel_id)
                        if channel:
                            message = (
                                f"Alert: The first listing price for item ID {item_id} is **${formatted_first_listing_price}**, "
                                f"which is lower than the average market price of **${formatted_average_price}**."
                                f"To withdraw money please click here https://www.torn.com/properties.php#/p=options&tab=vault"
                            )
                            await channel.send(message)
            await asyncio.sleep(self.check_interval)  # Use the configured interval

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

    @item.command(name='setinterval')
    @checks.is_owner()
    async def set_check_interval(self, ctx, hours: int):
        """Sets the interval for checking market values in hours."""
        if hours <= 0:
            await ctx.send("Please enter a positive number of hours.")
            return
        self.check_interval = hours * 3600  # Convert hours to seconds
        await ctx.send(f"Check interval set to {hours} hours.")

    def cog_unload(self):
        """Cancel the background tasks when the cog is unloaded."""
        self._market_task.cancel()
