-- First-class Snowflake Cortex Agent visible under AI & ML > Agents.
-- Five governed custom tools expose the specialist AML capabilities.
USE ROLE ACCOUNTADMIN;
USE DATABASE SHADOWTRACE_AI;
USE SCHEMA AML;

GRANT DATABASE ROLE SNOWFLAKE.CORTEX_AGENT_USER TO ROLE ACCOUNTADMIN;

CREATE OR REPLACE FUNCTION fn_agent_risk(p_case_id VARCHAR)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
  SELECT TO_JSON(OBJECT_CONSTRUCT_KEEP_NULL(
    'case_id', case_id,
    'risk_score', risk_score,
    'risk_band', risk_band,
    'evidence_strength', evidence_strength,
    'top_risk_factors', top_risk_factors,
    'recommended_route', recommended_route,
    'score_breakdown', score_breakdown,
    'scoring_version', scoring_version
  ))
  FROM vw_case_risk_summary
  WHERE case_id = p_case_id
$$;

CREATE OR REPLACE FUNCTION fn_agent_typologies(p_case_id VARCHAR)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
  SELECT TO_JSON(ARRAY_AGG(OBJECT_CONSTRUCT_KEEP_NULL(
    'signal_type', signal_type,
    'signal_detected', signal_detected,
    'risk_points', risk_points,
    'explanation', explanation
  )) WITHIN GROUP (ORDER BY risk_points DESC))
  FROM vw_all_typology_signals
  WHERE case_id = p_case_id
$$;

CREATE OR REPLACE FUNCTION fn_agent_network(p_case_id VARCHAR)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
  SELECT TO_JSON(ARRAY_AGG(OBJECT_CONSTRUCT_KEEP_NULL(
    'source_account_id', source_account_id,
    'target_account_id', target_account_id,
    'relationship_type', relationship_type,
    'event_count', event_count,
    'total_amount', total_amount,
    'evidence', evidence
  )) WITHIN GROUP (ORDER BY relationship_type, source_account_id, target_account_id))
  FROM vw_case_network
  WHERE case_id = p_case_id
$$;

CREATE OR REPLACE FUNCTION fn_agent_evidence(p_case_id VARCHAR)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
  SELECT TO_JSON(OBJECT_CONSTRUCT_KEEP_NULL(
    'case_id', c.case_id,
    'account_id', c.account_id,
    'documents', (
      SELECT ARRAY_AGG(OBJECT_CONSTRUCT_KEEP_NULL(
        'document_type', d.document_type,
        'file_name', d.file_name,
        'extraction_confidence', d.extraction_confidence,
        'risk_indicators', d.risk_indicators,
        'evidence_summary', d.evidence_summary,
        'review_status', d.review_status
      ))
      FROM document_evidence d
      WHERE d.case_id = c.case_id
    ),
    'external_intelligence', (
      SELECT ARRAY_AGG(OBJECT_CONSTRUCT_KEEP_NULL(
        'source_type', w.source_type,
        'entity_name', w.entity_name,
        'risk_level', w.risk_level,
        'match_strength', w.match_strength,
        'summary', w.summary
      ))
      FROM external_watchlist w
      WHERE w.matched_account_id = c.account_id
         OR w.matched_account_id IN (
           SELECT source_account_id FROM vw_case_network WHERE case_id = c.case_id
           UNION
           SELECT target_account_id FROM vw_case_network WHERE case_id = c.case_id
         )
    )
  ))
  FROM case_alerts c
  WHERE c.case_id = p_case_id
$$;

CREATE OR REPLACE FUNCTION fn_agent_case_brief(p_case_id VARCHAR)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
  SELECT TO_JSON(OBJECT_CONSTRUCT_KEEP_NULL(
    'case_id', case_id,
    'executive_summary', executive_summary,
    'suspicion_hypothesis', suspicion_hypothesis,
    'evidence_summary', evidence_summary,
    'missing_evidence', missing_evidence,
    'recommended_action', recommended_action,
    'audit_timeline', audit_timeline
  ))
  FROM vw_case_intelligence_brief
  WHERE case_id = p_case_id
$$;

