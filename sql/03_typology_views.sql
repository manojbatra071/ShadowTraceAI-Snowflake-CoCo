USE DATABASE SHADOWTRACE_AI;
USE SCHEMA AML;

CREATE OR REPLACE VIEW vw_wage_harvesting_signals AS
WITH payroll AS (
  SELECT
    ca.case_id,
    ca.account_id AS employer_account_id,
    t.to_account_id AS worker_account_id,
    t.transaction_ts AS payroll_ts,
    t.amount AS wage_amount
  FROM case_alerts ca
  JOIN transactions t
    ON t.from_account_id = ca.account_id
   AND t.transaction_type = 'PAYROLL'
), onward AS (
  SELECT
    p.case_id,
    p.employer_account_id,
    p.worker_account_id,
    p.payroll_ts,
    p.wage_amount,
    o.to_account_id AS controller_account_id,
    o.amount AS onward_amount,
    DATEDIFF('hour', p.payroll_ts, o.transaction_ts) AS hours_to_onward
  FROM payroll p
  JOIN transactions o
    ON o.from_account_id = p.worker_account_id
   AND o.transaction_type = 'TRANSFER'
   AND o.transaction_ts BETWEEN p.payroll_ts AND DATEADD('hour', 24, p.payroll_ts)
), aggregated AS (
  SELECT
    case_id,
    employer_account_id AS account_id,
    COUNT(DISTINCT worker_account_id) AS impacted_workers,
    COUNT(DISTINCT controller_account_id) AS controller_accounts,
    ROUND(SUM(onward_amount) / NULLIF(SUM(wage_amount), 0), 3) AS onward_ratio,
    ROUND(AVG(hours_to_onward), 1) AS avg_hours_to_onward
  FROM onward
  GROUP BY case_id, employer_account_id
)
SELECT
  case_id,
  account_id,
  'WAGE_HARVESTING' AS signal_type,
  IFF(impacted_workers >= 3 AND onward_ratio >= 0.70, TRUE, FALSE) AS signal_detected,
  IFF(impacted_workers >= 3 AND onward_ratio >= 0.70, 25, 0) AS risk_points,
  impacted_workers,
  controller_accounts,
  onward_ratio,
  avg_hours_to_onward,
  'Multiple payroll recipients transfer most wages to common controllers within 24 hours.' AS explanation
FROM aggregated;

CREATE OR REPLACE VIEW vw_account_control_signals AS
WITH shared_access AS (
  SELECT
    device_id,
    ip_address,
    COUNT(DISTINCT account_id) AS shared_account_count,
    ARRAY_AGG(DISTINCT account_id) WITHIN GROUP (ORDER BY account_id) AS controlled_accounts
  FROM device_ip_signals
  WHERE login_result = 'SUCCESS'
  GROUP BY device_id, ip_address
), case_links AS (
  SELECT DISTINCT
    ca.case_id,
    ca.account_id,
    s.device_id,
    s.ip_address,
    s.shared_account_count,
    s.controlled_accounts
  FROM case_alerts ca
  JOIN accounts employer ON employer.account_id = ca.account_id
  JOIN accounts worker ON worker.employer_id = employer.employer_id
  JOIN device_ip_signals d ON d.account_id = worker.account_id
  JOIN shared_access s ON s.device_id = d.device_id AND s.ip_address = d.ip_address
)
SELECT
  case_id,
  account_id,
  'ACCOUNT_CONTROL' AS signal_type,
  IFF(MAX(shared_account_count) >= 4, TRUE, FALSE) AS signal_detected,
  IFF(MAX(shared_account_count) >= 4, 25, 0) AS risk_points,
  MAX(shared_account_count) AS shared_account_count,
  MAX(device_id) AS shared_device_id,
  MAX(ip_address) AS shared_ip_address,
  ANY_VALUE(controlled_accounts) AS controlled_accounts,
  'A common device and IP access several worker, controller, or funnel accounts.' AS explanation
FROM case_links
GROUP BY case_id, account_id;

