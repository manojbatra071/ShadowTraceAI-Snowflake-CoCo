# Five-minute demo script

## 0:00 — Position the problem

“Modern-slavery AML reviews are fragmented across transactions, KYC, device
signals, external intelligence, and documents. ShadowTraceAI connects those
signals in Snowflake and gives the investigator an explainable, auditable
decision workspace.”

Open Snowsight and briefly show the objects in `SHADOWTRACE_AI.AML`.

## 0:35 — Prove the SQL execution

Run:

```sql
SELECT signal_type, risk_points, explanation
FROM SHADOWTRACE_AI.AML.vw_all_typology_signals
WHERE case_id = 'CASE-C003' AND signal_detected
ORDER BY risk_points DESC;
```

Point out all five typologies and that each signal is a view over seeded
transaction/KYC/device data.

## 1:10 — Open the investigation workspace

Open the native Streamlit app and select `CASE-C003`. On **Overview**, show the
`92/100 CRITICAL` score, strong evidence, and recommended SAR escalation route.

## 1:45 — Explain the connected behavior

On **Account Network**, trace:

1. Horizon Works pays five worker accounts.
2. Workers rapidly transfer most wages to `ACC-I-106`.
3. The controller consolidates funds into `ACC-I-107`.
4. The funnel performs a foreign cash withdrawal.
5. The worker/controller/funnel accounts share a device and IP.

## 2:30 — Show multi-source evidence

On **Evidence**, show:

- payroll register mismatch;
- contract deduction and excessive-hours clauses;
- low-confidence altered identity scan;
- shared accommodation/controller contact;
- adverse media and registry intelligence.

Emphasize that raw and unstructured-document metadata remain in Snowflake.

## 3:10 — Explain 92, do not merely display it

On **Risk Score**, walk through:

| Factor | Points |
|---|---:|
| Wage harvesting | 25 |
| Account control | 25 |
| Spending anomaly | 14 |
| Geographic risk | 12 |
| Sector risk | 8 |
| External intelligence | 4 |
| Document evidence | 4 |
| **Total** | **92** |

## 3:45 — Show the copilot brief

On **Case Intelligence Brief**, read the executive summary and suspicion
hypothesis. Open the Cortex prompt expander to demonstrate grounded context and
the deterministic fallback.

## 4:20 — Complete the human workflow

On **Reviewer Decision**:

- reviewer: `AML Demo Reviewer`;
- decision: `Escalate to SAR`;
- rationale: `Multi-source evidence supports escalation for formal SAR assessment.`;
- acknowledge the human decision gate;
- record the decision.

## 4:45 — Prove auditability

Open **Audit Trail** and show the new `REVIEWER_DECISION` event. In Snowsight,
run:

```sql
SELECT d.decision_id, d.decision, d.reviewer_name, d.decided_at,
       a.audit_event_id, a.event_type, a.event_detail
FROM SHADOWTRACE_AI.AML.case_decisions d
JOIN SHADOWTRACE_AI.AML.audit_events a
  ON a.object_id = d.decision_id
WHERE d.case_id = 'CASE-C003'
ORDER BY d.decided_at DESC;
```

Close with: “One Snowflake evidence plane, one explainable score, and one
audit-ready human decision.”

