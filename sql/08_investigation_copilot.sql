-- Governed Investigation Copilot persistence and audit logging.
USE DATABASE SHADOWTRACE_AI;
USE SCHEMA AML;

CREATE TABLE IF NOT EXISTS case_copilot_messages (
  message_id VARCHAR PRIMARY KEY,
  case_id VARCHAR NOT NULL,
  session_id VARCHAR NOT NULL,
  message_ts TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
  message_role VARCHAR NOT NULL,
  actor_name VARCHAR NOT NULL,
  message_text VARCHAR NOT NULL,
  source_objects ARRAY,
  model_provider VARCHAR NOT NULL DEFAULT 'GOVERNED_RULES',
  grounding_mode VARCHAR NOT NULL DEFAULT 'CURATED_SNOWFLAKE_OBJECTS'
);

CREATE OR REPLACE PROCEDURE sp_record_copilot_message(
  p_case_id VARCHAR,
  p_session_id VARCHAR,
  p_message_role VARCHAR,
  p_actor_name VARCHAR,
  p_message_text VARCHAR,
  p_source_objects VARCHAR
)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
  v_message_id VARCHAR DEFAULT UUID_STRING();
  v_audit_id VARCHAR DEFAULT UUID_STRING();
  v_case_count INTEGER DEFAULT 0;
  v_invalid_role EXCEPTION (-20003, 'Invalid copilot message role.');
  v_unknown_case EXCEPTION (-20004, 'Unknown case identifier.');
BEGIN
  IF (UPPER(p_message_role) NOT IN ('USER', 'ASSISTANT')) THEN
    RAISE v_invalid_role;
  END IF;

  SELECT COUNT(*) INTO :v_case_count
  FROM case_alerts
  WHERE case_id = :p_case_id;

  IF (v_case_count = 0) THEN
    RAISE v_unknown_case;
  END IF;

  BEGIN TRANSACTION;

  INSERT INTO case_copilot_messages (
    message_id, case_id, session_id, message_ts, message_role, actor_name,
    message_text, source_objects, model_provider, grounding_mode
  ) SELECT
    :v_message_id, :p_case_id, :p_session_id, CURRENT_TIMESTAMP(), UPPER(:p_message_role),
    :p_actor_name, :p_message_text,
    IFF(NULLIF(:p_source_objects, '') IS NULL, ARRAY_CONSTRUCT(), SPLIT(:p_source_objects, ',')),
    'GOVERNED_RULES', 'CURATED_SNOWFLAKE_OBJECTS'
  ;

  INSERT INTO audit_events (
    audit_event_id, case_id, event_ts, actor_type, actor_name, event_type,
    event_detail, object_type, object_id, event_metadata
  ) SELECT
    :v_audit_id, :p_case_id, CURRENT_TIMESTAMP(),
    IFF(UPPER(:p_message_role) = 'USER', 'HUMAN', 'SYSTEM'), :p_actor_name,
    'COPILOT_' || UPPER(:p_message_role) || '_MESSAGE',
    'Investigation Copilot ' || LOWER(:p_message_role) || ' message recorded.',
    'COPILOT_MESSAGE', :v_message_id,
    OBJECT_CONSTRUCT(
      'session_id', :p_session_id,
      'message_role', UPPER(:p_message_role),
      'message_text', :p_message_text,
      'source_objects', IFF(NULLIF(:p_source_objects, '') IS NULL, ARRAY_CONSTRUCT(), SPLIT(:p_source_objects, ',')),
      'grounding_mode', 'CURATED_SNOWFLAKE_OBJECTS'
    )
  ;

  COMMIT;
  RETURN v_message_id;
EXCEPTION
  WHEN OTHER THEN
    ROLLBACK;
    RAISE;
END;
$$;
