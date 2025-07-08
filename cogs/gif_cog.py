import logging
import io
import aiohttp
import discord
from PIL import Image, ImageSequence
from discord.ext import commands
from discord import app_commands, Interaction, File
from utils.log import log
from utils import ui
from utils.database import db
import asyncio


class GifCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        # 創建全域右鍵選單 - 允許在 DM 中使用
        self.context_menu = app_commands.ContextMenu(
            name='轉換為 GIF',
            callback=self.convert_message_image_to_gif,
        )
        # 設定為全域指令，並允許在 DM 中使用
        self.context_menu.allowed_contexts = app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=True)
        self.context_menu.allowed_installs = app_commands.AppInstallationType(guild=True, user=True)
        
        self.bot.tree.add_command(self.context_menu)

    def _get_attachment(self, message: discord.Message):
        """從訊息中獲取第一個有效的圖片附件"""
        
        # 找到第一張圖片
        attachment = None
        for att in message.attachments:
            if any(att.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.gif']):
                attachment = att
                break
        
        if not attachment:
            return None
        
        # 檢查檔案大小
        if attachment.size > 8 * 1024 * 1024:
            raise ValueError("❌ 圖片檔案過大！請選擇小於 8MB 的圖片。")
        return attachment

    async def _validate_image_url(self, url: str) -> bool:
        """驗證 URL 是否指向圖片（只檢查 Content-Type，不下載檔案）"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                # 只發送 HEAD 請求來檢查 Content-Type，不下載檔案內容
                async with session.head(url) as resp:
                    if resp.status == 200:
                        content_type = resp.headers.get('content-type', '').lower()
                        return content_type.startswith('image/')
        except asyncio.TimeoutError:
            logging.warning(f"驗證圖片 URL 超時: {url}")
        except Exception as e:
            logging.warning(f"驗證圖片 URL 失敗: {url} - {e}")
        return False

    def _get_url(self, message: discord.Message) -> str:
        """從訊息中獲取任何 HTTP/HTTPS URL"""
        import re
        
        # 找出所有 HTTP/HTTPS URL
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, message.content)
        
        return urls[0] if urls else None




    async def convert_message_image_to_gif(self, interaction: Interaction, message: discord.Message):
        """右鍵選單：將訊息中的圖片轉換為 GIF"""
        log(f"用戶 {interaction.user} 透過右鍵選單轉換圖片")
        await interaction.response.defer()
        
        try:
            attachment = None
            image_url = None
            
            # 首先嘗試獲取附件
            attachment = self._get_attachment(message)
            
            if attachment:
                image_url = attachment.url
                filename = attachment.filename
                file_size = attachment.size
            else:
                # 如果沒有附件，嘗試從訊息內容中獲取 URL
                image_url = self._get_url(message)
                if not image_url:
                    raise ValueError("❌ 此訊息沒有包含圖片或圖片URL！")
                
                # 驗證 URL 是否指向圖片（使用 HEAD 請求，不下載檔案）
                if not await self._validate_image_url(image_url):
                    raise ValueError("❌ URL 不是有效的圖片連結！")
                
                # 從 URL 中推測檔案名
                filename = image_url.split('/')[-1].split('?')[0]
                if not filename or '.' not in filename:
                    filename = "image_from_url.png"
                file_size = None  # URL 無法直接獲取檔案大小

            embed = discord.Embed(
                title="轉換圖片為 GIF",
                description=f"正在處理圖片: `{filename}`\n請稍候...",
                color=discord.Color.blue(),
            )
            embed.set_footer(text="轉換過程可能需要幾秒鐘，請耐心等待。")
            
            # 檢查是否已經是 GIF 格式
            embed = discord.Embed(
                title="✅ 圖片轉換成功",
                description="圖片已成功轉換為 GIF 格式！\n可使用左上角星號快速保存此圖片。\n-# --\n-# 將本應用[新增](https://discord.com/oauth2/authorize?client_id=1375013750305853440&integration_type=1&scope=applications.commands)至您的應用程式，隨處都能使用",
                color=discord.Color.green(),
            )
            embed.add_field(name="👤 來源圖片作者", value=f"{message.author.mention}", inline=True)
            embed.add_field(name="📂 來源圖檔", value=f"```{filename}```", inline=True)
            embed.set_footer(text=f"由 2GIF Bot 提供服務", icon_url=self.bot.user.display_avatar.url)
            
            if not filename.lower().endswith('.gif'):
                # 下載並轉換圖片 (使用預設設定)
                gif_data = await self._download_and_convert(image_url, 80, 30)
            
                if gif_data is None:
                    await interaction.edit_original_response(embed=ui.error_embed("❌ 圖片轉換失敗！"))
                    return
            
                # 準備檔案名稱
                original_name = filename.rsplit('.', 1)[0]
                gif_filename = f"{original_name}_converted.gif"
                # 發送轉換後的 GIF
                file = File(io.BytesIO(gif_data), filename=gif_filename)
                
                embed.set_image(url=f"attachment://{gif_filename}")
                await interaction.edit_original_response(
                    embed=embed,
                    attachments=[file]
                )
                
                # 記錄使用記錄到資料庫
                try:
                    await db.record_conversion(
                        user=interaction.user,
                        guild=interaction.guild,
                        file_size=file_size,
                        conversion_type="image_to_gif"
                    )
                except Exception as db_error:
                    logging.error(f"記錄轉換使用失敗: {db_error}")
                    
            else:
                logging.info("圖片已經是 GIF 格式，無需轉換。")
                embed.set_image(url=image_url)
                await interaction.edit_original_response(
                    embed=embed,
                )
                
                # 即使是 GIF 也記錄使用記錄
                try:
                    await db.record_conversion(
                        user=interaction.user,
                        guild=interaction.guild,
                        file_size=file_size,
                        conversion_type="gif_passthrough"
                    )
                except Exception as db_error:
                    logging.error(f"記錄轉換使用失敗: {db_error}")

            
            
        except Exception as e:
            logging.error(f"右鍵選單轉換 GIF 時發生錯誤: {e}")
            await interaction.edit_original_response(embed=ui.error_embed("❌ 轉換過程中發生錯誤！"))

    async def _download_and_convert(self, image_url: str, quality: int, max_frames: int) -> bytes:
        """下載並轉換圖片"""
        try:
            # 設定超時和大小限制
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(image_url) as resp:
                    if resp.status != 200:
                        logging.error(f"下載圖片失敗，狀態碼: {resp.status}")
                        return None
                    
                    # 檢查 Content-Type
                    content_type = resp.headers.get('content-type', '').lower()
                    if not content_type.startswith('image/'):
                        logging.error(f"URL 不是圖片: {content_type}")
                        return None
                    
                    # 檢查檔案大小
                    content_length = resp.headers.get('content-length')
                    if content_length:
                        file_size = int(content_length)
                        if file_size > 25 * 1024 * 1024:  # 25MB 限制
                            logging.error(f"圖片檔案過大: {file_size} bytes")
                            return None
                    
                    # 分塊讀取，避免一次性下載過大檔案
                    image_data = b''
                    max_size = 25 * 1024 * 1024  # 25MB
                    async for chunk in resp.content.iter_chunked(8192):  # 8KB 塊
                        image_data += chunk
                        if len(image_data) > max_size:
                            logging.error("下載過程中檔案超過大小限制")
                            return None
            
            # 轉換圖片為 GIF
            return await self.convert_image_to_gif(image_data, quality, max_frames)
            
        except asyncio.TimeoutError:
            logging.error("下載圖片超時")
            return None
        except Exception as e:
            logging.error(f"下載或轉換圖片時發生錯誤: {e}")
            return None

    async def convert_image_to_gif(self, image_data: bytes, quality: int = 80, max_frames: int = 30) -> bytes:
        """
        將圖片資料轉換為 GIF 格式
        
        Args:
            image_data: 原始圖片資料
            quality: GIF 品質 (1-100)
            max_frames: 最大幀數 (用於動態圖片)
        
        Returns:
            轉換後的 GIF 資料，如果失敗則返回 None
        """
        try:
            # 打開圖片
            with Image.open(io.BytesIO(image_data)) as img:
                # 如果是靜態圖片，直接轉換
                if getattr(img, 'is_animated', False) == False:
                    # 轉換為 RGB 模式 (GIF 需要)
                    if img.mode not in ['RGB', 'P']:
                        img = img.convert('RGB')
                    
                    # 如果圖片太大，進行縮放
                    if img.width > 1024 or img.height > 1024:
                        img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                    
                    # 轉換為 GIF
                    output = io.BytesIO()
                    img.save(output, format='GIF', optimize=True, quality=quality)
                    return output.getvalue()
                
                # 如果是動態圖片 (如 GIF 或 WebP)
                else:
                    frames = []
                    durations = []
                    
                    frame_count = 0
                    for frame in ImageSequence.Iterator(img):
                        if frame_count >= max_frames:
                            break
                        
                        # 轉換每一幀
                        frame = frame.convert('RGB')
                        
                        # 縮放幀
                        if frame.width > 512 or frame.height > 512:
                            frame.thumbnail((512, 512), Image.Resampling.LANCZOS)
                        
                        frames.append(frame)
                        
                        # 獲取幀間隔
                        duration = frame.info.get('duration', 100)
                        durations.append(duration)
                        
                        frame_count += 1
                    
                    if not frames:
                        return None
                    
                    # 保存為 GIF
                    output = io.BytesIO()
                    frames[0].save(
                        output,
                        format='GIF',
                        save_all=True,
                        append_images=frames[1:],
                        duration=durations,
                        loop=0,
                        optimize=True,
                        quality=quality
                    )
                    return output.getvalue()
                    
        except Exception as e:
            logging.error(f"圖片轉換錯誤: {e}")
            return None

async def setup(bot: commands.Bot):
    await bot.add_cog(GifCog(bot))
    logging.info(f'{__name__} 已載入')

