import discord
from discord.ext import commands
from utils import ui
import settings

class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @commands.command(name="info", help="顯示機器人資訊")
    async def info_command(self, ctx: commands.Context):
        """顯示機器人基本資訊"""
        embed = discord.Embed(
            title="🤖 GIF Bot 資訊",
            description="專業的圖片轉 GIF 機器人",
            color=discord.Color.blue()
        )
        
        # 基本資訊
        embed.add_field(
            name="📊 機器人統計",
            value=f"• 伺服器數量: {len(self.bot.guilds)}\n"
                  f"• 延遲: {round(self.bot.latency * 1000)}ms\n"
                  f"• 指令前綴: `{settings.PREFIX}`",
            inline=True
        )
        
        # 技術資訊
        embed.add_field(
            name="⚙️ 技術規格",
            value="• 程式語言: Python\n"
                  "• 框架: discord.py\n"
                  "• 圖片處理: Pillow\n"
                  "• 資料庫: SQLAlchemy",
            inline=True
        )
        
        # 版本資訊
        embed.add_field(
            name="🏷️ 版本資訊",
            value="• 版本: v2.0\n"
                  "• 最後更新: 2025/06/25\n"
                  "• 開源授權: MIT",
            inline=True
        )
        
        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed.set_footer(
                text=f"由 {self.bot.user.name} 提供服務",
                icon_url=self.bot.user.display_avatar.url
            )
        
        await ctx.send(embed=embed)

    @commands.command(name="ping", help="檢查機器人回應時間")
    async def ping_command(self, ctx: commands.Context):
        """檢查機器人延遲"""
        latency = round(self.bot.latency * 1000)
        
        if latency < 100:
            color = discord.Color.green()
            status = "優秀"
            emoji = "🟢"
        elif latency < 200:
            color = discord.Color.yellow() 
            status = "良好"
            emoji = "🟡"
        else:
            color = discord.Color.red()
            status = "較慢"
            emoji = "🔴"
        
        embed = discord.Embed(
            title=f"🏓 Pong! {emoji}",
            description=f"延遲: **{latency}ms** ({status})",
            color=color
        )
        
        embed.set_footer(text=f"請求者: {ctx.author.name}")
        
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
