-- Auditable execution records for the Case Orchestrator and specialist agents.
USE DATABASE SHADOWTRACE_AI;
USE SCHEMA AML;

CREATE TABLE IF NOT EXISTS case_agent_executions (
  agent_execution_id VARCHAR PRIMARY KEY,
  request_id VARCHAR NOT NULL,
  case_id VARCHAR NOT NULL,
  session_id VARCHAR NOT NULL,
  agent_name VARCHAR NOT NULL,
  executed_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
  execution_status VARCHAR NOT NULL DEFAULT 'COMPLETED',
  routing_reason VARCHAR,
  agent_response VARCHAR,
  source_objects ARRAY
);

CREATE OR REPLACE PROCEDURE sp_record_agent_execution(
  p_request_id VARCHAR,
  p_case_id VARCHAR,
  p_session_id VARCHAR,
  p_agent_name VARCHAR,
  p_routing_reason VARCHAR,
  p_agent_response VARCHAR,
  p_source_objects VARCHAR
)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
  v_execution_id VARCHAR DEFAULT UUID_STRING();
  v_audit_id VARCHAR DEFAULT UUID_STRING();
  v_case_count INTEGER DEFAULT 0;
  v_invalid_agent EXCEPTION (-20006, 'Invalid ShadowTraceAI agent name.');
  v_unknown_case EXCEPTION (-20007, 'Unknown case identifier.');
BEGIN
  IF (UPPER(p_agent_name) NOT IN (
    'CASE ORCHESTRATOR AGENT',
    'TYPOLOGY DETECTION AGENT',
    'NETWORK INTELLIGENCE AGENT',
    'EVIDENCE REVIEW AGENT',
    'RISK EXPLANATION AGENT',
    'CASE BRIEF AGENT'
  )) THEN
    RAISE v_invalid_agent;
  END IF;

  SELECT COUNT(*) INTO :v_case_count
  FROM case_alerts
  WHERE case_id = :p_case_id;

  IF (v_case_count = 0) THEN
    RAISE v_unknown_case;
  END IF;

  BEGIN TRANSACTION;

  INSERT INTO case_agent_executions (
    agent_execution_id, request_id, case_id, session_id, agent_name, executed_at,
    execution_status, routing_reason, agent_response, source_objects
  ) SELECT
    :v_execution_id, :p_request_id, :p_case_id, :p_session_id, :p_agent_name,
    CURRENT_TIMESTAMP(), 'COMPLETED', :p_routing_reason, :p_agent_response,
    IFF(NULLIF(:p_source_objects, '') IS NULL, ARRAY_CONSTRUCT(), SPLIT(:p_source_objects, ','))
  ;

  INSERT INTO audit_events (
    audit_event_id, case_id, event_ts, actor_type, actor_name, event_type,
    event_detail, object_type, object_id, event_metadata
  ) SELECT
    :v_audit_id, :p_case_id, CURRENT_TIMESTAMP(), 'AGENT', :p_agent_name,
    'AGENT_EXECUTION_COMPLETED', :p_agent_name || ' completed a governed case analysis.',
    'AGENT_EXECUTION', :v_execution_id,
    OBJECT_CONSTRUCT(
      'request_id', :p_request_id,
      'session_id', :p_session_id,
      'agent_name', :p_agent_name,
      'routing_reason', :p_routing_reason,
      'source_objects', IFF(NULLIF(:p_source_objects, '') IS NULL, ARRAY_CONSTRUCT(), SPLIT(:p_source_objects, ',')),
      'execution_status', 'COMPLETED'
    )
  ;

  COMMIT;
  RETURN v_execution_id;
EXCEPTION
  WHEN OTHER THEN
    ROLLBACK;
    RAISE;
END;
$$;
