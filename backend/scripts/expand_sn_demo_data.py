from datetime import date, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db import get_connection


TARGETS = [
    ("Intel Core i7-13700KF", "SN-DEMO-CPU-13700KF", 9),
    ("Intel Core i7-14700KF", "SN-DEMO-CPU-14700KF", 9),
    ("Intel Core i9-14900K", "SN-DEMO-CPU-14900K", 6),
    ("AMD Ryzen 7 9850X3D", "SN-DEMO-CPU-9850X3D", 6),
    ("AMD Ryzen 9 9950X3D2", "SN-DEMO-CPU-9950X3D2", 1),
    ("金百达 DDR5 96GB 6400", "SN-DEMO-MEM-KBD5-96", 9),
    ("金百达 DDR4 32GB 3600", "SN-DEMO-MEM-KBD4-32", 12),
    ("光威 DDR5 64GB 6400", "SN-DEMO-MEM-GWD5-64", 8),
    ("光威 DDR4 32GB 3600", "SN-DEMO-MEM-GWD4-32", 11),
    ("致态 TiPro9000 4TB", "SN-DEMO-SSD-TIPRO-4T", 6),
    ("三星 9100 PRO 8TB", "SN-DEMO-SSD-9100PRO-8T", 1),
    ("致态 TiPlus9100 4TB", "SN-DEMO-SSD-TIPLUS-4T", 8),
    ("三星 990 EVO Plus 4TB", "SN-DEMO-SSD-990EVO-4T", 6),
    ("华硕 ROG Z790-A 吹雪", "SN-DEMO-MB-Z790A", 5),
    ("微星 Z790 PROJECT ZERO", "SN-DEMO-MB-Z790PZ", 6),
    ("华硕 ROG X870E EXTREME", "SN-DEMO-MB-X870E", 1),
    ("微星 MAG X870E GODLIKE MAX", "SN-DEMO-MB-GODLIKE", 1),
]

LOCKED_PRODUCT_NAMES = {"华硕 ROG Z790-A 吹雪", "微星 Z790 PROJECT ZERO"}


def next_sn(cursor, product_id, prefix, offset):
    suffix = offset
    while True:
        sn_code = f"{prefix}-{suffix:04d}"
        cursor.execute(
            "SELECT 1 FROM product_sn WHERE sn_code = %s LIMIT 1",
            (sn_code,),
        )
        if not cursor.fetchone():
            return sn_code
        suffix += 1


def main():
    today = date.today()
    warranty_end = today + timedelta(days=365 * 3)
    inserted = 0
    locked_inserted = 0

    with get_connection() as connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT warehouse_id FROM warehouse ORDER BY warehouse_id LIMIT 1"
                )
                warehouse = cursor.fetchone()
                if not warehouse:
                    raise RuntimeError("warehouse 表没有数据")
                warehouse_id = warehouse["warehouse_id"]

                for product_name, prefix, target_in_stock in TARGETS:
                    cursor.execute(
                        """
                        SELECT product_id
                        FROM product
                        WHERE product_name = %s
                        """,
                        (product_name,),
                    )
                    product = cursor.fetchone()
                    if not product:
                        raise RuntimeError(f"商品不存在：{product_name}")

                    product_id = product["product_id"]
                    cursor.execute(
                        """
                        SELECT
                            SUM(CASE WHEN status = '在库' THEN 1 ELSE 0 END) AS in_stock_count,
                            COUNT(*) AS total_count
                        FROM product_sn
                        WHERE product_id = %s AND warehouse_id = %s
                        """,
                        (product_id, warehouse_id),
                    )
                    counts = cursor.fetchone()
                    in_stock_count = int(counts["in_stock_count"] or 0)
                    total_count = int(counts["total_count"] or 0)
                    missing = max(target_in_stock - in_stock_count, 0)

                    for i in range(1, missing + 1):
                        sn_code = next_sn(cursor, product_id, prefix, total_count + i)
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
                                product_id,
                                warehouse_id,
                                sn_code,
                                f"DEMO-BATCH-{today:%Y%m%d}",
                                today,
                                warranty_end,
                            ),
                        )
                        inserted += 1

                    if product_name in LOCKED_PRODUCT_NAMES:
                        locked_sn = f"SN-LOCK-{product_id}-0001"
                        cursor.execute(
                            "SELECT 1 FROM product_sn WHERE sn_code = %s LIMIT 1",
                            (locked_sn,),
                        )
                        if not cursor.fetchone():
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
                                VALUES (%s, %s, %s, %s, %s, %s, '锁定')
                                """,
                                (
                                    product_id,
                                    warehouse_id,
                                    locked_sn,
                                    f"LOCK-BATCH-{today:%Y%m%d}",
                                    today,
                                    warranty_end,
                                ),
                            )
                            locked_inserted += 1

                cursor.execute(
                    """
                    SELECT
                        product_id,
                        warehouse_id,
                        SUM(CASE WHEN status = '在库' THEN 1 ELSE 0 END) AS quantity
                    FROM product_sn
                    GROUP BY product_id, warehouse_id
                    """
                )
                stock_rows = cursor.fetchall()
                for row in stock_rows:
                    cursor.execute(
                        """
                        INSERT INTO stock (product_id, warehouse_id, quantity, updated_at)
                        VALUES (%s, %s, %s, NOW())
                        ON DUPLICATE KEY UPDATE
                            quantity = VALUES(quantity),
                            updated_at = VALUES(updated_at)
                        """,
                        (
                            row["product_id"],
                            row["warehouse_id"],
                            int(row["quantity"] or 0),
                        ),
                    )

            connection.commit()
        except Exception:
            connection.rollback()
            raise

    print(f"Inserted in-stock SN: {inserted}")
    print(f"Inserted locked SN: {locked_inserted}")


if __name__ == "__main__":
    main()