CREATE OR REPLACE VIEW vw_spending_anomaly_signals AS
WITH workers AS (
  SELECT DISTINCT ca.case_id, ca.account_id, t.to_account_id AS worker_account_id
  FROM case_alerts ca
  JOIN transactions t ON t.from_account_id = ca.account_id AND t.transaction_type = 'PAYROLL'
), flows AS (
  SELECT
    w.case_id,
    w.account_id,
    w.worker_account_id,
    SUM(IFF(t.transaction_type IN ('TRANSFER', 'CASH_WITHDRAWAL'), t.amount, 0)) AS transfer_or_cash_amount,
    SUM(IFF(t.transaction_type = 'CARD', t.amount, 0)) AS everyday_spend_amount,
    SUM(t.amount) AS total_outgoing
  FROM workers w
  JOIN transactions t ON t.from_account_id = w.worker_account_id
  GROUP BY w.case_id, w.account_id, w.worker_account_id
), aggregated AS (
  SELECT
    case_id,
    account_id,
    COUNT_IF(transfer_or_cash_amount / NULLIF(total_outgoing, 0) >= 0.80) AS anomalous_workers,
    ROUND(AVG(transfer_or_cash_amount / NULLIF(total_outgoing, 0)), 3) AS avg_transfer_or_cash_ratio,
    ROUND(AVG(everyday_spend_amount / NULLIF(total_outgoing, 0)), 3) AS avg_everyday_spend_ratio
  FROM flows
  GROUP BY case_id, account_id
)
SELECT
  case_id,
  account_id,
  'SPENDING_ANOMALY' AS signal_type,
  IFF(anomalous_workers >= 3, TRUE, FALSE) AS signal_detected,
  IFF(anomalous_workers >= 3, 14, 0) AS risk_points,
  anomalous_workers,
  avg_transfer_or_cash_ratio,
  avg_everyday_spend_ratio,
  'Worker accounts show minimal normal spending and rapid transfer or cash depletion.' AS explanation
FROM aggregated;

CREATE OR REPLACE VIEW vw_geographic_risk_signals AS
WITH payroll_workers AS (
  SELECT DISTINCT ca.case_id, ca.account_id, t.to_account_id AS worker_account_id
  FROM case_alerts ca
  JOIN transactions t ON t.from_account_id = ca.account_id AND t.transaction_type = 'PAYROLL'
), controllers AS (
  SELECT DISTINCT p.case_id, p.account_id, t.to_account_id AS network_account_id
  FROM payroll_workers p
  JOIN transactions t ON t.from_account_id = p.worker_account_id AND t.transaction_type = 'TRANSFER'
  WHERE t.to_account_id IS NOT NULL
), funnels AS (
  SELECT DISTINCT c.case_id, c.account_id, t.to_account_id AS network_account_id
  FROM controllers c
  JOIN transactions t ON t.from_account_id = c.network_account_id AND t.transaction_type = 'TRANSFER'
  WHERE t.to_account_id IS NOT NULL
), network_accounts AS (
  SELECT case_id, account_id, worker_account_id AS network_account_id FROM payroll_workers
  UNION
  SELECT case_id, account_id, network_account_id FROM controllers
  UNION
  SELECT case_id, account_id, network_account_id FROM funnels
), corridors AS (
  SELECT DISTINCT
    ca.case_id,
    ca.account_id,
    employer.country_code AS employer_country,
    worker.country_code AS worker_country
  FROM case_alerts ca
  JOIN accounts employer ON employer.account_id = ca.account_id
  JOIN transactions t ON t.from_account_id = ca.account_id AND t.transaction_type = 'PAYROLL'
  JOIN accounts worker ON worker.account_id = t.to_account_id
  WHERE worker.country_code <> employer.country_code
), cash_geography AS (
  SELECT
    n.case_id,
    n.account_id,
    COUNT_IF(t.transaction_type = 'CASH_WITHDRAWAL' AND t.counterparty_country <> employer.country_code) AS foreign_cash_events
  FROM network_accounts n
  JOIN accounts employer ON employer.account_id = n.account_id
  LEFT JOIN transactions t ON t.from_account_id = n.network_account_id
  GROUP BY n.case_id, n.account_id
)
SELECT
  c.case_id,
  c.account_id,
  'GEOGRAPHIC_RISK' AS signal_type,
  IFF(COUNT(DISTINCT c.worker_country) >= 3 AND MAX(g.foreign_cash_events) >= 1, TRUE, FALSE) AS signal_detected,
  IFF(COUNT(DISTINCT c.worker_country) >= 3 AND MAX(g.foreign_cash_events) >= 1, 12, 0) AS risk_points,
  COUNT(DISTINCT c.worker_country) AS cross_border_worker_countries,
  ARRAY_AGG(DISTINCT c.worker_country) WITHIN GROUP (ORDER BY c.worker_country) AS corridor_countries,
  MAX(g.foreign_cash_events) AS foreign_cash_events,
  'Cross-border worker recruitment is paired with out-of-country cash withdrawal.' AS explanation
FROM corridors c
JOIN cash_geography g ON g.case_id = c.case_id
GROUP BY c.case_id, c.account_id;

