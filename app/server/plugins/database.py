# pyright: reportPrivateUsage=false, reportAny=false, reportExplicitAny=false, reportUnknownMemberType=false, reportMissingTypeStubs=false
import sqlite3
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, cast, override

import aiosqlite
import aiosqlitepool.protocols
from aiosqlitepool import SQLiteConnectionPool
from litestar import Litestar
from litestar.config.app import AppConfig
from litestar.datastructures import State
from litestar.di import Provide
from litestar.exceptions import ImproperlyConfiguredException
from litestar.plugins import InitPluginProtocol


def set_connection_autocommit(connection: sqlite3.Connection, *, state: bool):
    connection.autocommit = state


@dataclass(kw_only=True)
class SQLitePoolConfig:
    database_path: str | Path

    pool_dependency_key: str = "db_pool"
    connection_dependency_key: str = "db_connection"

    pool_app_state_key: str = "db_pool"

    _POOL_APP_STATE_KEY_REGISTRY: ClassVar[set[str]] = field(init=False, default=set())

    pool_size: int | None = 10
    acquisition_timeout: int | None = 30
    idle_timeout: int | None = 86400
    operation_timeout: int | None = 10

    def _ensure_unique(
        self,
        registry_name: str,
        key: str,
        new_key: str | None = None,
        _iter: int = 0,
    ) -> str:
        new_key = new_key if new_key is not None else key
        if new_key in getattr(self.__class__, registry_name, {}):
            _iter += 1
            new_key = self._ensure_unique(registry_name, key, f"{key}_{_iter}", _iter)
        return new_key

    def __post_init__(self) -> None:
        self.pool_app_state_key = self._ensure_unique(
            "_POOL_APP_STATE_KEY_REGISTRY", self.pool_app_state_key
        )
        self.__class__._POOL_APP_STATE_KEY_REGISTRY.add(self.pool_app_state_key)

    async def _connection_factory(self):
        connection = await aiosqlite.connect(self.database_path)
        connection.row_factory = aiosqlite.Row

        if (inner := connection._connection) is not None:
            _ = await connection._execute(
                inner.setconfig, sqlite3.SQLITE_DBCONFIG_DQS_DDL, False
            )
            _ = await connection._execute(
                inner.setconfig, sqlite3.SQLITE_DBCONFIG_DQS_DML, False
            )

        _ = await connection.execute("PRAGMA journal_mode=WAL")
        _ = await connection.execute("PRAGMA synchronous=NORMAL")
        _ = await connection.execute("PRAGMA foreign_keys=ON")
        _ = await connection.execute("PRAGMA busy_timeout=100")
        _ = await connection.execute("PRAGMA recursive_triggers=ON")

        if (inner := connection._connection) is not None:
            _ = await connection._execute(set_connection_autocommit, inner, state=False)

        return cast(aiosqlitepool.protocols.Connection, cast(object, connection))

    @asynccontextmanager
    async def lifespan(self, app: Litestar):
        pool = SQLiteConnectionPool(
            self._connection_factory,
            pool_size=self.pool_size,
            acquisition_timeout=self.acquisition_timeout,
            idle_timeout=self.idle_timeout,
            operation_timeout=self.operation_timeout,
        )
        app.state[self.pool_app_state_key] = pool

        try:
            yield
        finally:
            await pool.close()

    def provide_pool(self, state: State) -> SQLiteConnectionPool:
        return state[self.pool_app_state_key]

    async def provide_connection(
        self, state: State
    ) -> AsyncGenerator[aiosqlite.Connection, Any]:
        pool: SQLiteConnectionPool = state[self.pool_app_state_key]

        async with pool.connection() as generic_connection:
            yield cast(aiosqlite.Connection, cast(object, generic_connection))


class SQLitePoolPlugin(InitPluginProtocol):
    def __init__(self, config: SQLitePoolConfig | Sequence[SQLitePoolConfig]) -> None:
        if isinstance(config, Sequence):
            self._config: Sequence[SQLitePoolConfig] = config
        else:
            self._config = [config]

    @property
    def config(self):
        return self._config

    def _validate_config(self):
        if len(self._config) == 1:
            return

        pool_dependency_keys = {c.pool_dependency_key for c in self._config}
        connection_keys = {c.connection_dependency_key for c in self._config}

        if len(pool_dependency_keys) != len(self._config):
            raise ImproperlyConfiguredException(
                "pool dependency keys are not unique across multiple configurations"
            )

        if len(connection_keys) != len(self._config):
            raise ImproperlyConfiguredException(
                "connection dependency keys are not unique across multiple configurations"
            )

    @override
    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        self._validate_config()

        for config in self._config:
            app_config.lifespan.append(config.lifespan)
            app_config.dependencies.update(
                {
                    config.pool_dependency_key: Provide(
                        config.provide_pool, sync_to_thread=False
                    ),
                    config.connection_dependency_key: Provide(
                        config.provide_connection
                    ),
                }
            )

        return app_config
