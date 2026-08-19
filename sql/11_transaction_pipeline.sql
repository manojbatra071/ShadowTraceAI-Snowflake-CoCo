-- Event-driven processing for newly inserted transactions.
-- Stream -> triggered task -> processing procedure -> cases/audit -> live views -> Cortex Agent tools.
USE ROLE ACCOUNTADMIN;
USE DATABASE SHADOWTRACE_AI;
USE SCHEMA AML;

CREATE TABLE IF NOT EXISTS transaction_processing_events (
  processing_event_id VARCHAR PRIMARY KEY,
  transaction_id VARCHAR NOT NULL,
  case_id VARCHAR,
  account_id VARCHAR,
  processed_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
  processor_name VARCHAR NOT NULL,
  processing_status VARCHAR NOT NULL,
  processing_detail VARCHAR
);

CREATE STREAM IF NOT EXISTS transactions_change_stream
  ON TABLE transactions
  APPEND_ONLY = TRUE;

CREATE OR REPLACE PROCEDURE sp_process_new_transactions()
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
  v_processed INTEGER DEFAULT 0;
BEGIN
  CREATE OR REPLACE TEMPORARY TABLE new_transaction_batch AS
  SELECT
    transaction_id, transaction_ts, from_account_id, to_account_id, amount,
    currency, transaction_type, channel, counterparty_country,
    merchant_category, description
  FROM transactions_change_stream
  WHERE METADATA$ACTION = 'INSERT';

  BEGIN TRANSACTION;

  MERGE INTO case_alerts target
  USING (
    SELECT DISTINCT
      a.account_id,
      'CASE-AUTO-' || REPLACE(a.account_id, 'ACC-', '') AS generated_case_id
    FROM new_transaction_batch b
    JOIN accounts a
      ON a.account_id = COALESCE(b.from_account_id, b.to_account_id)
  ) source
  ON target.account_id = source.account_id
  WHEN NOT MATCHED THEN INSERT (
    case_id, account_id, alert_type, alert_status, priority,
    created_at, assigned_to, alert_summary
  ) VALUES (
    source.generated_case_id, source.account_id, 'NEW_TRANSACTION_MONITORING',
    'OPEN', 'MEDIUM', CURRENT_TIMESTAMP(), 'UNASSIGNED',
    'Automatically created after a newly ingested transaction entered the AML monitoring stream.'
  );

  INSERT INTO transaction_processing_events (
    processing_event_id, transaction_id, case_id, account_id, processed_at,
    processor_name, processing_status, processing_detail
  )
  SELECT
    UUID_STRING(), b.transaction_id, c.case_id, a.account_id, CURRENT_TIMESTAMP(),
    'SP_PROCESS_NEW_TRANSACTIONS', 'PROCESSED',
    'Transaction captured from TRANSACTIONS_CHANGE_STREAM; case views and Cortex Agent tools now read the updated evidence.'
  FROM new_transaction_batch b
  JOIN accounts a
    ON a.account_id = COALESCE(b.from_account_id, b.to_account_id)
  LEFT JOIN case_alerts c
    ON c.account_id = a.account_id
  WHERE NOT EXISTS (
    SELECT 1 FROM transaction_processing_events existing
    WHERE existing.transaction_id = b.transaction_id
  );

  v_processed := SQLROWCOUNT;

  INSERT INTO audit_events (
    audit_event_id, case_id, event_ts, actor_type, actor_name, event_type,
    event_detail, object_type, object_id, event_metadata
  )
  SELECT
    UUID_STRING(), p.case_id, p.processed_at, 'SYSTEM', p.processor_name,
    'NEW_TRANSACTION_PROCESSED', p.processing_detail,
    'TRANSACTION', p.transaction_id,
    OBJECT_CONSTRUCT(
      'transaction_id', p.transaction_id,
      'account_id', p.account_id,
      'processing_status', p.processing_status,
      'pipeline', 'STREAM_TASK_PROCEDURE',
      'cortex_agent', 'SHADOWTRACE_AI.AML.SHADOWTRACE_AML_ORCHESTRATOR'
    )
  FROM transaction_processing_events p
  JOIN new_transaction_batch b ON b.transaction_id = p.transaction_id
  WHERE NOT EXISTS (
    SELECT 1 FROM audit_events existing
    WHERE existing.event_type = 'NEW_TRANSACTION_PROCESSED'
      AND existing.object_id = p.transaction_id
  );

  COMMIT;
  RETURN 'Processed ' || v_processed || ' new transaction(s).';
EXCEPTION
  WHEN OTHER THEN
    ROLLBACK;
    RAISE;
END;
$$;

CREATE OR REPLACE TASK process_new_transactions_task
  WAREHOUSE = COMPUTE_WH
  WHEN SYSTEM$STREAM_HAS_DATA('SHADOWTRACE_AI.AML.TRANSACTIONS_CHANGE_STREAM')
  AS CALL sp_process_new_transactions();

ALTER TASK process_new_transactions_task RESUME;

CREATE OR REPLACE VIEW vw_transaction_processing_status AS
SELECT
  p.processing_event_id,
  p.transaction_id,
  p.case_id,
  p.account_id,
  p.processed_at,
  p.processor_name,
  p.processing_status,
  p.processing_detail,
  r.risk_score,
  r.risk_band,
  r.recommended_route,
  'SHADOWTRACE_AI.AML.SHADOWTRACE_AML_ORCHESTRATOR' AS cortex_agent
FROM transaction_processing_events p
LEFT JOIN vw_case_risk_summary r ON r.case_id = p.case_id;

SHOW TASKS LIKE 'PROCESS_NEW_TRANSACTIONS_TASK' IN SCHEMA SHADOWTRACE_AI.AML;
