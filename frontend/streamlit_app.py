from __future__ import annotations

import os

import pandas as pd
import requests
import streamlit as st


API_URL = os.getenv("API_URL", "http://localhost:8000")


st.set_page_config(page_title="Clinical Gap Intelligence", layout="wide")
st.title("Clinical Gap Intelligence Platform")
st.caption("Synthetic-data clinical AI prototype. Outputs are AI-assisted and require clinical validation.")


@st.cache_data(ttl=30)
def get_patients() -> list[dict]:
    response = requests.get(f"{API_URL}/patients", timeout=10)
    response.raise_for_status()
    return response.json()


patients = get_patients()
if not patients:
    st.warning("No synthetic patients loaded.")
    st.stop()

with st.sidebar:
    st.header("Patient Cohort")
    condition_filter = st.text_input("Filter by condition")
    min_age = st.slider("Minimum age", 0, 100, 0)

filtered = [
    patient for patient in patients
    if (patient.get("age") or 0) >= min_age
    and (not condition_filter or condition_filter.lower() in " ".join(patient.get("conditions", [])).lower())
]

patient_options = {f"{p['name']} ({p['id']})": p["id"] for p in filtered}
if not patient_options:
    st.info("No patients match the current filters.")
    st.stop()

selected_label = st.selectbox("Select patient", list(patient_options))
patient_id = patient_options[selected_label]
question = st.text_area("Question", "Identify care gaps, documentation gaps, and revenue risks")
use_llm = st.toggle("Use configured LLM synthesis", value=False)

if st.button("Run Analysis", type="primary"):
    with st.spinner("Analyzing synthetic evidence..."):
        response = requests.post(
            f"{API_URL}/analyze-patient",
            json={"patient_id": patient_id, "question": question, "use_llm": use_llm},
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()

    st.subheader("Patient Summary")
    st.write(result["patient_summary"])

    tab_gaps, tab_evidence, tab_timeline = st.tabs(["Gaps & Risks", "Evidence", "Timeline"])

    with tab_gaps:
        cols = st.columns(3)
        sections = [
            ("Care Gaps", "care_gaps"),
            ("Documentation Gaps", "documentation_gaps"),
            ("Revenue/Quality Risks", "revenue_quality_risks"),
        ]
        for col, (title, key) in zip(cols, sections):
            with col:
                st.markdown(f"### {title}")
                for gap in result[key]:
                    st.info(f"**{gap['title']}**\n\n{gap['reason']}\n\nPriority: {gap['priority']} | Confidence: {gap['confidence']}")
                if not result[key]:
                    st.success("No configured findings.")

        st.markdown("### Recommended Actions")
        for action in result["recommended_actions"]:
            st.write(f"- {action}")

        st.markdown("### LLM Synthesis")
        st.write(result["llm_synthesis"])

    with tab_evidence:
        for item in result["retrieved_context"]:
            st.write(f"**{item['source_type']} | {item.get('date') or 'unknown date'}**")
            st.caption(item["id"])
            st.write(item["text"])
            st.divider()

    with tab_timeline:
        st.dataframe(pd.DataFrame(result["raw_timeline"]).drop(columns=["raw"], errors="ignore"), use_container_width=True)
