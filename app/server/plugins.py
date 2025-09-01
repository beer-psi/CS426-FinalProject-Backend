# pyright: reportUnusedFunction=false
import contextlib
import hashlib
import re
import sqlite3
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from errno import EINVAL, EISDIR
from pathlib import Path
from typing import Literal, cast, override

import click
import rich
from click import Group
from litestar.plugins import CLIPluginProtocol
from rich.prompt import Confirm

from app.config.base import settings

MIGRATION_FILE_RE = re.compile(
    r"(?P<version>\d+)_(?P<description>.+?)(?:\.(?P<migration_type>down|up))?\.sql"
)


@dataclass
class Migration:
    version: int
    description: str
    migration_type: Literal["down", "up"]
    sql: str
    checksum: bytes
    no_tx: bool

    @classmethod
    def from_file(cls, file: Path) -> "Migration":
        match = MIGRATION_FILE_RE.match(file.name)

        if match is None:
            raise ValueError(f"invalid migration file name: {file.name}")

        version = int(match.group("version"))
        description = match.group("description").replace("_", " ")
        migration_type = cast(
            Literal["down", "up"] | None, match.group("migration_type")
        )
        sql_bytes = file.read_bytes()
        checksum = hashlib.sha384(sql_bytes).digest()
        sql = sql_bytes.decode("utf-8")
        no_tx = sql.startswith("-- no-transaction")

        return cls(version, description, migration_type or "up", sql, checksum, no_tx)


class Migrator:
    def __init__(self, source: Path) -> None:
        if source.exists() and not source.is_dir():
            raise ValueError("given migration source is not a directory")

        self.source: Path = source
        self.migrations: list[Migration] = []

    def resolve_migrations(self):
        if self.source.exists():
            self.migrations = [
                Migration.from_file(file) for file in self.source.glob("*.sql")
            ]

        self.migrations.sort(key=lambda m: m.version)

        return self.migrations


def configure_connection(conn: sqlite3.Connection):
    # cursed fucking workaround since python 3.12 opens an implicit transaction if autocommit is set
    # to false, which disallows setting pragma.
    old_autocommit = conn.autocommit
    conn.autocommit = True

    _ = conn.setconfig(sqlite3.SQLITE_DBCONFIG_DQS_DDL, False)
    _ = conn.setconfig(sqlite3.SQLITE_DBCONFIG_DQS_DML, False)

    with contextlib.closing(conn.cursor()) as cursor:
        _ = cursor.execute("PRAGMA journal_mode=WAL")
        _ = cursor.execute("PRAGMA synchronous=NORMAL")
        _ = cursor.execute("PRAGMA foreign_keys=ON")
        _ = cursor.execute("PRAGMA busy_timeout=100")
        _ = cursor.execute("PRAGMA recursive_triggers=ON")

    conn.autocommit = old_autocommit


def ensure_migrations_table(conn: sqlite3.Connection):
    _ = conn.execute("""CREATE TABLE IF NOT EXISTS _sqlx_migrations (
        version BIGINT PRIMARY KEY,
        description TEXT NOT NULL,
        installed_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        success BOOLEAN NOT NULL,
        checksum BLOB NOT NULL,
        execution_time BIGINT NOT NULL
    )""")
    conn.commit()


def check_dirty_migration(conn: sqlite3.Connection):
    cursor = conn.execute(
        "SELECT version FROM _sqlx_migrations WHERE success = FALSE ORDER BY version LIMIT 1"
    )
    dirty_version: sqlite3.Row | None = cursor.fetchone()  # pyright: ignore[reportAny]

    if dirty_version is not None:
        rich.print(
            f"[bold][red]error:[/red][/bold] migration {dirty_version['version']} is partially applied, fix and remove row from `_sqlx_migrations` table"
        )
        exit(1)


def validate_applied_migrations(
    applied_migrations: list[sqlite3.Row],
    migrations: list[Migration],
    *,
    ignore_missing: bool = False,
):
    migration_versions = {migration.version for migration in migrations}

    for applied_migration in applied_migrations:
        if applied_migration["version"] not in migration_versions:
            msg = f"migration {applied_migration['version']} was previously applied but is missing in the resolved migrations"
            if not ignore_missing:
                rich.print(f"[bold][red]error:[/red][/bold] {msg}")
                exit(1)

            rich.print(f"[bold][yellow]warn:[/yellow][/bold] {msg}")


