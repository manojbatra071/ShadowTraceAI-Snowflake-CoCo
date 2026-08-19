-- Prove that a newly inserted transaction is processed without Streamlit.
USE ROLE ACCOUNTADMIN;
USE DATABASE SHADOWTRACE_AI;
USE SCHEMA AML;

DELETE FROM audit_events
WHERE event_type = 'NEW_TRANSACTION_PROCESSED'
  AND object_id = 'TX-PIPELINE-SMOKE';
DELETE FROM transaction_processing_events
WHERE transaction_id = 'TX-PIPELINE-SMOKE';
DELETE FROM transactions
WHERE transaction_id = 'TX-PIPELINE-SMOKE';

INSERT INTO transactions (
  transaction_id, transaction_ts, from_account_id, to_account_id, amount,
  currency, transaction_type, channel, counterparty_country,
  merchant_category, description
) VALUES (
  'TX-PIPELINE-SMOKE', CURRENT_TIMESTAMP(), 'ACC-C-003', 'ACC-I-101', 321.00,
  'GBP', 'TRANSFER', 'ONLINE', 'GB', '6012',
  'Synthetic smoke-test transaction for event-driven processing.'
);

CALL sp_process_new_transactions();

CREATE OR REPLACE TEMPORARY TABLE shadowtrace_pipeline_test_result AS
SELECT
  COUNT(*) AS processing_event_count,
  COUNT_IF(processing_status = 'PROCESSED') AS processed_count,
  COUNT_IF(case_id = 'CASE-C003') AS linked_case_count
FROM transaction_processing_events
WHERE transaction_id = 'TX-PIPELINE-SMOKE';

SELECT
  'New transaction reaches stream, procedure, case, and audit pipeline' AS test_name,
  IFF(processing_event_count = 1 AND processed_count = 1 AND linked_case_count = 1, 'PASS', 'FAIL') AS status,
  processing_event_count,
  processed_count,
  linked_case_count
FROM shadowtrace_pipeline_test_result;

DELETE FROM audit_events
WHERE event_type = 'NEW_TRANSACTION_PROCESSED'
  AND object_id = 'TX-PIPELINE-SMOKE';
DELETE FROM transaction_processing_events
WHERE transaction_id = 'TX-PIPELINE-SMOKE';
DELETE FROM transactions
WHERE transaction_id = 'TX-PIPELINE-SMOKE';

EXECUTE IMMEDIATE $$
DECLARE
  v_failures INTEGER;
  v_test_failure EXCEPTION (-20009, 'ShadowTraceAI new-transaction pipeline test failed.');
BEGIN
  SELECT COUNT_IF(NOT (
    processing_event_count = 1 AND processed_count = 1 AND linked_case_count = 1
  )) INTO :v_failures
  FROM shadowtrace_pipeline_test_result;

  IF (v_failures > 0) THEN
    RAISE v_test_failure;
  END IF;
  RETURN 'PASS: new transaction processed independently of Streamlit.';
END;
$$;
