USE DATABASE SHADOWTRACE_AI;
USE SCHEMA AML;

-- PUT is executed client-side by Snowflake CLI/CoCo. Run this file from the repo root.
PUT file://data/seed/accounts.csv @SEED_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://data/seed/transactions.csv @SEED_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://data/seed/kyc_profiles.csv @SEED_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://data/seed/device_ip_signals.csv @SEED_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://data/seed/external_watchlist.csv @SEED_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT file://data/seed/document_evidence.csv @SEED_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

TRUNCATE TABLE accounts;
TRUNCATE TABLE transactions;
TRUNCATE TABLE kyc_profiles;
TRUNCATE TABLE device_ip_signals;
TRUNCATE TABLE external_watchlist;
TRUNCATE TABLE document_evidence;

COPY INTO accounts
  FROM @SEED_STAGE/accounts.csv
  FILE_FORMAT = (FORMAT_NAME = CSV_SEED_FORMAT)
  MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

COPY INTO transactions
  FROM @SEED_STAGE/transactions.csv
  FILE_FORMAT = (FORMAT_NAME = CSV_SEED_FORMAT)
  MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

COPY INTO kyc_profiles
  FROM @SEED_STAGE/kyc_profiles.csv
  FILE_FORMAT = (FORMAT_NAME = CSV_SEED_FORMAT)
  MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

COPY INTO device_ip_signals
  FROM @SEED_STAGE/device_ip_signals.csv
  FILE_FORMAT = (FORMAT_NAME = CSV_SEED_FORMAT)
  MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

COPY INTO external_watchlist
  FROM @SEED_STAGE/external_watchlist.csv
  FILE_FORMAT = (FORMAT_NAME = CSV_SEED_FORMAT)
  MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

CREATE OR REPLACE TEMPORARY TABLE document_evidence_seed (
  document_id VARCHAR,
  case_id VARCHAR,
  account_id VARCHAR,
  document_type VARCHAR,
  file_name VARCHAR,
  uploaded_at TIMESTAMP_TZ,
  extraction_confidence NUMBER(5,2),
  metadata VARCHAR,
  risk_indicators VARCHAR,
  evidence_summary VARCHAR,
  review_status VARCHAR
);

COPY INTO document_evidence_seed
  FROM @SEED_STAGE/document_evidence.csv
  FILE_FORMAT = (FORMAT_NAME = CSV_SEED_FORMAT)
  MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

INSERT INTO document_evidence (
  document_id, case_id, account_id, document_type, file_name, uploaded_at,
  extraction_confidence, metadata, risk_indicators, evidence_summary, review_status
)
SELECT
  document_id, case_id, account_id, document_type, file_name, uploaded_at,
  extraction_confidence, PARSE_JSON(metadata), PARSE_JSON(risk_indicators),
  evidence_summary, review_status
FROM document_evidence_seed;

MERGE INTO case_alerts target
USING (
  SELECT * FROM VALUES
    ('CASE-C003', 'ACC-C-003', 'MODERN_SLAVERY_NETWORK', 'OPEN', 'CRITICAL',
     '2026-07-01 08:30:00 +00:00'::TIMESTAMP_TZ, 'AML_DEMO_REVIEWER',
     'Corporate payroll activity links five workers to a shared controller and funnel account.'),
    ('CASE-C010', 'ACC-C-010', 'PAYROLL_MONITORING', 'OPEN', 'LOW',
     '2026-07-01 08:35:00 +00:00'::TIMESTAMP_TZ, 'AML_DEMO_REVIEWER',
     'Routine payroll monitoring alert retained as a benign comparison case.')
  source(case_id, account_id, alert_type, alert_status, priority, created_at, assigned_to, alert_summary)
) source
ON target.case_id = source.case_id
WHEN MATCHED THEN UPDATE SET
  target.account_id = source.account_id,
  target.alert_type = source.alert_type,
  target.alert_status = source.alert_status,
  target.priority = source.priority,
  target.created_at = source.created_at,
  target.assigned_to = source.assigned_to,
  target.alert_summary = source.alert_summary
WHEN NOT MATCHED THEN INSERT (
  case_id, account_id, alert_type, alert_status, priority, created_at, assigned_to, alert_summary
) VALUES (
  source.case_id, source.account_id, source.alert_type, source.alert_status, source.priority,
  source.created_at, source.assigned_to, source.alert_summary
);

DELETE FROM audit_events WHERE case_id IN ('CASE-C003', 'CASE-C010');
INSERT INTO audit_events (
  audit_event_id, case_id, event_ts, actor_type, actor_name, event_type,
  event_detail, object_type, object_id, event_metadata
)
SELECT column1, column2, column3::TIMESTAMP_TZ, column4, column5, column6, column7, column8, column9, PARSE_JSON(column10)
FROM VALUES
  ('AUD-C003-001', 'CASE-C003', '2026-07-01 08:30:00 +00:00', 'SYSTEM', 'Transaction Monitor',
   'ALERT_CREATED', 'Created modern-slavery network alert.', 'CASE', 'CASE-C003', '{"source":"transactions"}'),
  ('AUD-C003-002', 'CASE-C003', '2026-07-01 08:31:00 +00:00', 'SYSTEM', 'Typology SQL',
   'SIGNALS_EVALUATED', 'Evaluated wage harvesting, account control, spending, geography, and sector signals.', 'CASE', 'CASE-C003', '{"typologies":5}'),
  ('AUD-C003-003', 'CASE-C003', '2026-07-01 08:32:00 +00:00', 'SYSTEM', 'Evidence Pipeline',
   'EVIDENCE_LINKED', 'Linked four documents and three external intelligence records.', 'CASE', 'CASE-C003', '{"documents":4,"external_records":3}'),
  ('AUD-C010-001', 'CASE-C010', '2026-07-01 08:35:00 +00:00', 'SYSTEM', 'Transaction Monitor',
   'ALERT_CREATED', 'Created routine payroll comparison alert.', 'CASE', 'CASE-C010', '{"source":"transactions"}');

