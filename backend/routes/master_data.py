from flask import Blueprint

from db import query_all
from responses import error, success

master_data_bp = Blueprint("master_data", __name__)


def _list_simple_table(table_name, id_column, name_column, extra_columns=None):
    extra_columns = extra_columns or []
    selected = [
        f"{id_column} AS id",
        f"{name_column} AS name",
        *extra_columns,
    ]
    sql = f"SELECT {', '.join(selected)} FROM {table_name} ORDER BY {id_column}"
    return query_all(sql)


@master_data_bp.get("/api/brands")
def get_brands():
    try:
        return success(_list_simple_table("brand", "brand_id", "brand_name"))
    except Exception as exc:
        return error(f"查询品牌失败：{exc}", code=500)


@master_data_bp.get("/api/categories")
def get_categories():
    try:
        return success(_list_simple_table("category", "category_id", "category_name"))
    except Exception as exc:
        return error(f"查询分类失败：{exc}", code=500)


@master_data_bp.get("/api/suppliers")
def get_suppliers():
    try:
        return success(
            _list_simple_table(
                "supplier",
                "supplier_id",
                "supplier_name",
                ["contact", "phone"],
            )
        )
    except Exception as exc:
        return error(f"查询供应商失败：{exc}", code=500)


@master_data_bp.get("/api/customers")
def get_customers():
    try:
        rows = query_all(
            """
            SELECT
                customer_id AS id,
                customer_name AS name,
                contact,
                phone,
                customer_level AS level
            FROM customer
            ORDER BY customer_id
            """
        )
        return success(rows)
    except Exception as exc:
        return error(f"查询客户失败：{exc}", code=500)


@master_data_bp.get("/api/warehouses")
def get_warehouses():
    try:
        rows = query_all(
            """
            SELECT
                warehouse_id AS id,
                warehouse_name AS name,
                manager
            FROM warehouse
            ORDER BY warehouse_id
            """
        )
        return success(rows)
    except Exception as exc:
        return error(f"查询仓库失败：{exc}", code=500)
