USE DATABASE SHADOWTRACE_AI;
USE SCHEMA AML;

CREATE OR REPLACE VIEW vw_case_brief_prompt AS
WITH signal_text AS (
  SELECT
    case_id,
    LISTAGG(signal_type || ': ' || explanation, '\n') WITHIN GROUP (ORDER BY risk_points DESC) AS signals
  FROM vw_all_typology_signals
  WHERE signal_detected
  GROUP BY case_id
), evidence_text AS (
  SELECT
    case_id,
    LISTAGG(document_type || ': ' || evidence_summary, '\n') WITHIN GROUP (ORDER BY document_id) AS documents
  FROM document_evidence
  GROUP BY case_id
), audit_text AS (
  SELECT
    case_id,
    LISTAGG(TO_VARCHAR(event_ts, 'YYYY-MM-DD HH24:MI') || ' — ' || event_type || ': ' || event_detail, '\n')
      WITHIN GROUP (ORDER BY event_ts) AS timeline
  FROM audit_events
  GROUP BY case_id
)
SELECT
  ca.case_id,
  'You are an AML investigation copilot. Summarize only the supplied evidence. '
  || 'Do not claim guilt or recommend autonomous filing. Return a concise investigation brief with: '
  || 'executive summary, suspicion hypothesis, evidence summary, missing evidence, and recommended action.'
  || '\n\nCASE: ' || ca.case_id
  || '\nACCOUNT: ' || a.display_name || ' (' || ca.account_id || ')'
  || '\nRISK: ' || r.risk_score || '/100 ' || r.risk_band
  || '\nEVIDENCE STRENGTH: ' || r.evidence_strength
  || '\nSIGNALS:\n' || COALESCE(s.signals, 'No detected typology signals')
  || '\nDOCUMENTS:\n' || COALESCE(e.documents, 'No document evidence')
  || '\nAUDIT TIMELINE:\n' || COALESCE(au.timeline, 'No audit events')
  AS prompt_text
FROM case_alerts ca
JOIN accounts a ON a.account_id = ca.account_id
JOIN vw_case_risk_summary r ON r.case_id = ca.case_id
LEFT JOIN signal_text s ON s.case_id = ca.case_id
LEFT JOIN evidence_text e ON e.case_id = ca.case_id
LEFT JOIN audit_text au ON au.case_id = ca.case_id;

CREATE OR REPLACE VIEW vw_case_intelligence_brief AS
WITH signal_text AS (
  SELECT
    case_id,
    LISTAGG(signal_type || ' (' || risk_points || ' pts): ' || explanation, '\n')
      WITHIN GROUP (ORDER BY risk_points DESC) AS evidence_summary
  FROM vw_all_typology_signals
  WHERE signal_detected
  GROUP BY case_id
), missing AS (
  SELECT
    ca.case_id,
    CASE
      WHEN COUNT(d.document_id) = 0 THEN 'Obtain payroll, identity, employment, and accommodation records.'
      WHEN MIN(d.extraction_confidence) < 0.75 THEN 'Manually validate the low-confidence identity document and confirm worker contact ownership.'
      ELSE 'Confirm beneficial ownership and interview affected customers using safeguarding procedures.'
    END AS missing_evidence
  FROM case_alerts ca
  LEFT JOIN document_evidence d ON d.case_id = ca.case_id
  GROUP BY ca.case_id
), audit_text AS (
  SELECT
    case_id,
    LISTAGG(TO_VARCHAR(event_ts, 'YYYY-MM-DD HH24:MI') || ' — ' || actor_name || ': ' || event_detail, '\n')
      WITHIN GROUP (ORDER BY event_ts) AS audit_timeline
  FROM audit_events
  GROUP BY case_id
)
SELECT
  ca.case_id,
  ca.account_id,
  a.display_name AS account_name,
  r.risk_score,
  r.risk_band,
  r.evidence_strength,
  ca.case_id || ' concerns ' || a.display_name || ', a ' || LOWER(a.account_type)
    || ' account with a Snowflake SQL risk score of ' || r.risk_score || '/100 (' || r.risk_band || '). '
    || 'The alert is supported by ' || r.detected_typology_count || ' detected typologies, '
    || r.document_count || ' linked documents, and ' || r.high_intelligence_hits || ' high-risk intelligence matches.'
    AS executive_summary,
  CASE
    WHEN r.risk_score >= 90 THEN
      'The employer may be facilitating wage harvesting: worker payroll is rapidly consolidated through accounts accessed from a common device and ultimately cashed out.'
    ELSE
      'Current evidence does not yet establish a coordinated exploitation network; continue proportionate review.'
  END AS suspicion_hypothesis,
  COALESCE(s.evidence_summary, 'No typology signals detected.') AS evidence_summary,
  m.missing_evidence,
  CASE r.recommended_route
    WHEN 'ESCALATE_TO_SAR' THEN 'Reviewer should consider Escalate to SAR. Filing remains a human decision.'
    WHEN 'REQUEST_MORE_EVIDENCE' THEN 'Request and validate additional evidence before escalation.'
    WHEN 'MONITOR_CASE' THEN 'Keep the case under enhanced monitoring.'
    ELSE 'Close as false positive if the reviewer confirms the benign explanation.'
  END AS recommended_action,
  COALESCE(au.audit_timeline, 'No audit events recorded.') AS audit_timeline,
  p.prompt_text
