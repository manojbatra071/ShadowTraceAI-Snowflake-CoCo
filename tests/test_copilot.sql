-- Smoke-test the governed copilot persistence and linked audit events.
USE DATABASE SHADOWTRACE_AI;
USE SCHEMA AML;

DELETE FROM audit_events
WHERE event_metadata:session_id::VARCHAR = 'SHADOWTRACE-COPILOT-SMOKE-TEST';
DELETE FROM case_copilot_messages
WHERE session_id = 'SHADOWTRACE-COPILOT-SMOKE-TEST';

CALL sp_record_copilot_message(
  'CASE-C003',
  'SHADOWTRACE-COPILOT-SMOKE-TEST',
  'USER',
  'Automated smoke test',
  'Why is this case high risk?',
  ''
);

CALL sp_record_copilot_message(
  'CASE-C003',
  'SHADOWTRACE-COPILOT-SMOKE-TEST',
  'ASSISTANT',
  'ShadowTraceAI Investigation Copilot',
  'Grounded smoke-test response.',
  'vw_case_risk_summary,vw_all_typology_signals'
);

CREATE OR REPLACE TEMPORARY TABLE shadowtrace_copilot_test_result AS
SELECT
  (SELECT COUNT(*) FROM case_copilot_messages
   WHERE session_id = 'SHADOWTRACE-COPILOT-SMOKE-TEST') AS message_count,
  (SELECT COUNT(*) FROM audit_events
   WHERE event_metadata:session_id::VARCHAR = 'SHADOWTRACE-COPILOT-SMOKE-TEST') AS audit_count,
  (SELECT MAX(ARRAY_SIZE(source_objects)) FROM case_copilot_messages
   WHERE session_id = 'SHADOWTRACE-COPILOT-SMOKE-TEST') AS maximum_source_count;

SELECT
  'Copilot messages and linked audit events persist' AS test_name,
  IFF(message_count = 2 AND audit_count = 2 AND maximum_source_count = 2, 'PASS', 'FAIL') AS status,
  message_count,
  audit_count,
  maximum_source_count
FROM shadowtrace_copilot_test_result;

DELETE FROM audit_events
WHERE event_metadata:session_id::VARCHAR = 'SHADOWTRACE-COPILOT-SMOKE-TEST';
DELETE FROM case_copilot_messages
WHERE session_id = 'SHADOWTRACE-COPILOT-SMOKE-TEST';

EXECUTE IMMEDIATE $$
DECLARE
  v_failures INTEGER;
  v_test_failure EXCEPTION (-20005, 'ShadowTraceAI copilot smoke test failed.');
BEGIN
  SELECT COUNT_IF(NOT (message_count = 2 AND audit_count = 2 AND maximum_source_count = 2))
  INTO :v_failures
  FROM shadowtrace_copilot_test_result;

  IF (v_failures > 0) THEN
    RAISE v_test_failure;
  END IF;
  RETURN 'PASS: copilot persistence and audit linkage succeeded.';
END;
$$;
