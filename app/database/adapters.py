from datetime import UTC, datetime

import aiosqlite


def adapt_datetime(val: datetime) -> str:
    return val.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S")


def convert_datetime(val: bytes) -> datetime:
    return datetime.fromisoformat(val.decode()).replace(tzinfo=UTC)


def register_adapters():
    aiosqlite.register_adapter(datetime, adapt_datetime)


def register_converters():
    aiosqlite.register_converter("datetime", convert_datetime)