class MigratorCLIPlugin(CLIPluginProtocol):
    @override
    def on_cli_init(self, cli: Group) -> None:
        super().on_cli_init(cli)

        @cli.group(
            "database",
            invoke_without_command=False,
            help="Commands for creating and dropping database.",
        )
        def db():
            pass

        @db.command(
            "create",
            help="Creates the database at the specified database path.",
        )
        @click.option(
            "-D",
            "--database-path",
            help=f"Location of the DB, by default will be read from the DATABASE_PATH env var or `.env` files. (env: {settings.app.DATABASE_PATH})",
            type=Path,
            default=Path(settings.app.DATABASE_PATH)
            if settings.app.DATABASE_PATH
            else None,
        )
        def db_create(*, database_path: Path | None):
            if database_path is None:
                rich.print(
                    "[bold][red]error:[/red][/bold] no database path provided. provide one with --database-path or the DATABASE_PATH env var."
                )
                exit(EINVAL)

            if database_path.exists() and not database_path.is_file():
                rich.print(
                    "[bold][red]error:[/red][/bold] given database path already exists as a directory"
                )
                exit(EISDIR)

            if database_path.exists():
                return

            conn = sqlite3.connect(database_path, autocommit=False)

            configure_connection(conn)
            ensure_migrations_table(conn)

        @db.command(
            "drop",
            help="Drops the database at the specified database path.",
        )
        @click.option(
            "-D",
            "--database-path",
            help=f"Location of the DB, by default will be read from the DATABASE_PATH env var or `.env` files. (env: {settings.app.DATABASE_PATH})",
            type=Path,
            default=Path(settings.app.DATABASE_PATH)
            if settings.app.DATABASE_PATH
            else None,
        )
        def db_drop(*, database_path: Path | None):
            if database_path is None:
                rich.print(
                    "[bold][red]error:[/red][/bold] no database path provided. provide one with --database-path or the DATABASE_PATH env var."
                )
                exit(EINVAL)

            if database_path.exists() and not database_path.is_file():
                rich.print(
                    "[bold][red]error:[/red][/bold] given database path exists as a directory"
                )
                exit(EISDIR)

            if not database_path.exists():
                return

            if Confirm.ask(f"Drop database at {database_path}?", default=False):
                database_path.unlink()

                for extension in ("journal", "shm", "wal"):
                    database_extra_path = database_path.with_suffix(
                        f"{database_path.suffix}-{extension}"
                    )

                    if database_extra_path.exists():
                        database_extra_path.unlink()
            else:
                exit(1)

        @db.command(
            "reset",
            help="Drops the database at the specified database path, re-creates it, and runs any pending migrations",
        )
        @click.option(
            "--source",
            help="Path to folder containing migrations",
            type=Path,
            default=Path("migrations"),
        )
        @click.option(
            "-D",
            "--database-path",
            help=f"Location of the DB, by default will be read from the DATABASE_PATH env var or `.env` files. (env: {settings.app.DATABASE_PATH})",
            type=Path,
            default=Path(settings.app.DATABASE_PATH)
            if settings.app.DATABASE_PATH
            else None,
        )
        def db_reset(*, source: Path | None, database_path: Path | None):
            db_drop.callback(database_path=database_path)  # pyright: ignore[reportOptionalCall]
            db_create.callback(database_path=database_path)  # pyright: ignore[reportOptionalCall]
            migrate_run.callback(  # pyright: ignore[reportOptionalCall]
                source=source,
                dry_run=False,
                ignore_missing=False,
                database_path=database_path,
                target_version=None,
            )

        @db.command(
            "reset",
            help="Creates the database at the specified database path and runs any pending migrations",
        )
        @click.option(
            "--source",
            help="Path to folder containing migrations",
            type=Path,
            default=Path("migrations"),
        )
        @click.option(
            "-D",
            "--database-path",
            help=f"Location of the DB, by default will be read from the DATABASE_PATH env var or `.env` files. (env: {settings.app.DATABASE_PATH})",
            type=Path,
            default=Path(settings.app.DATABASE_PATH)
            if settings.app.DATABASE_PATH
            else None,
        )
        def db_setup(*, source: Path | None, database_path: Path | None):
            db_create.callback(database_path=database_path)  # pyright: ignore[reportOptionalCall]
            migrate_run.callback(  # pyright: ignore[reportOptionalCall]
                source=source,
                dry_run=False,
                ignore_missing=False,
                database_path=database_path,
                target_version=None,
            )

        @cli.group(
            "migrate",
            invoke_without_command=False,
            help="Commands for creating and running migrations.",
        )
        def migrate():
            pass

        @migrate.command(
            "add",
            help="Create a new migration with the given DESCRIPTION.",
            short_help="Create a new migration with the given description.",
        )
        @click.argument("description")
        @click.option(
            "--source",
            help="Path to folder containing migrations",
            type=Path,
            default=Path("migrations"),
        )
        def migrate_add(description: str, *, source: Path):
            if source.exists() and not source.is_dir():
                rich.print(
                    "[bold][red]error:[/red][/bold] migration source is not a directory"
                )
                exit(EINVAL)

            if not source.exists():
                try:
                    source.mkdir(parents=True)
                except OSError as e:
                    rich.print(
                        "[bold][red]error:[/red][/bold] unable to create migrations directory"
                    )
                    exit(e.errno)

            migration_version = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
            migration_description = description.replace(" ", "_")

            for migration_type in ("up", "down"):
                migration_file = (
                    source
                    / f"{migration_version}_{migration_description}.{migration_type}.sql"
                )

                rich.print(f"Creating [cyan]{migration_file}[/cyan]")

                try:
                    _ = migration_file.write_text(
                        f"-- Add {migration_type} migration script here"
                    )
                except Exception as e:
                    rich.print(
                        f"[bold][red]error:[/red][/bold] unable to create migration file: {e}"
                    )
                    exit(1)

        @migrate.command("run", help="Run all pending migrations.")
        @click.option(
            "--source",
            help="Path to folder containing migrations",
            type=Path,
            default=Path("migrations"),
        )
        @click.option(
            "--dry-run",
            help="List all the migrations to be run without applying",
            is_flag=True,
        )
        @click.option(
            "--ignore-missing",
            help="Ignore applied migrations that are missing in the resolved migrations",
            is_flag=True,
        )
        @click.option(
            "-D",
            "--database-path",
            help=f"Location of the DB, by default will be read from the DATABASE_PATH env var or `.env` files. (env: {settings.app.DATABASE_PATH})",
            type=Path,
            default=Path(settings.app.DATABASE_PATH)
            if settings.app.DATABASE_PATH
            else None,
        )
        @click.option(
            "--target-version",
            help="Apply migrations up to the specified version. If unspecified, apply all pending migrations. If already at the target version, then no-op.",
            type=int,
            default=None,
        )
        def migrate_run(
            *,
            source: Path,
            dry_run: bool,
            ignore_missing: bool,
            database_path: Path | None,
            target_version: int | None,
        ):
            if database_path is None:
                rich.print(
                    "[bold][red]error:[/red][/bold] no database path provided. provide one with --database-path or the DATABASE_PATH env var."
                )
                exit(EINVAL)

            try:
                migrator = Migrator(source)
                migrations = migrator.resolve_migrations()
            except ValueError as e:
                rich.print(f"[bold][red]error:[/red][/bold] {e}")
                exit(EINVAL)

            conn = sqlite3.connect(database_path, autocommit=False)
            conn.row_factory = sqlite3.Row

            configure_connection(conn)
            ensure_migrations_table(conn)
            check_dirty_migration(conn)

            cursor = conn.execute(
                "SELECT version, checksum FROM _sqlx_migrations ORDER BY version"
            )
            applied_migrations: list[sqlite3.Row] = cursor.fetchall()

            validate_applied_migrations(
                applied_migrations,
                migrations,
                ignore_missing=ignore_missing,
            )

            if len(applied_migrations) > 0:
                latest_version: int = max(  # pyright: ignore[reportAny]
                    applied_migrations,
                    key=lambda x: x["version"],  # pyright: ignore[reportAny]
                )["version"]
            else:
                latest_version = 0

            if target_version is not None and target_version < latest_version:
                rich.print(
                    f"[bold][red]error:[/red][/bold] migration {target_version} is older than the latest applied migration {latest_version}"
                )
                exit(1)

            checksum_map: dict[int, bytes] = {
                x["version"]: x["checksum"] for x in applied_migrations
            }

            for migration in migrations:
                if migration.migration_type == "down":
                    continue

                checksum = checksum_map.get(migration.version)

                if checksum is not None and checksum != migration.checksum:
                    rich.print(
                        f"[bold][red]error:[/red][/bold] migration {migration.version} was previously applied but has been modified"
                    )
                    exit(1)

                if checksum is not None:
                    continue

                skip = target_version is not None and migration.version > target_version
                displayed_version = f"[cyan]{migration.version}[/cyan]/[green]{migration.migration_type}[/green] {migration.description}"

                if skip:
                    rich.print(f"Skipped {displayed_version}")
                elif dry_run:
                    rich.print(f"Can apply {displayed_version}")
                else:
                    try:
                        start_time = time.perf_counter_ns()
                        cursor = conn.executescript(migration.sql)
                        _ = cursor.execute(
                            "INSERT INTO _sqlx_migrations(version, description, success, checksum, execution_time) VALUES (?, ?, ?, ?, ?)",
                            (
                                migration.version,
                                migration.description,
                                True,
                                migration.checksum,
                                -1,
                            ),
                        )
                        conn.commit()
                        end_time = time.perf_counter_ns()
                    except sqlite3.Error as e:
                        rich.print(
                            f"[bold][red]error:[/red][/bold] while executing migration: {e}"
                        )
                        exit(1)

                    with contextlib.suppress(sqlite3.Error):
                        _ = cursor.execute(
                            "UPDATE _sqlx_migrations SET execution_time = ? WHERE version = ?",
                            (end_time - start_time, migration.version),
                        )
                        conn.commit()

                    rich.print(
                        f"Applied {displayed_version} ({(end_time - start_time) / 1000000:.4f}ms)",
                    )

        @migrate.command("revert", help="Revert migrations with a down file.")
        @click.option(
            "--source",
            help="Path to folder containing migrations",
            type=Path,
            default=Path("migrations"),
        )
        @click.option(
            "--dry-run",
            help="List all the migrations to be run without applying",
            is_flag=True,
        )
        @click.option(
            "--ignore-missing",
            help="Ignore applied migrations that are missing in the resolved migrations",
            is_flag=True,
        )
        @click.option(
            "-D",
            "--database-path",
            help=f"Location of the DB, by default will be read from the DATABASE_PATH env var or `.env` files. (env: {settings.app.DATABASE_PATH})",
            type=Path,
            default=Path(settings.app.DATABASE_PATH)
            if settings.app.DATABASE_PATH
            else None,
        )
        @click.option(
            "--target-version",
            help="Apply migrations up to the specified version. If unspecified, apply all pending migrations. If already at the target version, then no-op.",
            type=int,
            default=None,
        )
        def migrate_revert(
            *,
            source: Path,
            dry_run: bool,
            ignore_missing: bool,
            database_path: Path | None,
            target_version: int | None,
        ):
            if database_path is None:
                rich.print(
                    "[bold][red]error:[/red][/bold] no database path provided. provide one with --database-path or the DATABASE_PATH env var."
                )
                exit(EINVAL)

            try:
                migrator = Migrator(source)
                migrations = migrator.resolve_migrations()
            except ValueError as e:
                rich.print(f"[bold][red]error:[/red][/bold] {e}")
                exit(EINVAL)

            conn = sqlite3.connect(database_path, autocommit=False)
            conn.row_factory = sqlite3.Row

            configure_connection(conn)
            ensure_migrations_table(conn)
            check_dirty_migration(conn)

            cursor = conn.execute(
                "SELECT version, checksum FROM _sqlx_migrations ORDER BY version"
            )
            applied_migrations: list[sqlite3.Row] = cursor.fetchall()

            validate_applied_migrations(
                applied_migrations,
                migrations,
                ignore_missing=ignore_missing,
            )

            if len(applied_migrations) > 0:
                latest_version: int = max(  # pyright: ignore[reportAny]
                    applied_migrations,
                    key=lambda x: x["version"],  # pyright: ignore[reportAny]
                )["version"]
            else:
                latest_version = 0

            if target_version is not None and target_version < latest_version:
                rich.print(
                    f"[bold][red]error:[/red][/bold] migration {target_version} is older than the latest applied migration {latest_version}"
                )
                exit(1)

            checksum_map: dict[int, bytes] = {
                x["version"]: x["checksum"] for x in applied_migrations
            }

            for migration in reversed(migrations):
                if migration.migration_type == "up":
                    continue

                if migration.version not in checksum_map:
                    continue

                skip = (
                    target_version is not None and migration.version <= target_version
                )
                displayed_version = f"[cyan]{migration.version}[/cyan]/[green]{migration.migration_type}[/green] {migration.description}"

                if skip:
                    rich.print(f"Skipped {displayed_version}")
                elif dry_run:
                    rich.print(f"Can apply {displayed_version}")
                else:
                    try:
                        start_time = time.perf_counter_ns()
                        cursor = conn.executescript(migration.sql)
                        _ = cursor.execute(
                            "DELETE FROM _sqlx_migrations WHERE version = ?",
                            (migration.version,),
                        )
                        conn.commit()
                        end_time = time.perf_counter_ns()
                    except sqlite3.Error as e:
                        rich.print(
                            f"[bold][red]error:[/red][/bold] while executing migration: {e}"
                        )
                        exit(1)

                    with contextlib.suppress(sqlite3.Error):
                        _ = cursor.execute(
                            "UPDATE _sqlx_migrations SET execution_time = ? WHERE version = ?",
                            (end_time - start_time, migration.version),
                        )
                        conn.commit()

                    rich.print(
                        f"Applied {displayed_version} ({(end_time - start_time) / 1000000:.4f}ms)",
                    )

                if target_version is None:
                    break

        @migrate.command("info", help="List all available migrations.")
        @click.option(
            "--source",
            help="Path to folder containing migrations",
            type=Path,
            default=Path("migrations"),
        )
        @click.option(
            "-D",
            "--database-path",
            help=f"Location of the DB, by default will be read from the DATABASE_PATH env var or `.env` files. (env: {settings.app.DATABASE_PATH})",
            type=Path,
            default=Path(settings.app.DATABASE_PATH)
            if settings.app.DATABASE_PATH
            else None,
        )
        def migrate_info(*, source: Path, database_path: Path | None):
            if database_path is None:
                rich.print(
                    "[bold][red]error:[/red][/bold] no database path provided. provide one with --database-path or the DATABASE_PATH env var."
                )
                exit(EINVAL)

            try:
                migrator = Migrator(source)
                migrations = migrator.resolve_migrations()
            except ValueError as e:
                rich.print(f"[bold][red]error:[/red][/bold] {e}")
                exit(EINVAL)

            conn = sqlite3.connect(database_path, autocommit=False)
            conn.row_factory = sqlite3.Row

            configure_connection(conn)
            ensure_migrations_table(conn)

            cursor = conn.execute(
                "SELECT version, checksum FROM _sqlx_migrations ORDER BY version"
            )
            applied_migrations: dict[int, bytes] = {
                row["version"]: row["checksum"]
                for row in cursor.fetchall()  # pyright: ignore[reportAny]
            }

            for migration in migrations:
                if migration.migration_type == "down":
                    continue

                checksum = applied_migrations.get(migration.version)
                checksum_mismatch = (
                    checksum is not None and checksum != migration.checksum
                )

                if checksum_mismatch:
                    status_message = "[red]installed (different checksum)[/red]"
                elif checksum is not None:
                    status_message = "[green]installed[/green]"
                else:
                    status_message = "[yellow]pending[/yellow]"

                rich.print(
                    f"[cyan]{migration.version}[/cyan]/{status_message} {migration.description}"
                )

                if checksum_mismatch:
                    assert checksum is not None

                    rich.print(f"applied migration had checksum {checksum.hex()}")
                    rich.print(
                        f"local migration has checksum {migration.checksum.hex()}"
                    )
