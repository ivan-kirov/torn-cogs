import discord
from redbot.core import commands, checks
import requests
import asyncio
import json
import logging

# Create a logger and configure it to write to a file
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Default to INFO level to prevent detailed logging initially

handler = logging.FileHandler('/home/minecraft/redenv/torn_item_monitor.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class ItemMonitor(commands.Cog):
    """Cog for monitoring Torn API item market values."""

    def __init__(self, bot):
        self.bot = bot
        self.check_interval = 2  # Default interval to 2 seconds
        self.item_data_file = '/home/minecraft/redenv/item_data.json'  # Path to the JSON file
        self.market_check_interval = 2160  # Default to 6 hours
        self.market_channel_id = None  # Channel ID to send market alerts

        # Initialize item data
        self.items = self.load_item_data()

        # Debug statements to verify initialization
        logger.info('Initialized item data')

        # Start the background tasks
        self._task = self.bot.loop.create_task(self.check_for_item_values())
        self._market_task = self.bot.loop.create_task(self.check_market_values())

    def load_item_data(self):
        """Load item data from the JSON file."""
        try:
            with open(self.item_data_file, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        return data

    def save_item_data(self):
        """Save item data to the JSON file."""
        with open(self.item_data_file, 'w') as f:
            json.dump(self.items, f, indent=4)

    @commands.group()
    async def item(self, ctx):
        """Group command for Torn API item monitoring related commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid item command passed...')

    @item.command(name='add')
    @checks.is_owner()
    async def add_item(self, ctx, item_id: str):
        """Adds an item ID to the monitoring list."""
        if item_id not in self.items:
            self.items[item_id] = {'name': None, 'market_value': None}
            self.save_item_data()
            logger.info(f"Item ID {item_id} has been added to monitoring")
            await ctx.send(f"Item ID {item_id} has been added to monitoring.")
        else:
            logger.info(f"Item ID {item_id} is already being monitored")
            await ctx.send(f"Item ID {item_id} is already being monitored.")

    @item.command(name='remove')
    @checks.is_owner()
    async def remove_item(self, ctx, item_id: str):
        """Removes an item ID from the monitoring list."""
        if item_id in self.items:
            del self.items[item_id]
            self.save_item_data()
            logger.info(f"Item ID {item_id} has been removed from monitoring")
            await ctx.send(f"Item ID {item_id} has been removed from monitoring.")
        else:
            logger.warning(f"Item ID {item_id} is not being monitored")
            await ctx.send(f"Item ID {item_id} is not being monitored.")

    @item.command(name='list')
    async def list_items(self, ctx):
        """Lists all item IDs currently being monitored."""
        if self.items:
            item_ids = list(self.items.keys())
            logger.info(f"Currently monitoring item IDs: {item_ids}")
            await ctx.send(f"Currently monitoring the following item IDs: {', '.join(item_ids)}")
        else:
            logger.info("No item IDs are currently being monitored")
            await ctx.send("No item IDs are currently being monitored.")

    @item.command(name='setinterval')
    @checks.is_owner()
    async def set_interval(self, ctx, hours: int):
        """Sets the time interval between checks in hours."""
        if hours < 0:
            await ctx.send("Interval must be a positive number.")
            return
        self.check_interval = hours * 3600  # Convert hours to seconds
        logger.info(f"Check interval has been set to {hours} hours ({self.check_interval} seconds)")
        await ctx.send(f"Check interval has been set to {hours} hours.")


    @item.command(name='setmarketinterval')
    @checks.is_owner()
    async def set_market_interval(self, ctx, seconds: int):
        """Sets the time interval for market value checks."""
        if seconds < 1:
            await ctx.send("Interval must be at least 1 second.")
            return
        self.market_check_interval = seconds
        logger.info(f"Market check interval has been set to {seconds} seconds")
        await ctx.send(f"Market check interval has been set to {seconds} seconds.")

    @item.command(name='setmarketchannel')
    @checks.is_owner()
    async def set_market_channel(self, ctx, channel: discord.TextChannel):
        """Sets the channel to send market alerts."""
        self.market_channel_id = channel.id
        logger.info(f"Market alerts will be sent to channel: {channel.name}")
        await ctx.send(f"Market alerts will be sent to channel: {channel.mention}")

    async def perform_check(self, ctx, item_id):
        """Performs the check for a given item ID and sends the result to the Discord channel."""
        logger.info(f"Performing check for item ID: {item_id}")
        url = f"https://api.torn.com/item/{item_id}?key=FUKFxlv59sFjmDNK"
        response = requests.get(url)
        data = response.json()

        logger.debug(f"Response data for item {item_id}: {json.dumps(data, indent=4)}")

        item = data.get("items", {}).get(item_id, {})
        if item:
            current_market_value = item.get('market_value', 0)
            item_name = item.get('name', 'Unknown')
            previous_market_value = self.items[item_id].get('market_value', 0)
            self.items[item_id]['name'] = item_name
            self.items[item_id]['market_value'] = current_market_value
            self.save_item_data()

            logger.debug(f"Item {item_id}: Current market value = {current_market_value}, Previous market value = {previous_market_value}")

            if current_market_value != previous_market_value:
                channel = discord.utils.get(self.bot.get_all_channels(), id=self.market_channel_id)
                if channel:
                    message = (f"Item {item_name} (ID {item_id}) has a new market value: {current_market_value}.")
                    await channel.send(message)
                else:
                    logger.warning("Market alert channel not found")
                    await ctx.send("Market alert channel not found. Please check the channel setting.")
        else:
            logger.error(f"Could not retrieve data for item {item_id}")
            await ctx.send(f"Could not retrieve data for item {item_id}.")

    async def check_for_item_values(self):
        """Periodically checks for item values for each item ID."""
        logger.info("Starting check for item values")
        await self.bot.wait_until_ready()
        while True:
            for item_id in self.items:
                try:
                    await self.perform_check(None, item_id)  # Passing `None` for context
                except Exception as e:
                    logger.error(f"Error performing check for item {item_id}: {e}")
            await asyncio.sleep(self.check_interval)  # Use the adjustable interval

    async def check_market_values(self):
        """Periodically checks market values and sends alerts if the lowest cost is lower than market value."""
        logger.info("Starting market value check")
        await self.bot.wait_until_ready()
        while True:
            for item_id in self.items:
                try:
                    url = f"https://api.torn.com/market/{item_id}?selections=&key=FUKFxlv59sFjmDNK"
                    response = requests.get(url)
                    data = response.json()
                    
                    logger.debug(f"Market data for item {item_id}: {json.dumps(data, indent=4)}")

                    lowest_cost = min(bazaar_item['cost'] for bazaar_item in data.get("bazaar", []))
                    market_value = self.items[item_id].get('market_value', float('inf'))

                    logger.debug(f"Item {item_id}: Lowest cost = {lowest_cost}, Market value = {market_value}")

                    if lowest_cost < market_value and self.market_channel_id:
                        channel = discord.utils.get(self.bot.get_all_channels(), id=self.market_channel_id)
                        if channel:
                            item_name = self.items[item_id].get('name', 'Unknown')
                            message = (f"Alert: The lowest cost for {item_name} (ID {item_id}) on the market is {lowest_cost}, which is lower than the market value {market_value}.")
                            await channel.send(message)
                        else:
                            logger.warning("Market alert channel not found")
                except Exception as e:
                    logger.error(f"Error checking market values for item {item_id}: {e}")
            await asyncio.sleep(self.market_check_interval)  # Use the adjustable interval

    def cog_unload(self):
        """Cancel the background tasks when the cog is unloaded."""
        if hasattr(self, '_task'):
            self._task.cancel()
        if hasattr(self, '_market_task'):
            self._market_task.cancel()
