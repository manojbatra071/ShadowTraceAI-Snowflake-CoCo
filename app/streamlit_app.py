"""ShadowTraceAI — Snowflake-native AML investigation copilot."""

from __future__ import annotations

import json
import math
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
      :root { --ink:#e8eef5; --muted:#8ea0b5; --cyan:#46d9d1; --red:#ff5368; }
      .stApp { background:
        radial-gradient(circle at 80% 0%, rgba(18,94,106,.22), transparent 28rem),
        linear-gradient(150deg, #071019 0%, #0a1420 56%, #0e1825 100%); }
      [data-testid="stSidebar"] { background:#08111b; border-right:1px solid #1e3446; }
      h1,h2,h3 { letter-spacing:-.025em; }
      .eyebrow { color:#46d9d1; font-size:.74rem; font-weight:700; letter-spacing:.14em; }
      .hero { font-size:2.05rem; font-weight:750; line-height:1.08; color:#f4f8fb; margin:.2rem 0; }
      .subtle { color:#8ea0b5; font-size:.92rem; }
      .risk-card { border:1px solid #63313d; background:linear-gradient(135deg,#241721,#121722);
        border-radius:14px; padding:1.1rem 1.2rem; }
      .risk-score { color:#ff5368; font-size:2.3rem; font-weight:800; }
      .risk-band { color:#ff8998; font-weight:700; letter-spacing:.09em; }
      .brief-card { border-left:3px solid #46d9d1; background:#0c1925;
        border-radius:0 12px 12px 0; padding:1rem 1.15rem; margin:.5rem 0 1rem; }
      .signal-pill { display:inline-block; margin:.2rem .35rem .2rem 0; padding:.28rem .55rem;
        border:1px solid #2f6570; border-radius:99px; color:#8fe8e2; font-size:.78rem; }
      div[data-testid="stMetric"] { background:#0c1925; border:1px solid #193045;
        padding:.75rem; border-radius:12px; }
      div[data-testid="stDataFrame"] { border:1px solid #193045; border-radius:10px; }
      .stButton>button, .stFormSubmitButton>button { border-radius:9px; font-weight:700; }
    </style>
    """,
    unsafe_allow_html=True,
)

DB = "SHADOWTRACE_AI.AML"


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
        "Primary employer": "#46d9d1",
        "Worker": "#5fa8ff",
        "Controller": "#f0a14a",
        "Funnel": "#ff697c",
        "Cash-out": "#9c6cff",
        "Connected": "#8ea0b5",
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
                textfont={"color": "#dbe7f0", "size": 10},
                hovertext=[f"{node}<br>{role}" for node in role_nodes],
                hoverinfo="text",
                marker={"size": 25 if role == "Primary employer" else 18, "color": color, "line": {"width": 2, "color": "#09131d"}},
            )
        )
    figure.update_layout(
        height=540,
        margin={"l": 10, "r": 10, "t": 20, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False},
        yaxis={"visible": False, "scaleanchor": "x", "scaleratio": 1},
        legend={"orientation": "h", "y": -0.03, "font": {"color": "#b9c8d6"}},
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
    st.markdown('<div class="eyebrow">SHADOWTRACEAI</div>', unsafe_allow_html=True)
    st.markdown("### Investigation workspace")
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

st.markdown('<div class="eyebrow">AML INTELLIGENCE COPILOT</div>', unsafe_allow_html=True)
st.markdown('<div class="hero">Connected evidence. Explainable decisions.</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="subtle">{selected_case} · {case_row["display_name"]} · '
    f'Status {case_row["alert_status"]}</div>',
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

