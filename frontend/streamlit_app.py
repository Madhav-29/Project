from __future__ import annotations

import os
import time

import requests
import streamlit as st


API_URL = os.getenv("API_URL", "http://localhost:8000")
DEFAULT_QUESTION = "Identify care gaps, documentation gaps, and revenue risks"


st.set_page_config(page_title="Clinical AI Platform", layout="centered")
st.title("Clinical AI Platform")
st.caption("Live synthetic-care gap dashboard. AI-assisted output requires clinical validation.")


def api_get(path: str) -> dict | list[dict]:
    response = requests.get(f"{API_URL}{path}", timeout=10)
    response.raise_for_status()
    return response.json()


def api_post(path: str, payload: dict) -> dict:
    response = requests.post(f"{API_URL}{path}", json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=10)
def get_patients() -> list[dict]:
    return api_get("/patients")  # type: ignore[return-value]


@st.cache_data(ttl=5)
def get_live_overview() -> dict:
    return api_get("/live/overview")  # type: ignore[return-value]


try:
    overview = get_live_overview()
    patients = get_patients()
except requests.RequestException as exc:
    st.error(f"Backend is not reachable at {API_URL}. Start FastAPI and refresh. Details: {exc}")
    st.stop()

top = st.columns(4)
top[0].metric("Status", overview["status"].upper())
top[1].metric("Patients", overview["patient_count"])
top[2].metric("Analyses", overview["analysis_count"])
top[3].metric("Index", "Ready" if overview["index_ready"] else "Build")

with st.sidebar:
    st.subheader("Live Controls")
    live_mode = st.toggle("Auto refresh", value=False)
    use_llm = st.toggle("Use LLM", value=False)
    st.caption(f"Data source: {overview['data_source']}")

if not patients:
    st.warning("No synthetic patients are loaded.")
    st.stop()

patient_labels = {
    f"{patient['name']} | age {patient.get('age') or 'unknown'} | {', '.join(patient.get('conditions', [])[:2])}": patient["id"]
    for patient in patients
}

patient_label = st.selectbox("Patient", list(patient_labels))
question = st.text_input("Question", DEFAULT_QUESTION)

run = st.button("Run live analysis", type="primary", use_container_width=True)
if run:
    with st.spinner("Reviewing timeline, rules, and retrieved evidence..."):
        st.session_state["last_result"] = api_post(
            "/analyze-patient",
            {
                "patient_id": patient_labels[patient_label],
                "question": question or DEFAULT_QUESTION,
                "use_llm": use_llm,
            },
        )
        get_live_overview.clear()

result = st.session_state.get("last_result")
if result:
    st.subheader("Summary")
    st.write(result["patient_summary"])

    counts = st.columns(3)
    counts[0].metric("Care Gaps", len(result["care_gaps"]))
    counts[1].metric("Documentation", len(result["documentation_gaps"]))
    counts[2].metric("Quality Risks", len(result["revenue_quality_risks"]))

    st.subheader("Highest Priority Findings")
    findings = result["care_gaps"] + result["documentation_gaps"] + result["revenue_quality_risks"]
    for gap in findings[:6]:
        st.markdown(f"**{gap['title']}**")
        st.write(gap["reason"])
        st.caption(f"{gap['type']} | priority {gap['priority']} | confidence {gap['confidence']}")
        st.divider()

    with st.expander("Evidence"):
        for item in result["retrieved_context"][:8]:
            st.write(f"**{item['source_type']} - {item.get('date') or 'unknown date'}**")
            st.write(item["text"])

    with st.expander("AI synthesis"):
        st.write(result["llm_synthesis"])
else:
    last = overview.get("last_analysis")
    if last:
        st.info(
            f"Last analysis: {last['patient_name']} at {last['ran_at']} "
            f"({last['care_gaps']} care gaps, {last['documentation_gaps']} documentation gaps)."
        )
    else:
        st.info("Select a synthetic patient and run a live analysis.")

if live_mode:
    time.sleep(10)
    st.rerun()
