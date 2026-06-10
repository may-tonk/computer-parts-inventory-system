START TRANSACTION;

CREATE TEMPORARY TABLE tmp_target_stock (
  product_name VARCHAR(150) NOT NULL PRIMARY KEY,
  sn_prefix VARCHAR(80) NOT NULL,
  target_in_stock INT NOT NULL
);

INSERT INTO tmp_target_stock (product_name, sn_prefix, target_in_stock) VALUES
('Intel Core i7-13700KF', 'SN-DEMO-CPU-13700KF', 9),
('Intel Core i7-14700KF', 'SN-DEMO-CPU-14700KF', 9),
('Intel Core i9-14900K', 'SN-DEMO-CPU-14900K', 6),
('AMD Ryzen 7 9850X3D', 'SN-DEMO-CPU-9850X3D', 6),
('AMD Ryzen 9 9950X3D2', 'SN-DEMO-CPU-9950X3D2', 1),
('金百达 DDR5 96GB 6400', 'SN-DEMO-MEM-KBD5-96', 9),
('金百达 DDR4 32GB 3600', 'SN-DEMO-MEM-KBD4-32', 12),
('光威 DDR5 64GB 6400', 'SN-DEMO-MEM-GWD5-64', 8),
('光威 DDR4 32GB 3600', 'SN-DEMO-MEM-GWD4-32', 11),
('致态 TiPro9000 4TB', 'SN-DEMO-SSD-TIPRO-4T', 6),
('三星 9100 PRO 8TB', 'SN-DEMO-SSD-9100PRO-8T', 1),
('致态 TiPlus9100 4TB', 'SN-DEMO-SSD-TIPLUS-4T', 8),
('三星 990 EVO Plus 4TB', 'SN-DEMO-SSD-990EVO-4T', 6),
('华硕 ROG Z790-A 吹雪', 'SN-DEMO-MB-Z790A', 5),
('微星 Z790 PROJECT ZERO', 'SN-DEMO-MB-Z790PZ', 6),
('华硕 ROG X870E EXTREME', 'SN-DEMO-MB-X870E', 1),
('微星 MAG X870E GODLIKE MAX', 'SN-DEMO-MB-GODLIKE', 1);

CREATE TEMPORARY TABLE tmp_seq (n INT NOT NULL PRIMARY KEY);
INSERT INTO tmp_seq (n) VALUES
(1),(2),(3),(4),(5),(6),(7),(8),(9),(10),
(11),(12),(13),(14),(15),(16),(17),(18),(19),(20);

INSERT INTO product_sn (
  product_id,
  warehouse_id,
  sn_code,
  batch_no,
  inbound_date,
  warranty_end_date,
  status
)
SELECT
  p.product_id,
  w.warehouse_id,
  CONCAT(t.sn_prefix, '-', LPAD(existing.total_count + seq.n, 4, '0')) AS sn_code,
  CONCAT('DEMO-BATCH-', DATE_FORMAT(CURDATE(), '%Y%m%d')),
  CURDATE(),
  DATE_ADD(CURDATE(), INTERVAL 36 MONTH),
  '在库'
FROM tmp_target_stock t
JOIN product p ON p.product_name = t.product_name
JOIN (SELECT warehouse_id FROM warehouse ORDER BY warehouse_id LIMIT 1) w
JOIN (
  SELECT
    p2.product_id,
    COALESCE(SUM(CASE WHEN ps.status = '在库' THEN 1 ELSE 0 END), 0) AS in_stock_count,
    COALESCE(COUNT(ps.sn_id), 0) AS total_count
  FROM product p2
  LEFT JOIN product_sn ps ON ps.product_id = p2.product_id
  GROUP BY p2.product_id
) existing ON existing.product_id = p.product_id
JOIN tmp_seq seq ON seq.n <= GREATEST(t.target_in_stock - existing.in_stock_count, 0);

INSERT INTO product_sn (
  product_id,
  warehouse_id,
  sn_code,
  batch_no,
  inbound_date,
  warranty_end_date,
  status
)
SELECT
  p.product_id,
  w.warehouse_id,
  CONCAT('SN-LOCK-', p.product_id, '-0001'),
  CONCAT('LOCK-BATCH-', DATE_FORMAT(CURDATE(), '%Y%m%d')),
  CURDATE(),
  DATE_ADD(CURDATE(), INTERVAL 36 MONTH),
  '锁定'
FROM product p
JOIN (SELECT warehouse_id FROM warehouse ORDER BY warehouse_id LIMIT 1) w
WHERE p.product_name IN ('华硕 ROG Z790-A 吹雪', '微星 Z790 PROJECT ZERO')
  AND NOT EXISTS (
    SELECT 1
    FROM product_sn ps
    WHERE ps.sn_code = CONCAT('SN-LOCK-', p.product_id, '-0001')
  );

INSERT INTO stock (product_id, warehouse_id, quantity, updated_at)
SELECT
  ps.product_id,
  ps.warehouse_id,
  SUM(CASE WHEN ps.status = '在库' THEN 1 ELSE 0 END) AS quantity,
  NOW()
FROM product_sn ps
GROUP BY ps.product_id, ps.warehouse_id
ON DUPLICATE KEY UPDATE
  quantity = VALUES(quantity),
  updated_at = VALUES(updated_at);

COMMIT;
