from app.server.plugins.database import SQLitePoolConfig

from .base import settings

sqlite = SQLitePoolConfig(database_path=settings.app.DATABASE_PATH)
