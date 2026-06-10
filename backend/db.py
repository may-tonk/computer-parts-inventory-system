from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal

import pymysql
from pymysql.cursors import DictCursor

from config import Config


@contextmanager
def get_connection():
    connection = pymysql.connect(cursorclass=DictCursor, **Config.DB_CONFIG)
    try:
        yield connection
    finally:
        connection.close()


def query_all(sql, params=None):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()


def query_one(sql, params=None):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchone()


def execute(sql, params=None):
    with get_connection() as connection:
        try:
            with connection.cursor() as cursor:
                affected = cursor.execute(sql, params or ())
            connection.commit()
            return affected
        except Exception:
            connection.rollback()
            raise


def test_connection():
    return query_one("SELECT COUNT(*) AS brandCount FROM brand")


def to_camel(snake_name):
    parts = snake_name.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def serialize_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return value


def serialize_row(row, camel_case=True):
    if row is None:
        return None
    result = {}
    for key, value in row.items():
        result[to_camel(key) if camel_case else key] = serialize_value(value)
    return result


def serialize_rows(rows, camel_case=True):
    return [serialize_row(row, camel_case=camel_case) for row in rows]
