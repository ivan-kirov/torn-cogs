import discord
from redbot.core import commands, Config, checks
import requests
import asyncio
import time

class TornMonitor(commands.Cog):
    """Cog for monitoring Torn API purchases."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Unique identifier for storing settings
        self.config.register_global(previous_total_prices={})  # Global configuration for previous total prices
        self.config.register_global(user_ids=[])  # Global configuration for user IDs to monitor
        self.config.register_global(api_key=None)  # Global configuration for the Torn API key

    @commands.group()
    async def mug(self, ctx):
        """Group command for Torn API monitoring related commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid mug command passed...")

    @mug.command(name="setapikey")
    @checks.is_owner()
    async def setapikey(self, ctx, api_key: str):
        """Sets the Torn API key."""
        await self.config.api_key.set(api_key)
        await ctx.send("Torn API key has been set successfully.")

    @mug.command(name="add", aliases=["+"])
    async def adduser(self, ctx, user_id: str):
        """Adds a user ID to the monitoring list."""
        async with self.config.user_ids() as user_ids:
            if user_id not in user_ids:
                user_ids.append(user_id)
                await ctx.send(f"User ID {user_id} has been added to monitoring.")
            else:
                await ctx.send(f"User ID {user_id} is already being monitored.")

    @mug.command(name="remove", aliases=["-"])
    async def removeuser(self, ctx, user_id: str):
        """Removes a user ID from the monitoring list."""
        async with self.config.user_ids() as user_ids:
            if user_id in user_ids:
                user_ids.remove(user_id)
                await ctx.send(f"User ID {user_id} has been removed from monitoring.")
            else:
                await ctx.send(f"User ID {user_id} is not being monitored.")

    @mug.command(name="list")
    async def listusers(self, ctx):
        """Lists all user IDs currently being monitored."""
        user_ids = await self.config.user_ids()
        if user_ids:
            await ctx.send(f"Currently monitoring the following user IDs: {', '.join(user_ids)}")
        else:
            await ctx.send("No user IDs are currently being monitored.")

    @mug.command(name="test")
    async def test_output(self, ctx):
        """Sends a test output message with a specific user ID."""
        test_user_id = "2383169"
        api_key = await self.config.api_key()
        if not api_key:
            await ctx.send("API key is not set. Please set the API key using `!mug setapikey`.")
            return

        url = f"https://api.torn.com/user/{test_user_id}?selections=profile,bazaar&key={api_key}"
        response = requests.get(url)
        data = response.json()

        if "bazaar" in data:
            current_total_price = sum(item["price"] for item in data["bazaar"])
            last_action_timestamp = data.get("last_action", {}).get("timestamp", None)
            current_timestamp = int(time.time())
            seconds_since_last_action = current_timestamp - last_action_timestamp if last_action_timestamp else None

            channel = discord.utils.get(self.bot.get_all_channels(), name='torn')  # Replace 'torn' with your channel name
            if channel:
                mug_link = f"https://www.torn.com/loader.php?sid=attack&user2ID={test_user_id}"
                if seconds_since_last_action is not None:
                    await channel.send(
                        f"Test User {test_user_id}: Bazaar total price is {current_total_price}. "
                        f"[Mug]({mug_link}) Last action was {seconds_since_last_action} seconds ago."
                    )
                else:
                    await channel.send(
                        f"Test User {test_user_id}: Bazaar total price is {current_total_price}. [Mug]({mug_link})"
                    )
            else:
                await ctx.send("Channel 'torn' not found. Please check the channel name.")
        else:
            await ctx.send(f"Could not retrieve bazaar data for test user {test_user_id}.")

    async def check_for_purchases(self):
        """Periodically checks for purchases for each user ID."""
        await self.bot.wait_until_ready()
        while True:
            api_key = await self.config.api_key()
            if not api_key:
                print("API key is not set. Skipping Torn API checks.")
                await asyncio.sleep(30)
                continue

            user_ids = await self.config.user_ids()
            for user_id in user_ids:
                url = f"https://api.torn.com/user/{user_id}?selections=profile,bazaar&key={api_key}"
                response = requests.get(url)
                data = response.json()

                if "bazaar" in data:
                    current_total_price = sum(item["price"] for item in data["bazaar"])
                    previous_total_prices = await self.config.previous_total_prices()

                    # Calculate the last action time in seconds
                    last_action_timestamp = data.get("last_action", {}).get("timestamp", None)
                    current_timestamp = int(time.time())
                    seconds_since_last_action = current_timestamp - last_action_timestamp if last_action_timestamp else None

                    if user_id in previous_total_prices:
                        previous_total_price = previous_total_prices[user_id]
                        if current_total_price < previous_total_price:
                            difference = previous_total_price - current_total_price
                            if difference > 3000000:
                                channel = discord.utils.get(self.bot.get_all_channels(), name='torn')  # Replace with your channel name
                                if channel:
                                    mug_link = f"https://www.torn.com/loader.php?sid=attack&user2ID={user_id}"
                                    if seconds_since_last_action is not None:
                                        await channel.send(
                                            f"User {user_id}: Items were purchased! Total spent: {difference}. "
                                            f"[Mug]({mug_link}) Last action was {seconds_since_last_action} seconds ago."
                                        )
                                    else:
                                        await channel.send(
                                            f"User {user_id}: Items were purchased! Total spent: {difference}. [Mug]({mug_link})"
                                        )
                                else:
                                    print("Channel not found.")
                        else:
                            print(f"User {user_id}: No purchases detected.")
                    else:
                        print(f"User {user_id}: This is the first check, setting the baseline total price.")

                    previous_total_prices[user_id] = current_total_price
                    await self.config.previous_total_prices.set(previous_total_prices)

            await asyncio.sleep(2)  # Check every 2 seconds

    def cog_unload(self):
        self._task.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        self._task = self.bot.loop.create_task(self.check_for_purchases())
