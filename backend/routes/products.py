from flask import Blueprint, request

from db import (
    execute,
    get_connection,
    query_one,
    query_all,
    serialize_row,
    serialize_rows,
)
from responses import error, success

products_bp = Blueprint("products", __name__)


ATTRIBUTE_TABLES = {
    "CPU": "cpu_attributes",
    "内存条": "memory_attributes",
    "硬盘": "disk_attributes",
    "主板": "motherboard_attributes",
}

ATTRIBUTE_FIELDS = {
    "CPU": {
        "table": "cpu_attributes",
        "fields": [
            ("cores", "cores"),
            ("threads", "threads"),
            ("baseFrequency", "base_frequency"),
            ("maxFrequency", "max_frequency"),
            ("socketType", "socket_type"),
            ("tdp", "tdp"),
        ],
    },
    "内存条": {
        "table": "memory_attributes",
        "fields": [
            ("capacity", "capacity"),
            ("memoryType", "memory_type"),
            ("frequency", "frequency"),
            ("timing", "timing"),
        ],
    },
    "硬盘": {
        "table": "disk_attributes",
        "fields": [
            ("diskType", "disk_type"),
            ("interfaceType", "interface_type"),
            ("capacity", "capacity"),
            ("cacheSize", "cache_size"),
        ],
    },
    "主板": {
        "table": "motherboard_attributes",
        "fields": [
            ("chipset", "chipset"),
            ("socketType", "socket_type"),
            ("formFactor", "form_factor"),
            ("memorySlots", "memory_slots"),
            ("maxMemory", "max_memory"),
        ],
    },
}

VALID_PRODUCT_STATUSES = {"在售", "停用"}


