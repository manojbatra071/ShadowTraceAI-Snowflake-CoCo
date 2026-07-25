USE DATABASE SHADOWTRACE_AI;
USE SCHEMA AML;

CREATE OR REPLACE VIEW vw_all_typology_signals AS
SELECT case_id, account_id, signal_type, signal_detected, risk_points, explanation
FROM vw_wage_harvesting_signals
UNION ALL
SELECT case_id, account_id, signal_type, signal_detected, risk_points, explanation
FROM vw_account_control_signals
UNION ALL
SELECT case_id, account_id, signal_type, signal_detected, risk_points, explanation
FROM vw_spending_anomaly_signals
UNION ALL
SELECT case_id, account_id, signal_type, signal_detected, risk_points, explanation
FROM vw_geographic_risk_signals
UNION ALL
SELECT case_id, account_id, signal_type, signal_detected, risk_points, explanation
FROM vw_sector_risk_signals;

CREATE OR REPLACE VIEW vw_case_risk_summary AS
WITH typology AS (
  SELECT
    ca.case_id,
    ca.account_id,
    COALESCE(SUM(IFF(s.signal_detected, s.risk_points, 0)), 0) AS typology_points,
    COUNT_IF(s.signal_detected) AS detected_typology_count,
    MAX(IFF(s.signal_type = 'WAGE_HARVESTING' AND s.signal_detected, s.risk_points, 0)) AS wage_points,
    MAX(IFF(s.signal_type = 'ACCOUNT_CONTROL' AND s.signal_detected, s.risk_points, 0)) AS control_points,
    MAX(IFF(s.signal_type = 'SPENDING_ANOMALY' AND s.signal_detected, s.risk_points, 0)) AS spending_points,
    MAX(IFF(s.signal_type = 'GEOGRAPHIC_RISK' AND s.signal_detected, s.risk_points, 0)) AS geography_points,
    MAX(IFF(s.signal_type = 'SECTOR_RISK' AND s.signal_detected, s.risk_points, 0)) AS sector_points
  FROM case_alerts ca
  LEFT JOIN vw_all_typology_signals s ON s.case_id = ca.case_id
  GROUP BY ca.case_id, ca.account_id
), case_entities AS (
  SELECT case_id, account_id AS entity_account_id FROM case_alerts
  UNION
  SELECT case_id, source_account_id FROM vw_case_network
  UNION
  SELECT case_id, target_account_id FROM vw_case_network
), intelligence AS (
  SELECT
    ca.case_id,
    COUNT_IF(w.risk_level = 'HIGH') AS high_intelligence_hits,
    IFF(COUNT_IF(w.risk_level = 'HIGH') > 0, 4, 0) AS intelligence_points
  FROM case_alerts ca
  LEFT JOIN case_entities e ON e.case_id = ca.case_id
  LEFT JOIN external_watchlist w ON w.matched_account_id = e.entity_account_id
  GROUP BY ca.case_id
), documents AS (
  SELECT
    ca.case_id,
    COUNT(DISTINCT d.document_id) AS document_count,
    COUNT_IF(ARRAY_SIZE(d.risk_indicators) > 0) AS risky_document_count,
    MIN(d.extraction_confidence) AS minimum_extraction_confidence,
    IFF(COUNT_IF(ARRAY_SIZE(d.risk_indicators) > 0) >= 3, 4, 0) AS document_points
  FROM case_alerts ca
  LEFT JOIN document_evidence d ON d.case_id = ca.case_id
  GROUP BY ca.case_id
), scored AS (
  SELECT
    t.*,
    i.high_intelligence_hits,
    i.intelligence_points,
    d.document_count,
    d.risky_document_count,
    d.minimum_extraction_confidence,
    d.document_points,
    LEAST(100, t.typology_points + i.intelligence_points + d.document_points) AS risk_score
  FROM typology t
  JOIN intelligence i ON i.case_id = t.case_id
  JOIN documents d ON d.case_id = t.case_id
)
SELECT
  case_id,
  account_id,
  risk_score,
  CASE
    WHEN risk_score >= 90 THEN 'CRITICAL'
    WHEN risk_score >= 70 THEN 'HIGH'
    WHEN risk_score >= 40 THEN 'MEDIUM'
    ELSE 'LOW'
  END AS risk_band,
  CASE
    WHEN detected_typology_count >= 4 AND high_intelligence_hits > 0 AND risky_document_count >= 3 THEN 'STRONG'
    WHEN detected_typology_count >= 2 AND (high_intelligence_hits > 0 OR risky_document_count > 0) THEN 'MODERATE'
    ELSE 'LIMITED'
  END AS evidence_strength,
  ARRAY_CONSTRUCT_COMPACT(
    IFF(wage_points > 0, 'Wage harvesting: rapid onward transfer by multiple workers', NULL),
    IFF(control_points > 0, 'Account control: shared device and IP across the network', NULL),
    IFF(spending_points > 0, 'Spending anomaly: wages depleted with little everyday spending', NULL),
    IFF(geography_points > 0, 'Geographic risk: recruitment corridor and foreign cash-out', NULL),
    IFF(sector_points > 0, 'Sector risk: construction and incomplete ownership data', NULL),
    IFF(intelligence_points > 0, 'External intelligence: high-risk adverse media/watchlist match', NULL),
    IFF(document_points > 0, 'Document evidence: payroll, identity, contract, and accommodation inconsistencies', NULL)
  ) AS top_risk_factors,
  CASE
    WHEN risk_score >= 90 THEN 'ESCALATE_TO_SAR'
    WHEN risk_score >= 70 THEN 'REQUEST_MORE_EVIDENCE'
    WHEN risk_score >= 40 THEN 'MONITOR_CASE'
    ELSE 'CLOSE_AS_FALSE_POSITIVE'
  END AS recommended_route,
  OBJECT_CONSTRUCT(
    'wage_harvesting', wage_points,
    'account_control', control_points,
    'spending_anomaly', spending_points,
    'geographic_risk', geography_points,
    'sector_risk', sector_points,
    'external_intelligence', intelligence_points,
    'document_evidence', document_points
  ) AS score_breakdown,
  detected_typology_count,
  document_count,
  high_intelligence_hits,
  minimum_extraction_confidence,
  'SHADOWTRACE_SQL_V1' AS scoring_version
