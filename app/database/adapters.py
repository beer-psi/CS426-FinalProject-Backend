from datetime import UTC, datetime

import aiosqlite


def adapt_datetime(val: datetime) -> str:
    return val.strftime("%Y-%m-%d %H:%M:%S")


def convert_datetime(val: bytes) -> datetime:
    dt = datetime.fromisoformat(val.decode())

    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)

    return dt


def register_adapters():
    aiosqlite.register_adapter(datetime, adapt_datetime)


def register_converters():
    aiosqlite.register_converter("datetime", convert_datetime)
