from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
import re

from flask import Blueprint, request

from db import get_connection, query_all, query_one, serialize_row, serialize_rows
from responses import error, success

orders_bp = Blueprint("orders", __name__)


def _clean_text(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _required_int(payload, key, message):
    value = payload.get(key)
    if value is None or value == "":
        raise ValueError(message)
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(message)


def _positive_int(value, message):
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise ValueError(message)
    if value <= 0:
        raise ValueError(message)
    return value


def _non_negative_decimal(value, message):
    try:
        value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(message)
    if value < 0:
        raise ValueError(message)
    return value


def _parse_date(value, message, required=True):
    if not value:
        if required:
            raise ValueError(message)
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(message)


def _generate_document_id(cursor, table_name, column_name, prefix, current_date):
    date_part = current_date.strftime("%Y%m%d")
    base = f"{prefix}{date_part}"
    cursor.execute(
        f"""
        SELECT {column_name} AS id
        FROM {table_name}
        WHERE {column_name} LIKE %s
        ORDER BY {column_name} DESC
        LIMIT 50
        """,
        (f"{base}%",),
    )
    rows = cursor.fetchall()
    next_number = 1
    for row in rows:
        document_id = str(row["id"])
        suffix = document_id[len(base) :]
        if len(suffix) == 3 and suffix.isdigit():
            next_number = max(next_number, int(suffix) + 1)
    return f"{base}{next_number:03d}"


def _next_unique_sn(cursor, product_id, current_date, sequence):
    base = f"SN-P{product_id}-{current_date.strftime('%Y%m%d')}"
    next_number = sequence
    while True:
        sn_code = f"{base}-{next_number:04d}"
        cursor.execute(
            "SELECT 1 FROM product_sn WHERE sn_code = %s LIMIT 1",
            (sn_code,),
        )
        if not cursor.fetchone():
            return sn_code, next_number + 1
        next_number += 1


@orders_bp.get("/api/purchase-orders")
def get_purchase_orders():
    try:
        filters = []
        params = []

        keyword = request.args.get("keyword", "").strip()
        supplier_id = request.args.get("supplierId")
        buyer_id = request.args.get("buyerId")
        warehouse_id = request.args.get("warehouseId")
        status = request.args.get("status")
        start_date = request.args.get("startDate")
        end_date = request.args.get("endDate")

        if keyword:
            filters.append("(po.purchase_id LIKE %s OR s.supplier_name LIKE %s)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if supplier_id:
            filters.append("po.supplier_id = %s")
            params.append(supplier_id)
        if buyer_id:
            filters.append("po.buyer_id = %s")
            params.append(buyer_id)
        if warehouse_id:
            filters.append("po.warehouse_id = %s")
            params.append(warehouse_id)
        if status:
            filters.append("po.status = %s")
            params.append(status)
        if start_date:
            filters.append("po.order_date >= %s")
            params.append(start_date)
        if end_date:
            filters.append("po.order_date <= %s")
            params.append(end_date)

        where_sql = f"WHERE {' AND '.join(filters)}" if filters else ""
        rows = query_all(
            f"""
            SELECT
                po.purchase_id AS id,
                po.supplier_id,
                s.supplier_name,
                po.buyer_id,
                COALESCE(u.real_name, CONCAT('用户', po.buyer_id)) AS buyer_name,
                po.warehouse_id,
                w.warehouse_name,
                po.order_date,
                po.total_amount,
                po.status,
                po.remark,
                po.created_at
            FROM purchase_order po
            JOIN supplier s ON po.supplier_id = s.supplier_id
            JOIN warehouse w ON po.warehouse_id = w.warehouse_id
            LEFT JOIN system_user u ON po.buyer_id = u.user_id
            {where_sql}
            ORDER BY po.order_date DESC, po.purchase_id DESC
            """,
            params,
        )
        return success(serialize_rows(rows))
    except Exception as exc:
        return error(f"查询采购单列表失败：{exc}", code=500)


@orders_bp.get("/api/purchase-orders/<purchase_id>")
def get_purchase_order_detail(purchase_id):
    try:
        order = query_one(
            """
            SELECT
                po.purchase_id AS id,
                po.supplier_id,
                s.supplier_name,
                po.buyer_id,
                COALESCE(u.real_name, CONCAT('用户', po.buyer_id)) AS buyer_name,
                po.warehouse_id,
                w.warehouse_name,
                po.order_date,
                po.total_amount,
                po.status,
                po.remark,
                po.created_at
            FROM purchase_order po
            JOIN supplier s ON po.supplier_id = s.supplier_id
            JOIN warehouse w ON po.warehouse_id = w.warehouse_id
            LEFT JOIN system_user u ON po.buyer_id = u.user_id
            WHERE po.purchase_id = %s
            """,
            (purchase_id,),
        )

        if not order:
            return error("采购单不存在", code=404)

        details = query_all(
            """
            SELECT
                pd.detail_id AS id,
                pd.product_id,
                p.product_name,
                c.category_name,
                b.brand_name,
                p.model,
                pd.quantity,
                pd.unit_price,
                pd.subtotal,
                pd.batch_no,
                pd.production_date
            FROM purchase_detail pd
            JOIN product p ON pd.product_id = p.product_id
            JOIN category c ON p.category_id = c.category_id
            JOIN brand b ON p.brand_id = b.brand_id
            WHERE pd.purchase_id = %s
            ORDER BY pd.detail_id
            """,
            (purchase_id,),
        )

        sn_rows = query_all(
            """
            SELECT
                io.inbound_no,
                ib.sn_code,
                ps.product_id,
                p.product_name,
                ps.batch_no,
                ps.status,
                ps.inbound_date,
                ps.warranty_end_date
            FROM inbound_order io
            JOIN inbound_detail ib ON io.inbound_no = ib.inbound_no
            JOIN product_sn ps ON ib.sn_code = ps.sn_code
            JOIN product p ON ps.product_id = p.product_id
            WHERE io.purchase_id = %s
            ORDER BY ps.product_id, ib.sn_code
            """,
            (purchase_id,),
        )

        data = serialize_row(order)
        data["details"] = serialize_rows(details)
        data["snCodes"] = serialize_rows(sn_rows)
        return success(data)
    except Exception as exc:
        return error(f"查询采购单详情失败：{exc}", code=500)


@orders_bp.post("/api/purchase-orders")
def create_purchase_order():
    try:
        payload = request.get_json(silent=True) or {}
        supplier_id = _required_int(payload, "supplierId", "请选择供应商")
        buyer_id = _required_int(payload, "buyerId", "请填写采购员 ID")
        warehouse_id = _required_int(payload, "warehouseId", "请选择入库仓库")
        order_date = _parse_date(payload.get("orderDate"), "采购日期格式应为 YYYY-MM-DD")
        remark = _clean_text(payload.get("remark"))
        raw_details = payload.get("details") or []

        if not raw_details:
            return error("请至少填写一条采购明细", code=400)

        details = []
        for index, item in enumerate(raw_details, start=1):
            product_id = _required_int(item, "productId", f"第 {index} 条明细请选择配件")
            quantity = _positive_int(item.get("quantity"), f"第 {index} 条明细采购数量必须大于 0")
            unit_price = _non_negative_decimal(
                item.get("unitPrice"),
                f"第 {index} 条明细采购单价不能小于 0",
            )
            production_date = _parse_date(
                item.get("productionDate"),
                f"第 {index} 条明细生产日期格式应为 YYYY-MM-DD",
                required=False,
            )
            subtotal = unit_price * quantity
            details.append(
                {
                    "productId": product_id,
                    "quantity": quantity,
                    "unitPrice": unit_price,
                    "subtotal": subtotal,
                    "batchNo": _clean_text(item.get("batchNo")),
                    "productionDate": production_date,
                }
            )

        total_amount = sum((item["subtotal"] for item in details), Decimal("0"))
        warranty_end_date = order_date + timedelta(days=365 * 3)
        generated_sn_codes = []

        with get_connection() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT supplier_id FROM supplier WHERE supplier_id = %s",
                        (supplier_id,),
                    )
                    if not cursor.fetchone():
                        return error("供应商不存在", code=400)

                    cursor.execute(
                        "SELECT warehouse_id FROM warehouse WHERE warehouse_id = %s",
                        (warehouse_id,),
                    )
                    if not cursor.fetchone():
                        return error("仓库不存在", code=400)

                    cursor.execute(
                        "SELECT user_id FROM system_user WHERE user_id = %s",
                        (buyer_id,),
                    )
                    if not cursor.fetchone():
                        return error("采购员不存在", code=400)

                    product_map = {}
                    for item in details:
                        cursor.execute(
                            """
                            SELECT
                                p.product_id,
                                p.product_name,
                                p.status
                            FROM product p
                            WHERE p.product_id = %s
                            """,
                            (item["productId"],),
                        )
                        product = cursor.fetchone()
                        if not product:
                            return error(f"配件不存在：{item['productId']}", code=400)
                        if product["status"] != "在售":
                            return error(
                                f"配件已停用，不能采购：{product['product_name']}",
                                code=400,
                            )
                        product_map[item["productId"]] = product

                    purchase_id = _generate_document_id(
                        cursor,
                        "purchase_order",
                        "purchase_id",
                        "PO",
                        order_date,
                    )
                    inbound_no = _generate_document_id(
                        cursor,
                        "inbound_order",
                        "inbound_no",
                        "IN",
                        order_date,
                    )

                    cursor.execute(
                        """
                        INSERT INTO purchase_order (
                            purchase_id,
                            supplier_id,
                            buyer_id,
                            warehouse_id,
                            order_date,
                            total_amount,
                            status,
                            remark
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, '已完成', %s)
                        """,
                        (
                            purchase_id,
                            supplier_id,
                            buyer_id,
                            warehouse_id,
                            order_date,
                            total_amount,
                            remark,
                        ),
                    )

                    cursor.execute(
                        """
                        INSERT INTO inbound_order (
                            inbound_no,
                            purchase_id,
                            warehouse_id,
                            inbound_time,
                            total_amount,
                            maker_id
                        )
                        VALUES (%s, %s, %s, NOW(), %s, %s)
                        """,
                        (
                            inbound_no,
                            purchase_id,
                            warehouse_id,
                            total_amount,
                            buyer_id,
                        ),
                    )

                    stock_increments = {}
                    sn_sequences = {}
                    for item in details:
                        cursor.execute(
                            """
                            INSERT INTO purchase_detail (
                                purchase_id,
                                product_id,
                                quantity,
                                unit_price,
                                batch_no,
                                production_date
                            )
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """,
                            (
                                purchase_id,
                                item["productId"],
                                item["quantity"],
                                item["unitPrice"],
                                item["batchNo"],
                                item["productionDate"],
                            ),
                        )

                        if item["productId"] not in sn_sequences:
                            cursor.execute(
                                """
                                SELECT COUNT(*) AS total_count
                                FROM product_sn
                                WHERE product_id = %s
                                """,
                                (item["productId"],),
                            )
                            sn_sequences[item["productId"]] = (
                                int(cursor.fetchone()["total_count"] or 0) + 1
                            )

                        for _ in range(item["quantity"]):
                            sn_code, next_sequence = _next_unique_sn(
                                cursor,
                                item["productId"],
                                order_date,
                                sn_sequences[item["productId"]],
                            )
                            sn_sequences[item["productId"]] = next_sequence
                            generated_sn_codes.append(sn_code)

                            cursor.execute(
                                """
                                INSERT INTO product_sn (
                                    product_id,
                                    warehouse_id,
                                    sn_code,
                                    batch_no,
                                    inbound_date,
                                    warranty_end_date,
                                    status
                                )
                                VALUES (%s, %s, %s, %s, %s, %s, '在库')
                                """,
                                (
                                    item["productId"],
                                    warehouse_id,
                                    sn_code,
                                    item["batchNo"],
                                    order_date,
                                    warranty_end_date,
                                ),
                            )
                            cursor.execute(
                                """
                                INSERT INTO inbound_detail (inbound_no, sn_code)
                                VALUES (%s, %s)
                                """,
                                (inbound_no, sn_code),
                            )

                        stock_increments[item["productId"]] = (
                            stock_increments.get(item["productId"], 0)
                            + item["quantity"]
                        )

                    for product_id, quantity in stock_increments.items():
                        cursor.execute(
                            """
                            INSERT INTO stock (
                                product_id,
                                warehouse_id,
                                quantity,
                                updated_at
                            )
                            VALUES (%s, %s, %s, NOW())
                            ON DUPLICATE KEY UPDATE
                                quantity = quantity + VALUES(quantity),
                                updated_at = NOW()
                            """,
                            (product_id, warehouse_id, quantity),
                        )

                connection.commit()
            except Exception:
                connection.rollback()
                raise

        return success(
            {
                "id": purchase_id,
                "inboundNo": inbound_no,
                "totalAmount": float(total_amount),
                "generatedSnCodes": generated_sn_codes,
            },
            message="采购入库成功",
            code=201,
        )
    except ValueError as exc:
        return error(str(exc), code=400)
    except Exception as exc:
        return error(f"新建采购单失败：{exc}", code=500)


@orders_bp.get("/api/sales-orders")
def get_sales_orders():
    try:
        filters = []
        params = []

        keyword = request.args.get("keyword", "").strip()
        customer_id = request.args.get("customerId")
        seller_id = request.args.get("sellerId")
        warehouse_id = request.args.get("warehouseId")
        status = request.args.get("status")
        start_date = request.args.get("startDate")
        end_date = request.args.get("endDate")

        if keyword:
            filters.append("(so.sales_id LIKE %s OR c.customer_name LIKE %s)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if customer_id:
            filters.append("so.customer_id = %s")
            params.append(customer_id)
        if seller_id:
            filters.append("so.seller_id = %s")
            params.append(seller_id)
        if warehouse_id:
            filters.append("so.warehouse_id = %s")
            params.append(warehouse_id)
        if status:
            filters.append("so.status = %s")
            params.append(status)
        if start_date:
            filters.append("so.order_date >= %s")
            params.append(start_date)
        if end_date:
            filters.append("so.order_date <= %s")
            params.append(end_date)

        where_sql = f"WHERE {' AND '.join(filters)}" if filters else ""
        rows = query_all(
            f"""
            SELECT
                so.sales_id AS id,
                so.customer_id,
                c.customer_name,
                so.seller_id,
                COALESCE(u.real_name, CONCAT('用户', so.seller_id)) AS seller_name,
                so.warehouse_id,
                w.warehouse_name,
                so.order_date,
                so.total_amount,
                so.discount_rate,
                so.paid_amount,
                so.status,
                so.remark,
                so.created_at
            FROM sales_order so
            JOIN customer c ON so.customer_id = c.customer_id
            JOIN warehouse w ON so.warehouse_id = w.warehouse_id
            LEFT JOIN system_user u ON so.seller_id = u.user_id
            {where_sql}
            ORDER BY so.order_date DESC, so.sales_id DESC
            """,
            params,
        )
        return success(serialize_rows(rows))
    except Exception as exc:
        return error(f"查询销售单列表失败：{exc}", code=500)


@orders_bp.post("/api/sales-orders")
def create_sales_order():
    try:
        payload = request.get_json(silent=True) or {}
        customer_id = _required_int(payload, "customerId", "请选择客户")
        seller_id = _required_int(payload, "sellerId", "请填写销售员 ID")
        warehouse_id = _required_int(payload, "warehouseId", "请选择出库仓库")
        order_date = _parse_date(payload.get("orderDate"), "销售日期格式应为 YYYY-MM-DD")
        discount_rate = _non_negative_decimal(payload.get("discountRate", 1), "折扣率不能小于 0")
        if discount_rate > 1:
            raise ValueError("折扣率不能大于 1")
        remark = _clean_text(payload.get("remark"))
        raw_details = payload.get("details") or []

        if not raw_details:
            return error("请至少填写一条销售明细", code=400)

        details = []
        seen_sn_codes = set()
        for index, item in enumerate(raw_details, start=1):
            sn_code = _clean_text(item.get("snCode"))
            if not sn_code:
                raise ValueError(f"第 {index} 条明细请选择 SN 码")
            if sn_code in seen_sn_codes:
                raise ValueError(f"SN 码重复选择：{sn_code}")
            seen_sn_codes.add(sn_code)

            unit_price = _non_negative_decimal(
                item.get("unitPrice"),
                f"第 {index} 条明细销售单价不能小于 0",
            )
            details.append({"snCode": sn_code, "unitPrice": unit_price})

        total_amount = sum((item["unitPrice"] for item in details), Decimal("0"))
        paid_amount = (total_amount * discount_rate).quantize(Decimal("0.01"))

        with get_connection() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT customer_id FROM customer WHERE customer_id = %s",
                        (customer_id,),
                    )
                    if not cursor.fetchone():
                        return error("客户不存在", code=400)

                    cursor.execute(
                        "SELECT warehouse_id FROM warehouse WHERE warehouse_id = %s",
                        (warehouse_id,),
                    )
                    if not cursor.fetchone():
                        return error("仓库不存在", code=400)

                    cursor.execute(
                        "SELECT user_id FROM system_user WHERE user_id = %s",
                        (seller_id,),
                    )
                    if not cursor.fetchone():
                        return error("销售员不存在", code=400)

                    stock_decrements = {}
                    for item in details:
                        cursor.execute(
                            """
                            SELECT
                                ps.sn_code,
                                ps.product_id,
                                ps.warehouse_id,
                                ps.status,
                                p.product_name,
                                p.status AS product_status
                            FROM product_sn ps
                            JOIN product p ON ps.product_id = p.product_id
                            WHERE ps.sn_code = %s
                            FOR UPDATE
                            """,
                            (item["snCode"],),
                        )
                        sn_row = cursor.fetchone()
                        if not sn_row:
                            return error(f"SN 码不存在：{item['snCode']}", code=400)
                        if sn_row["warehouse_id"] != warehouse_id:
                            return error(
                                f"SN 码不属于当前仓库：{item['snCode']}",
                                code=400,
                            )
                        if sn_row["status"] != "在库":
                            return error(
                                f"SN 码当前状态为 {sn_row['status']}，不能销售：{item['snCode']}",
                                code=400,
                            )
                        if sn_row["product_status"] != "在售":
                            return error(
                                f"配件已停用，不能销售：{sn_row['product_name']}",
                                code=400,
                            )
                        item["productId"] = sn_row["product_id"]
                        stock_key = (sn_row["product_id"], warehouse_id)
                        stock_decrements[stock_key] = stock_decrements.get(stock_key, 0) + 1

                    for (product_id, stock_warehouse_id), quantity in stock_decrements.items():
                        cursor.execute(
                            """
                            SELECT quantity
                            FROM stock
                            WHERE product_id = %s AND warehouse_id = %s
                            FOR UPDATE
                            """,
                            (product_id, stock_warehouse_id),
                        )
                        stock = cursor.fetchone()
                        if not stock or int(stock["quantity"]) < quantity:
                            return error("库存不足，不能销售", code=400)

                    sales_id = _generate_document_id(
                        cursor,
                        "sales_order",
                        "sales_id",
                        "SO",
                        order_date,
                    )
                    outbound_no = _generate_document_id(
                        cursor,
                        "outbound_order",
                        "outbound_no",
                        "OUT",
                        order_date,
                    )

                    cursor.execute(
                        """
                        INSERT INTO sales_order (
                            sales_id,
                            customer_id,
                            seller_id,
                            warehouse_id,
                            order_date,
                            total_amount,
                            discount_rate,
                            paid_amount,
                            status,
                            remark
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, '已完成', %s)
                        """,
                        (
                            sales_id,
                            customer_id,
                            seller_id,
                            warehouse_id,
                            order_date,
                            total_amount,
                            discount_rate,
                            paid_amount,
                            remark,
                        ),
                    )

                    cursor.execute(
                        """
                        INSERT INTO outbound_order (
                            outbound_no,
                            sales_id,
                            warehouse_id,
                            outbound_time,
                            total_amount,
                            maker_id
                        )
                        VALUES (%s, %s, %s, NOW(), %s, %s)
                        """,
                        (
                            outbound_no,
                            sales_id,
                            warehouse_id,
                            paid_amount,
                            seller_id,
                        ),
                    )

                    for item in details:
                        cursor.execute(
                            """
                            INSERT INTO sales_detail (
                                sales_id,
                                sn_code,
                                product_id,
                                unit_price
                            )
                            VALUES (%s, %s, %s, %s)
                            """,
                            (
                                sales_id,
                                item["snCode"],
                                item["productId"],
                                item["unitPrice"],
                            ),
                        )
                        cursor.execute(
                            """
                            INSERT INTO outbound_detail (outbound_no, sn_code)
                            VALUES (%s, %s)
                            """,
                            (outbound_no, item["snCode"]),
                        )
                        cursor.execute(
                            """
                            UPDATE product_sn
                            SET status = '已售'
                            WHERE sn_code = %s
                            """,
                            (item["snCode"],),
                        )

                    for (product_id, stock_warehouse_id), quantity in stock_decrements.items():
                        cursor.execute(
                            """
                            UPDATE stock
                            SET quantity = quantity - %s,
                                updated_at = NOW()
                            WHERE product_id = %s AND warehouse_id = %s
                            """,
                            (quantity, product_id, stock_warehouse_id),
                        )

                    cursor.execute(
                        """
                        UPDATE customer
                        SET total_spent = total_spent + %s
                        WHERE customer_id = %s
                        """,
                        (paid_amount, customer_id),
                    )

                connection.commit()
            except Exception:
                connection.rollback()
                raise

        return success(
            {
                "id": sales_id,
                "outboundNo": outbound_no,
                "totalAmount": float(total_amount),
                "paidAmount": float(paid_amount),
                "soldSnCodes": [item["snCode"] for item in details],
            },
            message="销售出库成功",
            code=201,
        )
    except ValueError as exc:
        return error(str(exc), code=400)
    except Exception as exc:
        return error(f"新建销售单失败：{exc}", code=500)


@orders_bp.post("/api/sales-orders/<sales_id>/return")
def return_sales_order(sales_id):
    try:
        with get_connection() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT
                            sales_id,
                            customer_id,
                            warehouse_id,
                            paid_amount,
                            status
                        FROM sales_order
                        WHERE sales_id = %s
                        FOR UPDATE
                        """,
                        (sales_id,),
                    )
                    order = cursor.fetchone()
                    if not order:
                        return error("销售单不存在", code=404)
                    if order["status"] != "已完成":
                        return error(f"当前销售单状态为 {order['status']}，不能退货", code=400)

                    cursor.execute(
                        """
                        SELECT
                            sd.sn_code,
                            sd.product_id,
                            ps.warehouse_id,
                            ps.status AS sn_status
                        FROM sales_detail sd
                        JOIN product_sn ps ON sd.sn_code = ps.sn_code
                        WHERE sd.sales_id = %s
                        FOR UPDATE
                        """,
                        (sales_id,),
                    )
                    details = cursor.fetchall()
                    if not details:
                        return error("销售单没有明细，不能退货", code=400)

                    stock_increments = {}
                    for item in details:
                        if item["sn_status"] != "已售":
                            return error(
                                f"SN 码当前状态为 {item['sn_status']}，不能退货：{item['sn_code']}",
                                code=400,
                            )
                        stock_key = (item["product_id"], item["warehouse_id"])
                        stock_increments[stock_key] = stock_increments.get(stock_key, 0) + 1

                    cursor.execute(
                        """
                        UPDATE sales_order
                        SET status = '已退货'
                        WHERE sales_id = %s
                        """,
                        (sales_id,),
                    )

                    for item in details:
                        cursor.execute(
                            """
                            UPDATE product_sn
                            SET status = '在库'
                            WHERE sn_code = %s
                            """,
                            (item["sn_code"],),
                        )

                    for (product_id, warehouse_id), quantity in stock_increments.items():
                        cursor.execute(
                            """
                            INSERT INTO stock (
                                product_id,
                                warehouse_id,
                                quantity,
                                updated_at
                            )
                            VALUES (%s, %s, %s, NOW())
                            ON DUPLICATE KEY UPDATE
                                quantity = quantity + VALUES(quantity),
                                updated_at = NOW()
                            """,
                            (product_id, warehouse_id, quantity),
                        )

                    cursor.execute(
                        """
                        UPDATE customer
                        SET total_spent = GREATEST(total_spent - %s, 0)
                        WHERE customer_id = %s
                        """,
                        (order["paid_amount"], order["customer_id"]),
                    )

                connection.commit()
            except Exception:
                connection.rollback()
                raise

        return success(
            {
                "id": sales_id,
                "returnedSnCodes": [item["sn_code"] for item in details],
            },
            message="退货成功",
        )
    except Exception as exc:
        return error(f"销售退货失败：{exc}", code=500)


@orders_bp.get("/api/sales-orders/<sales_id>")
def get_sales_order_detail(sales_id):
    try:
        order = query_one(
            """
            SELECT
                so.sales_id AS id,
                so.customer_id,
                c.customer_name,
                so.seller_id,
                COALESCE(u.real_name, CONCAT('用户', so.seller_id)) AS seller_name,
                so.warehouse_id,
                w.warehouse_name,
                so.order_date,
                so.total_amount,
                so.discount_rate,
                so.paid_amount,
                so.status,
                so.remark,
                so.created_at
            FROM sales_order so
            JOIN customer c ON so.customer_id = c.customer_id
            JOIN warehouse w ON so.warehouse_id = w.warehouse_id
            LEFT JOIN system_user u ON so.seller_id = u.user_id
            WHERE so.sales_id = %s
            """,
            (sales_id,),
        )

        if not order:
            return error("销售单不存在", code=404)

        details = query_all(
            """
            SELECT
                sd.detail_id AS id,
                sd.sn_code,
                sd.product_id,
                p.product_name,
                c.category_name,
                b.brand_name,
                p.model,
                sd.unit_price,
                sd.subtotal,
                ps.status AS sn_status
            FROM sales_detail sd
            JOIN product p ON sd.product_id = p.product_id
            JOIN category c ON p.category_id = c.category_id
            JOIN brand b ON p.brand_id = b.brand_id
            LEFT JOIN product_sn ps ON sd.sn_code = ps.sn_code
            WHERE sd.sales_id = %s
            ORDER BY sd.detail_id
            """,
            (sales_id,),
        )

        data = serialize_row(order)
        data["details"] = serialize_rows(details)
        return success(data)
    except Exception as exc:
        return error(f"查询销售单详情失败：{exc}", code=500)
