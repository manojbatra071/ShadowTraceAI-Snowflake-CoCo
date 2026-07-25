# CoCo CLI prompt journal

This journal records the natural-language prompts used to drive and verify the
Snowflake implementation. Start the session from the repository root:

```powershell
cortex -c <snowflake-connection> -w . --plan
```

CoCo is run in plan mode so every SQL write is reviewed before execution. Secrets,
connection files, and customer data are never included in prompts or committed.

## 1. Inspect the schema

> Inspect `sql/01_schema.sql` and the objects currently available in
> `SHADOWTRACE_AI.AML`. Compare table names, column types, primary identifiers,
> stages, and views. Report drift and do not modify anything yet.

Evidence to retain: CoCo's Snowflake object search/table output and its schema
drift summary.

## 2. Generate and validate typology SQL views

> Read `data/seed/*.csv`, `sql/01_schema.sql`, and
> `sql/03_typology_views.sql`. Validate the five modern-slavery typologies:
> wage harvesting, account control, spending anomaly, geographic risk, and
> sector risk. Execute each view for `CASE-C003`, explain every join, and flag
> false-positive risks. Preserve the human-safeguarding context.

Evidence to retain: query result showing five detected signal rows for
`CASE-C003`.

## 3. Build explainable risk scoring

> Review `sql/04_risk_scoring.sql`. Confirm that the score is derived from
> visible signal points rather than a case-ID override. Run
> `vw_case_risk_summary` for all demo cases, reconcile the score breakdown, and
> verify that `CASE-C003` is exactly `92 / CRITICAL / STRONG` while the benign
> comparison stays LOW.

Evidence to retain: the two-row risk summary and expanded `score_breakdown`.

## 4. Create the Streamlit application

> Use the Snowflake `developing-with-streamlit` skill to inspect
> `app/streamlit_app.py`. Verify all eight tabs, Snowpark session usage,
> parameterized queries, the Plotly account network, and the reviewer decision
> form. Make only focused fixes and keep the app Snowflake-native.

Evidence to retain: CoCo's file diff plus the deployed Streamlit URL.

## 5. Debug queries

> Execute the SQL files in order and debug any Snowflake compilation or data
> loading failures. For each fix, explain the failing statement, the root cause,
> and the smallest correction. Then run `tests/test_risk_logic.sql`. Do not
> weaken a test merely to make it pass.

Evidence to retain: final test output with six PASS rows.

## 6. Summarize case evidence

> Query `vw_case_intelligence_brief`, `vw_case_network`,
> `document_evidence`, and `external_watchlist` for `CASE-C003`. Produce a
> concise investigation brief grounded only in returned evidence. Separate
> suspicion from fact, list missing evidence, and state that SAR escalation
> requires a human reviewer.

Evidence to retain: CoCo's evidence-grounded answer and the underlying query IDs.

## 7. Verify the reviewer audit write

> Call `sp_record_case_decision` in a demo transaction for `CASE-C003` using
> `ESCALATE_TO_SAR`, then show the matching rows in `case_decisions` and
> `audit_events`. Verify the actor, rationale, timestamps, and linked decision
> ID. Use demo data only.

Evidence to retain: the stored procedure result and linked audit rows.

> Submission note: terminal screenshots/query IDs should be captured from the
> connected Snowflake account after these prompts are executed. This repository
> intentionally contains no fabricated command output.

