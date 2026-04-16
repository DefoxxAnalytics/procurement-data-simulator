SAMPLE_QUERIES = """-- Sample queries for dataset.sqlite
-- Run:  sqlite3 dataset.sqlite < sample_queries.sql

-- 1. Top 10 suppliers by total transaction spend
SELECT s.name, ROUND(SUM(t.amount), 2) AS total_spend
FROM transactions t JOIN suppliers s ON s.supplier_id = t.supplier_id
GROUP BY s.supplier_id ORDER BY total_spend DESC LIMIT 10;

-- 2. Monthly spend trend
SELECT strftime('%Y-%m', date) AS month, ROUND(SUM(amount), 2) AS spend
FROM transactions GROUP BY month ORDER BY month;

-- 3. Category spend mix (share of total)
SELECT c.name,
       ROUND(SUM(t.amount), 2) AS spend,
       ROUND(100.0 * SUM(t.amount) / (SELECT SUM(amount) FROM transactions), 2) AS pct
FROM transactions t JOIN categories c ON c.category_id = t.category_id
GROUP BY c.category_id ORDER BY spend DESC;

-- 4. Contract coverage: PO spend on-contract vs off-contract
SELECT is_contract_backed, COUNT(*) AS pos, ROUND(SUM(total_amount), 2) AS spend
FROM purchase_orders GROUP BY is_contract_backed;

-- 5. Invoice 3-way-match exception rate
SELECT match_status, COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM invoices), 2) AS pct
FROM invoices GROUP BY match_status ORDER BY cnt DESC;

-- 6. Days payable outstanding (paid invoices only)
SELECT ROUND(AVG(julianday(paid_date) - julianday(invoice_date)), 1) AS avg_dpo
FROM invoices WHERE paid_date IS NOT NULL;

-- 7. Policy violations by severity
SELECT severity, violation_type, COUNT(*) AS cnt
FROM policy_violations GROUP BY severity, violation_type ORDER BY severity, cnt DESC;

-- 8. PR -> PO conversion rate
SELECT
  (SELECT COUNT(*) FROM purchase_requisitions WHERE status = 'converted_to_po') * 1.0 /
  (SELECT COUNT(*) FROM purchase_requisitions) AS conversion_rate;

-- 9. Suppliers with active contracts but also off-contract POs (maverick spend indicator)
SELECT s.name,
       SUM(CASE WHEN po.is_contract_backed = 1 THEN po.total_amount ELSE 0 END) AS on_contract,
       SUM(CASE WHEN po.is_contract_backed = 0 THEN po.total_amount ELSE 0 END) AS off_contract
FROM suppliers s JOIN purchase_orders po ON po.supplier_id = s.supplier_id
WHERE s.supplier_id IN (SELECT supplier_id FROM contracts WHERE status = 'active')
GROUP BY s.supplier_id
HAVING off_contract > 0
ORDER BY off_contract DESC LIMIT 20;

-- 10. Benford first-digit distribution on invoice amounts
SELECT CAST(SUBSTR(CAST(CAST(invoice_amount AS INTEGER) AS TEXT), 1, 1) AS INTEGER) AS leading_digit,
       COUNT(*) AS cnt
FROM invoices WHERE invoice_amount >= 1
GROUP BY leading_digit ORDER BY leading_digit;
"""
