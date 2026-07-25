-- ShadowTraceAI: AML Intelligence Copilot on Snowflake
-- Run with a role that can create a database, schema, stage, and Streamlit app.

CREATE DATABASE IF NOT EXISTS SHADOWTRACE_AI;
CREATE SCHEMA IF NOT EXISTS SHADOWTRACE_AI.AML;
USE DATABASE SHADOWTRACE_AI;
USE SCHEMA AML;

CREATE OR REPLACE FILE FORMAT CSV_SEED_FORMAT
  TYPE = CSV
  PARSE_HEADER = TRUE
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  TRIM_SPACE = TRUE
  NULL_IF = ('', 'NULL');

CREATE STAGE IF NOT EXISTS SEED_STAGE
  DIRECTORY = (ENABLE = TRUE)
  FILE_FORMAT = CSV_SEED_FORMAT;

CREATE TABLE IF NOT EXISTS accounts (
  account_id VARCHAR PRIMARY KEY,
  customer_id VARCHAR NOT NULL,
  account_type VARCHAR NOT NULL,
  display_name VARCHAR NOT NULL,
  sector VARCHAR,
  country_code VARCHAR(2),
  address_id VARCHAR,
  employer_id VARCHAR,
  opened_date DATE,
  declared_monthly_income NUMBER(18,2),
  declared_employee_count INTEGER,
  account_status VARCHAR DEFAULT 'ACTIVE'
);

CREATE TABLE IF NOT EXISTS transactions (
  transaction_id VARCHAR PRIMARY KEY,
  transaction_ts TIMESTAMP_TZ NOT NULL,
  from_account_id VARCHAR,
  to_account_id VARCHAR,
  amount NUMBER(18,2) NOT NULL,
  currency VARCHAR(3) NOT NULL,
  transaction_type VARCHAR NOT NULL,
  channel VARCHAR,
  counterparty_country VARCHAR(2),
  merchant_category VARCHAR,
  description VARCHAR
);

CREATE TABLE IF NOT EXISTS kyc_profiles (
  kyc_profile_id VARCHAR PRIMARY KEY,
  account_id VARCHAR NOT NULL,
  legal_name VARCHAR NOT NULL,
  nationality_or_incorporation VARCHAR(2),
  occupation_or_business VARCHAR,
  expected_monthly_turnover NUMBER(18,2),
  beneficial_owner_status VARCHAR,
  identity_status VARCHAR,
  phone_number VARCHAR,
  email VARCHAR,
  residential_or_registered_address VARCHAR,
  last_reviewed_at TIMESTAMP_TZ
);

CREATE TABLE IF NOT EXISTS device_ip_signals (
  signal_id VARCHAR PRIMARY KEY,
  account_id VARCHAR NOT NULL,
  observed_at TIMESTAMP_TZ NOT NULL,
  device_id VARCHAR,
  ip_address VARCHAR,
  ip_country VARCHAR(2),
  is_vpn BOOLEAN,
  login_result VARCHAR,
  signal_type VARCHAR
);

CREATE TABLE IF NOT EXISTS external_watchlist (
  watchlist_id VARCHAR PRIMARY KEY,
  entity_name VARCHAR NOT NULL,
  matched_account_id VARCHAR,
  source_type VARCHAR NOT NULL,
  source_name VARCHAR,
  match_strength NUMBER(5,2),
  risk_level VARCHAR,
  published_date DATE,
  summary VARCHAR,
  source_url VARCHAR
);

CREATE TABLE IF NOT EXISTS document_evidence (
  document_id VARCHAR PRIMARY KEY,
  case_id VARCHAR NOT NULL,
  account_id VARCHAR NOT NULL,
  document_type VARCHAR NOT NULL,
  file_name VARCHAR,
  uploaded_at TIMESTAMP_TZ,
  extraction_confidence NUMBER(5,2),
  metadata VARIANT,
  risk_indicators ARRAY,
  evidence_summary VARCHAR,
  review_status VARCHAR DEFAULT 'PENDING'
);

CREATE TABLE IF NOT EXISTS case_alerts (
  case_id VARCHAR PRIMARY KEY,
  account_id VARCHAR NOT NULL,
  alert_type VARCHAR NOT NULL,
  alert_status VARCHAR DEFAULT 'OPEN',
  priority VARCHAR,
  created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
  assigned_to VARCHAR,
  alert_summary VARCHAR
);

CREATE TABLE IF NOT EXISTS case_risk_scores (
  risk_score_id VARCHAR PRIMARY KEY,
  case_id VARCHAR NOT NULL,
  calculated_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
  risk_score INTEGER,
  risk_band VARCHAR,
  evidence_strength VARCHAR,
  top_risk_factors ARRAY,
  recommended_route VARCHAR,
  score_breakdown VARIANT,
  scoring_version VARCHAR
);

CREATE TABLE IF NOT EXISTS case_decisions (
  decision_id VARCHAR PRIMARY KEY,
  case_id VARCHAR NOT NULL,
  decision VARCHAR NOT NULL,
  reviewer_name VARCHAR NOT NULL,
  rationale VARCHAR,
  decided_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS audit_events (
  audit_event_id VARCHAR PRIMARY KEY,
  case_id VARCHAR NOT NULL,
  event_ts TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
  actor_type VARCHAR NOT NULL,
  actor_name VARCHAR NOT NULL,
  event_type VARCHAR NOT NULL,
  event_detail VARCHAR,
  object_type VARCHAR,
  object_id VARCHAR,
  event_metadata VARIANT
);

CREATE TABLE IF NOT EXISTS case_intelligence_briefs (
  brief_id VARCHAR PRIMARY KEY,
  case_id VARCHAR NOT NULL,
  generated_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
  generation_method VARCHAR NOT NULL,
  executive_summary VARCHAR,
  suspicion_hypothesis VARCHAR,
  evidence_summary VARCHAR,
  missing_evidence VARCHAR,
  recommended_action VARCHAR,
  audit_timeline VARCHAR,
  prompt_text VARCHAR
);

