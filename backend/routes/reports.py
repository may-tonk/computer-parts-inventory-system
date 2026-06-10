from datetime import date, timedelta

from flask import Blueprint, request

from db import query_all, query_one, serialize_row, serialize_rows
from responses import error, success

reports_bp = Blueprint("reports", __name__)


def _date_range(days=7):
    today = date.today()
    start = today - timedelta(days=days - 1)
    return [start + timedelta(days=index) for index in range(days)]


def _money(value):
    return float(value or 0)


@reports_bp.get("/api/dashboard/summary")
def get_dashboard_summary():
    try:
        totals = query_one(
            """
            SELECT
                (SELECT COUNT(*) FROM product) AS product_count,
                (SELECT COALESCE(SUM(quantity), 0) FROM stock) AS total_stock,
                (SELECT COUNT(*) FROM product_sn WHERE status = '在库') AS in_stock_sn_count,
                (SELECT COUNT(*) FROM product_sn WHERE status = '已售') AS sold_sn_count,
                (SELECT COUNT(*) FROM product_sn WHERE status = '锁定') AS locked_sn_count,
                (SELECT COUNT(*) FROM v_inventory_warning) AS low_stock_count,
                (
                    SELECT COALESCE(SUM(total_amount), 0)
                    FROM purchase_order
                    WHERE status = '已完成' AND order_date = CURDATE()
                ) AS today_purchase_amount,
                (
                    SELECT COALESCE(SUM(paid_amount), 0)
                    FROM sales_order
                    WHERE status = '已完成' AND order_date = CURDATE()
                ) AS today_effective_sales_amount,
                (
                    SELECT COALESCE(SUM(paid_amount), 0)
                    FROM sales_order
                    WHERE status = '已退货' AND order_date = CURDATE()
                ) AS today_return_amount,
                (
                    SELECT COUNT(*)
                    FROM sales_order
                    WHERE status = '已完成'
                ) AS completed_sales_count,
                (
                    SELECT COUNT(*)
                    FROM sales_order
                    WHERE status = '已退货'
                ) AS returned_sales_count
            """
        )

        recent_purchases = query_all(
            """
            SELECT
                po.purchase_id AS id,
                s.supplier_name,
                w.warehouse_name,
                po.order_date,
                po.total_amount,
                po.status
            FROM purchase_order po
            JOIN supplier s ON po.supplier_id = s.supplier_id
            JOIN warehouse w ON po.warehouse_id = w.warehouse_id
            ORDER BY po.created_at DESC, po.order_date DESC
            LIMIT 5
            """
        )
        recent_sales = query_all(
            """
            SELECT
                so.sales_id AS id,
                c.customer_name,
                w.warehouse_name,
                so.order_date,
                so.paid_amount,
                so.status
            FROM sales_order so
            JOIN customer c ON so.customer_id = c.customer_id
            JOIN warehouse w ON so.warehouse_id = w.warehouse_id
            ORDER BY so.created_at DESC, so.order_date DESC
            LIMIT 5
            """
        )

        return success(
            {
                "totals": serialize_row(totals),
                "recentPurchases": serialize_rows(recent_purchases),
                "recentSales": serialize_rows(recent_sales),
            }
        )
    except Exception as exc:
        return error(f"查询首页看板失败：{exc}", code=500)