def _clean_text(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _non_negative_number(value, default=0):
    if value is None or value == "":
        return default
    value = float(value)
    if value < 0:
        raise ValueError
    return value


def _non_negative_int(value, default=0):
    if value is None or value == "":
        return default
    value = int(value)
    if value < 0:
        raise ValueError
    return value


def _get_category(cursor, category_id):
    cursor.execute(
        "SELECT category_id, category_name FROM category WHERE category_id = %s",
        (category_id,),
    )
    return cursor.fetchone()


def _ensure_brand_exists(cursor, brand_id):
    cursor.execute("SELECT brand_id FROM brand WHERE brand_id = %s", (brand_id,))
    return cursor.fetchone() is not None


def _normalize_product_payload(payload):
    name = _clean_text(payload.get("name"))
    category_id = payload.get("categoryId")
    brand_id = payload.get("brandId")
    model = _clean_text(payload.get("model"))
    status = payload.get("status") or "在售"

    if not name:
        raise ValueError("请输入配件名称")
    if not category_id:
        raise ValueError("请选择分类")
    if not brand_id:
        raise ValueError("请选择品牌")
    if status not in VALID_PRODUCT_STATUSES:
        raise ValueError("配件状态只能是 在售 或 停用")

    try:
        category_id = int(category_id)
        brand_id = int(brand_id)
        purchase_price = _non_negative_number(payload.get("purchasePrice"), 0)
        sale_price = _non_negative_number(payload.get("salePrice"), 0)
        warning_value = _non_negative_int(payload.get("warningValue"), 0)
    except (TypeError, ValueError):
        raise ValueError("价格和库存预警值必须为非负数字")

    return {
        "name": name,
        "categoryId": category_id,
        "brandId": brand_id,
        "model": model,
        "purchasePrice": purchase_price,
        "salePrice": sale_price,
        "warningValue": warning_value,
        "status": status,
        "remark": _clean_text(payload.get("remark")),
        "attributes": payload.get("attributes") or {},
    }


def _attribute_values(category_name, attributes):
    config = ATTRIBUTE_FIELDS.get(category_name)
    if not config:
        return None, [], []

    values = []
    columns = []
    for frontend_key, column_name in config["fields"]:
        # Keep compatibility with the earlier frontend field name.
        value = attributes.get(frontend_key)
        if frontend_key == "cacheSize" and value is None:
            value = attributes.get("cache")
        columns.append(column_name)
        values.append(value)
    return config["table"], columns, values


def _replace_attributes(cursor, product_id, category_name, attributes):
    for table_name in ATTRIBUTE_TABLES.values():
        cursor.execute(f"DELETE FROM {table_name} WHERE product_id = %s", (product_id,))

    table_name, columns, values = _attribute_values(category_name, attributes)
    if not table_name:
        return

    column_sql = ", ".join(["product_id", *columns])
    placeholder_sql = ", ".join(["%s"] * (len(columns) + 1))
    cursor.execute(
        f"INSERT INTO {table_name} ({column_sql}) VALUES ({placeholder_sql})",
        (product_id, *values),
    )


@products_bp.get("/api/products")
def get_products():
    try:
        filters = []
        params = []

        keyword = request.args.get("keyword", "").strip()
        category_id = request.args.get("categoryId")
        brand_id = request.args.get("brandId")
        status = request.args.get("status")

        if keyword:
            filters.append("(p.product_name LIKE %s OR p.model LIKE %s)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if category_id:
            filters.append("p.category_id = %s")
            params.append(category_id)
        if brand_id:
            filters.append("p.brand_id = %s")
            params.append(brand_id)
        if status:
            filters.append("p.status = %s")
            params.append(status)

        where_sql = f"WHERE {' AND '.join(filters)}" if filters else ""
        rows = query_all(
            f"""
            SELECT
                p.product_id AS id,
                p.product_name AS name,
                p.category_id,
                c.category_name,
                p.brand_id,
                b.brand_name,
                p.model,
                p.purchase_price,
                p.sale_price,
                p.warning_value,
                COALESCE(SUM(s.quantity), 0) AS stock,
                p.status,
                p.created_at
            FROM product p
            JOIN category c ON p.category_id = c.category_id
            JOIN brand b ON p.brand_id = b.brand_id
            LEFT JOIN stock s ON p.product_id = s.product_id
            {where_sql}
            GROUP BY
                p.product_id,
                p.product_name,
                p.category_id,
                c.category_name,
                p.brand_id,
                b.brand_name,
                p.model,
                p.purchase_price,
                p.sale_price,
                p.warning_value,
                p.status,
                p.created_at
            ORDER BY p.product_id
            """,
            params,
        )
        return success(serialize_rows(rows))
    except Exception as exc:
        return error(f"查询配件列表失败：{exc}", code=500)


@products_bp.get("/api/products/<int:product_id>")
def get_product_detail(product_id):
    try:
        product = query_one(
            """
            SELECT
                p.product_id AS id,
                p.product_name AS name,
                p.category_id,
                c.category_name,
                p.brand_id,
                b.brand_name,
                p.model,
                p.purchase_price,
                p.sale_price,
                p.warning_value,
                p.status,
                p.remark,
                p.created_at
            FROM product p
            JOIN category c ON p.category_id = c.category_id
            JOIN brand b ON p.brand_id = b.brand_id
            WHERE p.product_id = %s
            """,
            (product_id,),
        )

        if not product:
            return error("配件不存在", code=404)

        table_name = ATTRIBUTE_TABLES.get(product["category_name"])
        attributes = {}
        if table_name:
            attribute_row = query_one(
                f"SELECT * FROM {table_name} WHERE product_id = %s",
                (product_id,),
            )
            if attribute_row:
                attribute_row.pop("product_id", None)
                attributes = serialize_row(attribute_row)

        data = serialize_row(product)
        data["attributes"] = attributes
        return success(data)
    except Exception as exc:
        return error(f"查询配件详情失败：{exc}", code=500)


@products_bp.post("/api/products")
def create_product():
    try:
        payload = request.get_json(silent=True) or {}
        data = _normalize_product_payload(payload)

        with get_connection() as connection:
            try:
                with connection.cursor() as cursor:
                    category = _get_category(cursor, data["categoryId"])
                    if not category:
                        return error("分类不存在", code=400)
                    if not _ensure_brand_exists(cursor, data["brandId"]):
                        return error("品牌不存在", code=400)

                    cursor.execute(
                        """
                        INSERT INTO product (
                            product_name,
                            category_id,
                            brand_id,
                            model,
                            purchase_price,
                            sale_price,
                            warning_value,
                            status,
                            remark
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            data["name"],
                            data["categoryId"],
                            data["brandId"],
                            data["model"],
                            data["purchasePrice"],
                            data["salePrice"],
                            data["warningValue"],
                            data["status"],
                            data["remark"],
                        ),
                    )
                    product_id = cursor.lastrowid
                    _replace_attributes(
                        cursor,
                        product_id,
                        category["category_name"],
                        data["attributes"],
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

        product = query_one(
            """
            SELECT
                p.product_id AS id,
                p.product_name AS name,
                p.category_id,
                c.category_name,
                p.brand_id,
                b.brand_name,
                p.model,
                p.purchase_price,
                p.sale_price,
                p.warning_value,
                0 AS stock,
                p.status,
                p.created_at
            FROM product p
            JOIN category c ON p.category_id = c.category_id
            JOIN brand b ON p.brand_id = b.brand_id
            WHERE p.product_id = %s
            """,
            (product_id,),
        )
        return success(serialize_row(product), message="配件已新增", code=201)
    except ValueError as exc:
        return error(str(exc), code=400)
    except Exception as exc:
        return error(f"新增配件失败：{exc}", code=500)


@products_bp.put("/api/products/<int:product_id>")
def update_product(product_id):
    try:
        payload = request.get_json(silent=True) or {}
        data = _normalize_product_payload(payload)

        with get_connection() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT product_id FROM product WHERE product_id = %s",
                        (product_id,),
                    )
                    if not cursor.fetchone():
                        return error("配件不存在", code=404)

                    category = _get_category(cursor, data["categoryId"])
                    if not category:
                        return error("分类不存在", code=400)
                    if not _ensure_brand_exists(cursor, data["brandId"]):
                        return error("品牌不存在", code=400)

                    cursor.execute(
                        """
                        UPDATE product
                        SET
                            product_name = %s,
                            category_id = %s,
                            brand_id = %s,
                            model = %s,
                            purchase_price = %s,
                            sale_price = %s,
                            warning_value = %s,
                            status = %s,
                            remark = %s
                        WHERE product_id = %s
                        """,
                        (
                            data["name"],
                            data["categoryId"],
                            data["brandId"],
                            data["model"],
                            data["purchasePrice"],
                            data["salePrice"],
                            data["warningValue"],
                            data["status"],
                            data["remark"],
                            product_id,
                        ),
                    )
                    _replace_attributes(
                        cursor,
                        product_id,
                        category["category_name"],
                        data["attributes"],
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

        return success({"id": product_id}, message="配件已更新")
    except ValueError as exc:
        return error(str(exc), code=400)
    except Exception as exc:
        return error(f"更新配件失败：{exc}", code=500)


@products_bp.put("/api/products/<int:product_id>/status")
def update_product_status(product_id):
    try:
        payload = request.get_json(silent=True) or {}
        status = payload.get("status")

        if status not in VALID_PRODUCT_STATUSES:
            return error("配件状态只能是 在售 或 停用", code=400)

        product = query_one(
            "SELECT product_id FROM product WHERE product_id = %s",
            (product_id,),
        )
        if not product:
            return error("配件不存在", code=404)

        execute(
            "UPDATE product SET status = %s WHERE product_id = %s",
            (status, product_id),
        )
        return success(
            {"id": product_id, "status": status},
            message="配件状态已更新",
        )
    except Exception as exc:
        return error(f"更新配件状态失败：{exc}", code=500)


@products_bp.put("/api/products/<int:product_id>/warning-value")
def update_product_warning_value(product_id):
    try:
        payload = request.get_json(silent=True) or {}
        warning_value = payload.get("warningValue")

        if warning_value is None:
            return error("请填写库存预警值", code=400)

        try:
            warning_value = int(warning_value)
        except (TypeError, ValueError):
            return error("库存预警值必须是整数", code=400)

        if warning_value < 0:
            return error("库存预警值不能小于 0", code=400)

        product = query_one(
            "SELECT product_id FROM product WHERE product_id = %s",
            (product_id,),
        )
        if not product:
            return error("配件不存在", code=404)

        execute(
            "UPDATE product SET warning_value = %s WHERE product_id = %s",
            (warning_value, product_id),
        )
        return success(
            {"id": product_id, "warningValue": warning_value},
            message="库存预警值已更新",
        )
    except Exception as exc:
        return error(f"更新库存预警值失败：{exc}", code=500)
