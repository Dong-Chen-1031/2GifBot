import os
import sys
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

# Discord 機器人設定檔案

# Discord 機器人 Token
DISCORD_BOT_TOKEN = str(os.getenv("DISCORD_BOT_TOKEN"))

AUTO_RELOAD = True # 是否自動重新載入 Cogs

# 開發者指令的開發者ID
DEV_ID = list(map(int, os.getenv("DEV_ID").split(","))) if os.getenv("DEV_ID") else []

# 檢查 Token 是否存在
if DISCORD_BOT_TOKEN is None:
    print("錯誤: 找不到 DISCORD_BOT_TOKEN 環境變數")
    print("請確認 .env 檔案中已正確設置 DISCORD_BOT_TOKEN")
    print("格式應為: DISCORD_BOT_TOKEN = \"你的Token\"")
    sys.exit(1)

# 機器人開發者指令前綴
PREFIX = ".dev "