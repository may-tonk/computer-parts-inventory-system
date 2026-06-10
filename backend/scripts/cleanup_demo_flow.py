import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from db import get_connection


DEMO_REMARK = "规范演示数据-退货统计闭环"


def main():
    with get_connection() as connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT ps.sn_code, ps.product_id, ps.warehouse_id, ps.status
                    FROM purchase_order po
                    JOIN inbound_order io ON po.purchase_id = io.purchase_id
                    JOIN inbound_detail ib ON io.inbound_no = ib.inbound_no
                    JOIN product_sn ps ON ib.sn_code = ps.sn_code
                    WHERE po.remark = %s
                    """,
                    (DEMO_REMARK,),
                )
                sn_rows = cursor.fetchall()

                stock_decrements = {}
                for row in sn_rows:
                    if row["status"] == "在库":
                        key = (row["product_id"], row["warehouse_id"])
                        stock_decrements[key] = stock_decrements.get(key, 0) + 1

                cursor.execute(
                    """
                    SELECT sales_id, customer_id, paid_amount, status
                    FROM sales_order
                    WHERE remark = %s
                    """,
                    (DEMO_REMARK,),
                )
                sales_rows = cursor.fetchall()

                for row in sales_rows:
                    if row["status"] == "已完成":
                        cursor.execute(
                            """
                            UPDATE customer
                            SET total_spent = GREATEST(total_spent - %s, 0)
                            WHERE customer_id = %s
                            """,
                            (row["paid_amount"], row["customer_id"]),
                        )

                for (product_id, warehouse_id), quantity in stock_decrements.items():
                    cursor.execute(
                        """
                        UPDATE stock
                        SET quantity = GREATEST(quantity - %s, 0),
                            updated_at = NOW()
                        WHERE product_id = %s AND warehouse_id = %s
                        """,
                        (quantity, product_id, warehouse_id),
                    )

                cursor.execute(
                    """
                    DELETE od
                    FROM outbound_detail od
                    JOIN outbound_order oo ON od.outbound_no = oo.outbound_no
                    JOIN sales_order so ON oo.sales_id = so.sales_id
                    WHERE so.remark = %s
                    """,
                    (DEMO_REMARK,),
                )
                cursor.execute(
                    """
                    DELETE oo
                    FROM outbound_order oo
                    JOIN sales_order so ON oo.sales_id = so.sales_id
                    WHERE so.remark = %s
                    """,
                    (DEMO_REMARK,),
                )
                cursor.execute(
                    """
                    DELETE sd
                    FROM sales_detail sd
                    JOIN sales_order so ON sd.sales_id = so.sales_id
                    WHERE so.remark = %s
                    """,
                    (DEMO_REMARK,),
                )
                cursor.execute("DELETE FROM sales_order WHERE remark = %s", (DEMO_REMARK,))

                cursor.execute(
                    """
                    DELETE ib
                    FROM inbound_detail ib
                    JOIN inbound_order io ON ib.inbound_no = io.inbound_no
                    JOIN purchase_order po ON io.purchase_id = po.purchase_id
                    WHERE po.remark = %s
                    """,
                    (DEMO_REMARK,),
                )
                cursor.execute(
                    """
                    DELETE io
                    FROM inbound_order io
                    JOIN purchase_order po ON io.purchase_id = po.purchase_id
                    WHERE po.remark = %s
                    """,
                    (DEMO_REMARK,),
                )
                if sn_rows:
                    placeholders = ", ".join(["%s"] * len(sn_rows))
                    cursor.execute(
                        f"DELETE FROM product_sn WHERE sn_code IN ({placeholders})",
                        tuple(row["sn_code"] for row in sn_rows),
                    )
                cursor.execute(
                    """
                    DELETE pd
                    FROM purchase_detail pd
                    JOIN purchase_order po ON pd.purchase_id = po.purchase_id
                    WHERE po.remark = %s
                    """,
                    (DEMO_REMARK,),
                )
                cursor.execute("DELETE FROM purchase_order WHERE remark = %s", (DEMO_REMARK,))
            connection.commit()
            print("Demo flow cleaned")
        except Exception:
            connection.rollback()
            raise


if __name__ == "__main__":
    main()
