# ShadowTraceAI: Five-Minute Judge Presentation

For a five-minute pitch, tell one clear story: fragmented AML evidence goes in,
Snowflake agents investigate it, and an accountable human makes the final
decision.

## Preparation

Before presenting, open these in separate browser tabs:

1. The Streamlit app with `CASE-C003` selected.
2. Snowsight **AI & ML > Agents > SHADOWTRACE_AML_ORCHESTRATOR**.
3. A Snowflake worksheet containing:

```sql
SELECT *
FROM SHADOWTRACE_AI.AML.CASE_AGENT_EXECUTIONS
WHERE CASE_ID = 'CASE-C003'
ORDER BY EXECUTED_AT DESC;

SELECT *
FROM SHADOWTRACE_AI.AML.AUDIT_EVENTS
WHERE CASE_ID = 'CASE-C003'
ORDER BY EVENT_TS DESC;
```

Keep the Streamlit app on **Overview** initially. Open the chatbot once before
the presentation so that the Snowflake warehouse is warm.

## 0:00-0:30 — Hook

Say:

> Modern-slavery AML investigations rarely fail because banks have no data.
> They fail because the evidence is fragmented across transactions, KYC,
> devices, documents, watchlists, and investigator notes.
>
> ShadowTraceAI turns that fragmented evidence into one explainable,
> network-aware, audit-ready investigation inside Snowflake.

Then deliver the one-liner:

> ShadowTraceAI is a Snowflake-powered AML intelligence copilot that detects
> modern-slavery risk patterns, explains connected-account evidence, and turns
> suspicious alerts into accountable investigation decisions.

## 0:30-1:00 — The business problem

Show the **Overview** tab.

Say:

> Traditional transaction monitoring may identify an unusual payment, but
> trafficking indicators often appear only when multiple signals are connected.
>
> In this case, we need to connect payroll diversion, common account control,
> unusual spending behaviour, geographic exposure, sector risk, documents, and
> external intelligence.
>
> Today, investigators often assemble this manually. That increases
> investigation time, inconsistency, and regulatory risk.

## 1:00-1:35 — Snowflake architecture

Briefly show the processing pipeline on the **Overview** tab.

Say:

> Snowflake is the intelligence and execution layer—not merely the database.
>
> New transactions are captured through a Snowflake stream and triggered task.
> SQL detection views evaluate five modern-slavery typologies. The explainable
> scoring layer calculates a score from zero to one hundred. A first-class
> Cortex Agent then selects governed specialist tools to investigate the case.

Switch briefly to **AI & ML > Agents** and show the Cortex Agent and its tools.

Say:

> This is the deployed `SHADOWTRACE_AML_ORCHESTRATOR`. It coordinates five
> governed specialist capabilities: risk, typologies, network, evidence, and
> case brief.
>
> Every specialist reads controlled Snowflake objects. None of these tools can
> file a SAR or make the final regulatory decision.

Do not spend time opening every tool configuration.

## 1:35-2:45 — Investigate CASE-C003

Return to Streamlit and select `CASE-C003`.

Open the **Risk Score** tab.

Say:

> Our demo case is Horizon Works Construction. ShadowTraceAI scores it **92 out
> of 100—CRITICAL—with STRONG evidence**.
>
> The score is explainable. Wage harvesting contributes 25 points, account
> control 25, spending anomaly 14, geographic risk 12, sector risk 8, with
> additional document and external-intelligence evidence.

Show **Typology Signals** briefly.

Say:

> All five target typologies are detected. This is not an unexplained
> machine-learning score; every point is linked to a specific signal and
> supporting data.

## 2:45-3:25 — Network intelligence

Open **Account Network**.

Say:

> The network view shows why individual transaction review is insufficient.
>
> The corporate employer pays multiple worker accounts. Those accounts rapidly
> transfer funds to a common controller, funds are consolidated into a funnel
> account, and then cashed out.
>
> Shared device and IP signals further indicate that supposedly independent
> accounts may be controlled by one operator.

Focus on the employer-to-workers-to-controller-to-cash-out path.

## 3:25-4:05 — Live chatbot

Click **Ask ShadowTrace**.

Ask:

> Why is this case scored 92 and what action is recommended?

While the response is running, say:

> This question is sent to the deployed Cortex Agent. The agent plans the
> request, invokes the Risk Explanation tool, grounds the response in
> `VW_CASE_RISK_SUMMARY`, and records the interaction and tool execution in
> Snowflake.

When the response appears, point out:

- `92/100 CRITICAL`
- Evidence strength
- Top risk factors
- Recommended SAR-assessment route
- Snowflake source objects

Avoid the full five-tool question during the timed presentation because it
takes longer. Use it only if the judges request a deeper demonstration.

## 4:05-4:35 — Human in the loop

Open **Reviewer Decision**.

Say:

> ShadowTraceAI recommends a route, but it does not make the regulatory
> decision.
>
> A named reviewer must select an outcome, provide a rationale, and explicitly
> acknowledge that no SAR is being filed automatically.

Select **Escalate to SAR**, provide the rationale, select the acknowledgement,
and record the decision.

Clarify:

> Escalate to SAR means escalation for formal SAR assessment—not automatic
> filing.

## 4:35-4:50 — Auditability

Open **Audit Trail**.

Say:

> The decision is now stored with the reviewer, timestamp, rationale, linked
> decision ID, and audit event.
>
> The chatbot messages, specialist executions, evidence sources, risk
> calculation, and human decision are all traceable inside Snowflake.

## 4:50-5:00 — Close

Say:

> ShadowTraceAI reduces investigation effort, improves consistency, reveals
> connected-account behaviour, and gives AML teams an evidence-led path from a
> new transaction to an accountable human decision.
>
> It is Snowflake-first, explainable, agentic, and designed for one of the most
> difficult financial-crime problems: detecting potential modern slavery hidden
> across fragmented data.

## If the chatbot is slow

Do not wait silently. Say:

> The Cortex Agent is currently executing its governed Snowflake tool. While
> that completes, I will show the persisted execution trail from an earlier
> question.

Switch to the prepared worksheet and run:

```sql
SELECT
    executed_at,
    agent_name,
    routing_reason,
    execution_status,
    source_objects
FROM SHADOWTRACE_AI.AML.CASE_AGENT_EXECUTIONS
WHERE case_id = 'CASE-C003'
ORDER BY executed_at DESC;
```

Return to the chatbot after showing the audit records.

## Likely judge questions

### Is this genuinely using Snowflake AI?

> Yes. The deployed Cortex Agent is visible under Snowflake AI & ML. Streamlit
> invokes it through `SNOWFLAKE.CORTEX.DATA_AGENT_RUN`, and its governed tools
> are backed by Snowflake SQL UDFs and views.

### Are these six separate Cortex Agents?

> There is one first-class Cortex orchestration agent with five governed
> specialist tools. The specialist executions are separately identified and
> audited, but they are not presented as six independent Cortex Agent objects.

### Can the agent file a SAR?

> No. Its tools are read-only. Only the reviewer-decision procedure can record a
> controlled human outcome, and escalation means formal assessment rather than
> automatic filing.

### What happens when a new transaction arrives?

> An append-only Snowflake stream captures it. A triggered task runs the
> processing procedure, links or creates the case, refreshes the live signal and
> risk views, and makes the new evidence available to the Cortex Agent and
> Streamlit application.

### Why not use a black-box machine-learning score?

> Explainability is essential in AML. ShadowTraceAI shows the exact typology,
> points, evidence strength, source objects, connected accounts, and recommended
> route behind the score.
