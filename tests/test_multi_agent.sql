-- Smoke-test all six routed agents and their linked Snowflake audit records.
USE DATABASE SHADOWTRACE_AI;
USE SCHEMA AML;

DELETE FROM audit_events
WHERE event_metadata:session_id::VARCHAR = 'SHADOWTRACE-MULTI-AGENT-SMOKE-TEST';
DELETE FROM case_agent_executions
WHERE session_id = 'SHADOWTRACE-MULTI-AGENT-SMOKE-TEST';

CALL sp_record_agent_execution('REQ-SMOKE', 'CASE-C003', 'SHADOWTRACE-MULTI-AGENT-SMOKE-TEST',
  'Case Orchestrator Agent', 'Smoke-test route', 'Orchestration completed.', 'vw_case_risk_summary');
CALL sp_record_agent_execution('REQ-SMOKE', 'CASE-C003', 'SHADOWTRACE-MULTI-AGENT-SMOKE-TEST',
  'Typology Detection Agent', 'Smoke-test route', 'Typology analysis completed.', 'vw_all_typology_signals');
CALL sp_record_agent_execution('REQ-SMOKE', 'CASE-C003', 'SHADOWTRACE-MULTI-AGENT-SMOKE-TEST',
  'Network Intelligence Agent', 'Smoke-test route', 'Network analysis completed.', 'vw_case_network');
CALL sp_record_agent_execution('REQ-SMOKE', 'CASE-C003', 'SHADOWTRACE-MULTI-AGENT-SMOKE-TEST',
  'Evidence Review Agent', 'Smoke-test route', 'Evidence review completed.', 'document_evidence,external_watchlist');
CALL sp_record_agent_execution('REQ-SMOKE', 'CASE-C003', 'SHADOWTRACE-MULTI-AGENT-SMOKE-TEST',
  'Risk Explanation Agent', 'Smoke-test route', 'Risk explanation completed.', 'vw_case_risk_summary');
CALL sp_record_agent_execution('REQ-SMOKE', 'CASE-C003', 'SHADOWTRACE-MULTI-AGENT-SMOKE-TEST',
  'Case Brief Agent', 'Smoke-test route', 'Case brief completed.', 'vw_case_intelligence_brief');

CREATE OR REPLACE TEMPORARY TABLE shadowtrace_multi_agent_test_result AS
SELECT
  (SELECT COUNT(*) FROM case_agent_executions
   WHERE session_id = 'SHADOWTRACE-MULTI-AGENT-SMOKE-TEST') AS execution_count,
  (SELECT COUNT(DISTINCT agent_name) FROM case_agent_executions
   WHERE session_id = 'SHADOWTRACE-MULTI-AGENT-SMOKE-TEST') AS distinct_agent_count,
  (SELECT COUNT(*) FROM audit_events
   WHERE event_metadata:session_id::VARCHAR = 'SHADOWTRACE-MULTI-AGENT-SMOKE-TEST') AS audit_count;

SELECT
  'Orchestrator and five specialist agents persist auditable executions' AS test_name,
  IFF(execution_count = 6 AND distinct_agent_count = 6 AND audit_count = 6, 'PASS', 'FAIL') AS status,
  execution_count,
  distinct_agent_count,
  audit_count
FROM shadowtrace_multi_agent_test_result;

DELETE FROM audit_events
WHERE event_metadata:session_id::VARCHAR = 'SHADOWTRACE-MULTI-AGENT-SMOKE-TEST';
DELETE FROM case_agent_executions
WHERE session_id = 'SHADOWTRACE-MULTI-AGENT-SMOKE-TEST';

EXECUTE IMMEDIATE $$
DECLARE
  v_failures INTEGER;
  v_test_failure EXCEPTION (-20008, 'ShadowTraceAI multi-agent smoke test failed.');
BEGIN
  SELECT COUNT_IF(NOT (execution_count = 6 AND distinct_agent_count = 6 AND audit_count = 6))
  INTO :v_failures
  FROM shadowtrace_multi_agent_test_result;

  IF (v_failures > 0) THEN
    RAISE v_test_failure;
  END IF;
  RETURN 'PASS: orchestrator and five specialist agents are auditable.';
END;
$$;
