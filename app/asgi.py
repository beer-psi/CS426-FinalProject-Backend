from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import sqlite3

import aiosqlite
from litestar import Litestar
from litestar.datastructures import State
from litestar.di import Provide


def provide_db_connection(state: State) -> aiosqlite.Connection:
    return state["db_connection"]  # pyright: ignore[reportAny]


def set_connection_autocommit(connection: sqlite3.Connection, *, state: bool):
    connection.autocommit = state


@asynccontextmanager
async def db_connection(app: "Litestar") -> AsyncGenerator[None, None]:
    db_connection = app.state.get("db_connection")

    if db_connection is None:
        from app.database import adapters

        adapters.register_adapters()
        adapters.register_converters()

        db_connection = await aiosqlite.connect(
            "data/database.sqlite3", autocommit=True
        )
        db_connection.row_factory = aiosqlite.Row

        if (inner_connection := db_connection._connection) is not None:  # pyright: ignore[reportPrivateUsage]
            _ = await db_connection._execute(  # pyright: ignore[reportAny, reportPrivateUsage, reportUnknownMemberType]
                inner_connection.setconfig, sqlite3.SQLITE_DBCONFIG_DQS_DDL, False
            )
            _ = await db_connection._execute(  # pyright: ignore[reportAny, reportPrivateUsage, reportUnknownMemberType]
                inner_connection.setconfig, sqlite3.SQLITE_DBCONFIG_DQS_DML, False
            )

        _ = await db_connection.execute("PRAGMA journal_mode=WAL")
        _ = await db_connection.execute("PRAGMA synchronous=NORMAL")
        _ = await db_connection.execute("PRAGMA foreign_keys=ON")
        _ = await db_connection.execute("PRAGMA busy_timeout=100")
        _ = await db_connection.execute("PRAGMA optimize=0x10002")
        _ = await db_connection.execute("PRAGMA recursive_triggers=ON")

        # sqlite3 autocommit=False doesn't allow setting pragmas, hence this workaround
        if (inner_connection := db_connection._connection) is not None:  # pyright: ignore[reportPrivateUsage]
            _ = await db_connection._execute(  # pyright: ignore[reportAny, reportPrivateUsage, reportUnknownMemberType]
                set_connection_autocommit, inner_connection, state=False
            )

        app.state["db_connection"] = db_connection

    try:
        yield
    finally:
        if (inner_connection := db_connection._connection) is not None:  # pyright: ignore[reportPrivateUsage]
            _ = await db_connection._execute(  # pyright: ignore[reportAny, reportPrivateUsage, reportUnknownMemberType]
                set_connection_autocommit, inner_connection, state=True
            )

        _ = await db_connection.execute("PRAGMA optimize")
        _ = await db_connection.close()


def create_app() -> "Litestar":
    import tomllib
    from pathlib import Path

    from litestar.openapi.config import OpenAPIConfig
    from litestar.openapi.plugins import JsonRenderPlugin, RedocRenderPlugin

    from app.domain.accounts.guards import auth
    from app.server import routers
    from app.server.plugins import MigratorCLIPlugin

    pyproject = tomllib.loads(
        (Path(__file__).parent.parent / "pyproject.toml").read_text()
    )

    return Litestar(
        routers.route_handlers,
        dependencies={
            "db_connection": Provide(provide_db_connection, sync_to_thread=False)
        },
        lifespan=[db_connection],
        on_app_init=[auth.on_app_init],
        openapi_config=OpenAPIConfig(
            title=pyproject["project"]["name"],  # pyright: ignore[reportAny]
            version=pyproject["project"]["version"],  # pyright: ignore[reportAny]
            description=pyproject["project"]["description"],  # pyright: ignore[reportAny]
            render_plugins=[
                RedocRenderPlugin(),
                JsonRenderPlugin(),
            ],
        ),
        plugins=[MigratorCLIPlugin()],
    )


app = create_app()