@reports_bp.get("/api/reports/sales")
def get_sales_report():
    try:
        start_date = request.args.get("startDate")
        end_date = request.args.get("endDate")

        filters = []
        params = []
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
                so.order_date AS date,
                COALESCE(SUM(CASE WHEN so.status = '已完成' THEN so.paid_amount ELSE 0 END), 0)
                    AS effective_sales_amount,
                COALESCE(SUM(CASE WHEN so.status = '已退货' THEN so.paid_amount ELSE 0 END), 0)
                    AS return_amount,
                COUNT(CASE WHEN so.status = '已完成' THEN 1 END) AS effective_order_count,
                COUNT(CASE WHEN so.status = '已退货' THEN 1 END) AS returned_order_count
            FROM sales_order so
            {where_sql}
            GROUP BY so.order_date
            ORDER BY so.order_date
            """,
            params,
        )
        return success(serialize_rows(rows))
    except Exception as exc:
        return error(f"查询销售统计失败：{exc}", code=500)


@reports_bp.get("/api/reports/overview")
def get_report_overview():
    try:
        days = int(request.args.get("days", 7))
        days = min(max(days, 1), 30)
        days_list = _date_range(days)
        start_date = days_list[0].strftime("%Y-%m-%d")
        end_date = days_list[-1].strftime("%Y-%m-%d")

        sales_rows = query_all(
            """
            SELECT
                order_date AS date,
                COALESCE(SUM(CASE WHEN status = '已完成' THEN paid_amount ELSE 0 END), 0)
                    AS effective_sales_amount,
                COALESCE(SUM(CASE WHEN status = '已退货' THEN paid_amount ELSE 0 END), 0)
                    AS return_amount,
                COUNT(CASE WHEN status = '已完成' THEN 1 END) AS effective_order_count,
                COUNT(CASE WHEN status = '已退货' THEN 1 END) AS returned_order_count
            FROM sales_order
            WHERE order_date BETWEEN %s AND %s
            GROUP BY order_date
            """,
            (start_date, end_date),
        )
        sales_by_date = {str(row["date"]): row for row in sales_rows}
        sales_trend = []
        for item_date in days_list:
            key = item_date.strftime("%Y-%m-%d")
            row = sales_by_date.get(key, {})
            sales_trend.append(
                {
                    "date": key,
                    "effectiveSalesAmount": _money(row.get("effective_sales_amount")),
                    "returnAmount": _money(row.get("return_amount")),
                    "effectiveOrderCount": int(row.get("effective_order_count") or 0),
                    "returnedOrderCount": int(row.get("returned_order_count") or 0),
                }
            )

        category_sales = query_all(
            """
            SELECT
                c.category_name,
                COUNT(sd.detail_id) AS sales_quantity,
                COALESCE(SUM(sd.subtotal), 0) AS sales_amount
            FROM sales_order so
            JOIN sales_detail sd ON so.sales_id = sd.sales_id
            JOIN product p ON sd.product_id = p.product_id
            JOIN category c ON p.category_id = c.category_id
            WHERE so.status = '已完成'
            GROUP BY c.category_id, c.category_name
            ORDER BY sales_amount DESC
            """
        )
        category_stock = query_all(
            """
            SELECT
                c.category_name,
                COALESCE(SUM(st.quantity), 0) AS stock_quantity
            FROM stock st
            JOIN product p ON st.product_id = p.product_id
            JOIN category c ON p.category_id = c.category_id
            GROUP BY c.category_id, c.category_name
            ORDER BY stock_quantity DESC
            """
        )
        hot_products = query_all(
            """
            SELECT
                p.product_id,
                p.product_name,
                c.category_name,
                b.brand_name,
                COUNT(sd.detail_id) AS sales_quantity,
                COALESCE(SUM(sd.subtotal), 0) AS sales_amount
            FROM sales_order so
            JOIN sales_detail sd ON so.sales_id = sd.sales_id
            JOIN product p ON sd.product_id = p.product_id
            JOIN category c ON p.category_id = c.category_id
            JOIN brand b ON p.brand_id = b.brand_id
            WHERE so.status = '已完成'
            GROUP BY p.product_id, p.product_name, c.category_name, b.brand_name
            ORDER BY sales_quantity DESC, sales_amount DESC
            LIMIT 8
            """
        )
        returned_orders = query_all(
            """
            SELECT
                so.sales_id AS id,
                c.customer_name,
                so.order_date,
                so.paid_amount,
                so.status
            FROM sales_order so
            JOIN customer c ON so.customer_id = c.customer_id
            WHERE so.status = '已退货'
            ORDER BY so.created_at DESC, so.order_date DESC
            LIMIT 8
            """
        )
        warning_summary = query_all(
            """
            SELECT
                category_name,
                COUNT(*) AS warning_count
            FROM v_inventory_warning
            GROUP BY category_name
            ORDER BY warning_count DESC
            """
        )

        return success(
            {
                "salesTrend": sales_trend,
                "categorySales": serialize_rows(category_sales),
                "categoryStock": serialize_rows(category_stock),
                "hotProducts": serialize_rows(hot_products),
                "returnedOrders": serialize_rows(returned_orders),
                "warningSummary": serialize_rows(warning_summary),
            }
        )
    except Exception as exc:
        return error(f"查询统计报表失败：{exc}", code=500)
