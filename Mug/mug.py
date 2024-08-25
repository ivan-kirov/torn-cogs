import discord
from redbot.core import commands, checks
import requests
import asyncio
import time
import json
import locale
import logging

# Create a logger and configure it to write to a file
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Default to INFO level to prevent detailed logging initially

handler = logging.FileHandler('/home/minecraft/redenv/torn_monitor.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class TornMonitor(commands.Cog):
    """Cog for monitoring Torn API purchases."""

    def __init__(self, bot):
        self.bot = bot
        # Initialize user data with default values
        self.user_data = {
            'user_ids': [],
            'previous_total_prices': {},
            'api_key': None
        }

        # Debug statements to verify initialization
        logger.info('Initialized user data')

        # Start the background task
        self._task = self.bot.loop.create_task(self.check_for_purchases())

        # Set the locale in the initialization
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
            logger.info("Locale set to en_US.UTF-8")
        except locale.Error as e:
            logger.error(f"Error setting locale: {e}")

    @commands.group()
    async def mug(self, ctx):
        """Group command for Torn API monitoring related commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid mug command passed...')

    @mug.command(name='setapikey')
    async def setapikey(self, ctx, api_key: str):
        """Sets the Torn API key."""
        try:
            self.user_data['api_key'] = api_key
            logger.info('Torn API key has been set successfully')
            await ctx.send('Torn API key has been set successfully.')
        except Exception as e:
            logger.error(f"Error setting API key: {e}")
            await ctx.send("An error occurred while setting the API key.")

    @mug.command(name="add", aliases=["+"])
    async def adduser(self, ctx, user_id: str):
        """Adds a user ID to the monitoring list."""
        if user_id not in self.user_data['user_ids']:
            self.user_data['user_ids'].append(user_id)
            logger.info(f"User ID {user_id} has been added to monitoring")
            await ctx.send(f"User ID {user_id} has been added to monitoring.")
        else:
            logger.info(f"User ID {user_id} is already being monitored")
            await ctx.send(f"User ID {user_id} is already being monitored.")

    @mug.command(name="remove", aliases=["-"])
    async def removeuser(self, ctx, user_id: str):
        """Removes a user ID from the monitoring list."""
        if user_id in self.user_data['user_ids']:
            self.user_data['user_ids'].remove(user_id)
            logger.info(f"User ID {user_id} has been removed from monitoring")
            await ctx.send(f"User ID {user_id} has been removed from monitoring.")
        else:
            logger.warning(f"User ID {user_id} is not being monitored")
            await ctx.send(f"User ID {user_id} is not being monitored.")

    @mug.command(name="list")
    async def listusers(self, ctx):
        """Lists all user IDs currently being monitored."""
        user_ids = self.user_data.get('user_ids', [])
        if user_ids:
            logger.info(f"Currently monitoring user IDs: {user_ids}")
            await ctx.send(f"Currently monitoring the following user IDs: {', '.join(user_ids)}")
        else:
            logger.info("No user IDs are currently being monitored")
            await ctx.send("No user IDs are currently being monitored.")

    @mug.command(name="togglelogging")
    @checks.is_owner()
    async def toggle_logging(self, ctx, enable: bool):
        """Toggles detailed logging on or off."""
        if enable:
            logger.setLevel(logging.DEBUG)
            logger.info("Detailed logging has been enabled")
            await ctx.send("Detailed logging has been enabled.")
        else:
            logger.setLevel(logging.INFO)
            logger.info("Detailed logging has been disabled")
            await ctx.send("Detailed logging has been disabled.")

    async def perform_check(self, ctx, user_id):
        """Performs the check for a given user ID and sends the result to the Discord channel."""
        logger.info(f"Performing check for user ID: {user_id}")
        api_key = self.user_data.get('api_key')
        if not api_key:
            logger.warning("API key is not set")
            await ctx.send("API key is not set. Please set the API key using `!mug setapikey`.")
            return

        url = f"https://api.torn.com/user/{user_id}?selections=profile,bazaar&key={api_key}"
        response = requests.get(url)
        data = response.json()

        logger.debug(f"Response data for user {user_id}: {json.dumps(data, indent=4)}")

        if "bazaar" in data:
            try:
                current_total_price = sum(item.get("price", 0) * item.get("quantity", 1) for item in data["bazaar"])
            except Exception as e:
                logger.error(f"Error calculating current total price: {e}")
                await ctx.send("Error calculating the current bazaar price.")
                return

            last_action_timestamp = data.get("last_action", {}).get("timestamp", None)
            current_timestamp = int(time.time())
            seconds_since_last_action = current_timestamp - last_action_timestamp if last_action_timestamp else None

            status = data.get("status", {}).get("state", "Unknown")
            revivable = data.get("revivable", 0)

            previous_total_prices = self.user_data.get('previous_total_prices', {})
            previous_total_price = previous_total_prices.get(user_id, 0)

            logger.debug(f"User {user_id}: Current total price = {current_total_price}, Previous total price = {previous_total_price}")
            logger.debug(f"User {user_id}: Status = {status}, Revivable = {revivable}")
            logger.debug(f"User {user_id}: Seconds since last action = {seconds_since_last_action}")

            if current_total_price < previous_total_price:
                difference = previous_total_price - current_total_price
                if difference > 5000000 and (status == "Okay" or (status == "Hospital" and revivable == 1)):
                    channel = discord.utils.get(self.bot.get_all_channels(), name='torn')
                    if channel:
                        # Format the current total price as currency
                        formatted_price = locale.format_string('%s', current_total_price, grouping=True, thousands_sep=',')
                        mug_link = f"https://www.torn.com/loader.php?sid=attack&user2ID={user_id}"
                        # Include the formatted price in the message
                        message = (f"Player {data.get('name', 'Unknown')}: Available money on hand is {formatted_price}. [Mug]({mug_link})")

                        if seconds_since_last_action is not None:
                            message += f" Last action was {seconds_since_last_action} seconds ago."
                        
                        await channel.send(message)
                    else:
                        logger.warning("Channel 'torn' not found")
                        await ctx.send("Channel 'torn' not found. Please check the channel name.")
                else:
                    logger.debug(f"User {user_id}: Conditions not met for posting a message")
            else:
                logger.debug(f"User {user_id}: No purchases detected or conditions not met")

            # Update the previous total price
            self.user_data['previous_total_prices'][user_id] = current_total_price
        else:
            logger.error(f"Could not retrieve bazaar or profile data for user {user_id}")
            await ctx.send(f"Could not retrieve bazaar or profile data for user {user_id}.")

    async def check_for_purchases(self):
        """Periodically checks for purchases for each user ID."""
        logger.info("Starting check for purchases")
        await self.bot.wait_until_ready()
        while True:
            api_key = self.user_data.get('api_key')
            if not api_key:
                logger.warning("API key is not set. Skipping Torn API checks")
                await asyncio.sleep(30)
                continue

            user_ids = self.user_data.get('user_ids', [])
            for user_id in user_ids:
                try:
                    await self.perform_check(None, user_id)  # Passing `None` for context
                except Exception as e:
                    logger.error(f"Error performing check for user {user_id}: {e}")

            await asyncio.sleep(2)  # Check every 2 seconds

    def cog_unload(self):
        """Cancel the background task when the cog is unloaded."""
        if hasattr(self, '_task'):
            self._task.cancel()

