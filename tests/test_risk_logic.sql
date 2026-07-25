USE DATABASE SHADOWTRACE_AI;
USE SCHEMA AML;

CREATE OR REPLACE TEMPORARY TABLE shadowtrace_test_results (
  test_name VARCHAR,
  expected VARCHAR,
  actual VARCHAR,
  status VARCHAR
);

INSERT INTO shadowtrace_test_results
SELECT
  'CASE-C003 score is 92',
  '92',
  TO_VARCHAR(MAX(risk_score)),
  IFF(MAX(risk_score) = 92, 'PASS', 'FAIL')
FROM vw_case_risk_summary
WHERE case_id = 'CASE-C003';

INSERT INTO shadowtrace_test_results
SELECT
  'CASE-C003 band is CRITICAL',
  'CRITICAL',
  MAX(risk_band),
  IFF(MAX(risk_band) = 'CRITICAL', 'PASS', 'FAIL')
FROM vw_case_risk_summary
WHERE case_id = 'CASE-C003';

INSERT INTO shadowtrace_test_results
SELECT
  'CASE-C003 evidence is STRONG',
  'STRONG',
  MAX(evidence_strength),
  IFF(MAX(evidence_strength) = 'STRONG', 'PASS', 'FAIL')
FROM vw_case_risk_summary
WHERE case_id = 'CASE-C003';

INSERT INTO shadowtrace_test_results
SELECT
  'All five modern-slavery typologies detected',
  '5',
  TO_VARCHAR(COUNT_IF(signal_detected)),
  IFF(COUNT_IF(signal_detected) = 5, 'PASS', 'FAIL')
FROM vw_all_typology_signals
WHERE case_id = 'CASE-C003';

INSERT INTO shadowtrace_test_results
SELECT
  'CASE-C003 route requires reviewer SAR escalation decision',
  'ESCALATE_TO_SAR',
  MAX(recommended_route),
  IFF(MAX(recommended_route) = 'ESCALATE_TO_SAR', 'PASS', 'FAIL')
FROM vw_case_risk_summary
WHERE case_id = 'CASE-C003';

INSERT INTO shadowtrace_test_results
SELECT
  'Benign comparison remains LOW',
  'LOW',
  MAX(risk_band),
  IFF(MAX(risk_band) = 'LOW', 'PASS', 'FAIL')
FROM vw_case_risk_summary
WHERE case_id = 'CASE-C010';

SELECT * FROM shadowtrace_test_results ORDER BY test_name;

EXECUTE IMMEDIATE $$
DECLARE
  v_failed_tests INTEGER;
  v_test_failure EXCEPTION (-20002, 'ShadowTraceAI risk logic tests failed.');
BEGIN
  SELECT COUNT_IF(status = 'FAIL') INTO :v_failed_tests
  FROM shadowtrace_test_results;

  IF (v_failed_tests > 0) THEN
    RAISE v_test_failure;
  END IF;
  RETURN 'PASS: all ShadowTraceAI SQL tests succeeded.';
END;
$$;

