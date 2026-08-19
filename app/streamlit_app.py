"""ShadowTraceAI — Snowflake-native AML investigation copilot."""

from __future__ import annotations

import json
import math
import uuid
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="ShadowTraceAI | AML Intelligence Copilot",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      :root {
        color-scheme:light; --navy:#102a43; --ink:#243b53; --muted:#627d98;
        --teal:#0f766e; --teal-soft:#ecfdf8; --red:#b42318; --surface:#ffffff;
        --canvas:#f4f7fa; --line:#d8e1ea; --shadow:0 8px 24px rgba(16,42,67,.055);
      }
      html, body, .stApp, [data-testid="stAppViewContainer"] { color-scheme:light; }
      .stApp, [data-testid="stAppViewContainer"] {
        background:linear-gradient(180deg,#f8fafc 0,#f4f7fa 30rem,#f4f7fa 100%); color:var(--ink); }
      [data-testid="stHeader"] { background:rgba(248,250,252,.94); border-bottom:1px solid #e7edf3; }
      [data-testid="stToolbar"] { color:var(--navy); }
      [data-testid="stSidebar"] { background:#fff; border-right:1px solid var(--line);
        box-shadow:8px 0 28px rgba(16,42,67,.035); }
      [data-testid="stSidebar"] > div:first-child { padding-top:1.5rem; }
      [data-testid="stSidebar"] hr { border-color:#e7edf3; }
      [data-testid="stMainBlockContainer"] { max-width:1480px; padding-top:2rem; padding-bottom:4rem; }
      h1,h2,h3,h4 { color:var(--navy); letter-spacing:-.025em; }
      p, label, [data-testid="stCaptionContainer"] { color:var(--ink); }
      a { color:var(--teal); }
      .eyebrow { color:var(--teal); font-size:.72rem; font-weight:800; letter-spacing:.14em; }
      .brand-title { color:var(--navy); font-size:1.12rem; font-weight:800; margin:.28rem 0 .15rem; }
      .brand-copy { color:var(--muted); font-size:.78rem; line-height:1.45; }
      .brand-mark { width:2.35rem; height:2.35rem; display:grid; place-items:center;
        border:1px solid #9fd4cf; border-radius:.72rem; color:var(--teal); background:var(--teal-soft);
        font-size:1.15rem; font-weight:800; }
      .workspace-header { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem;
        background:linear-gradient(135deg,#fff 0%,#f3f8fb 72%,#ecfdf8 100%);
        border:1px solid var(--line); border-radius:1rem; padding:1.35rem 1.5rem; margin:0 0 1.15rem;
        box-shadow:var(--shadow); }
      .hero { font-size:2rem; font-weight:780; line-height:1.1; color:var(--navy); margin:.22rem 0 .25rem; }
      .subtle { color:var(--muted); font-size:.9rem; }
      .live-chip { flex:none; padding:.38rem .68rem; border:1px solid #a7d9d4; border-radius:99px;
        color:#0b615b; background:#fff; font-size:.72rem; font-weight:750; white-space:nowrap; }
      .risk-card { min-height:8.25rem; border:1px solid #f2b8b5;
        background:linear-gradient(135deg,#fff7f6,#fff); border-radius:.85rem;
        padding:1.05rem 1.15rem; box-shadow:0 6px 18px rgba(180,35,24,.045); }
      .risk-score { color:var(--red); font-size:2.35rem; line-height:1.05; font-weight:820; }
      .risk-band { color:#912018; font-size:.82rem; font-weight:800; letter-spacing:.09em; }
      .brief-card { border:1px solid var(--line); border-left:3px solid var(--teal); background:#fff;
        border-radius:0 .75rem .75rem 0; padding:1rem 1.1rem; margin:.45rem 0 1rem;
        color:var(--ink); box-shadow:0 5px 16px rgba(16,42,67,.035); }
      .signal-pill { display:inline-block; margin:.2rem .35rem .35rem 0; padding:.3rem .58rem;
        border:1px solid #a7d9d4; border-radius:99px; color:#0b615b; background:var(--teal-soft);
        font-size:.77rem; font-weight:650; }
      div[data-testid="stMetric"] { min-height:8.25rem; background:#fff; border:1px solid var(--line);
        padding:.85rem 1rem; border-radius:.85rem; box-shadow:var(--shadow); }
      div[data-testid="stMetric"] label { color:var(--muted); font-weight:650; }
      div[data-testid="stMetricValue"] { color:var(--navy); font-weight:780; }
      div[data-testid="stDataFrame"] { color-scheme:light; background:#fff; border:1px solid var(--line);
        border-radius:.75rem; overflow:hidden; box-shadow:0 5px 16px rgba(16,42,67,.035); }
      div[data-testid="stDataFrame"] * { color-scheme:light; }
      [data-testid="stTabs"] { margin-top:.15rem; }
      [data-testid="stTabs"] [data-baseweb="tab-list"] { gap:.15rem; background:#fff;
        border:1px solid var(--line); border-radius:.75rem; padding:.28rem .35rem; box-shadow:var(--shadow); }
      [data-testid="stTabs"] [data-baseweb="tab"] { color:#526d82; border-radius:.5rem; padding:.55rem .78rem; }
      [data-testid="stTabs"] [aria-selected="true"] { color:#0b615b; background:#eaf7f5; font-weight:750; }
      [data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color:var(--teal); }
      [data-testid="stForm"] { background:#fff; border:1px solid var(--line); border-radius:.85rem;
        padding:1rem 1.1rem; box-shadow:var(--shadow); }
      [data-baseweb="input"] > div, [data-baseweb="textarea"] > div,
      [data-baseweb="select"] > div { background:#fff; border-color:#b8c7d5; color:var(--navy); }
      [data-baseweb="popover"], [role="listbox"] { color-scheme:light; background:#fff; color:var(--ink); }
      [data-testid="stExpander"] { background:#fff; border:1px solid var(--line); border-radius:.75rem; }
      [data-testid="stChatMessage"] { background:#fff; border:1px solid var(--line);
        border-radius:.85rem; padding:.2rem .45rem; box-shadow:0 4px 14px rgba(16,42,67,.035); }
      [data-testid="stChatInput"] { background:#fff; border-color:#a7b9c8; }
      .copilot-banner { border:1px solid #a7d9d4; background:linear-gradient(135deg,#fff,#ecfdf8);
        border-radius:.9rem; padding:1rem 1.1rem; margin:.25rem 0 1rem; box-shadow:var(--shadow); }
      .copilot-title { color:var(--navy); font-size:1.05rem; font-weight:780; margin-bottom:.25rem; }
      .source-chip { display:inline-block; margin:.15rem .28rem .1rem 0; padding:.22rem .48rem;
        border:1px solid #c9d7e3; border-radius:99px; color:#526d82; background:#f8fafc;
        font-family:monospace; font-size:.68rem; }
      .st-key-chat_launcher { position:fixed; right:1.45rem; bottom:1.35rem; z-index:999999; }
      .st-key-chat_launcher button { min-height:3.25rem; padding:.75rem 1.05rem;
        border-radius:999px; border:1px solid #0b615b; background:var(--teal); color:#fff;
        box-shadow:0 12px 30px rgba(15,118,110,.28); font-size:.86rem; }
      .st-key-chat_launcher button:hover { background:#0b615b; border-color:#094f4a; color:#fff; }
      div[data-testid="stDialog"] { background:rgba(16,42,67,.04); }
      div[data-testid="stDialog"] div[role="dialog"] { position:fixed; right:1.4rem; bottom:5.2rem;
        top:auto; left:auto; width:min(430px,calc(100vw - 2rem));
        height:min(680px,calc(100dvh - 6.6rem)); max-height:calc(100dvh - 6.6rem); overflow:hidden;
        margin:0; border:1px solid var(--line); border-radius:1rem;
        box-shadow:0 22px 60px rgba(16,42,67,.2); }
      div[data-testid="stDialog"] div[role="dialog"] > div { max-height:100%; overflow-y:auto;
        overscroll-behavior:contain; }
      div[data-testid="stDialog"] [data-testid="stDialogBody"] { max-height:calc(100dvh - 10.5rem);
        overflow-y:auto; overscroll-behavior:contain; padding-bottom:1rem; scrollbar-gutter:stable; }
      div[data-testid="stDialog"] [data-testid="stDialogBody"]::-webkit-scrollbar { width:8px; }
      div[data-testid="stDialog"] [data-testid="stDialogBody"]::-webkit-scrollbar-thumb {
        background:#b8c7d5; border-radius:99px; }
      div[data-testid="stDialog"] [data-testid="stChatMessage"] { box-shadow:none; }
      div[data-testid="stDialog"] [data-testid="stForm"] { padding:.55rem .6rem;
        margin-bottom:.25rem; border-color:#c9d7e3; box-shadow:none; }
      div[data-testid="stDialog"] [data-testid="stForm"] .stButton button { min-height:2.55rem; }
      [data-testid="stAlert"] { border-radius:.7rem; border-width:1px; }
      .stButton>button, .stFormSubmitButton>button, .stDownloadButton>button {
        border-radius:.55rem; font-weight:720; border-color:#9bb0c2; background:#fff; color:var(--navy); }
      .stButton>button:hover, .stDownloadButton>button:hover { border-color:var(--teal); color:var(--teal); }
      .stFormSubmitButton>button[kind="primary"] { background:var(--teal); border-color:var(--teal); color:#fff; }
      code, pre { color-scheme:light; }
      @media (max-width:900px) { .workspace-header { align-items:flex-start; flex-direction:column; }
        .hero { font-size:1.65rem; }
        .st-key-chat_launcher { right:.85rem; bottom:.85rem; }
        div[data-testid="stDialog"] div[role="dialog"] { right:.75rem; bottom:4.7rem;
          width:calc(100vw - 1.5rem); height:calc(100dvh - 5.7rem); max-height:calc(100dvh - 5.7rem); }
        div[data-testid="stDialog"] [data-testid="stDialogBody"] { max-height:calc(100dvh - 9.5rem); } }
    </style>
    """,
    unsafe_allow_html=True,
)

DB = "SHADOWTRACE_AI.AML"
CORTEX_AGENT = "SHADOWTRACE_AI.AML.SHADOWTRACE_AML_ORCHESTRATOR"


@st.cache_resource
def get_session():
    """Use the active native session, with a st.connection fallback for local runs."""
    try:
        from snowflake.snowpark.context import get_active_session

        return get_active_session()
    except Exception:
        return st.connection("snowflake").session()


def query(sql: str, params: list[Any] | None = None) -> pd.DataFrame:
    frame = get_session().sql(sql, params=params or []).to_pandas()
    frame.columns = [str(column).lower() for column in frame.columns]
    return frame


def scalar(value: Any, fallback: str = "—") -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return fallback
    return str(value)


def parse_semistructured(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if value is None:
        return {}
    try:
        return json.loads(str(value))
    except (TypeError, json.JSONDecodeError):
        return value


def money(value: Any) -> str:
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return "0.00"


def signal_row(signals: pd.DataFrame, name: str) -> pd.Series | None:
    matches = signals[signals["signal_type"].str.lower() == name.lower()]
    return None if matches.empty else matches.iloc[0]


def agent_result(name: str, response: str, sources: list[str], reason: str) -> dict[str, Any]:
    return {"agent": name, "response": response, "sources": sources, "routing_reason": reason}


def risk_explanation_agent(case_id: str, risk: pd.Series) -> dict[str, Any]:
    score = int(risk["risk_score"])
    route = str(risk["recommended_route"]).replace("_", " ").title()
    breakdown = parse_semistructured(risk["score_breakdown"])
    factors = []
    if isinstance(breakdown, dict):
        factors = sorted(breakdown.items(), key=lambda item: float(item[1]), reverse=True)
    factor_text = "; ".join(
        f"**{str(name).replace('_', ' ').title()}** contributes **{int(points)} points**"
        for name, points in factors
    )
    response = (
        f"{case_id} is scored **{score}/100 ({risk['risk_band']})** with "
        f"**{risk['evidence_strength']}** evidence. {factor_text}. "
        f"The resulting route is **{route}**, subject to a named reviewer's decision."
    )
    return agent_result("Risk Explanation Agent", response, ["vw_case_risk_summary"], "Risk or score explanation requested")


def typology_detection_agent(question: str, signals: pd.DataFrame, transactions: pd.DataFrame) -> dict[str, Any]:
    prompt = question.lower()
    if any(term in prompt for term in ("wage", "payroll", "harvest")):
        row = signal_row(signals, "WAGE_HARVESTING")
        explanation = scalar(row["explanation"]) if row is not None else "No wage-harvesting signal was detected."
        points = int(row["risk_points"]) if row is not None else 0
        return agent_result(
            "Typology Detection Agent",
            f"The wage-harvesting detector contributes **{points} points**. {explanation}",
            ["vw_wage_harvesting_signals", "vw_all_typology_signals", "transactions"],
            "Wage-harvesting or payroll pattern requested",
        )
    if any(term in prompt for term in ("transaction", "spending", "amount", "payment")):
        if transactions.empty:
            summary = "No scoped transactions are available for this case."
        else:
            highest = transactions.sort_values("amount", ascending=False).iloc[0]
            total = transactions["amount"].astype(float).sum()
            summary = (
                f"The scoped dataset contains **{len(transactions)} transactions** totalling "
                f"**{money(total)}**. The largest is **{money(highest['amount'])} {highest['currency']}** "
                f"for {scalar(highest['description'])}."
            )
        anomaly = signal_row(signals, "SPENDING_ANOMALY")
        anomaly_text = scalar(anomaly["explanation"]) if anomaly is not None else ""
        return agent_result(
            "Typology Detection Agent",
            f"{summary} {anomaly_text}".strip(),
            ["transactions", "vw_spending_anomaly_signals"],
            "Transaction or spending-anomaly analysis requested",
        )
    if any(term in prompt for term in ("geograph", "country", "location", "jurisdiction")):
        row = signal_row(signals, "GEOGRAPHIC_RISK")
        countries = sorted(set(transactions["counterparty_country"].dropna().astype(str)))
        explanation = scalar(row["explanation"]) if row is not None else "No geographic-risk signal was detected."
        return agent_result(
            "Typology Detection Agent",
            f"Observed counterparty countries are **{', '.join(countries) or 'not available'}**. {explanation}",
            ["vw_geographic_risk_signals", "transactions", "device_ip_signals"],
            "Geographic-risk analysis requested",
        )
    detected = signals[signals["signal_detected"] == True]  # noqa: E712
    summary = "; ".join(
        f"**{row.signal_type.replace('_', ' ').title()}** (+{int(row.risk_points)}): {row.explanation}"
        for row in detected.itertuples()
    ) or "No active typology signals were detected."
    return agent_result(
        "Typology Detection Agent",
        summary,
        ["vw_all_typology_signals"],
        "General typology assessment requested",
    )


def network_intelligence_agent(edges: pd.DataFrame, signals: pd.DataFrame) -> dict[str, Any]:
    relationship_counts = edges["relationship_type"].value_counts().to_dict() if not edges.empty else {}
    relationships = ", ".join(
        f"{str(name).replace('_', ' ').title()} ({count})" for name, count in relationship_counts.items()
    ) or "no material connections"
    control = signal_row(signals, "ACCOUNT_CONTROL")
    control_text = scalar(control["explanation"]) if control is not None else "No account-control signal was detected."
    return agent_result(
        "Network Intelligence Agent",
        f"The case network contains **{len(edges)} evidence edges**: {relationships}. {control_text}",
        ["vw_case_network", "vw_account_control_signals", "device_ip_signals"],
        "Connected-account or control analysis requested",
    )


def evidence_review_agent(question: str, docs: pd.DataFrame, intel: pd.DataFrame, brief: pd.Series) -> dict[str, Any]:
    prompt = question.lower()
    if any(term in prompt for term in ("missing", "gap", "more evidence", "need next")):
        response = (
            f"The investigation brief identifies these evidence gaps: **{scalar(brief['missing_evidence'])}** "
            "These should be obtained before treating the hypothesis as a concluded finding."
        )
    else:
        reviewed = int((docs["review_status"].str.upper() == "REVIEWED").sum()) if not docs.empty else 0
        high_intel = int((intel["risk_level"].str.upper() == "HIGH").sum()) if not intel.empty else 0
        response = (
            f"The case has **{len(docs)} document records** ({reviewed} reviewed) and "
            f"**{len(intel)} external-intelligence matches** ({high_intel} high risk). "
            f"The combined evidence summary is: {scalar(brief['evidence_summary'])}"
        )
    return agent_result(
        "Evidence Review Agent",
        response,
        ["document_evidence", "external_watchlist", "vw_case_intelligence_brief"],
        "Document, external-intelligence, or evidence-gap review requested",
    )


def case_brief_agent(question: str, account_name: str, risk: pd.Series, brief: pd.Series) -> dict[str, Any]:
    prompt = question.lower()
    route = str(risk["recommended_route"]).replace("_", " ").title()
    if any(term in prompt for term in ("action", "recommend", "decision", "sar", "what should")):
        response = (
            f"The explainable model recommends **{route}**. {scalar(brief['recommended_action'])} "
            "This is decision support only; use the **Reviewer Decision** tab for the accountable human decision."
        )
    elif any(term in prompt for term in ("hypothesis", "suspicion")):
        response = scalar(brief["suspicion_hypothesis"])
    else:
        response = f"For **{account_name}**: {scalar(brief['executive_summary'])}"
    return agent_result(
        "Case Brief Agent",
        response,
        ["vw_case_intelligence_brief", "vw_case_risk_summary"],
        "Narrative, hypothesis, or recommended-action support requested",
    )


def orchestrate_case_question(
    question: str,
    case_id: str,
    account_name: str,
    risk: pd.Series,
    signals: pd.DataFrame,
    edges: pd.DataFrame,
    docs: pd.DataFrame,
    intel: pd.DataFrame,
    transactions: pd.DataFrame,
    brief: pd.Series,
) -> dict[str, Any]:
    """Route a case question to bounded specialist agents and synthesize their outputs."""
    prompt = question.lower().strip()
    selected: list[str] = []
    if any(term in prompt for term in ("score", "risk", "92", "critical", "points", "band")):
        selected.append("risk")
    if any(term in prompt for term in ("typology", "typologies", "wage", "payroll", "harvest", "transaction", "spending", "amount", "payment", "geograph", "country", "location", "jurisdiction", "sector")):
        selected.append("typology")
    if any(term in prompt for term in ("network", "connected", "controller", "account control", "shared device", "funnel", "cash-out")):
        selected.append("network")
    if any(term in prompt for term in ("document", "watchlist", "adverse", "media", "evidence", "missing", "gap", "need next")):
        selected.append("evidence")
    if any(term in prompt for term in ("summary", "summarise", "summarize", "brief", "hypothesis", "suspicion", "action", "recommend", "decision", "sar", "what should")):
        selected.append("brief")
    if not selected:
        selected = ["risk", "brief"]

    handlers = {
        "risk": lambda: risk_explanation_agent(case_id, risk),
        "typology": lambda: typology_detection_agent(question, signals, transactions),
        "network": lambda: network_intelligence_agent(edges, signals),
        "evidence": lambda: evidence_review_agent(question, docs, intel, brief),
        "brief": lambda: case_brief_agent(question, account_name, risk, brief),
    }
    contributions = [handlers[name]() for name in dict.fromkeys(selected)]
    agent_names = [item["agent"] for item in contributions]
    sources = list(dict.fromkeys(source for item in contributions for source in item["sources"]))
    sections = "\n\n".join(f"**{item['agent']}**\n\n{item['response']}" for item in contributions)
    answer = (
        f"_Case Orchestrator routed this question to {len(contributions)} specialist agent(s): "
        f"{', '.join(agent_names)}._\n\n{sections}"
    )
    return {
        "answer": answer,
        "sources": sources,
        "agents": agent_names,
        "contributions": contributions,
        "routing_reason": f"Matched governed intent routes: {', '.join(dict.fromkeys(selected))}",
    }


def record_copilot_message(
    case_id: str,
    session_id: str,
    role: str,
    actor: str,
    text: str,
    sources: list[str],
) -> None:
    query(
        f"CALL {DB}.sp_record_copilot_message(?, ?, ?, ?, ?, ?)",
        [case_id, session_id, role, actor, text, ",".join(sources)],
    )


def record_agent_execution(
    request_id: str,
    case_id: str,
    session_id: str,
    agent_name: str,
    routing_reason: str,
    response: str,
    sources: list[str],
) -> None:
    query(
        f"CALL {DB}.sp_record_agent_execution(?, ?, ?, ?, ?, ?, ?)",
        [request_id, case_id, session_id, agent_name, routing_reason, response, ",".join(sources)],
    )


def run_cortex_agent(question: str, case_id: str) -> dict[str, Any]:
    """Run the first-class Snowflake Cortex Agent and normalize its tool trace."""
    request_body = json.dumps(
        {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Active case is {case_id}. {question}",
                        }
                    ],
                }
            ]
        }
    )
    response_frame = query(
        f"SELECT TRY_PARSE_JSON(SNOWFLAKE.CORTEX.DATA_AGENT_RUN('{CORTEX_AGENT}', ?)) AS agent_response",
        [request_body],
    )
    payload = parse_semistructured(response_frame.iloc[0]["agent_response"])
    if not isinstance(payload, dict) or payload.get("status") not in (None, "completed"):
        raise RuntimeError("Cortex Agent did not return a completed response.")

    content = payload.get("content", [])
    answer_parts = [str(item["text"]) for item in content if isinstance(item, dict) and item.get("type") == "text" and item.get("text")]
    tool_names = []
    for item in content:
        if not isinstance(item, dict):
            continue
        tool_use = item.get("tool_use")
        if isinstance(tool_use, dict) and tool_use.get("name"):
            tool_names.append(str(tool_use["name"]))
    if not answer_parts:
        raise RuntimeError("Cortex Agent returned no final text response.")

    tool_agents = {
        "risk_explanation": ("Risk Explanation Agent", ["vw_case_risk_summary"]),
        "typology_detection": ("Typology Detection Agent", ["vw_all_typology_signals"]),
        "network_intelligence": ("Network Intelligence Agent", ["vw_case_network", "device_ip_signals"]),
        "evidence_review": ("Evidence Review Agent", ["document_evidence", "external_watchlist"]),
        "case_brief": ("Case Brief Agent", ["vw_case_intelligence_brief"]),
    }
    contributions = []
    for tool_name in dict.fromkeys(tool_names):
        if tool_name not in tool_agents:
            continue
        agent_name, source_objects = tool_agents[tool_name]
        contributions.append(
            agent_result(
                agent_name,
                f"Snowflake Cortex Agent invoked the `{tool_name}` governed custom tool for {case_id}.",
                source_objects,
                f"Selected by the Cortex Agent orchestration plan as tool `{tool_name}`",
            )
        )
    sources = list(dict.fromkeys(source for item in contributions for source in item["sources"]))
    agent_names = [item["agent"] for item in contributions]
    answer = (
        f"_Snowflake Cortex Agent orchestration completed"
        f"{f' using {', '.join(agent_names)}' if agent_names else ''}._\n\n"
        + "\n\n".join(answer_parts)
    )
    return {
        "answer": answer,
        "sources": sources,
        "agents": agent_names,
        "contributions": contributions,
        "routing_reason": f"First-class Cortex Agent selected tools: {', '.join(dict.fromkeys(tool_names)) or 'none'}",
        "backend": "SNOWFLAKE_CORTEX_AGENT",
    }


@st.cache_data(ttl=30, show_spinner=False)
def load_cases() -> pd.DataFrame:
    return query(
        f"""
        SELECT c.case_id, c.account_id, a.display_name, c.alert_status, c.priority,
               r.risk_score, r.risk_band, r.evidence_strength, r.recommended_route
        FROM {DB}.case_alerts c
        JOIN {DB}.accounts a ON a.account_id = c.account_id
        LEFT JOIN {DB}.vw_case_risk_summary r ON r.case_id = c.case_id
        ORDER BY r.risk_score DESC NULLS LAST
        """
    )


def role_for(node: str, primary: str, edges: pd.DataFrame) -> str:
    if node == primary:
        return "Primary employer"
    incoming = edges[edges["target_account_id"] == node]["relationship_type"].tolist()
    if "CASH_OUT" in incoming or node == "EXTERNAL_CASH":
        return "Cash-out"
    if "CONSOLIDATION" in incoming:
        return "Funnel"
    if "FUNDS_TO_CONTROLLER" in incoming:
        return "Controller"
    if "PAYROLL" in incoming:
        return "Worker"
    return "Connected"


def network_chart(edges: pd.DataFrame, primary: str, names: dict[str, str]) -> go.Figure:
    if edges.empty:
        return go.Figure()
    nodes = sorted(set(edges["source_account_id"]) | set(edges["target_account_id"]))
    ordered = [primary] + [node for node in nodes if node != primary]
    positions: dict[str, tuple[float, float]] = {primary: (0.0, 0.0)}
    others = ordered[1:]
    for index, node in enumerate(others):
        angle = (2 * math.pi * index / max(len(others), 1)) - math.pi / 2
        radius = 1.1 if role_for(node, primary, edges) == "Worker" else 1.55
        positions[node] = (radius * math.cos(angle), radius * math.sin(angle))

    figure = go.Figure()
    edge_colors = {
        "PAYROLL": "#438ca0",
        "FUNDS_TO_CONTROLLER": "#f0a14a",
        "CONSOLIDATION": "#ff697c",
        "CASH_OUT": "#ff5368",
        "SHARED_DEVICE_IP": "#4f6275",
    }
    for row in edges.itertuples():
        x0, y0 = positions[row.source_account_id]
        x1, y1 = positions[row.target_account_id]
        figure.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line={"width": 1.8, "color": edge_colors.get(row.relationship_type, "#557083")},
                hoverinfo="text",
                text=[row.relationship_type, row.relationship_type],
                showlegend=False,
            )
        )

    role_colors = {
        "Primary employer": "#0f766e",
        "Worker": "#2563eb",
        "Controller": "#d97706",
        "Funnel": "#be123c",
        "Cash-out": "#7c3aed",
        "Connected": "#64748b",
    }
    for role, color in role_colors.items():
        role_nodes = [node for node in ordered if role_for(node, primary, edges) == role]
        if not role_nodes:
            continue
        figure.add_trace(
            go.Scatter(
                x=[positions[node][0] for node in role_nodes],
                y=[positions[node][1] for node in role_nodes],
                mode="markers+text",
                name=role,
                text=[names.get(node, node) for node in role_nodes],
                textposition="bottom center",
                textfont={"color": "#243b53", "size": 10},
                hovertext=[f"{node}<br>{role}" for node in role_nodes],
                hoverinfo="text",
                marker={"size": 25 if role == "Primary employer" else 18, "color": color, "line": {"width": 2, "color": "#ffffff"}},
            )
        )
    figure.update_layout(
        height=540,
        margin={"l": 10, "r": 10, "t": 20, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#243b53"},
        xaxis={"visible": False},
        yaxis={"visible": False, "scaleanchor": "x", "scaleratio": 1},
        legend={"orientation": "h", "y": -0.03, "font": {"color": "#526d82"}},
    )
    return figure


try:
    cases = load_cases()
except Exception as exc:
    st.error("Snowflake connection or setup is incomplete.")
    st.code("snow sql -f sql/01_schema.sql\nsnow sql -f sql/02_load_seed_data.sql\n"
            "snow sql -f sql/03_typology_views.sql\nsnow sql -f sql/04_risk_scoring.sql\n"
            "snow sql -f sql/05_case_brief.sql\nsnow sql -f sql/06_decisions_audit.sql")
    st.caption(f"Connection detail: {exc}")
    st.stop()

if cases.empty:
    st.warning("No cases are available. Run the seed and view SQL files.")
    st.stop()

with st.sidebar:
    st.markdown(
        '<div class="brand-mark">◇</div><div class="brand-title">ShadowTraceAI</div>'
        '<div class="brand-copy">AML intelligence workspace<br>Snowflake-native investigation</div>',
        unsafe_allow_html=True,
    )
    st.markdown("#### Case selection")
    labels = {
        row.case_id: f"{row.case_id} · {row.risk_band or 'UNSCORED'} · {row.display_name}"
        for row in cases.itertuples()
    }
    selected_case = st.selectbox("Active case", list(labels), format_func=labels.get)
    st.divider()
    st.caption("Domain-Specific AI Copilot")
    st.caption("Snowflake SQL · Cortex-ready · Human decision gate")
    if st.button("Refresh case data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

case_row = cases[cases["case_id"] == selected_case].iloc[0]
account_id = case_row["account_id"]

st.markdown(
    f'<div class="workspace-header"><div><div class="eyebrow">AML INTELLIGENCE COPILOT</div>'
    f'<div class="hero">Connected evidence. Explainable decisions.</div>'
    f'<div class="subtle">{selected_case} · {case_row["display_name"]} · '
    f'Status {case_row["alert_status"]}</div></div>'
    f'<div class="live-chip">● LIVE SNOWFLAKE DATA</div></div>',
    unsafe_allow_html=True,
)

tabs = st.tabs(
    [
        "Overview",
        "Typology Signals",
        "Account Network",
        "Evidence",
        "Risk Score",
        "Case Intelligence Brief",
        "Reviewer Decision",
        "Audit Trail",
    ]
)

with tabs[0]:
    left, middle, right = st.columns([1.15, 1, 1])
    with left:
        st.markdown(
            f'<div class="risk-card"><div class="eyebrow">COMPOSITE RISK</div>'
            f'<div class="risk-score">{int(case_row["risk_score"])}/100</div>'
            f'<div class="risk-band">{case_row["risk_band"]}</div></div>',
            unsafe_allow_html=True,
        )
    middle.metric("Evidence strength", case_row["evidence_strength"])
    right.metric("Recommended route", case_row["recommended_route"].replace("_", " ").title())
    alert = query(
        f"""SELECT alert_summary, alert_type, created_at, assigned_to
            FROM {DB}.case_alerts WHERE case_id = ?""",
        [selected_case],
    ).iloc[0]
    st.markdown("### Why this case exists")
    st.write(alert["alert_summary"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Alert type", alert["alert_type"].replace("_", " ").title())
    c2.metric("Owner", alert["assigned_to"])
    c3.metric("Opened", pd.to_datetime(alert["created_at"]).strftime("%d %b %Y"))
    st.markdown("### New-transaction processing")
    pipeline_events = query(
        f"""
        SELECT transaction_id, processed_at, processing_status, processor_name,
               risk_score, risk_band, recommended_route, cortex_agent
        FROM {DB}.vw_transaction_processing_status
        WHERE case_id = ?
        ORDER BY processed_at DESC
        LIMIT 10
        """,
        [selected_case],
    )
    p1, p2, p3 = st.columns(3)
    p1.metric("Ingestion pipeline", "STREAM + TASK")
    p2.metric("Cortex Agent", "REGISTERED")
    p3.metric("Processed transactions", len(pipeline_events))
    st.caption(
        "New transaction → TRANSACTIONS_CHANGE_STREAM → PROCESS_NEW_TRANSACTIONS_TASK → "
        "SP_PROCESS_NEW_TRANSACTIONS → live risk views → SHADOWTRACE_AML_ORCHESTRATOR"
    )
    if not pipeline_events.empty:
        with st.expander("Recent processing events"):
            st.dataframe(pipeline_events, use_container_width=True, hide_index=True)

with tabs[1]:
    signals = query(
        f"""SELECT signal_type, signal_detected, risk_points, explanation
            FROM {DB}.vw_all_typology_signals
            WHERE case_id = ? ORDER BY risk_points DESC""",
        [selected_case],
    )
    detected = signals[signals["signal_detected"] == True]  # noqa: E712
    st.markdown(
        "".join(f'<span class="signal-pill">{row.signal_type.replace("_", " ").title()} · +{row.risk_points}</span>'
                for row in detected.itertuples()),
        unsafe_allow_html=True,
    )
    st.dataframe(
        signals.rename(columns=str.title),
        use_container_width=True,
        hide_index=True,
        column_config={"Risk_Points": st.column_config.ProgressColumn("Risk points", min_value=0, max_value=25)},
    )

with tabs[2]:
    edges = query(
        f"""SELECT source_account_id, target_account_id, relationship_type,
                   event_count, total_amount, evidence
            FROM {DB}.vw_case_network WHERE case_id = ?""",
        [selected_case],
    )
    node_ids = sorted(set(edges.get("source_account_id", [])) | set(edges.get("target_account_id", [])))
    if node_ids:
        quoted = ",".join("?" for _ in node_ids)
        accounts = query(
            f"""SELECT account_id, display_name FROM {DB}.accounts WHERE account_id IN ({quoted})""",
            node_ids,
        )
        names = dict(zip(accounts["account_id"], accounts["display_name"]))
        names["EXTERNAL_CASH"] = "External cash-out"
        st.plotly_chart(network_chart(edges, account_id, names), use_container_width=True)
        st.dataframe(edges, use_container_width=True, hide_index=True)
    else:
        st.info("No connected-account edges detected.")

with tabs[3]:
    doc_tab, intel_tab, tx_tab = st.tabs(["Documents", "External intelligence", "Transactions"])
    with doc_tab:
        docs = query(
            f"""SELECT document_id, document_type, file_name, extraction_confidence,
                       risk_indicators, evidence_summary, review_status
                FROM {DB}.document_evidence WHERE case_id = ? ORDER BY uploaded_at""",
            [selected_case],
        )
        docs["risk_indicators"] = docs["risk_indicators"].map(lambda value: ", ".join(parse_semistructured(value)))
        st.dataframe(docs, use_container_width=True, hide_index=True)
    with intel_tab:
        intel = query(
            f"""SELECT source_type, entity_name, risk_level, match_strength, published_date,
                       summary, source_url
                FROM {DB}.external_watchlist
                WHERE matched_account_id = ?
                   OR matched_account_id IN (
                     SELECT source_account_id FROM {DB}.vw_case_network WHERE case_id = ?
                     UNION
                     SELECT target_account_id FROM {DB}.vw_case_network WHERE case_id = ?
                   )
                ORDER BY risk_level DESC, match_strength DESC""",
            [account_id, selected_case, selected_case],
        )
        st.dataframe(
            intel,
            use_container_width=True,
            hide_index=True,
            column_config={"source_url": st.column_config.LinkColumn("Source")},
        )
    with tx_tab:
        tx = query(
            f"""SELECT transaction_ts, from_account_id, to_account_id, amount, currency,
                       transaction_type, channel, counterparty_country, description
                FROM {DB}.transactions
                WHERE from_account_id = ? OR to_account_id = ?
                   OR from_account_id IN (
                     SELECT source_account_id FROM {DB}.vw_case_network WHERE case_id = ?
                   )
                ORDER BY transaction_ts DESC""",
            [account_id, account_id, selected_case],
        )
        st.dataframe(tx, use_container_width=True, hide_index=True)

with tabs[4]:
    risk = query(f"SELECT * FROM {DB}.vw_case_risk_summary WHERE case_id = ?", [selected_case]).iloc[0]
    left, right = st.columns([0.85, 1.4])
    with left:
        st.markdown(
            f'<div class="risk-card"><div class="eyebrow">EXPLAINABLE SCORE</div>'
            f'<div class="risk-score">{int(risk["risk_score"])}/100</div>'
            f'<div class="risk-band">{risk["risk_band"]}</div>'
            f'<div class="subtle">{risk["evidence_strength"]} evidence · {risk["scoring_version"]}</div></div>',
            unsafe_allow_html=True,
        )
    breakdown = parse_semistructured(risk["score_breakdown"])
    if isinstance(breakdown, dict):
        chart_data = pd.DataFrame(
            {"factor": [key.replace("_", " ").title() for key in breakdown], "points": list(breakdown.values())}
        ).sort_values("points")
        right.bar_chart(chart_data, x="factor", y="points", horizontal=True, color="#46d9d1")
    st.markdown("### Top risk factors")
    for factor in parse_semistructured(risk["top_risk_factors"]):
        st.markdown(f"- {factor}")
    st.info("The score recommends a route; it never files a SAR autonomously.")

with tabs[5]:
    brief = query(
        f"""SELECT executive_summary, suspicion_hypothesis, evidence_summary,
                   missing_evidence, recommended_action, audit_timeline, prompt_text
            FROM {DB}.vw_case_intelligence_brief WHERE case_id = ?""",
        [selected_case],
    ).iloc[0]
    for heading, key in [
        ("Executive summary", "executive_summary"),
        ("Suspicion hypothesis", "suspicion_hypothesis"),
        ("Evidence summary", "evidence_summary"),
        ("Missing evidence", "missing_evidence"),
        ("Recommended action", "recommended_action"),
    ]:
        st.markdown(f"#### {heading}")
        st.markdown(f'<div class="brief-card">{scalar(brief[key]).replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    with st.expander("Cortex / Snowflake Intelligence prompt"):
        st.code(brief["prompt_text"])

with tabs[6]:
    st.markdown("### Human decision gate")
    st.caption("A recommendation is not a regulatory filing. A named reviewer must decide and provide rationale.")
    decision_labels = {
        "Escalate to SAR": "ESCALATE_TO_SAR",
        "Request more evidence": "REQUEST_MORE_EVIDENCE",
        "Monitor case": "MONITOR_CASE",
        "Close as false positive": "CLOSE_AS_FALSE_POSITIVE",
    }
    with st.form("review_decision", clear_on_submit=False):
        reviewer = st.text_input("Reviewer name", value="AML Demo Reviewer")
        choice = st.radio("Decision", list(decision_labels), horizontal=True)
        rationale = st.text_area(
            "Rationale",
            value="Multi-source evidence supports escalation for formal SAR assessment.",
            height=110,
        )
        acknowledge = st.checkbox("I confirm this is a human review decision and no SAR is filed automatically.")
        submitted = st.form_submit_button("Record decision", type="primary", use_container_width=True)
    if submitted:
        if not reviewer.strip() or not rationale.strip() or not acknowledge:
            st.error("Reviewer, rationale, and human-decision acknowledgement are required.")
        else:
            try:
                result = query(
                    f"CALL {DB}.sp_record_case_decision(?, ?, ?, ?)",
                    [selected_case, decision_labels[choice], reviewer.strip(), rationale.strip()],
                )
                st.success(f"Decision recorded. Audit ID linkage created ({result.iloc[0, 0]}).")
                st.cache_data.clear()
            except Exception as exc:
                st.error(f"Decision was not saved: {exc}")
    decisions = query(
        f"""SELECT decided_at, reviewer_name, decision, rationale
            FROM {DB}.case_decisions WHERE case_id = ? ORDER BY decided_at DESC""",
        [selected_case],
    )
    if not decisions.empty:
        st.markdown("### Decision history")
        st.dataframe(decisions, use_container_width=True, hide_index=True)

with tabs[7]:
    audit = query(
        f"""SELECT event_ts, actor_type, actor_name, event_type, event_detail, object_type, object_id
            FROM {DB}.audit_events WHERE case_id = ? ORDER BY event_ts DESC""",
        [selected_case],
    )
    st.dataframe(audit, use_container_width=True, hide_index=True)
    st.download_button(
        "Download audit trail (CSV)",
        audit.to_csv(index=False).encode("utf-8"),
        file_name=f"{selected_case.lower()}-audit-trail.csv",
        mime="text/csv",
    )

@st.dialog("Ask ShadowTrace", width="small")
def show_copilot_popup():
    st.caption("First-class Snowflake Cortex Agent + five governed specialist tools. Decisions remain human-controlled.")
    st.caption(f"Active context: **{selected_case}** / {case_row['display_name']}")
    with st.expander("Cortex Agent and tool team"):
        st.markdown(
            "- **SHADOWTRACE_AML_ORCHESTRATOR** - visible Cortex Agent object\n"
            "- **typology_detection** - exploitation patterns\n"
            "- **network_intelligence** - connected accounts and control\n"
            "- **evidence_review** - documents and external intelligence\n"
            "- **risk_explanation** - score, band and factors\n"
            "- **case_brief** - hypothesis, narrative and action"
        )
    with st.expander("Investigator settings"):
        copilot_actor = st.text_input(
            "Investigator name",
            value="AML Demo Reviewer",
            key=f"copilot_actor_{selected_case}",
        )
    notice_key = f"copilot_notice_{selected_case}"
    if notice_key in st.session_state:
        notice_level, notice_text = st.session_state.pop(notice_key)
        if notice_level == "success":
            st.success(notice_text)
        else:
            st.warning(notice_text)

    suggestions = [
        "Give me a full review of risk, typologies, network, evidence, and recommended action.",
        "Why is this case scored 92?",
        "Summarise the wage-harvesting evidence.",
        "Explain the connected account network.",
        "What evidence is missing?",
    ]
    selected_prompt = None
    with st.expander("Suggested questions"):
        for suggestion in suggestions:
            if st.button(
                suggestion,
                key=f"copilot_suggestion_{selected_case}_{suggestion}",
                use_container_width=True,
            ):
                selected_prompt = suggestion

    if "copilot_session_id" not in st.session_state:
        st.session_state.copilot_session_id = str(uuid.uuid4())
    history_key = f"copilot_history_{selected_case}"
    if history_key not in st.session_state:
        stored_messages = query(
            f"""
            SELECT message_role, actor_name, message_text, TO_JSON(source_objects) AS source_objects
            FROM (
              SELECT message_role, actor_name, message_text, source_objects, message_ts
              FROM {DB}.case_copilot_messages
              WHERE case_id = ?
              ORDER BY message_ts DESC
              LIMIT 20
            )
            ORDER BY message_ts
            """,
            [selected_case],
        )
        st.session_state[history_key] = [
            {
                "role": str(row.message_role).lower(),
                "actor": row.actor_name,
                "content": row.message_text,
                "sources": parse_semistructured(row.source_objects) or [],
            }
            for row in stored_messages.itertuples()
        ]

    history = st.session_state[history_key]
    conversation = st.container(height=230, border=False)
    with conversation:
        if not history:
            st.caption("Ask a question or choose a suggestion to begin the case conversation.")
        for message in history:
            role = "assistant" if message["role"] == "assistant" else "user"
            with st.chat_message(role):
                st.markdown(message["content"])
                if message.get("sources"):
                    st.caption("Sources: " + " | ".join(f"`{source}`" for source in message["sources"]))

    st.markdown("**Ask your own question**")
    with st.form(f"copilot_question_form_{selected_case}", clear_on_submit=True):
        question_column, send_column = st.columns([3.5, 1])
        typed_prompt = question_column.text_input(
            "Question",
            placeholder="Ask about the score, evidence or network",
            key=f"copilot_question_input_{selected_case}",
            label_visibility="collapsed",
        )
        question_submitted = send_column.form_submit_button("Send", type="primary", use_container_width=True)

    prompt = selected_prompt or (typed_prompt.strip() if question_submitted and typed_prompt.strip() else None)
    if prompt:
        clean_actor = copilot_actor.strip() or "Unnamed investigator"
        persistence_errors = []
        try:
            record_copilot_message(
                selected_case,
                st.session_state.copilot_session_id,
                "USER",
                clean_actor,
                prompt,
                [],
            )
            user_recorded = True
        except Exception as exc:
            user_recorded = False
            persistence_errors.append(f"Question audit failed: {exc}")

        cortex_fallback_reason = None
        try:
            with st.spinner("Snowflake Cortex Agent is planning and invoking tools..."):
                orchestration = run_cortex_agent(prompt, selected_case)
        except Exception as exc:
            cortex_fallback_reason = str(exc)
            orchestration = orchestrate_case_question(
                prompt,
                selected_case,
                str(case_row["display_name"]),
                risk,
                signals,
                edges,
                docs,
                intel,
                tx,
                brief,
            )
            orchestration["backend"] = "GOVERNED_LOCAL_FALLBACK"
        answer = orchestration["answer"]
        sources = orchestration["sources"]
        request_id = str(uuid.uuid4())
        agent_runs_recorded = 0
        for contribution in orchestration["contributions"]:
            try:
                record_agent_execution(
                    request_id,
                    selected_case,
                    st.session_state.copilot_session_id,
                    contribution["agent"],
                    contribution["routing_reason"],
                    contribution["response"],
                    contribution["sources"],
                )
                agent_runs_recorded += 1
            except Exception as exc:
                persistence_errors.append(f"{contribution['agent']} execution audit failed: {exc}")
        try:
            record_agent_execution(
                request_id,
                selected_case,
                st.session_state.copilot_session_id,
                "Case Orchestrator Agent",
                orchestration["routing_reason"],
                answer,
                sources,
            )
            agent_runs_recorded += 1
        except Exception as exc:
            persistence_errors.append(f"Case Orchestrator execution audit failed: {exc}")
        try:
            record_copilot_message(
                selected_case,
                st.session_state.copilot_session_id,
                "ASSISTANT",
                "ShadowTraceAI Investigation Copilot",
                answer,
                sources,
            )
            assistant_recorded = True
        except Exception as exc:
            assistant_recorded = False
            persistence_errors.append(f"Response audit failed: {exc}")

        history.extend(
            [
                {"role": "user", "actor": clean_actor, "content": prompt, "sources": []},
                {"role": "assistant", "actor": "ShadowTraceAI Investigation Copilot", "content": answer, "sources": sources},
            ]
        )
        expected_agent_runs = len(orchestration["contributions"]) + 1
        if user_recorded and assistant_recorded and agent_runs_recorded == expected_agent_runs:
            if cortex_fallback_reason:
                st.session_state[notice_key] = (
                    "warning",
                    "The first-class Cortex Agent was unavailable for this turn, so the governed local "
                    f"orchestrator completed it instead. Detail: {cortex_fallback_reason}",
                )
            else:
                st.session_state[notice_key] = (
                    "success",
                    f"Snowflake Cortex Agent and {len(orchestration['contributions'])} selected tool(s) "
                    "completed. Executions and messages were recorded in Snowflake.",
                )
        else:
            st.session_state[notice_key] = ("warning", " ".join(persistence_errors))
        st.rerun(scope="fragment")


if st.button("Ask ShadowTrace", key="chat_launcher"):
    show_copilot_popup()
