from flask import Blueprint

from db import test_connection
from responses import error, success

health_bp = Blueprint("health", __name__)


@health_bp.get("/api/health")
def health():
    return success("backend is running")


@health_bp.get("/api/db-test")
def db_test():
    try:
        result = test_connection()
        return success(result)
    except Exception as exc:
        return error(f"数据库连接失败：{exc}", code=500)
