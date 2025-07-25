# 2GifBot - Discord GIF 轉換機器人

一個專門用於將圖片轉換為 GIF 格式的 Discord 機器人，採用右鍵選單設計，支援全域使用和私人訊息。方便使用者將圖片加入最愛選單。

## ✨ 主要功能

- 🖼️ **圖片轉 GIF** - 支援多種圖片格式轉換為 GIF
- 🖱️ **右鍵選單** - 簡單直覺的操作方式
- 🌍 **全域可用** - 在所有安裝機器人的伺服器中都能使用
- 💬 **私人訊息支援** - 可在 DM 和群組對話中使用
- ⚡ **快速處理** - 自動優化圖片大小和品質
- 🔄 **動態圖片支援** - 處理 GIF、WebP 等動態圖片格式
- 🎯 **智能檢測** - 已是 GIF 格式的檔案直接返回，無需重複轉換

## 📁 專案結構

```
2GifBot/
├── bot.py                    # 機器人主程式入口
├── settings.py               # 配置文件管理
├── requirements.txt          # 依賴套件清單
├── README.md                # 專案說明文件
├── .env                     # 環境變數配置 (需要創建)
├── cogs/                    # 功能模組目錄
│   ├── dev_cog.py          # 開發者工具模組 (包含統計功能)
│   └── gif_cog.py          # GIF 轉換核心模組
├── utils/                   # 工具函數目錄
│   ├── database.py          # 資料庫操作模組
│   ├── log.py              # 日誌系統
│   ├── ui.py               # UI 工具函數
│   └── types.py            # 型別定義
├── data/                    # 資料儲存目錄
│   └── gif_bot.db           # SQLite 資料庫 (自動產生)
└── logs/                    # 日誌檔案目錄
    └── 2025-06-24.log      # 每日日誌檔案
```

## 🚀 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 環境設定

在專案根目錄創建 `.env` 檔案：

```env
DISCORD_BOT_TOKEN=你的機器人Token
DEV_ID=你的開發者ID (逗號分隔多個ID)
```

### 3. Discord 開發者設定

