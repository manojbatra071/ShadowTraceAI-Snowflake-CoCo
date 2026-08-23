-- End-to-end acceptance test for the accountable human decision gate.
-- Uses an isolated temporary case and removes all persisted test records.
USE DATABASE SHADOWTRACE_AI;
USE SCHEMA AML;

SET hitl_case_id = 'CASE-HITL-SMOKE';
SET hitl_reviewer = 'SHADOWTRACE-HITL-SMOKE-TEST';

DELETE FROM audit_events WHERE case_id = $hitl_case_id;
DELETE FROM case_decisions WHERE case_id = $hitl_case_id;
DELETE FROM case_alerts WHERE case_id = $hitl_case_id;

INSERT INTO case_alerts (
  case_id, account_id, alert_type, alert_status, priority, assigned_to, alert_summary
) VALUES (
  $hitl_case_id, 'ACC-C-003', 'HITL_SMOKE_TEST', 'OPEN', 'LOW', NULL,
  'Temporary case used to verify reviewer decision controls.'
);

CREATE OR REPLACE TEMPORARY TABLE shadowtrace_hitl_status_snapshots (
  decision VARCHAR,
  expected_status VARCHAR,
  actual_status VARCHAR,
  actual_assignee VARCHAR
);

CALL sp_record_case_decision(
  $hitl_case_id, 'REQUEST_MORE_EVIDENCE', $hitl_reviewer,
  'Smoke test: request supporting evidence.'
);
INSERT INTO shadowtrace_hitl_status_snapshots
SELECT 'REQUEST_MORE_EVIDENCE', 'EVIDENCE_REQUESTED', alert_status, assigned_to
FROM case_alerts WHERE case_id = $hitl_case_id;

CALL sp_record_case_decision(
  $hitl_case_id, 'MONITOR_CASE', $hitl_reviewer,
  'Smoke test: retain the case for monitoring.'
);
INSERT INTO shadowtrace_hitl_status_snapshots
SELECT 'MONITOR_CASE', 'REVIEWED', alert_status, assigned_to
FROM case_alerts WHERE case_id = $hitl_case_id;

CALL sp_record_case_decision(
  $hitl_case_id, 'CLOSE_AS_FALSE_POSITIVE', $hitl_reviewer,
  'Smoke test: exercise the false-positive outcome.'
);
INSERT INTO shadowtrace_hitl_status_snapshots
SELECT 'CLOSE_AS_FALSE_POSITIVE', 'REVIEWED', alert_status, assigned_to
FROM case_alerts WHERE case_id = $hitl_case_id;

CALL sp_record_case_decision(
  $hitl_case_id, 'ESCALATE_TO_SAR', $hitl_reviewer,
  'Smoke test: escalate for formal SAR assessment; no SAR is filed automatically.'
);
INSERT INTO shadowtrace_hitl_status_snapshots
SELECT 'ESCALATE_TO_SAR', 'REVIEWED', alert_status, assigned_to
FROM case_alerts WHERE case_id = $hitl_case_id;

CREATE OR REPLACE TEMPORARY TABLE shadowtrace_hitl_invalid_result (
  invalid_decision_rejected BOOLEAN
);

EXECUTE IMMEDIATE $$
BEGIN
  CALL sp_record_case_decision(
    'CASE-HITL-SMOKE', 'AUTO_FILE_SAR', 'SHADOWTRACE-HITL-SMOKE-TEST',
    'This invalid autonomous action must be rejected.'
  );
  INSERT INTO shadowtrace_hitl_invalid_result VALUES (FALSE);
EXCEPTION
  WHEN OTHER THEN
    INSERT INTO shadowtrace_hitl_invalid_result VALUES (TRUE);
END;
$$;

CREATE OR REPLACE TEMPORARY TABLE shadowtrace_hitl_test_result AS
SELECT
  (SELECT COUNT(*) FROM case_decisions WHERE case_id = $hitl_case_id) AS decision_count,
  (SELECT COUNT(*) FROM audit_events
   WHERE case_id = $hitl_case_id AND event_type = 'REVIEWER_DECISION') AS audit_count,
  (SELECT COUNT(*)
   FROM case_decisions d
   JOIN audit_events a
     ON a.object_id = d.decision_id
    AND a.object_type = 'DECISION'
    AND a.actor_type = 'HUMAN'
    AND a.actor_name = d.reviewer_name
   WHERE d.case_id = $hitl_case_id) AS linked_human_audit_count,
  (SELECT COUNT_IF(
      actual_status = expected_status
      AND actual_assignee = $hitl_reviewer
   ) FROM shadowtrace_hitl_status_snapshots) AS correct_status_count,
  (SELECT BOOLOR_AGG(invalid_decision_rejected)
   FROM shadowtrace_hitl_invalid_result) AS invalid_decision_rejected;

SELECT
  'Human decision persistence, audit linkage, routing, and guardrail' AS test_name,
  IFF(
    decision_count = 4
    AND audit_count = 4
    AND linked_human_audit_count = 4
    AND correct_status_count = 4
    AND invalid_decision_rejected,
    'PASS', 'FAIL'
  ) AS status,
  decision_count,
  audit_count,
  linked_human_audit_count,
  correct_status_count,
  invalid_decision_rejected
FROM shadowtrace_hitl_test_result;

-- Cleanup occurs before the assertion so a failed test does not pollute the demo.
DELETE FROM audit_events WHERE case_id = $hitl_case_id;
DELETE FROM case_decisions WHERE case_id = $hitl_case_id;
DELETE FROM case_alerts WHERE case_id = $hitl_case_id;

EXECUTE IMMEDIATE $$
DECLARE
  v_failures INTEGER;
  v_test_failure EXCEPTION (-20006, 'ShadowTraceAI human-in-the-loop test failed.');
BEGIN
  SELECT COUNT_IF(NOT (
    decision_count = 4
    AND audit_count = 4
    AND linked_human_audit_count = 4
    AND correct_status_count = 4
    AND invalid_decision_rejected
  ))
  INTO :v_failures
  FROM shadowtrace_hitl_test_result;

  IF (v_failures > 0) THEN
    RAISE v_test_failure;
  END IF;
  RETURN 'PASS: human reviewer decisions are controlled, persisted, audited, and non-autonomous.';
END;
$$;
