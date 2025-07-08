import logging
import os
import sys
import time
import discord
from discord.ext import commands,tasks
from discord import app_commands, Interaction
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils import ui
from utils.log import log
from utils.database import db
from datetime import datetime

import settings

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot:commands.Bot = bot

    @commands.command(name="stats", help="查看機器人統計資訊")
    async def stats(self, ctx: commands.Context, target: str = None):
        """查看統計資訊"""
        if ctx.author.id not in settings.DEV_ID:
            return
        
        try:
            if target is None:
                # 顯示全域統計
                try:
                    embed = await self._show_global_stats()
                    await ctx.send(embed=embed)
                except Exception as e:
                    logging.error(f"顯示全域統計時發生錯誤: {e}")
                    await ctx.send(
                        embed=ui.error_embed("❌ 無法獲取統計資料！")
                    )
            elif target.startswith('<@') and target.endswith('>'):
                # 用戶統計
                user_id = int(target[2:-1].replace('!', ''))
                await self._show_user_stats(ctx, user_id)
            elif target.isdigit():
                # 可能是用戶 ID 或伺服器 ID
                target_id = int(target)
                if ctx.guild and target_id == ctx.guild.id:
                    await self._show_guild_stats(ctx, target_id)
                else:
                    await self._show_user_stats(ctx, target_id)
            else:
                await ctx.send(
                    embed=ui.error_embed("❌ 無效的目標格式！請使用用戶提及或 ID。")
                )
        except Exception as e:
            logging.error(f"查看統計時發生錯誤: {e}")
            await ctx.send(
                embed=ui.error_embed("❌ 查看統計時發生錯誤！")
            )

    async def _show_database_stats(self):
        db_stats = await db.get_database_stats()
            
        embed = discord.Embed(
            title="📊 資料庫統計資訊",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🏰 伺服器總數",
            value=f"`{db_stats.get('total_guilds', 0):,}` 個",
            inline=True
        )
        
        embed.add_field(
            name="👥 用戶總數", 
            value=f"`{db_stats.get('total_users', 0):,}` 人",
            inline=True
        )
        
        embed.add_field(
            name="📝 使用記錄",
            value=f"`{db_stats.get('total_usage_logs', 0):,}` 筆",
            inline=True
        )
        
        embed.add_field(
            name="💾 資料庫路徑",
            value=f"`{db_stats.get('database_path', 'N/A')}`",
            inline=False
        )
        
        embed.timestamp = datetime.now()
        return embed

    @commands.command(name="dbstats", help="查看資料庫統計資訊")
    async def database_stats(self, ctx: commands.Context):
        """查看資料庫統計資訊"""
        if ctx.author.id not in settings.DEV_ID:
            await ctx.send(embed=ui.error_embed("❌ 只有開發者可以執行此指令！"))
            return
        
        try:
            embed = await self._show_database_stats()
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logging.error(f"查看資料庫統計時發生錯誤: {e}")
            await ctx.send(embed=ui.error_embed("❌ 無法獲取資料庫統計資訊！"))

    @commands.command(name="cleanup", help="清理舊的使用記錄")
    async def cleanup_logs(self, ctx: commands.Context, days: int = 90):
        """清理舊的使用記錄"""
        # 檢查是否為機器人擁有者
        app_info = await self.bot.application_info()
        if ctx.author.id != app_info.owner.id:
            await ctx.send(
                embed=ui.error_embed("❌ 只有機器人擁有者可以執行此指令！")
            )
            return
        
        try:
            deleted_count = await db.cleanup_old_logs(days)
            
            embed = discord.Embed(
                title="🧹 清理完成",
                description=f"已清理 {deleted_count} 筆 {days} 天前的舊使用記錄",
                color=discord.Color.green()
            )
            
            await ctx.send(embed=embed)
            log(f"管理員 {ctx.author} 清理了 {days} 天前的記錄")
            
        except Exception as e:
            logging.error(f"清理記錄時發生錯誤: {e}")
            await ctx.send(
                embed=ui.error_embed("❌ 清理記錄時發生錯誤！")
            )
    


    @tasks.loop(seconds=30)
    async def auto_update_stats(self):
        db_stats = await db.get_database_stats()
        user_count = await self.bot.fetch_channel("1387694673052827719")
        await user_count.edit(
            name=f"用戶數量: {db_stats.get('total_users', 0):,}"
        )
        run_times_count = await self.bot.fetch_channel("1387696476712337449")
        await run_times_count.edit(
            name=f"使用次數: {db_stats.get('total_usage_logs', 0):,}"
        )
        embeds=[]
        data_channel = await self.bot.fetch_channel("1387699070373724242")
        database_embed = await data_channel.fetch_message("1387699322337886218")
        embed = await self._show_database_stats()
        embeds.append(embed)
        embed = await self._show_global_stats()
        embeds.append(embed)
        await database_embed.edit(embeds=embeds)

    @auto_update_stats.before_loop
    async def before_auto_update_stats(self):
        """等待機器人準備完成"""
        await self.bot.wait_until_ready()

    async def cog_load(self):
        """當 Cog 載入時啟動定時任務"""
        self.auto_update_stats.start()
        logging.info("已啟動自動更新統計任務")

    def cog_unload(self):
        """當 Cog 卸載時停止定時任務"""
        self.auto_update_stats.cancel()
        logging.info("已停止自動更新統計任務")

    async def _show_global_stats(self):
        """顯示全域統計"""
        # 獲取排行榜
        top_users = await db.get_top_users(5)
        recent_usage = await db.get_recent_usage(10)
        
        embed = discord.Embed(
            title="📊 機器人全域統計",
            description="以下是機器人的使用統計資訊",
            color=discord.Color.blue()
        )
        
        # 使用者排行榜
        if top_users:
            top_users_text = ""
            for i, user in enumerate(top_users, 1):
                top_users_text += f"{i}. `{user['username']}` - `{user['total_conversions']}` 次轉換\n"
            embed.add_field(
                name="🏆 使用者排行榜 (前5名)",
                value=top_users_text or "無資料",
                inline=False
            )
        
        # 最近活動
        if recent_usage:
            recent_text = ""
            for usage in recent_usage[:5]:
                guild_info = usage['guild_name'] if usage['guild_name'] != 'DM' else '私人訊息'
                recent_text += f"• **{usage['username']}** 在 `{guild_info if guild_info else f"伺服器: {usage['guild_id']}"}` 呼叫轉換\n"
            embed.add_field(
                name="🕐 最近活動 (前5筆)",
                value=recent_text or "無資料",
                inline=False
            )

        embed.timestamp = datetime.now()            
        return embed
        

    async def _show_user_stats(self, ctx, user_id: int):
        """顯示用戶統計"""
        try:
            user_stats = await db.get_user_stats(user_id)
            
            if not user_stats:
                embed = ui.error_embed("❌ 找不到該用戶的使用記錄！")
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"📊 用戶統計 - {user_stats['username']}",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📈 總轉換次數",
                value=f"`{user_stats['total_conversions']}` 次",
                inline=True
            )
            
            embed.add_field(
                name="🕐 本月轉換次數",
                value=f"`{user_stats['recent_conversions']}` 次",
                inline=True
            )
            
            embed.add_field(
                name="📅 首次使用",
                value=f"<t:{int(datetime.fromisoformat(user_stats['created_at']).timestamp())}:R>",
                inline=True
            )
            
            embed.add_field(
                name="🔄 最後使用",
                value=f"<t:{int(datetime.fromisoformat(user_stats['last_seen']).timestamp())}:R>",
                inline=True
            )
            
            if user_stats['display_name']:
                embed.add_field(
                    name="👤 顯示名稱",
                    value=user_stats['display_name'],
                    inline=True
                )
            
            embed.set_footer(text=f"用戶 ID: {user_id}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logging.error(f"顯示用戶統計時發生錯誤: {e}")
            await ctx.send(
                embed=ui.error_embed("❌ 無法獲取用戶統計資料！")
            )

    async def _show_guild_stats(self, ctx, guild_id: int):
        """顯示伺服器統計"""
        try:
            guild_stats = await db.get_guild_stats(guild_id)
            
            if not guild_stats:
                embed = ui.error_embed("❌ 找不到該伺服器的使用記錄！")
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"📊 伺服器統計 - {guild_stats['guild_name']}",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="📈 總轉換次數",
                value=f"`{guild_stats['total_conversions']}` 次",
                inline=True
            )
            
            embed.add_field(
                name="👥 活躍用戶數",
                value=f"`{guild_stats['active_users']}` 人",
                inline=True
            )
            
            embed.add_field(
                name="👤 伺服器成員數",
                value=f"`{guild_stats['member_count']}` 人",
                inline=True
            )
            
            embed.add_field(
                name="📅 安裝日期",
                value=f"<t:{int(datetime.fromisoformat(guild_stats['installed_at']).timestamp())}:D>",
                inline=True
            )
            
            embed.add_field(
                name="🔄 最後活動",
                value=f"<t:{int(datetime.fromisoformat(guild_stats['last_seen']).timestamp())}:R>",
                inline=True
            )
            
            embed.set_footer(text=f"伺服器 ID: {guild_id}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logging.error(f"顯示伺服器統計時發生錯誤: {e}")
            await ctx.send(
                embed=ui.error_embed("❌ 無法獲取伺服器統計資料！")
            )



# 在 setup 函數中啟動檔案監控
async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
    logging.info(f'{__name__} 已載入')
