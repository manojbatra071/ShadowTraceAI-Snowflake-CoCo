USE DATABASE SHADOWTRACE_AI;
USE SCHEMA AML;

CREATE OR REPLACE PROCEDURE sp_record_case_decision(
  p_case_id VARCHAR,
  p_decision VARCHAR,
  p_reviewer_name VARCHAR,
  p_rationale VARCHAR
)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
  v_decision_id VARCHAR DEFAULT UUID_STRING();
  v_audit_id VARCHAR DEFAULT UUID_STRING();
  v_invalid_decision EXCEPTION (-20001, 'Invalid reviewer decision.');
BEGIN
  IF (p_decision NOT IN (
    'ESCALATE_TO_SAR',
    'REQUEST_MORE_EVIDENCE',
    'MONITOR_CASE',
    'CLOSE_AS_FALSE_POSITIVE'
  )) THEN
    RAISE v_invalid_decision;
  END IF;

  BEGIN TRANSACTION;

  INSERT INTO case_decisions (
    decision_id, case_id, decision, reviewer_name, rationale, decided_at
  ) VALUES (
    :v_decision_id, :p_case_id, :p_decision, :p_reviewer_name, :p_rationale, CURRENT_TIMESTAMP()
  );

  INSERT INTO audit_events (
    audit_event_id, case_id, event_ts, actor_type, actor_name, event_type,
    event_detail, object_type, object_id, event_metadata
  ) VALUES (
    :v_audit_id, :p_case_id, CURRENT_TIMESTAMP(), 'HUMAN', :p_reviewer_name,
    'REVIEWER_DECISION', 'Reviewer selected ' || :p_decision || '. Rationale: ' || :p_rationale,
    'DECISION', :v_decision_id, OBJECT_CONSTRUCT('decision', :p_decision)
  );

  UPDATE case_alerts
  SET
    alert_status = IFF(:p_decision = 'REQUEST_MORE_EVIDENCE', 'EVIDENCE_REQUESTED', 'REVIEWED'),
    assigned_to = :p_reviewer_name
  WHERE case_id = :p_case_id;

  COMMIT;
  RETURN v_decision_id;
EXCEPTION
  WHEN OTHER THEN
    ROLLBACK;
    RAISE;
END;
$$;

