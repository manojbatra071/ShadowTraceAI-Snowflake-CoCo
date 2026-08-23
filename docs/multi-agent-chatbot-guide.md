# ShadowTraceAI Multi-Agent Orchestration and Chatbot Guide

## What is deployed

ShadowTraceAI uses one first-class Snowflake Cortex Agent:

`SHADOWTRACE_AI.AML.SHADOWTRACE_AML_ORCHESTRATOR`

The Cortex Agent acts as the investigation orchestrator. It plans each request
and selects one or more of five governed specialist tools. This is an
orchestrator-and-specialist-tool architecture, not six independent Cortex Agent
objects.

| Specialist capability | Cortex tool | Grounded Snowflake source |
|---|---|---|
| Risk Explanation Agent | `risk_explanation` | `VW_CASE_RISK_SUMMARY` |
| Typology Detection Agent | `typology_detection` | `VW_ALL_TYPOLOGY_SIGNALS` |
| Network Intelligence Agent | `network_intelligence` | `VW_CASE_NETWORK` and device/IP evidence |
| Evidence Review Agent | `evidence_review` | `DOCUMENT_EVIDENCE` and `EXTERNAL_WATCHLIST` |
| Case Brief Agent | `case_brief` | `VW_CASE_INTELLIGENCE_BRIEF` |

Each tool is backed by a read-only SQL UDF. The agent has no tool that records a
reviewer decision or files a SAR.

## How orchestration works

1. The investigator selects a case in the Streamlit application.
2. The popup automatically supplies the active case identifier with the
   investigator's question.
3. Streamlit calls `SNOWFLAKE.CORTEX.DATA_AGENT_RUN` for the Cortex Agent.
4. The Cortex Agent interprets the question and creates a tool plan.
5. It invokes only the relevant specialist tools. A full review invokes all
   five.
6. Each tool reads curated Snowflake tables or views and returns structured
   case evidence.
7. The Cortex Agent synthesizes the tool results into one evidence-led answer.
8. Streamlit records the question, answer, selected specialists, sources, and
   execution trace in Snowflake.

Example routing:

| Investigator question | Expected specialist selection |
|---|---|
| Why is the score 92? | Risk Explanation |
| What trafficking typologies were detected? | Typology Detection |
| Who controls the connected accounts? | Network Intelligence |
| What documents or watchlist evidence exist? | Evidence Review |
| What action is recommended? | Case Brief |
| Give me a full investigation review | All five specialists |

## How the chatbot works

The **Ask ShadowTrace** button opens a bottom-right popup without taking space
from the main investigation tabs. The popup provides suggested questions and a
free-text question field.

For every submitted question, the application:

1. Records the user message through `SP_RECORD_COPILOT_MESSAGE`.
2. Calls the live Cortex Agent.
3. Reads the Cortex Agent tool-use trace and maps each tool to its specialist
   identity and Snowflake sources.
4. Records each selected specialist and the Case Orchestrator through
   `SP_RECORD_AGENT_EXECUTION`.
5. Records the final assistant response and its source objects.
6. Shows the answer and source names in the conversation.

The persisted evidence is available in:

- `CASE_COPILOT_MESSAGES` for the conversation.
- `CASE_AGENT_EXECUTIONS` for agent routing and specialist executions.
- `AUDIT_EVENTS` for linked copilot and agent audit records.

## Reliability and fallback

The Cortex Agent is the primary chatbot backend. If that call is unavailable,
the Streamlit application uses a bounded deterministic router over the same
loaded case data. The UI explicitly warns the investigator when fallback was
used. A fallback response is not presented as a Cortex Agent execution.

## Human control

The chatbot provides decision support only. It cannot submit a reviewer
decision or file a SAR. The named reviewer must use the **Reviewer Decision**
tab, provide a rationale, acknowledge human accountability, and select one of
the four controlled outcomes.

## Live acceptance coverage

`tests/test_chatbot_end_to_end.sql` sends a real full-review question to the
deployed Cortex Agent and requires:

- a completed response;
- all five governed tools in the tool-use trace;
- a substantive answer containing the expected score of 92;
- no tool failure, SQL compilation error, or time-limit response.

Additional tests verify conversation persistence, source-object linkage, six
auditable execution identities (the orchestrator plus five specialists), and
test-record cleanup.

## Judge-ready demonstration

1. In Snowsight, open **AI & ML > Agents** and show
   `SHADOWTRACE_AML_ORCHESTRATOR`.
2. Open its configuration and show the five governed custom tools.
3. Open `SHADOWTRACEAI_APP` and select `CASE-C003`.
4. Click **Ask ShadowTrace**.
5. Ask: `Give me a full review of risk, typologies, network, evidence, and recommended action.`
6. Show the answer containing `92/100 CRITICAL`, the detected typologies,
   connected-account network, evidence, and recommended route.
7. Show `CASE_AGENT_EXECUTIONS` to demonstrate specialist routing.
8. Show `CASE_COPILOT_MESSAGES` and `AUDIT_EVENTS` to demonstrate traceability.
9. Finish in **Reviewer Decision** to show that regulatory action remains under
   human control.
