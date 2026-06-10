from os import getenv

from dotenv import load_dotenv

load_dotenv()


def _get_bool(name, default=False):
    value = getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name, default):
    value = getenv(name)
    if value is None or value == "":
        return default
    return int(value)


class Config:
    FLASK_HOST = getenv("FLASK_HOST", "127.0.0.1")
    FLASK_PORT = _get_int("FLASK_PORT", 5000)
    FLASK_DEBUG = _get_bool("FLASK_DEBUG", True)

    CORS_ORIGINS = [
        origin.strip()
        for origin in getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]

    DB_CONFIG = {
        "host": getenv("DB_HOST", "localhost"),
        "port": _get_int("DB_PORT", 3306),
        "user": getenv("DB_USER", ""),
        "password": getenv("DB_PASSWORD", ""),
        "database": getenv("DB_NAME", ""),
        "charset": getenv("DB_CHARSET", "utf8mb4"),
        "autocommit": False,
        "connect_timeout": _get_int("DB_CONNECT_TIMEOUT", 5),
        "read_timeout": _get_int("DB_READ_TIMEOUT", 5),
        "write_timeout": _get_int("DB_WRITE_TIMEOUT", 5),
    }
