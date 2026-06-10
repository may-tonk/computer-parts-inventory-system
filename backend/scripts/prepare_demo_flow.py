import json
import sys
from datetime import date
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import create_app
from db import query_all, query_one


DEMO_REMARK = "规范演示数据-退货统计闭环"


def post_json(client, url, payload):
    response = client.post(url, json=payload)
    data = response.get_json()
    if response.status_code >= 400:
        raise RuntimeError(f"{url} failed: {data}")
    return data["data"]


def main():
    existing = query_one(
        """
        SELECT COUNT(*) AS count
        FROM purchase_order
        WHERE remark = %s
        """,
        (DEMO_REMARK,),
    )
    if existing and int(existing["count"] or 0) > 0:
        print(json.dumps({"skipped": True, "reason": "demo flow already exists"}, ensure_ascii=False))
        return

    product = query_one(
        """
        SELECT product_id
        FROM product
        WHERE status = '在售'
        ORDER BY product_id
        LIMIT 1
        """
    )
    supplier = query_one("SELECT supplier_id FROM supplier ORDER BY supplier_id LIMIT 1")
    customer = query_one("SELECT customer_id FROM customer ORDER BY customer_id LIMIT 1")
    warehouse = query_one("SELECT warehouse_id FROM warehouse ORDER BY warehouse_id LIMIT 1")
    employee = query_one("SELECT user_id FROM system_user ORDER BY user_id LIMIT 1")

    if not all([product, supplier, customer, warehouse, employee]):
        raise RuntimeError("Missing product/supplier/customer/warehouse/employee seed data")

    today = date.today().strftime("%Y-%m-%d")
    app = create_app()
    client = app.test_client()

    purchase = post_json(
        client,
        "/api/purchase-orders",
        {
            "supplierId": supplier["supplier_id"],
            "buyerId": employee["user_id"],
            "warehouseId": warehouse["warehouse_id"],
            "orderDate": today,
            "remark": DEMO_REMARK,
            "details": [
                {
                    "productId": product["product_id"],
                    "quantity": 3,
                    "unitPrice": 1200,
                    "batchNo": f"DEMO-FLOW-{today.replace('-', '')}",
                    "productionDate": today,
                }
            ],
        },
    )

    sn_codes = purchase["generatedSnCodes"]
    if len(sn_codes) < 3:
        raise RuntimeError(f"Expected 3 generated SN codes, got {sn_codes}")

    completed_sale = post_json(
        client,
        "/api/sales-orders",
        {
            "customerId": customer["customer_id"],
            "sellerId": employee["user_id"],
            "warehouseId": warehouse["warehouse_id"],
            "orderDate": today,
            "discountRate": 1,
            "remark": DEMO_REMARK,
            "details": [{"snCode": sn_codes[0], "unitPrice": 1680}],
        },
    )

    returned_sale = post_json(
        client,
        "/api/sales-orders",
        {
            "customerId": customer["customer_id"],
            "sellerId": employee["user_id"],
            "warehouseId": warehouse["warehouse_id"],
            "orderDate": today,
            "discountRate": 1,
            "remark": DEMO_REMARK,
            "details": [{"snCode": sn_codes[1], "unitPrice": 1580}],
        },
    )
    returned_result = post_json(
        client,
        f"/api/sales-orders/{returned_sale['id']}/return",
        {},
    )

    states = query_all(
        """
        SELECT sn_code, status
        FROM product_sn
        WHERE sn_code IN (%s, %s, %s)
        ORDER BY sn_code
        """,
        tuple(sn_codes[:3]),
    )

    result = {
        "purchase": purchase,
        "completedSale": completed_sale,
        "returnedSale": returned_sale,
        "returnResult": returned_result,
        "snStates": states,
    }
    print(json.dumps(result, ensure_ascii=False, default=str, indent=2))


if __name__ == "__main__":
    main()