FROM scored;

MERGE INTO case_risk_scores target
USING (
  SELECT
    'RISK-' || case_id || '-V1' AS risk_score_id,
    case_id,
    '2026-07-01 08:33:00 +00:00'::TIMESTAMP_TZ AS calculated_at,
    risk_score,
    risk_band,
    evidence_strength,
    top_risk_factors,
    recommended_route,
    score_breakdown,
    scoring_version
  FROM vw_case_risk_summary
) source
ON target.risk_score_id = source.risk_score_id
WHEN MATCHED THEN UPDATE SET
  target.calculated_at = source.calculated_at,
  target.risk_score = source.risk_score,
  target.risk_band = source.risk_band,
  target.evidence_strength = source.evidence_strength,
  target.top_risk_factors = source.top_risk_factors,
  target.recommended_route = source.recommended_route,
  target.score_breakdown = source.score_breakdown,
  target.scoring_version = source.scoring_version
WHEN NOT MATCHED THEN INSERT (
  risk_score_id, case_id, calculated_at, risk_score, risk_band, evidence_strength,
  top_risk_factors, recommended_route, score_breakdown, scoring_version
) VALUES (
  source.risk_score_id, source.case_id, source.calculated_at, source.risk_score,
  source.risk_band, source.evidence_strength, source.top_risk_factors,
  source.recommended_route, source.score_breakdown, source.scoring_version
);

MERGE INTO audit_events target
USING (
  SELECT
    'AUD-' || case_id || '-RISK-V1' AS audit_event_id,
    case_id,
    '2026-07-01 08:33:00 +00:00'::TIMESTAMP_TZ AS event_ts,
    'SYSTEM' AS actor_type,
    'Explainable Risk SQL' AS actor_name,
    'RISK_SCORE_CALCULATED' AS event_type,
    'Calculated ' || risk_score || '/100 ' || risk_band
      || ' risk with ' || evidence_strength || ' evidence.' AS event_detail,
    'RISK_SCORE' AS object_type,
    'RISK-' || case_id || '-V1' AS object_id,
    OBJECT_CONSTRUCT('score', risk_score, 'band', risk_band, 'version', scoring_version) AS event_metadata
  FROM vw_case_risk_summary
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
