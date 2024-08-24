import discord
from redbot.core import commands, Config, checks
import requests
import asyncio

class TornMonitor(commands.Cog):
    """Cog for monitoring Torn API purchases."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Unique identifier for storing settings
        self.config.register_global(previous_total_prices={})  # Global configuration for previous total prices
        self.config.register_global(user_ids=[])  # Global configuration for user IDs to monitor
        self.config.register_global(api_key=None)  # Global configuration for the Torn API key

    @commands.command()
    @checks.is_owner()
    async def setapikey(self, ctx, api_key: str):
        """Sets the Torn API key."""
        await self.config.api_key.set(api_key)
        await ctx.send("Torn API key has been set successfully.")

    @commands.command()
    async def adduser(self, ctx, user_id: str):
        """Adds a user ID to the monitoring list."""
        async with self.config.user_ids() as user_ids:
            if user_id not in user_ids:
                user_ids.append(user_id)
                await ctx.send(f"User ID {user_id} has been added to monitoring.")
            else:
                await ctx.send(f"User ID {user_id} is already being monitored.")

    @commands.command()
    async def removeuser(self, ctx, user_id: str):
        """Removes a user ID from the monitoring list."""
        async with self.config.user_ids() as user_ids:
            if user_id in user_ids:
                user_ids.remove(user_id)
                await ctx.send(f"User ID {user_id} has been removed from monitoring.")
            else:
                await ctx.send(f"User ID {user_id} is not being monitored.")

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
                    
                    if user_id in previous_total_prices:
                        previous_total_price = previous_total_prices[user_id]
                        if current_total_price < previous_total_price:
                            difference = previous_total_price - current_total_price
                            if difference > 3000000 :
                                channel = discord.utils.get(self.bot.get_all_channels(), name='torn')  # Replace with your channel name
                                if channel:
                                    await channel.send(f"User {user_id}: Items were purchased! Total spent: {difference}")
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
