from .sniper import BazaarSniper

async def setup(bot):
    await bot.add_cog(BazaarSniper(bot))