FROM case_alerts ca
JOIN accounts a ON a.account_id = ca.account_id
JOIN vw_case_risk_summary r ON r.case_id = ca.case_id
LEFT JOIN signal_text s ON s.case_id = ca.case_id
JOIN missing m ON m.case_id = ca.case_id
LEFT JOIN audit_text au ON au.case_id = ca.case_id
JOIN vw_case_brief_prompt p ON p.case_id = ca.case_id;

MERGE INTO case_intelligence_briefs target
USING (
  SELECT
    'BRIEF-' || case_id || '-SQL-V1' AS brief_id,
    case_id,
    '2026-07-01 08:34:00 +00:00'::TIMESTAMP_TZ AS generated_at,
    'DETERMINISTIC_SQL' AS generation_method,
    executive_summary,
    suspicion_hypothesis,
    evidence_summary,
    missing_evidence,
    recommended_action,
    audit_timeline,
    prompt_text
  FROM vw_case_intelligence_brief
) source
ON target.brief_id = source.brief_id
WHEN MATCHED THEN UPDATE SET
  target.executive_summary = source.executive_summary,
  target.suspicion_hypothesis = source.suspicion_hypothesis,
  target.evidence_summary = source.evidence_summary,
  target.missing_evidence = source.missing_evidence,
  target.recommended_action = source.recommended_action,
  target.audit_timeline = source.audit_timeline,
  target.prompt_text = source.prompt_text
WHEN NOT MATCHED THEN INSERT (
  brief_id, case_id, generated_at, generation_method, executive_summary,
  suspicion_hypothesis, evidence_summary, missing_evidence, recommended_action,
  audit_timeline, prompt_text
) VALUES (
  source.brief_id, source.case_id, source.generated_at, source.generation_method,
  source.executive_summary, source.suspicion_hypothesis, source.evidence_summary,
  source.missing_evidence, source.recommended_action, source.audit_timeline, source.prompt_text
);

MERGE INTO audit_events target
USING (
  SELECT
    'AUD-' || case_id || '-BRIEF-SQL-V1' AS audit_event_id,
    case_id,
    '2026-07-01 08:34:00 +00:00'::TIMESTAMP_TZ AS event_ts,
    'SYSTEM' AS actor_type,
    'Case Intelligence SQL' AS actor_name,
    'CASE_BRIEF_GENERATED' AS event_type,
    'Generated evidence-grounded investigation brief and reviewer route.' AS event_detail,
    'CASE_BRIEF' AS object_type,
    'BRIEF-' || case_id || '-SQL-V1' AS object_id,
    OBJECT_CONSTRUCT('method', 'DETERMINISTIC_SQL') AS event_metadata
  FROM vw_case_intelligence_brief
) source
ON target.audit_event_id = source.audit_event_id
WHEN MATCHED THEN UPDATE SET
  target.event_detail = source.event_detail,
  target.event_metadata = source.event_metadata
WHEN NOT MATCHED THEN INSERT (
  audit_event_id, case_id, event_ts, actor_type, actor_name, event_type,
  event_detail, object_type, object_id, event_metadata
) VALUES (
  source.audit_event_id, source.case_id, source.event_ts, source.actor_type,
  source.actor_name, source.event_type, source.event_detail, source.object_type,
  source.object_id, source.event_metadata
);
