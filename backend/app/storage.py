import os
import json
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from typing import Optional, Any

# Environment Variables
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://argus:argus_password@localhost:5433/argus_db")

class RedisClient:
    _instance: Optional[redis.Redis] = None

    @classmethod
    def get_instance(cls) -> redis.Redis:
        if cls._instance is None:
            cls._instance = redis.from_url(REDIS_URL, decode_responses=True)
        return cls._instance

    @classmethod
    async def close(cls):
        if cls._instance:
            await cls._instance.aclose()
            cls._instance = None
            
    @classmethod
    async def get_json(cls, key: str) -> Optional[Any]:
        r = cls.get_instance()
        data = await r.get(key)
        return json.loads(data) if data else None

    @classmethod
    async def set_json(cls, key: str, value: Any, ttl: int = 60):
        r = cls.get_instance()
        await r.setex(key, ttl, json.dumps(value))


class ArqClient:
    _pool: Optional[Any] = None
    
    @classmethod
    async def get_redis(cls):
        from arq import create_pool
        from arq.connections import RedisSettings
        from urllib.parse import urlparse
        
        if cls._pool is None:
            # Parse URL manually for Arq Settings if not default
            url = urlparse(REDIS_URL)
            settings = RedisSettings(
                host=url.hostname or 'localhost',
                port=url.port or 6379,
                password=url.password,
                database=0
            )
            cls._pool = await create_pool(settings)
        return cls._pool
        
    @classmethod
    async def close(cls):
        if cls._pool:
            await cls._pool.close()
            cls._pool = None

class Database:
    _engine = None
    _sessionmaker = None

    @classmethod
    def init(cls):
        if cls._engine is None:
            cls._engine = create_async_engine(DATABASE_URL, echo=False)
            cls._sessionmaker = async_sessionmaker(cls._engine, expire_on_commit=False)
            
    @classmethod
    async def create_tables(cls):
        from sqlmodel import SQLModel
        # Ensure models are imported so metadata is populated
        from app.schemas.candle import Candle
        async with cls._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
    
    @classmethod
    def get_session(cls) -> AsyncSession:
        if cls._sessionmaker is None:
            cls.init()
        return cls._sessionmaker()

    @classmethod
    async def close(cls):
        if cls._engine:
            await cls._engine.dispose()
            cls._engine = None

# Dependency for FastAPI
async def get_db():
    async with Database.get_session() as session:
        yield session
