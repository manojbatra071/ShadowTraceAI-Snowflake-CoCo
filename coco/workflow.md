# CoCo-assisted build workflow

## Operating model

CoCo CLI is the Snowflake-aware pair engineer; SQL remains the auditable source
of truth. The workflow uses CoCo to inspect live objects, reason over local
files, execute queries, debug Snowflake-specific behavior, and verify the
deployed app.

```text
Local repo + natural-language prompt
              |
              v
       CoCo CLI (plan mode)
        /             \
 local file tools   Snowflake tools
        \             /
         reviewed SQL change
              |
              v
 schema -> seeds -> views -> score -> brief -> app -> tests
```

## Reproducible session

1. Start from the repository root with
   `cortex -c <connection> -w . --plan`.
2. Ask CoCo to inspect the live schema before allowing writes.
3. Execute the ordered build scripts through `sql/11_transaction_pipeline.sql`.
4. Ask CoCo to reconcile `CASE-C003` against the CSV evidence and every
   component in `score_breakdown`.
5. Execute the risk, copilot, multi-agent, Cortex Agent, and transaction-pipeline
   tests; retain result tables, tool traces, and query IDs.
6. Deploy with `sql/07_deploy_streamlit.sql` after setting the warehouse.
7. In the app, record the demo reviewer decision and have CoCo query the linked
   decision/audit rows.
8. Run the prompt in `prompts.md` that summarizes evidence and compare its
   claims with `vw_case_intelligence_brief`.

## Guardrails

- Plan mode is used for visible approval of SQL writes.
- Synthetic data only; names, IPs, URLs, and contact details are reserved examples.
- The score is deterministic SQL and remains usable without Cortex.
- Cortex-generated language receives a bounded prompt containing case evidence.
- A human reviewer is required for any escalation decision.
- The audit event is committed in the same stored-procedure transaction as the
  reviewer decision.
- Query IDs and terminal output are captured from the live account, not invented
  in documentation.

## Submission evidence checklist

- [ ] CoCo schema inspection output
- [ ] Five typology view results for `CASE-C003`
- [ ] `92 / CRITICAL / STRONG` risk result and score breakdown
- [ ] Six passing SQL tests
- [ ] Streamlit deployment URL
- [ ] `SHADOWTRACE_AML_ORCHESTRATOR` visible under AI & ML → Agents
- [ ] Cortex Agent tool-use trace for `CASE-C003`
- [ ] New-transaction stream/task processing evidence
- [ ] Decision row linked to its audit event
- [ ] CoCo evidence summary with supporting Snowflake query IDs
- [ ] Screenshots added to `docs/screenshots/`
