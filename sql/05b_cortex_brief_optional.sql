-- Optional: requires a region/account with Snowflake Cortex access.
-- The deterministic vw_case_intelligence_brief remains the auditable fallback.
USE DATABASE SHADOWTRACE_AI;
USE SCHEMA AML;

CREATE OR REPLACE VIEW vw_case_intelligence_brief_cortex AS
SELECT
  case_id,
  AI_COMPLETE(
    'llama3.1-70b',
    prompt_text
  ) AS cortex_brief,
  prompt_text
FROM vw_case_brief_prompt;
