from .mug import TornMonitor

async def setup(bot):
    await bot.add_cog(TornMonitor(bot))