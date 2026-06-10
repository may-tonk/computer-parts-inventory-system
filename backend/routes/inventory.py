from flask import Blueprint, request

from db import query_all, query_one, serialize_row, serialize_rows
from responses import error, success

inventory_bp = Blueprint("inventory", __name__)


@inventory_bp.get("/api/stocks/detail")
def get_stock_details():
    try:
        filters = []
        params = []

        keyword = request.args.get("keyword", "").strip()
        category_id = request.args.get("categoryId")
        brand_id = request.args.get("brandId")
        warehouse_id = request.args.get("warehouseId")

        if keyword:
            filters.append("(v.product_name LIKE %s OR v.brand_name LIKE %s)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if category_id:
            filters.append(
                "v.category_name = (SELECT category_name FROM category WHERE category_id = %s)"
            )
            params.append(category_id)
        if brand_id:
            filters.append("v.brand_name = (SELECT brand_name FROM brand WHERE brand_id = %s)")
            params.append(brand_id)
        if warehouse_id:
            filters.append("v.warehouse_id = %s")
            params.append(warehouse_id)

        where_sql = f"WHERE {' AND '.join(filters)}" if filters else ""
        rows = query_all(
            f"""
            SELECT
                product_id,
                product_name,
                category_name,
                brand_name,
                warehouse_id,
                warehouse_name,
                quantity,
                warning_value,
                stock_status AS status,
                updated_at
            FROM v_stock_detail v
            {where_sql}
            ORDER BY product_id, warehouse_id
            """,
            params,
        )
        return success(serialize_rows(rows))
    except Exception as exc:
        return error(f"查询库存汇总失败：{exc}", code=500)


@inventory_bp.get("/api/stocks/warnings")
def get_inventory_warnings():
    try:
        rows = query_all(
            """
            SELECT
                product_id,
                product_name,
                category_name,
                brand_name,
                warehouse_id,
                warehouse_name,
                quantity,
                warning_value,
                warning_type
            FROM v_inventory_warning
            ORDER BY product_id, warehouse_id
            """
        )
        return success(serialize_rows(rows))
    except Exception as exc:
        return error(f"查询库存预警失败：{exc}", code=500)


@inventory_bp.get("/api/product-sn")
def get_sn_list():
    try:
        filters = []
        params = []

        keyword = request.args.get("keyword", "").strip()
        product_id = request.args.get("productId")
        warehouse_id = request.args.get("warehouseId")
        status = request.args.get("status")

        if keyword:
            filters.append("(ps.sn_code LIKE %s OR p.product_name LIKE %s OR p.model LIKE %s)")
            params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
        if product_id:
            filters.append("ps.product_id = %s")
            params.append(product_id)
        if warehouse_id:
            filters.append("ps.warehouse_id = %s")
            params.append(warehouse_id)
        if status:
            filters.append("ps.status = %s")
            params.append(status)

        where_sql = f"WHERE {' AND '.join(filters)}" if filters else ""
        rows = query_all(
            f"""
            SELECT
                ps.sn_id AS id,
                ps.sn_code,
                ps.product_id,
                p.product_name,
                c.category_name,
                b.brand_name,
                p.model,
                ps.batch_no,
                ps.warehouse_id,
                w.warehouse_name,
                ps.status,
                ps.inbound_date,
                ps.warranty_end_date
            FROM product_sn ps
            JOIN product p ON ps.product_id = p.product_id
            JOIN category c ON p.category_id = c.category_id
            JOIN brand b ON p.brand_id = b.brand_id
            JOIN warehouse w ON ps.warehouse_id = w.warehouse_id
            {where_sql}
            ORDER BY ps.sn_id DESC
            LIMIT 300
            """,
            params,
        )
        return success(serialize_rows(rows))
    except Exception as exc:
        return error(f"查询 SN 列表失败：{exc}", code=500)


@inventory_bp.get("/api/product-sn/<path:sn_code>")
def get_sn_detail(sn_code):
    try:
        row = query_one(
            """
            SELECT
                ps.sn_code,
                ps.product_id,
                p.product_name,
                c.category_name,
                b.brand_name,
                p.model,
                ps.batch_no,
                ps.warehouse_id,
                w.warehouse_name,
                ps.status,
                ps.inbound_date,
                ps.warranty_end_date,
                io.inbound_no,
                po.purchase_id,
                po.order_date AS purchase_date,
                s.supplier_name,
                oo.outbound_no,
                so.sales_id,
                so.status AS sales_status,
                so.order_date AS sales_date,
                cu.customer_name,
                sd.unit_price AS sales_unit_price,
                so.paid_amount AS sales_paid_amount
            FROM product_sn ps
            JOIN product p ON ps.product_id = p.product_id
            JOIN category c ON p.category_id = c.category_id
            JOIN brand b ON p.brand_id = b.brand_id
            JOIN warehouse w ON ps.warehouse_id = w.warehouse_id
            LEFT JOIN inbound_detail ib ON ps.sn_code = ib.sn_code
            LEFT JOIN inbound_order io ON ib.inbound_no = io.inbound_no
            LEFT JOIN purchase_order po ON io.purchase_id = po.purchase_id
            LEFT JOIN supplier s ON po.supplier_id = s.supplier_id
            LEFT JOIN sales_detail sd ON ps.sn_code = sd.sn_code
            LEFT JOIN sales_order so ON sd.sales_id = so.sales_id
            LEFT JOIN customer cu ON so.customer_id = cu.customer_id
            LEFT JOIN outbound_detail od ON ps.sn_code = od.sn_code
            LEFT JOIN outbound_order oo ON od.outbound_no = oo.outbound_no
            WHERE ps.sn_code = %s
            """,
            (sn_code,),
        )
        if not row:
            return error("SN 码不存在", code=404)
        return success(serialize_row(row))
    except Exception as exc:
        return error(f"查询 SN 详情失败：{exc}", code=500)
