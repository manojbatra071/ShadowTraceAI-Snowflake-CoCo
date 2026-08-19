-- Execute the first-class Snowflake Cortex Agent and expose its tool trace.
USE ROLE ACCOUNTADMIN;
USE DATABASE SHADOWTRACE_AI;
USE SCHEMA AML;

SHOW AGENTS LIKE 'SHADOWTRACE_AML_ORCHESTRATOR' IN SCHEMA SHADOWTRACE_AI.AML;

SELECT TRY_PARSE_JSON(SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
  'SHADOWTRACE_AI.AML.SHADOWTRACE_AML_ORCHESTRATOR',
  $${
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "Why is CASE-C003 scored 92 and what route is recommended? Use the risk tool."
          }
        ]
      }
    ]
  }$$
)) AS agent_response;
