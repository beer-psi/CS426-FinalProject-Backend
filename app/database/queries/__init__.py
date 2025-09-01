from pathlib import Path

import aiosql

queries = aiosql.from_path(Path(__file__).parent, "aiosqlite", kwargs_only=True)  # pyright: ignore[reportUnknownMemberType]