CREATE OR REPLACE AGENT shadowtrace_aml_orchestrator
  COMMENT = 'AML investigation agent for modern-slavery and human-trafficking risk analysis.'
  PROFILE = '{"display_name":"ShadowTraceAI AML Orchestrator","color":"blue"}'
  FROM SPECIFICATION
  $$
  orchestration:
    budget:
      seconds: 45
      tokens: 12000

  instructions:
    response: |
      Act as an AML investigation copilot. Be concise, evidence-led, and explicit about uncertainty.
      Always identify the tools used and cite the Snowflake objects returned by those tools.
      Never claim that a SAR has been filed and never replace the named human reviewer.
    orchestration: |
      A case identifier such as CASE-C003 is required for case-specific analysis.
      Use risk_explanation for scores, bands, points, evidence strength, and route questions.
      Use typology_detection for wage harvesting, spending, geography, sector, and account-control signals.
      Use network_intelligence for connected accounts, devices, controllers, funnels, and cash-out paths.
      Use evidence_review for documents, watchlists, adverse media, corroboration, and evidence gaps.
      Use case_brief for summaries, suspicion hypotheses, missing evidence, and recommended actions.
      For a full investigation review, call all five tools before synthesizing the response.
    sample_questions:
      - question: "Why is CASE-C003 scored 92 and what route is recommended?"
      - question: "Show the connected-account evidence for CASE-C003."
      - question: "Run a full five-tool investigation review for CASE-C003."

  tools:
    - tool_spec:
        type: "generic"
        name: "risk_explanation"
        description: "Returns the explainable 0-100 risk score, band, factors, evidence strength, and recommended route for an AML case."
        input_schema:
          type: "object"
          properties:
            case_id:
              type: "string"
              description: "AML case identifier, for example CASE-C003."
          required:
            - "case_id"
    - tool_spec:
        type: "generic"
        name: "typology_detection"
        description: "Returns detected modern-slavery AML typologies and their evidence-backed risk points for a case."
        input_schema:
          type: "object"
          properties:
            case_id:
              type: "string"
              description: "AML case identifier, for example CASE-C003."
          required:
            - "case_id"
    - tool_spec:
        type: "generic"
        name: "network_intelligence"
        description: "Returns connected-account relationships, controllers, funnels, shared-device links, and cash-out paths."
        input_schema:
          type: "object"
          properties:
            case_id:
              type: "string"
              description: "AML case identifier, for example CASE-C003."
          required:
            - "case_id"
    - tool_spec:
        type: "generic"
        name: "evidence_review"
        description: "Returns document evidence and external intelligence used to corroborate or challenge a case hypothesis."
        input_schema:
          type: "object"
          properties:
            case_id:
              type: "string"
              description: "AML case identifier, for example CASE-C003."
          required:
            - "case_id"
    - tool_spec:
        type: "generic"
        name: "case_brief"
        description: "Returns the investigation brief, suspicion hypothesis, evidence gaps, timeline, and recommended action."
        input_schema:
          type: "object"
          properties:
            case_id:
              type: "string"
              description: "AML case identifier, for example CASE-C003."
          required:
            - "case_id"

  tool_resources:
    risk_explanation:
      type: "function"
      identifier: "SHADOWTRACE_AI.AML.FN_AGENT_RISK"
      execution_environment:
        type: "warehouse"
        warehouse: "COMPUTE_WH"
        query_timeout: 60
    typology_detection:
      type: "function"
      identifier: "SHADOWTRACE_AI.AML.FN_AGENT_TYPOLOGIES"
      execution_environment:
        type: "warehouse"
        warehouse: "COMPUTE_WH"
        query_timeout: 60
    network_intelligence:
      type: "function"
      identifier: "SHADOWTRACE_AI.AML.FN_AGENT_NETWORK"
      execution_environment:
        type: "warehouse"
        warehouse: "COMPUTE_WH"
        query_timeout: 60
    evidence_review:
      type: "function"
      identifier: "SHADOWTRACE_AI.AML.FN_AGENT_EVIDENCE"
      execution_environment:
        type: "warehouse"
        warehouse: "COMPUTE_WH"
        query_timeout: 60
    case_brief:
      type: "function"
      identifier: "SHADOWTRACE_AI.AML.FN_AGENT_CASE_BRIEF"
      execution_environment:
        type: "warehouse"
        warehouse: "COMPUTE_WH"
        query_timeout: 60
  $$;

SHOW AGENTS LIKE 'SHADOWTRACE_AML_ORCHESTRATOR' IN SCHEMA SHADOWTRACE_AI.AML;
DESCRIBE AGENT SHADOWTRACE_AI.AML.SHADOWTRACE_AML_ORCHESTRATOR;
