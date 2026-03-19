from __future__ import annotations

import os
import time
from typing import Any

import pandas as pd
import requests
import streamlit as st


API_URL = os.getenv("API_URL", "http://localhost:8000")
DEFAULT_QUESTION = "What care gaps exist for this patient?"
SUGGESTED_QUERIES = [
    "What care gaps exist for this patient?",
    "What documentation risks need review?",
    "What evidence supports these gaps?",
    "Summarize this patient's quality and revenue risks.",
    "What follow-up actions should the care team review?",
]


st.set_page_config(page_title="Clinical Gap Intelligence", layout="wide")

st.markdown(
    """
    <style>
      :root {
        --navy: #15324f;
        --teal: #0f766e;
        --teal-soft: #e6f5f2;
        --blue-soft: #eef6fb;
        --line: #d8e2ec;
        --text: #1f2937;
        --muted: #64748b;
        --panel: #ffffff;
        --surface: #f7fafc;
      }
      .block-container {
        padding-top: 1.35rem;
        padding-bottom: 2rem;
        max-width: 1320px;
      }
      [data-testid="stSidebar"] {
        background: var(--surface);
        border-right: 1px solid var(--line);
      }
      .app-header {
        padding: 1.45rem 1.6rem;
        border: 1px solid var(--line);
        border-radius: 10px;
        background: linear-gradient(135deg, #ffffff 0%, #f1f8fb 100%);
        margin-bottom: 1.2rem;
      }
      .eyebrow {
        color: var(--teal);
        font-size: 0.78rem;
        font-weight: 760;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
      }
      .app-title {
        color: var(--navy);
        font-size: 2.05rem;
        line-height: 1.15;
        font-weight: 780;
        margin: 0;
      }
      .app-subtitle {
        color: var(--muted);
        font-size: 1.02rem;
        margin-top: 0.45rem;
        max-width: 840px;
      }
      .section-title {
        color: var(--navy);
        font-size: 1.08rem;
        font-weight: 760;
        margin: 1rem 0 0.55rem 0;
      }
      .answer-panel {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 1.15rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
      }
      .kpi-card {
        border: 1px solid var(--line);
        border-radius: 10px;
        background: #ffffff;
        padding: 1rem;
        min-height: 112px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
      }
      .kpi-label {
        color: var(--muted);
        font-size: 0.76rem;
        font-weight: 760;
        text-transform: uppercase;
        letter-spacing: 0.04em;
      }
      .kpi-value {
        color: var(--navy);
        font-size: 1.85rem;
        font-weight: 780;
        margin-top: 0.25rem;
      }
      .kpi-note {
        color: var(--muted);
        font-size: 0.82rem;
        margin-top: 0.25rem;
      }
      .finding-card {
        border: 1px solid var(--line);
        border-left: 4px solid var(--teal);
        border-radius: 8px;
        background: #ffffff;
        padding: 1rem;
        margin-bottom: 0.8rem;
      }
      .finding-title {
        color: var(--navy);
        font-weight: 760;
        font-size: 1rem;
        margin-bottom: 0.35rem;
      }
      .finding-meta {
        color: var(--muted);
        font-size: 0.8rem;
        margin-top: 0.55rem;
      }
      .empty-state {
        border: 1px dashed #bfd0df;
        border-radius: 10px;
        background: #f8fbfd;
        color: var(--muted);
        padding: 1rem;
      }
      .timeline-box {
        border: 1px solid var(--line);
        border-radius: 10px;
        background: var(--blue-soft);
        color: var(--text);
        padding: 1rem;
      }
      .footer {
        color: var(--muted);
        font-size: 0.8rem;
        border-top: 1px solid var(--line);
        margin-top: 1.5rem;
        padding-top: 0.8rem;
      }
      div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 0.85rem 1rem;
      }
      div[data-testid="stMetricLabel"] p {
        color: var(--muted);
        font-weight: 760;
      }
      div[data-testid="stMetricValue"] {
        color: var(--navy);
      }
      .stButton > button {
        border-radius: 8px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_get(path: str) -> dict[str, Any] | list[dict[str, Any]]:
    response = requests.get(f"{API_URL}{path}", timeout=10)
    response.raise_for_status()
    return response.json()


def api_post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(f"{API_URL}{path}", json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=10)
def get_patients() -> list[dict[str, Any]]:
    return api_get("/patients")  # type: ignore[return-value]


@st.cache_data(ttl=5)
def get_live_overview() -> dict[str, Any]:
    return api_get("/live/overview")  # type: ignore[return-value]


def render_header() -> None:
    st.markdown(
        """
        <div class="app-header">
          <div class="eyebrow">Clinical Gap Intelligence</div>
          <h1 class="app-title">Clinical Gap Intelligence</h1>
          <div class="app-subtitle">
            AI Assistant for patient-specific care gap, documentation, and quality risk analysis
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi(label: str, value: str | int, note: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty(message: str) -> None:
    st.markdown(f'<div class="empty-state">{message}</div>', unsafe_allow_html=True)


def render_gap_card(gap: dict[str, Any]) -> None:
    evidence_count = len(gap.get("supporting_evidence", []))
    st.markdown(
        f"""
        <div class="finding-card">
          <div class="finding-title">{gap.get("title", "Finding")}</div>
          <div>{gap.get("reason", "No rationale available.")}</div>
          <div class="finding-meta">
            Priority: {gap.get("priority", "n/a").title()} &nbsp;|&nbsp;
            Confidence: {gap.get("confidence", "n/a").title()} &nbsp;|&nbsp;
            Window: {gap.get("time_window", "n/a")} &nbsp;|&nbsp;
            Evidence: {evidence_count}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_gap_list(items: list[dict[str, Any]], empty_message: str) -> None:
    if not items:
        render_empty(empty_message)
        return
    priority_order = {"high": 0, "medium": 1, "low": 2}
    for gap in sorted(items, key=lambda item: priority_order.get(item.get("priority", "low"), 3)):
        render_gap_card(gap)


def render_evidence(items: list[dict[str, Any]]) -> None:
    if not items:
        render_empty("No supporting evidence is available for the selected question.")
        return
    for item in items:
        st.markdown(
            f"**{item.get('source_type', 'Evidence').title()}** "
            f"`{item.get('date') or 'No date'}`"
        )
        st.write(item.get("text", ""))
        st.caption(item.get("id", ""))
        st.divider()


def evidence_dataframe(items: list[dict[str, Any]]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(columns=["source_type", "date", "text"])
    return pd.DataFrame(items)[[column for column in ["source_type", "date", "text", "score"] if column in items[0]]]


if "question_text" not in st.session_state:
    st.session_state.question_text = DEFAULT_QUESTION

render_header()

try:
    overview = get_live_overview()
    patients = get_patients()
except requests.RequestException:
    st.error(
        "Clinical Gap Intelligence is currently unable to connect to the analysis API. "
        "Confirm the backend service is running and refresh the page."
    )
    st.stop()

with st.sidebar:
    st.markdown("### Patient Context")
    data_source = st.selectbox("Data source", ["Synthea"], index=0)
    condition_filter = st.text_input("Condition contains", "")
    min_age = st.slider("Minimum age", 0, 100, 0)
    st.divider()
    st.markdown("### System Status")
    st.caption(f"Records: {overview.get('patient_count', len(patients))}")
    st.caption(f"Evidence index: {'Ready' if overview.get('index_ready') else 'Pending'}")
    st.caption(f"Data source: {overview.get('data_source', 'unknown')}")
    st.divider()
    auto_refresh = st.toggle("Refresh status", value=False)

filtered_patients = [
    patient
    for patient in patients
    if (patient.get("age") or 0) >= min_age
    and (
        not condition_filter
        or condition_filter.lower() in " ".join(patient.get("conditions", [])).lower()
    )
]

if not filtered_patients:
    render_empty("No patients match the selected filters. Adjust the patient context controls.")
    st.stop()

patient_labels = {
    f"{patient['name']} | Age {patient.get('age') or 'unknown'} | {', '.join(patient.get('conditions', [])[:2]) or 'No listed conditions'}": patient["id"]
    for patient in filtered_patients
}

result = st.session_state.get("last_answer")

status_cols = st.columns(4)
with status_cols[0]:
    render_kpi("Care Gaps", len(result["care_gaps"]) if result else "-", "Open items" if result else "Run analysis")
with status_cols[1]:
    render_kpi(
        "Documentation Gaps",
        len(result["documentation_gaps"]) if result else "-",
        "Review findings" if result else "Run analysis",
    )
with status_cols[2]:
    render_kpi(
        "Risk Items",
        len(result["revenue_quality_risks"]) if result else "-",
        "Quality and revenue" if result else "Run analysis",
    )
with status_cols[3]:
    render_kpi(
        "Evidence Sources",
        len(result["supporting_evidence"]) if result else "-",
        "Retrieved snippets" if result else "Run analysis",
    )

st.markdown('<div class="section-title">Ask a Clinical Question</div>', unsafe_allow_html=True)
input_cols = st.columns([0.42, 0.58])
with input_cols[0]:
    patient_label = st.selectbox("Patient", list(patient_labels))
with input_cols[1]:
    question = st.text_area("Question", key="question_text", height=92)

chip_cols = st.columns(5)
for index, suggested_query in enumerate(SUGGESTED_QUERIES):
    with chip_cols[index]:
        if st.button(suggested_query, use_container_width=True):
            st.session_state.question_text = suggested_query
            st.rerun()

run = st.button("Analyze", type="primary", use_container_width=True)
if run:
    with st.status("Analyzing patient context...", expanded=True) as status:
        st.write("Retrieving patient evidence")
        st.write("Evaluating clinical rules")
        st.write("Preparing assistant answer")
        try:
            st.session_state["last_answer"] = api_post(
                "/ask",
                {
                    "patient_id": patient_labels[patient_label],
                    "question": st.session_state.question_text or DEFAULT_QUESTION,
                    "data_source": data_source.lower(),
                },
            )
            get_live_overview.clear()
            status.update(label="Analysis complete", state="complete", expanded=False)
        except requests.RequestException:
            status.update(label="Analysis unavailable", state="error", expanded=True)
            st.error("Analysis could not be completed. Please confirm the API service is available and retry.")

if not result:
    render_empty("Select a patient, ask a clinical question, and run Analyze to view the assistant answer.")
else:
    tabs = st.tabs([
        "AI Answer",
        "Care Gaps",
        "Documentation",
        "Revenue & Quality",
        "Evidence",
        "Timeline",
        "Audit Trail",
    ])

    with tabs[0]:
        st.markdown('<div class="section-title">AI Assistant Answer</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="answer-panel">{result["answer"]}</div>', unsafe_allow_html=True)
        if result.get("model_status") == "fallback":
            st.info("AI Assistant summary unavailable. Configure model credentials to enable generated summaries.")
        st.markdown('<div class="section-title">Recommended Actions</div>', unsafe_allow_html=True)
        if result["recommended_actions"]:
            for action in result["recommended_actions"]:
                st.write(f"- {action}")
        else:
            render_empty("No recommended actions are available for this analysis.")
    with tabs[1]:
        render_gap_list(result["care_gaps"], "No care gaps were identified for the available evidence.")
    with tabs[2]:
        render_gap_list(result["documentation_gaps"], "No documentation gaps were identified for the available evidence.")
    with tabs[3]:
        render_gap_list(
            result["revenue_quality_risks"],
            "No revenue or quality risk items were identified for the available evidence.",
        )
    with tabs[4]:
        render_evidence(result["supporting_evidence"])
        evidence_frame = evidence_dataframe(result["supporting_evidence"])
        if not evidence_frame.empty:
            with st.expander("Evidence Table"):
                st.dataframe(evidence_frame, use_container_width=True, hide_index=True)
    with tabs[5]:
        st.markdown('<div class="section-title">Patient Timeline</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="timeline-box">{result["timeline_summary"]}</div>', unsafe_allow_html=True)
    with tabs[6]:
        st.markdown('<div class="section-title">Audit Trail</div>', unsafe_allow_html=True)
        audit = result.get("audit", {})
        if audit:
            st.json(audit)
        else:
            render_empty("No audit metadata is available for this request.")

st.markdown(
    '<div class="footer">Synthetic data environment for clinical AI engineering demonstration.</div>',
    unsafe_allow_html=True,
)

if auto_refresh:
    time.sleep(10)
    st.rerun()
