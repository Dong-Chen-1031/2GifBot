import logging
import os
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.sql import func
from sqlalchemy import select, update, delete, desc

# SQLAlchemy 基礎類別
Base = declarative_base()

class Guild(Base):
    """伺服器資料表模型"""
    __tablename__ = 'guilds'
    
    guild_id = Column(Integer, primary_key=True)
    guild_name = Column(String, nullable=False)
    member_count = Column(Integer, default=0)
    installed_at = Column(DateTime, default=func.now())
    last_seen = Column(DateTime, default=func.now())
    
    # 關聯關係
    usage_logs = relationship("UsageLog", back_populates="guild")

class User(Base):
    """用戶資料表模型"""
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    display_name = Column(String)
    created_at = Column(DateTime, default=func.now())
    last_seen = Column(DateTime, default=func.now())
    total_conversions = Column(Integer, default=0)
    
    # 關聯關係
    usage_logs = relationship("UsageLog", back_populates="user")

class UsageLog(Base):
    """使用記錄資料表模型"""
    __tablename__ = 'usage_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    guild_id = Column(Integer, ForeignKey('guilds.guild_id'))
    file_size = Column(Integer)
    conversion_type = Column(String)
    timestamp = Column(DateTime, default=func.now())
    
    # 關聯關係
    user = relationship("User", back_populates="usage_logs")
    guild = relationship("Guild", back_populates="usage_logs")

