# Architecture

ShadowTraceAI keeps detection, explanation, application state, and audit history
inside Snowflake. The Streamlit layer is intentionally thin.

```mermaid
flowchart LR
  subgraph Sources["Synthetic evidence sources"]
    TX[Transactions]
    KYC[KYC and accounts]
    DEV[Device and IP]
    EXT[Watchlist and adverse media]
    DOC[Document metadata]
  end

  subgraph Snowflake["Snowflake · SHADOWTRACE_AI.AML"]
    RAW[(Typed core tables)]
    SIG["Five typology views"]
    NET["vw_case_network"]
    RISK["vw_case_risk_summary<br/>0–100 explainable SQL"]
    BRIEF["vw_case_intelligence_brief<br/>+ Cortex-ready prompt"]
    DEC["sp_record_case_decision"]
    CHAT["sp_record_copilot_message"]
    HISTORY[(Copilot messages)]
    EXEC["sp_record_agent_execution"]
    RUNS[(Agent executions)]
    STREAM["TRANSACTIONS_CHANGE_STREAM"]
    TASK["PROCESS_NEW_TRANSACTIONS_TASK"]
    PROCESS["SP_PROCESS_NEW_TRANSACTIONS"]
    AUDIT[(Decisions + audit events)]
  end

  subgraph Experience["Native investigation experience"]
    APP["Streamlit in Snowflake<br/>8-tab case workspace"]
    ORCH["Cortex Agent object<br/>SHADOWTRACE_AML_ORCHESTRATOR"]
    SPECIALISTS["5 governed custom tools<br/>typology Â· network Â· evidence<br/>risk Â· case brief"]
    COPILOT["Floating chat popup<br/>single user experience"]
    REVIEW["Named human reviewer"]
  end

  Sources --> RAW
  TX --> STREAM
  STREAM --> TASK
  TASK --> PROCESS
  PROCESS --> RAW
  PROCESS --> AUDIT
  RAW --> SIG
  RAW --> NET
  SIG --> RISK
  RAW --> RISK
  RISK --> BRIEF
  NET --> APP
  RISK --> APP
  BRIEF --> APP
  SIG --> COPILOT
  NET --> COPILOT
  RISK --> COPILOT
  BRIEF --> COPILOT
  APP --> COPILOT
  COPILOT --> ORCH
  ORCH --> SPECIALISTS
  SPECIALISTS --> ORCH
  ORCH --> CHAT
  ORCH --> EXEC
  SPECIALISTS --> EXEC
  EXEC --> RUNS
  EXEC --> AUDIT
  CHAT --> HISTORY
  CHAT --> AUDIT
  HISTORY --> COPILOT
  APP --> REVIEW
  REVIEW --> DEC
  DEC --> AUDIT
  AUDIT --> APP
```

## Design decisions

### Snowflake-first

Typed Snowflake tables hold all structured evidence. Views express typology and
scoring logic, so an investigator can reproduce every score using SQL alone.
Streamlit reads those objects through the active Snowpark session.

### Deterministic score, optional generative narrative

The score and route never depend on an LLM. `vw_case_brief_prompt` packages
bounded evidence for Cortex, while `vw_case_intelligence_brief` provides a
deterministic brief when Cortex is unavailable. The optional
`05b_cortex_brief_optional.sql` demonstrates `SNOWFLAKE.CORTEX.COMPLETE`.

### Human decision gate

The system recommends a route but does not file a SAR. The reviewer must choose
one of four decisions and provide rationale. `sp_record_case_decision` stores
the decision and matching audit event in one transaction.

### Governed investigation conversation

The first-class Snowflake Cortex Agent `SHADOWTRACE_AML_ORCHESTRATOR` routes
questions to five bounded custom tools using the same curated Snowflake views
shown elsewhere in the application. It is visible and testable in Snowflake's
AI & ML Agent Admin UI. Every answer identifies tool use and source objects.
`sp_record_copilot_message` persists conversation turns, while
`sp_record_agent_execution` records every specialist and orchestrator run with
its routing reason and sources. Both create linked audit events. The entire
agent team is read-only and sends accountable outcomes through the human gate.

### New-transaction processing

Streamlit is not the processing engine. Inserts into `TRANSACTIONS` are
captured by `TRANSACTIONS_CHANGE_STREAM`. A triggered Snowflake task calls
`SP_PROCESS_NEW_TRANSACTIONS`, which creates or links a case, records the
processing event and audit entry, and makes the new evidence immediately
available to the SQL risk views and Cortex Agent custom tools.

### Evidence safety

The dataset is wholly synthetic. Example domains use `.test`, example IP ranges
use documentation blocks, and all person/company names are fictional.

## CASE-C003 network

```mermaid
flowchart LR
  EMP["ACC-C-003<br/>Horizon Works"]
  W1["ACC-I-101<br/>Worker"]
  W2["ACC-I-102<br/>Worker"]
  W3["ACC-I-103<br/>Worker"]
  W4["ACC-I-104<br/>Worker"]
  W5["ACC-I-105<br/>Worker"]
  CTRL["ACC-I-106<br/>Controller"]
  FUNNEL["ACC-I-107<br/>Funnel"]
  CASH(("Foreign<br/>cash-out"))

  EMP -->|payroll| W1 & W2 & W3 & W4 & W5
  W1 & W2 & W3 & W4 & W5 -->|rapid onward transfer| CTRL
  CTRL -->|consolidation| FUNNEL
  FUNNEL -->|cash withdrawal| CASH
```
