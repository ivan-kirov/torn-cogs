from .sniper import ItemMonitor

async def setup(bot):
    await bot.add_cog(ItemMonitor(bot))