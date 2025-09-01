import os
from dataclasses import dataclass, field


@dataclass
class AppSettings:
    DATABASE_PATH: str = field(
        default_factory=lambda: os.environ.get("DATABASE_PATH", "data/database.sqlite3")
    )
    SECRET_KEY: str = field(
        default_factory=lambda: os.environ.get("SECRET_KEY", os.urandom(32).hex())
    )
    GOOGLE_OAUTH2_CLIENT_ID: str | None = field(
        default_factory=lambda: os.environ.get("GOOGLE_OAUTH2_CLIENT_ID")
    )
    GOOGLE_OAUTH2_CLIENT_SECRET: str | None = field(
        default_factory=lambda: os.environ.get("GOOGLE_OAUTH2_CLIENT_SECRET")
    )


@dataclass
class Settings:
    app: AppSettings = field(default_factory=AppSettings)

    @classmethod
    def from_env(cls, dotenv_filename: str = ".env") -> "Settings":
        from dotenv import load_dotenv

        _ = load_dotenv(dotenv_filename, override=True)

        return Settings()


settings = Settings.from_env()
