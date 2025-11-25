from sqlalchemy import NullPool, create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings

params = {}
if settings.APP_ENV == "test":
    params = {"poolclass": NullPool}

engine = create_async_engine(settings.DB_URL_ASYNC, **params)


new_async_session = async_sessionmaker(bind=engine, expire_on_commit=False)


engine_null_pool = create_async_engine(settings.DB_URL_ASYNC, poolclass=NullPool)
new_async_session_null_pool = async_sessionmaker(bind=engine_null_pool, expire_on_commit=False)


sync_engine = create_engine(url=settings.DB_URL_SYNC)
new_sync_session = sessionmaker(bind=sync_engine, expire_on_commit=False)
