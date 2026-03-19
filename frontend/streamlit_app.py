from __future__ import annotations

import os
import time
from typing import Any

import pandas as pd
import requests
import streamlit as st


API_URL = os.getenv("API_URL", "http://localhost:8000")
DEFAULT_QUESTION = "Identify care gaps, documentation gaps, and revenue risks"


st.set_page_config(page_title="Clinical Gap Intelligence", layout="wide")

st.markdown(
    """
    <style>
      :root {
        --navy: #16324f;
        --teal: #0f766e;
        --sky: #e8f3fb;
        --line: #d9e2ec;
        --text: #1f2937;
        --muted: #64748b;
        --panel: #ffffff;
      }
      .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1280px;
      }
      [data-testid="stSidebar"] {
        background: #f7fafc;
        border-right: 1px solid var(--line);
      }
      .app-header {
        padding: 1.5rem 1.75rem;
        border: 1px solid var(--line);
        border-radius: 10px;
        background: linear-gradient(135deg, #ffffff 0%, #f1f8fb 100%);
        margin-bottom: 1.25rem;
      }
      .eyebrow {
        color: var(--teal);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
      }
      .app-title {
        color: var(--navy);
        font-size: 2rem;
        line-height: 1.15;
        font-weight: 760;
        margin: 0;
      }
      .app-subtitle {
        color: var(--muted);
        font-size: 1.02rem;
        margin-top: 0.45rem;
        max-width: 760px;
      }
      .section-title {
        color: var(--navy);
        font-size: 1.05rem;
        font-weight: 740;
        margin: 1rem 0 0.55rem 0;
      }
      .panel {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 1rem;
      }
      .kpi-card {
        border: 1px solid var(--line);
        border-radius: 10px;
        background: #ffffff;
        padding: 1rem 1rem 0.85rem 1rem;
        min-height: 112px;
      }
      .kpi-label {
        color: var(--muted);
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
      }
      .kpi-value {
        color: var(--navy);
        font-size: 1.75rem;
        font-weight: 760;
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
        font-weight: 730;
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
        font-weight: 700;
      }
      div[data-testid="stMetricValue"] {
        color: var(--navy);
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
    response = requests.post(f"{API_URL}{path}", json=payload, timeout=90)
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
          <h1 class="app-title">AI Assistant for Clinical Gap Intelligence</h1>
          <div class="app-subtitle">
            Review care gaps, documentation findings, quality risk signals, evidence summaries,
            and patient timeline context from structured clinical data.
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
        render_empty("No retrieved evidence is available for the selected question.")
        return
    for item in items:
        st.markdown(
            f"**{item.get('source_type', 'Evidence').title()}** "
            f"`{item.get('date') or 'No date'}`"
        )
        st.write(item.get("text", ""))
        st.caption(item.get("id", ""))
        st.divider()


def timeline_dataframe(events: list[dict[str, Any]]) -> pd.DataFrame:
    if not events:
        return pd.DataFrame(columns=["date", "type", "label", "text"])
    frame = pd.DataFrame(events).drop(columns=["raw"], errors="ignore")
    columns = [column for column in ["date", "type", "label", "text", "id"] if column in frame.columns]
    return frame[columns]


render_header()

try:
    overview = get_live_overview()
    patients = get_patients()
except requests.RequestException as exc:
    st.error(
        "The Clinical Gap Intelligence API is not reachable. "
        f"Confirm the FastAPI backend is running and that API_URL is set correctly. Current API_URL: {API_URL}."
    )
    with st.expander("Connection details"):
        st.write(str(exc))
    st.stop()

with st.sidebar:
    st.markdown("### Analysis Controls")
    st.caption("Clinical Gap Intelligence")
    use_llm = st.toggle("AI Assistant", value=False)
    live_mode = st.toggle("Auto refresh", value=False)
    st.divider()
    st.markdown("### Cohort Filters")
    condition_filter = st.text_input("Condition contains", "")
    min_age = st.slider("Minimum age", 0, 100, 0)
    st.divider()
    st.markdown("### System")
    st.caption(f"API: {API_URL}")
    st.caption(f"Data source: {overview.get('data_source', 'unknown')}")
    st.caption("For demonstration with synthetic data only.")

filtered_patients = [
    patient
    for patient in patients
    if (patient.get("age") or 0) >= min_age
    and (
        not condition_filter
        or condition_filter.lower() in " ".join(patient.get("conditions", [])).lower()
    )
]

status_cols = st.columns(4)
with status_cols[0]:
    render_kpi("Patients", overview.get("patient_count", len(patients)), "Available records")
with status_cols[1]:
    render_kpi("Analyses", overview.get("analysis_count", 0), "Session activity")
with status_cols[2]:
    render_kpi("Evidence Index", "Ready" if overview.get("index_ready") else "Pending", "Retrieval status")
with status_cols[3]:
    render_kpi("Assistant", "On" if use_llm else "Off", "LLM synthesis")

if not filtered_patients:
    render_empty("No patients match the selected filters. Adjust the cohort filters in the sidebar.")
    st.stop()

patient_labels = {
    f"{patient['name']} | Age {patient.get('age') or 'unknown'} | {', '.join(patient.get('conditions', [])[:2]) or 'No listed conditions'}": patient["id"]
    for patient in filtered_patients
}

st.markdown('<div class="section-title">Care Gap Analysis</div>', unsafe_allow_html=True)
control_cols = st.columns([0.44, 0.56])
with control_cols[0]:
    patient_label = st.selectbox("Patient", list(patient_labels))
with control_cols[1]:
    question = st.text_input("Clinical question", DEFAULT_QUESTION)

run = st.button("Run Analysis", type="primary", use_container_width=True)
if run:
    with st.status("Running clinical gap analysis...", expanded=True) as status:
        st.write("Building patient context")
        st.write("Retrieving supporting evidence")
        st.write("Applying care gap and documentation rules")
        if use_llm:
            st.write("Preparing AI Assistant synthesis")
        try:
            st.session_state["last_result"] = api_post(
                "/analyze-patient",
                {
                    "patient_id": patient_labels[patient_label],
                    "question": question or DEFAULT_QUESTION,
                    "use_llm": use_llm,
                },
            )
            get_live_overview.clear()
            status.update(label="Analysis complete", state="complete", expanded=False)
        except requests.RequestException as exc:
            status.update(label="Analysis failed", state="error", expanded=True)
            st.error("Analysis could not be completed. Confirm the backend is running and retry.")
            with st.expander("Error details"):
                st.write(str(exc))

result = st.session_state.get("last_result")

if not result:
    last = overview.get("last_analysis")
    if last:
        st.info(
            f"Most recent analysis: {last['patient_name']} "
            f"({last['care_gaps']} care gaps, {last['documentation_gaps']} documentation findings)."
        )
    else:
        render_empty("Select a patient and run an analysis to view findings, evidence, and timeline context.")
else:
    st.markdown('<div class="section-title">Patient Summary</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="panel">{result["patient_summary"]}</div>', unsafe_allow_html=True)

    finding_cols = st.columns(3)
    finding_cols[0].metric("Care Gaps", len(result["care_gaps"]))
    finding_cols[1].metric("Documentation Review", len(result["documentation_gaps"]))
    finding_cols[2].metric("Revenue & Quality Risk", len(result["revenue_quality_risks"]))

    tabs = st.tabs([
        "Care Gaps",
        "Documentation Gaps",
        "Revenue Risks",
        "Evidence Summary",
        "Patient Timeline",
        "AI Assistant",
    ])

    with tabs[0]:
        render_gap_list(result["care_gaps"], "No care gaps were identified for the available evidence.")
    with tabs[1]:
        render_gap_list(
            result["documentation_gaps"],
            "No documentation gaps were identified for the available evidence.",
        )
    with tabs[2]:
        render_gap_list(
            result["revenue_quality_risks"],
            "No revenue or quality risk signals were identified for the available evidence.",
        )
    with tabs[3]:
        render_evidence(result["retrieved_context"])
    with tabs[4]:
        frame = timeline_dataframe(result["raw_timeline"])
        if frame.empty:
            render_empty("No timeline events are available for this patient.")
        else:
            st.dataframe(frame, use_container_width=True, hide_index=True)
    with tabs[5]:
        st.markdown('<div class="section-title">Evidence-Grounded Synthesis</div>', unsafe_allow_html=True)
        st.write(result["llm_synthesis"])
        st.markdown('<div class="section-title">Recommended Actions</div>', unsafe_allow_html=True)
        if result["recommended_actions"]:
            for action in result["recommended_actions"]:
                st.write(f"- {action}")
        else:
            render_empty("No recommended actions are available.")

st.markdown('<div class="footer">For demonstration with synthetic data only.</div>', unsafe_allow_html=True)

if live_mode:
    time.sleep(10)
    st.rerun()