# 創建索引
Index('idx_usage_logs_user_id', UsageLog.user_id)
Index('idx_usage_logs_guild_id', UsageLog.guild_id)
Index('idx_usage_logs_timestamp', UsageLog.timestamp)
class Database:
    """SQLAlchemy 異步資料庫管理類別"""
    
    def __init__(self, db_path: str = "data/gif_bot.db"):
        """初始化資料庫連線"""
        self.db_path = db_path
        
        # 確保資料庫目錄存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # 創建異步引擎
        self.engine = create_async_engine(f'sqlite+aiosqlite:///{db_path}', echo=False)
        self.AsyncSessionLocal = async_sessionmaker(
            bind=self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        # 標記是否已初始化
        self._initialized = False
    
    async def _init_database(self):
        """初始化資料庫表格"""
        if self._initialized:
            return
            
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logging.info("資料庫初始化完成")
            self._initialized = True
        except Exception as e:
            logging.error(f"資料庫初始化錯誤: {e}")
    
    async def _ensure_initialized(self):
        """確保資料庫已初始化"""
        if not self._initialized:
            await self._init_database()
    
    async def add_guild(self, guild_id: int, guild_name: str, member_count: int = 0):
        """添加或更新伺服器資訊"""
        await self._ensure_initialized()
        try:
            async with self.AsyncSessionLocal() as session:
                # 查找現有伺服器
                stmt = select(Guild).where(Guild.guild_id == guild_id)
                result = await session.execute(stmt)
                guild = result.scalar_one_or_none()
                
                if guild:
                    # 更新現有伺服器
                    guild.guild_name = guild_name
                    guild.member_count = member_count
                    guild.last_seen = func.now()
                else:
                    # 創建新伺服器
                    guild = Guild(
                        guild_id=guild_id,
                        guild_name=guild_name,
                        member_count=member_count
                    )
                    session.add(guild)
                
                await session.commit()
                return guild.guild_id
        except Exception as e:
            logging.error(f"添加伺服器失敗: {e}")
            return None
    
    async def add_user(self, user_id: int, username: str, display_name: str = None):
        """添加或更新用戶資訊"""
        await self._ensure_initialized()
        try:
            async with self.AsyncSessionLocal() as session:
                # 查找現有用戶
                stmt = select(User).where(User.user_id == user_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                
                if user:
                    # 更新現有用戶
                    user.username = username
                    user.display_name = display_name
                    user.last_seen = func.now()
                else:
                    # 創建新用戶
                    user = User(
                        user_id=user_id,
                        username=username,
                        display_name=display_name
                    )
                    session.add(user)
                
                await session.commit()
                return user.user_id
        except Exception as e:
            logging.error(f"添加用戶失敗: {e}")
            return None
    
    async def log_usage(self, user_id: int, guild_id: int = None, 
                       file_size: int = None, conversion_type: str = "image_to_gif"):
        """記錄使用記錄"""
        await self._ensure_initialized()
        try:
            async with self.AsyncSessionLocal() as session:
                # 創建使用記錄
                usage_log = UsageLog(
                    user_id=user_id,
                    guild_id=guild_id,
                    file_size=file_size,
                    conversion_type=conversion_type
                )
                session.add(usage_log)
                
                # 更新用戶總轉換次數
                stmt = update(User).where(User.user_id == user_id).values(
                    total_conversions=User.total_conversions + 1,
                    last_seen=func.now()
                )
                await session.execute(stmt)
                
                await session.commit()
                return usage_log.id
        except Exception as e:
            logging.error(f"記錄使用記錄失敗: {e}")
            return None
    
    async def get_user_stats(self, user_id: int) -> Optional[dict]:
        """獲取用戶統計資訊"""
        await self._ensure_initialized()
        try:
            async with self.AsyncSessionLocal() as session:
                # 獲取用戶基本資訊
                stmt = select(User).where(User.user_id == user_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    return None
                
                # 獲取最近30天轉換次數
                recent_stmt = select(func.count(UsageLog.id)).where(
                    UsageLog.user_id == user_id,
                    UsageLog.timestamp >= func.datetime('now', '-30 days')
                )
                recent_result = await session.execute(recent_stmt)
                recent_conversions = recent_result.scalar() or 0
                
                return {
                    'username': user.username,
                    'display_name': user.display_name,
                    'total_conversions': user.total_conversions,
                    'created_at': user.created_at.isoformat(),
                    'last_seen': user.last_seen.isoformat(),
                    'recent_conversions': recent_conversions
                }
        except Exception as e:
            logging.error(f"獲取用戶統計失敗: {e}")
            return None
    
    async def get_guild_stats(self, guild_id: int) -> Optional[dict]:
        """獲取伺服器統計資訊"""
        await self._ensure_initialized()
        try:
            async with self.AsyncSessionLocal() as session:
                # 獲取伺服器基本資訊
                stmt = select(Guild).where(Guild.guild_id == guild_id)
                result = await session.execute(stmt)
                guild = result.scalar_one_or_none()
                
                if not guild:
                    return None
                
                # 獲取總轉換次數
                total_stmt = select(func.count(UsageLog.id)).where(UsageLog.guild_id == guild_id)
                total_result = await session.execute(total_stmt)
                total_conversions = total_result.scalar() or 0
                
                # 獲取活躍用戶數
                active_stmt = select(func.count(func.distinct(UsageLog.user_id))).where(
                    UsageLog.guild_id == guild_id
                )
                active_result = await session.execute(active_stmt)
                active_users = active_result.scalar() or 0
                
                return {
                    'guild_name': guild.guild_name,
                    'member_count': guild.member_count,
                    'installed_at': guild.installed_at.isoformat(),
                    'last_seen': guild.last_seen.isoformat(),
                    'total_conversions': total_conversions,
                    'active_users': active_users
                }
        except Exception as e:
            logging.error(f"獲取伺服器統計失敗: {e}")
            return None
    
    async def get_top_users(self, limit: int = 10) -> List[dict]:
        """獲取使用次數最多的用戶"""
        await self._ensure_initialized()
        try:
            async with self.AsyncSessionLocal() as session:
                stmt = select(User).order_by(desc(User.total_conversions)).limit(limit)
                result = await session.execute(stmt)
                users = result.scalars().all()
                
                return [
                    {
                        'user_id': user.user_id,
                        'username': user.username,
                        'display_name': user.display_name,
                        'total_conversions': user.total_conversions,
                        'last_seen': user.last_seen.isoformat()
                    }
                    for user in users
                ]
        except Exception as e:
            logging.error(f"獲取排行榜失敗: {e}")
            return []
    
    async def get_recent_usage(self, limit: int = 50) -> List[dict]:
        """獲取最近的使用記錄"""
        await self._ensure_initialized()
        try:
            async with self.AsyncSessionLocal() as session:
                stmt = (
                    select(UsageLog, User, Guild)
                    .join(User, UsageLog.user_id == User.user_id)
                    .outerjoin(Guild, UsageLog.guild_id == Guild.guild_id)
                    .order_by(desc(UsageLog.timestamp))
                    .limit(limit)
                )
                result = await session.execute(stmt)
                records = result.all()
                
                return [
                    {
                        'conversion_type': usage_log.conversion_type,
                        'timestamp': usage_log.timestamp.isoformat(),
                        'file_size': usage_log.file_size,
                        'username': user.username,
                        'guild_name': guild.guild_name if guild else 'DM',
                        'guild_id': guild.guild_id if guild else None
                    }
                    for usage_log, user, guild in records
                ]
        except Exception as e:
            logging.error(f"獲取最近使用記錄失敗: {e}")
            return []
    
    async def cleanup_old_logs(self, days: int = 90):
        """清理舊的使用記錄"""
        await self._ensure_initialized()
        try:
            async with self.AsyncSessionLocal() as session:
                stmt = delete(UsageLog).where(
                    UsageLog.timestamp < func.datetime('now', f'-{days} days')
                )
                result = await session.execute(stmt)
                await session.commit()
                
                deleted_count = result.rowcount
                logging.info(f"清理了 {deleted_count} 筆 {days} 天前的舊記錄")
                return deleted_count
        except Exception as e:
            logging.error(f"清理記錄失敗: {e}")
            return 0
    

    
    async def get_database_stats(self) -> dict:
        """獲取資料庫統計資訊"""
        await self._ensure_initialized()
        try:
            async with self.AsyncSessionLocal() as session:
                # 獲取各資料表的記錄數量
                guilds_count_stmt = select(func.count(Guild.guild_id))
                guilds_result = await session.execute(guilds_count_stmt)
                guilds_count = guilds_result.scalar()
                
                users_count_stmt = select(func.count(User.user_id))
                users_result = await session.execute(users_count_stmt)
                users_count = users_result.scalar()
                
                logs_count_stmt = select(func.count(UsageLog.id))
                logs_result = await session.execute(logs_count_stmt)
                logs_count = logs_result.scalar()
                
                return {
                    'total_guilds': guilds_count,
                    'total_users': users_count,
                    'total_usage_logs': logs_count,
                    'database_path': self.db_path
                }
        except Exception as e:
            logging.error(f"獲取資料庫統計失敗: {e}")
            return {}
    
    async def close(self):
        """關閉資料庫連線"""
        try:
            await self.engine.dispose()
            logging.info("資料庫連線已關閉")
        except Exception as e:
            logging.error(f"關閉資料庫連線失敗: {e}")
    
    async def record_conversion(self, user, guild, file_size: int = None, conversion_type: str = "image_to_gif"):
        """記錄轉換使用（自動記錄用戶和伺服器資訊）"""
        await self._ensure_initialized()
        try:
            # 記錄用戶資訊
            await self.add_user(
                user_id=user.id,
                username=user.name,
                display_name=user.display_name or user.global_name
            )
            
            # 記錄伺服器資訊（如果在伺服器中使用）
            guild_id = None
            if guild:
                await self.add_guild(guild.id, guild.name, guild.member_count)
                guild_id = guild.id
            
            # 記錄使用記錄
            log_id = await self.log_usage(
                user_id=user.id,
                guild_id=guild_id,
                file_size=file_size,
                conversion_type=conversion_type
            )
            
            logging.info(f"記錄轉換使用: 用戶 {user.name} 在 {'伺服器 ' + guild.name if guild else 'DM'} 進行了 {conversion_type} 轉換")
            return log_id
            
        except Exception as e:
            logging.error(f"記錄轉換使用失敗: {e}")
            return None

# 創建全域資料庫實例
db = Database()
