from datetime import UTC, datetime

import aiosqlite

DT_FORMAT = "%Y-%m-%d %H:%M:%S"


def adapt_datetime(val: datetime) -> str:
    return val.strftime(DT_FORMAT)


def convert_datetime(val: bytes) -> datetime:
    return datetime.strptime(val.decode(), DT_FORMAT).replace(tzinfo=UTC)


def register_adapters():
    aiosqlite.register_adapter(datetime, adapt_datetime)


def register_converters():
    aiosqlite.register_converter("datetime", convert_datetime)
