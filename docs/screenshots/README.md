# Live screenshot checklist

Screenshots must be captured from the connected Snowflake account after
deployment; this repository does not fabricate execution evidence.

Capture at 1440×900 or larger and save:

1. `01-snowsight-objects.png` — tables and views under `SHADOWTRACE_AI.AML`.
2. `02-typology-query.png` — five detected signal rows for `CASE-C003`.
3. `03-overview-92-critical.png` — Streamlit Overview.
4. `04-account-network.png` — connected employer/worker/controller/funnel graph.
5. `05-evidence.png` — document and external evidence.
6. `06-risk-breakdown.png` — seven explainable score components.
7. `07-case-brief.png` — case intelligence brief.
8. `08-reviewer-decision.png` — completed Escalate to SAR form.
9. `09-audit-trail.png` — stored decision and linked audit event.
10. `10-coco-cli.png` — CoCo query/test output with query ID visible.

Before capture, reset demo decisions if necessary:

```sql
DELETE FROM SHADOWTRACE_AI.AML.audit_events
WHERE case_id = 'CASE-C003' AND event_type = 'REVIEWER_DECISION';

DELETE FROM SHADOWTRACE_AI.AML.case_decisions
WHERE case_id = 'CASE-C003';

UPDATE SHADOWTRACE_AI.AML.case_alerts
SET alert_status = 'OPEN', assigned_to = 'AML_DEMO_REVIEWER'
WHERE case_id = 'CASE-C003';
```