CREATE OR REPLACE VIEW vw_sector_risk_signals AS
SELECT
  ca.case_id,
  ca.account_id,
  'SECTOR_RISK' AS signal_type,
  IFF(a.sector IN ('CONSTRUCTION', 'AGRICULTURE', 'HOSPITALITY', 'LABOUR_SERVICES')
      AND k.beneficial_owner_status <> 'COMPLETE', TRUE, FALSE) AS signal_detected,
  IFF(a.sector IN ('CONSTRUCTION', 'AGRICULTURE', 'HOSPITALITY', 'LABOUR_SERVICES')
      AND k.beneficial_owner_status <> 'COMPLETE', 8, 0) AS risk_points,
  a.sector,
  k.beneficial_owner_status,
  a.declared_employee_count,
  'Labour-intensive sector risk is elevated by incomplete beneficial ownership information.' AS explanation
FROM case_alerts ca
JOIN accounts a ON a.account_id = ca.account_id
JOIN kyc_profiles k ON k.account_id = ca.account_id;

CREATE OR REPLACE VIEW vw_case_network AS
WITH payroll_edges AS (
  SELECT
    ca.case_id,
    t.from_account_id AS source_account_id,
    t.to_account_id AS target_account_id,
    'PAYROLL' AS relationship_type,
    COUNT(*) AS event_count,
    SUM(t.amount) AS total_amount,
    'Source employer paid wages to worker account' AS evidence
  FROM case_alerts ca
  JOIN transactions t ON t.from_account_id = ca.account_id AND t.transaction_type = 'PAYROLL'
  GROUP BY ca.case_id, t.from_account_id, t.to_account_id
), worker_accounts AS (
  SELECT DISTINCT case_id, target_account_id AS account_id FROM payroll_edges
), controller_accounts AS (
  SELECT DISTINCT w.case_id, t.to_account_id AS account_id
  FROM worker_accounts w
  JOIN transactions t ON t.from_account_id = w.account_id AND t.transaction_type = 'TRANSFER'
  WHERE t.to_account_id IS NOT NULL
), funnel_accounts AS (
  SELECT DISTINCT c.case_id, t.to_account_id AS account_id
  FROM controller_accounts c
  JOIN transactions t ON t.from_account_id = c.account_id AND t.transaction_type = 'TRANSFER'
  WHERE t.to_account_id IS NOT NULL
), network_accounts AS (
  SELECT * FROM worker_accounts
  UNION
  SELECT * FROM controller_accounts
  UNION
  SELECT * FROM funnel_accounts
), onward_edges AS (
  SELECT
    n.case_id,
    t.from_account_id,
    COALESCE(t.to_account_id, 'EXTERNAL_CASH') AS target_account_id,
    CASE
      WHEN t.transaction_type = 'CASH_WITHDRAWAL' THEN 'CASH_OUT'
      WHEN c.account_id IS NOT NULL THEN 'CONSOLIDATION'
      ELSE 'FUNDS_TO_CONTROLLER'
    END AS relationship_type,
    COUNT(*) AS event_count,
    SUM(t.amount) AS total_amount,
    'Rapid onward movement or network cash-out' AS evidence
  FROM network_accounts n
  JOIN transactions t ON t.from_account_id = n.account_id
  LEFT JOIN controller_accounts c ON c.case_id = n.case_id AND c.account_id = n.account_id
  WHERE t.transaction_type IN ('TRANSFER', 'CASH_WITHDRAWAL')
    AND (t.to_account_id IS NOT NULL OR t.transaction_type = 'CASH_WITHDRAWAL')
  GROUP BY n.case_id, t.from_account_id, COALESCE(t.to_account_id, 'EXTERNAL_CASH'),
    CASE
      WHEN t.transaction_type = 'CASH_WITHDRAWAL' THEN 'CASH_OUT'
      WHEN c.account_id IS NOT NULL THEN 'CONSOLIDATION'
      ELSE 'FUNDS_TO_CONTROLLER'
    END
), shared_access_edges AS (
  SELECT DISTINCT
    n1.case_id,
    d1.account_id AS source_account_id,
    d2.account_id AS target_account_id,
    'SHARED_DEVICE_IP' AS relationship_type,
    1 AS event_count,
    0::NUMBER(18,2) AS total_amount,
    'Accounts share device ' || d1.device_id || ' and IP ' || d1.ip_address AS evidence
  FROM network_accounts n1
  JOIN network_accounts n2 ON n2.case_id = n1.case_id AND n2.account_id > n1.account_id
  JOIN device_ip_signals d1 ON d1.account_id = n1.account_id
  JOIN device_ip_signals d2
    ON d2.device_id = d1.device_id
   AND d2.ip_address = d1.ip_address
   AND d2.account_id = n2.account_id
)
SELECT * FROM payroll_edges
UNION ALL
SELECT * FROM onward_edges
UNION ALL
SELECT * FROM shared_access_edges;
