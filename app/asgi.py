from litestar import Litestar


def create_app() -> "Litestar":
    import tomllib
    from pathlib import Path

    from litestar.openapi.config import OpenAPIConfig
    from litestar.openapi.plugins import JsonRenderPlugin, RedocRenderPlugin

    from .config import sqlite
    from .domain.accounts.guards import auth
    from .server import routers
    from .server.plugins import MigratorCLIPlugin
    from .server.plugins.database import SQLitePoolPlugin

    pyproject = tomllib.loads(
        (Path(__file__).parent.parent / "pyproject.toml").read_text()
    )

    return Litestar(
        routers.route_handlers,
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
        plugins=[
            MigratorCLIPlugin(),
            SQLitePoolPlugin(sqlite),
        ],
    )


app = create_app()
