import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.config import settings
from app.models.base import Base
from app.models import User, Sento, Review  # noqa: F401 - メタデータ登録のため

# Alembic Config オブジェクト
config = context.config

# DB URL を app.config.settings から取得して上書き
config.set_main_option("sqlalchemy.url", settings.database_url)

# ロギング設定
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# autogenerate のためのメタデータ
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """オフラインモード（DB 接続なし）でマイグレーション実行。

    URL だけを設定し、Engine を作らずにマイグレーション SQL を出力する。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """非同期エンジンを使ってオンラインモードでマイグレーション実行。"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """オンラインモードでマイグレーション実行。"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
