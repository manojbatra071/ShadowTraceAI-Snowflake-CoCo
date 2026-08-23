-- Live acceptance test for the production chatbot's first-class Cortex Agent path.
-- Verifies that a full-review question invokes all five governed specialist tools.
USE DATABASE SHADOWTRACE_AI;
USE SCHEMA AML;

CREATE OR REPLACE TEMPORARY TABLE shadowtrace_chatbot_live_response AS
SELECT TRY_PARSE_JSON(SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
  'SHADOWTRACE_AI.AML.SHADOWTRACE_AML_ORCHESTRATOR',
  $$
  {
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "Active case is CASE-C003. Give me a full review of risk, typologies, network, evidence, and recommended action. Call all five tools before answering."
          }
        ]
      }
    ]
  }
  $$
)) AS payload;

CREATE OR REPLACE TEMPORARY TABLE shadowtrace_chatbot_test_result AS
SELECT
  payload:status::VARCHAR AS response_status,
  COUNT_IF(f.value:type::VARCHAR = 'text' AND NULLIF(f.value:text::VARCHAR, '') IS NOT NULL) AS text_part_count,
  COUNT(DISTINCT f.value:tool_use:name::VARCHAR) AS distinct_tool_count,
  COUNT_IF(
    f.value:type::VARCHAR = 'text'
    AND (
      LOWER(f.value:text::VARCHAR) LIKE '%cannot complete%'
      OR LOWER(f.value:text::VARCHAR) LIKE '%failed%'
      OR LOWER(f.value:text::VARCHAR) LIKE '%sql compilation error%'
      OR LOWER(f.value:text::VARCHAR) LIKE '%no valid data%'
      OR LOWER(f.value:text::VARCHAR) LIKE '%time limit%'
      OR LOWER(f.value:text::VARCHAR) LIKE '%analysis may be incomplete%'
    )
  ) AS failure_text_count,
  COUNT_IF(
    f.value:type::VARCHAR = 'text'
    AND f.value:text::VARCHAR LIKE '%92%'
  ) AS score_confirmation_count,
  LISTAGG(DISTINCT f.value:tool_use:name::VARCHAR, ', ')
    WITHIN GROUP (ORDER BY f.value:tool_use:name::VARCHAR) AS tools_used
FROM shadowtrace_chatbot_live_response,
LATERAL FLATTEN(INPUT => payload:content) f
GROUP BY payload:status::VARCHAR;

SELECT
  'Live chatbot invokes five governed tools and returns an answer' AS test_name,
  IFF(
    response_status = 'completed'
    AND text_part_count >= 1
    AND distinct_tool_count = 5
    AND failure_text_count = 0
    AND score_confirmation_count >= 1,
    'PASS', 'FAIL'
  ) AS status,
  response_status,
  text_part_count,
  distinct_tool_count,
  failure_text_count,
  score_confirmation_count,
  tools_used
FROM shadowtrace_chatbot_test_result;

EXECUTE IMMEDIATE $$
DECLARE
  v_failures INTEGER;
  v_test_failure EXCEPTION (-20009, 'ShadowTraceAI live chatbot test failed.');
BEGIN
  SELECT COUNT_IF(NOT (
    response_status = 'completed'
    AND text_part_count >= 1
    AND distinct_tool_count = 5
    AND failure_text_count = 0
    AND score_confirmation_count >= 1
  ))
  INTO :v_failures
  FROM shadowtrace_chatbot_test_result;

  IF (v_failures > 0) THEN
    RAISE v_test_failure;
  END IF;
  RETURN 'PASS: live chatbot used all five Cortex Agent tools and returned a grounded answer.';
END;
$$;