在 [Discord Developer Portal](https://discord.com/developers/applications) 中：

1. **Bot 設定**：
   - 啟用 `Message Content Intent`
   
2. **Installation 設定**：
   - 啟用 `Guild Install` (伺服器安裝)
   - 啟用 `User Install` (用戶安裝) - **重要：用於私人訊息功能**

3. **OAuth2 權限**：
   - `applications.commands` - 應用程式指令
   - `Send Messages` - 發送訊息
   - `Attach Files` - 附加檔案

### 4. 運行機器人

```bash
python bot.py
```

### 5. 邀請機器人到伺服器

使用 OAuth2 URL Generator 生成邀請連結，確保包含：
- `bot` 權限
- `applications.commands` 權限
- 必要的訊息和檔案權限

## 🎯 使用方法

### 右鍵選單操作 (推薦)

1. **找到包含圖片的訊息**
2. **右鍵點擊該訊息**
3. **選擇「應用程式」→「轉換為 GIF」**
4. **等待轉換完成並下載結果**

### 支援的使用環境

| 環境 | 可用性 | 說明 |
|------|--------|------|
| 伺服器頻道 | ✅ | 完全支援 |
| 私人訊息 | ✅ | 需要正確設定 User Install |
| 群組對話 | ✅ | 需要正確設定 User Install |
| 討論串 | ✅ | 完全支援 |

### 支援的圖片格式

- **PNG** - 包含透明背景
- **JPG/JPEG** - 標準圖片格式
- **WebP** - 現代圖片格式，支援動態
- **BMP** - 點陣圖格式
- **TIFF** - 高品質圖片格式
- **GIF** - 智能檢測，已是 GIF 格式則直接返回原檔案

## ⚙️ 技術規格

### 圖片處理限制

- **檔案大小限制**: 8MB
- **靜態圖片最大尺寸**: 1024 x 1024 px (自動縮放)
- **動態圖片最大尺寸**: 512 x 512 px (自動縮放)
- **動態圖片最大幀數**: 30 幀
- **輸出品質**: 80 (固定優化值)

### 自動優化功能

- **智慧縮放**: 保持比例自動調整尺寸
- **品質優化**: 平衡檔案大小與視覺品質
- **幀數控制**: 限制動態圖片幀數以控制檔案大小
- **格式標準化**: 統一輸出為優化的 GIF 格式
- **智能檢測**: 自動識別 GIF 檔案，避免重複轉換

## 🔧 開發者工具

機器人內建開發者工具，用於開發和維護：

### 指令前綴
- 開發者指令前綴：`.dev `

### 可用指令

- `.dev load <模組名稱>` - 載入指定模組
- `.dev unload <模組名稱>` - 卸載指定模組  
- `.dev reload [模組名稱]` - 重新載入模組

### 統計指令

- `.dev stats` - 查看機器人全域統計資訊
- `.dev stats <用戶ID>` - 查看特定用戶的使用統計
- `.dev stats <@用戶>` - 查看特定用戶的使用統計
- `.dev cleanup [天數]` - 清理舊的使用記錄 (僅機器人擁有者)
- `.dev dbstats` - 查看資料庫統計資訊 (開發者專用)

## 📊 資料庫功能

### 自動記錄

機器人會在用戶使用轉換功能時自動記錄：

- **用戶資訊**: 使用轉換功能的用戶資料
- **伺服器資訊**: 使用轉換功能時所在的伺服器資料
- **使用記錄**: 每次 GIF 轉換的詳細記錄（檔案名稱、大小、時間等）

### 統計資訊

- **全域統計**: 總使用次數、活躍用戶排行榜、最近活動
- **用戶統計**: 個人使用次數、首次/最後使用時間
- **伺服器統計**: 伺服器內的使用統計、總用戶數

### 資料記錄策略

- **被動記錄**: 只有在實際使用轉換功能時才記錄資料
- **即時更新**: 每次轉換時自動更新用戶和伺服器資訊
- **避免冗餘**: 不會主動同步所有用戶或伺服器資料

### 隱私保護

- 僅記錄必要的統計資訊
- 不記錄訊息內容或圖片資料

## 🛠️ 核心技術

### 資料庫系統
- **SQLAlchemy** - 現代化的 ORM 框架
- **aiosqlite** - 異步 SQLite 驅動
- **自動遷移** - 資料庫結構自動初始化

### 圖片處理引擎
- **Pillow (PIL)** - 高效能圖片處理庫
- **aiohttp** - 異步 HTTP 客戶端，用於圖片下載
- **非同步處理** - 不阻塞其他機器人功能

### 機器人架構
- **discord.py** - Discord API 封裝
- **Cogs 系統** - 模組化設計，易於維護
- **全域指令** - 跨伺服器一致體驗

### 日誌與監控
- **Rich** - 美化控制台輸出
- **檔案日誌** - 按日期自動分類
- **錯誤追蹤** - 完整的錯誤記錄和處理

## 📋 依賴套件

```
discord.py     # Discord API 封裝器
rich           # 美化控制台輸出  
python-dotenv  # 環境變數管理
watchdog       # 檔案監控 (用於自動重載)
Pillow         # 圖片處理核心庫
aiohttp        # 異步 HTTP 客戶端
sqlalchemy     # 現代化 ORM 框架
aiosqlite      # 異步 SQLite 驅動
```

## 🎯 使用範例

### 基本使用流程

1. **用戶上傳圖片**：
   ```
   用戶: [上傳 photo.png]
   ```

2. **使用右鍵選單**：
   ```
   用戶: 右鍵點擊 → 應用程式 → 轉換為 GIF
   ```

3. **機器人處理**：
   ```
   系統: 🔄 正在轉換圖片: photo.png...
   ```

4. **完成轉換**：
   ```
   機器人: ✅ 圖片已成功轉換為 GIF！
           📁 原檔案: photo.png
           📁 新檔案: photo_converted.gif
           [附加檔案: photo_converted.gif]
   ```

### 特殊情況處理

- **已是 GIF 格式**：
  ```
  機器人: ✅ 檔案已是 GIF 格式
          直接提供原始檔案。
          [附加檔案: original.gif]
  ```

### 支援的轉換類型

- **靜態轉 GIF**: PNG, JPG, WebP → GIF
- **動態重新編碼**: WebP → 優化的 GIF
- **GIF 檢測**: 已是 GIF → 直接返回原檔案
- **尺寸優化**: 大圖片自動縮放
- **品質優化**: 平衡檔案大小與畫質

## 🆘 常見問題

### Q: 機器人無法啟動？
**A:** 請檢查：
- `.env` 檔案是否正確設定 `DISCORD_BOT_TOKEN`
- Discord Bot Token 是否有效且具備必要權限
- 依賴套件是否完整安裝

### Q: 右鍵選單沒有出現？
**A:** 請確認：
- 機器人已正確邀請到伺服器
- 機器人具備 `applications.commands` 權限
- 等待全域指令同步完成 (最多 1 小時)
- 重新啟動 Discord 客戶端

### Q: 無法在私人訊息中使用？
**A:** 請檢查：
- Discord Developer Portal 中是否啟用了 `User Install`
- 是否啟用了 `Message Content Intent`
- 機器人是否支援用戶安裝模式

### Q: 圖片轉換失敗？
**A:** 可能原因：
- 圖片檔案過大 (超過 8MB)
- 圖片格式不支援
- 網路連線問題
- 查看機器人日誌檔案了解詳細錯誤

### Q: 轉換速度很慢？
**A:** 影響因素：
- 原始圖片檔案大小
- 伺服器網路狀況
- 動態圖片的幀數和複雜度
- 一般情況下 1-10 秒內完成

### Q: 上傳的是 GIF 檔案還會轉換嗎？
**A:** 不會！機器人會智能檢測檔案格式，如果已經是 GIF 格式，會直接返回原檔案並提示無需轉換。

## 📄 授權條款

此專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

**使用本服務即表示您同意遵守上述條款與政策。**

## 🚀 未來計劃

- [ ] 添加更多圖片格式支援
- [ ] 支援影片轉換
- [ ] 支援更大的檔案尺寸

## 📞 聯絡資訊

如有問題或建議，歡迎開啟 Issue 或聯絡專案維護者。

---

*最後更新：2025年6月24日*
