"""
app.py — single-file Streamlit UI for Sourcr.

Enter an investment thesis, run the SourcingFlow, and view the resulting
Opportunity Briefs and the pipeline confidence chart.

Run from the project root:
    streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the src/ layout importable when Streamlit runs this file directly.
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

from sourcr.crews.reporting_crew.render import render_brief_markdown
from sourcr.main import OUTPUT_DIR, SourcingFlow
from sourcr.models import EXAMPLE_THESIS, IndustryFocus, InvestmentThesis, OwnershipType

st.set_page_config(page_title="Sourcr", page_icon="🧭", layout="wide")
st.title("🧭 Sourcr — M&A target sourcing")
st.caption(
    "Enter an investment thesis; a multi-agent pipeline finds candidate "
    "companies, verifies them, surfaces decision-makers, and writes briefs."
)

# --------------------------------------------------------------------------- #
# Thesis form (pre-filled with the example thesis)                            #
# --------------------------------------------------------------------------- #
_industries = list(IndustryFocus)
_ownerships = list(OwnershipType)

with st.form("thesis"):
    c1, c2 = st.columns(2)
    with c1:
        industry = st.selectbox(
            "Industry", _industries, format_func=lambda x: x.value,
            index=_industries.index(EXAMPLE_THESIS.industry),
        )
        sub_sector = st.text_input("Sub-sector", EXAMPLE_THESIS.sub_sector)
        geography = st.text_input("Geography", EXAMPLE_THESIS.geography)
        ownership = st.selectbox(
            "Ownership preference", _ownerships, format_func=lambda x: x.value,
            index=_ownerships.index(EXAMPLE_THESIS.ownership_preference),
        )
    with c2:
        rev_min = st.number_input(
            "Revenue min (USD)", min_value=0, step=1_000_000,
            value=int(EXAMPLE_THESIS.revenue_min or 0),
        )
        rev_max = st.number_input(
            "Revenue max (USD)", min_value=0, step=1_000_000,
            value=int(EXAMPLE_THESIS.revenue_max or 0),
        )
        emp_min = st.number_input(
            "Employees min", min_value=0, step=10,
            value=int(EXAMPLE_THESIS.employee_min or 0),
        )
        emp_max = st.number_input(
            "Employees max", min_value=0, step=10,
            value=int(EXAMPLE_THESIS.employee_max or 0),
        )
    notes = st.text_area("Notes / extra screening criteria", EXAMPLE_THESIS.notes or "")
    max_candidates = st.slider("Max candidates", 1, 8, 3)
    submitted = st.form_submit_button("Run pipeline 🚀")

# --------------------------------------------------------------------------- #
# Run the pipeline + render results                                           #
# --------------------------------------------------------------------------- #
if submitted:
    thesis = InvestmentThesis(
        industry=industry,
        sub_sector=sub_sector,
        geography=geography,
        revenue_min=rev_min or None,
        revenue_max=rev_max or None,
        employee_min=emp_min or None,
        employee_max=emp_max or None,
        ownership_preference=ownership,
        notes=notes or None,
    )

    with st.spinner("Running pipeline — research → (verify ∥ contacts) → briefs… this can take a minute."):
        try:
            flow = SourcingFlow()
            flow.kickoff(
                inputs={"thesis": thesis.model_dump(), "max_candidates": int(max_candidates)}
            )
            briefs = flow.state.briefs
        except Exception as exc:  # surface failures in the UI rather than the console
            st.error(f"Pipeline failed: {exc}")
            st.stop()

    st.success(f"Done — {len(briefs)} opportunity brief(s).")

    chart = OUTPUT_DIR / "pipeline_confidence.png"
    if briefs and chart.exists():
        st.subheader("Pipeline confidence")
        st.image(str(chart))

    badge = {"HIGH": "🟢", "MEDIUM": "🟡", "LOW": "🟠", "NEEDS_REVIEW": "🔴"}
    for b in briefs:
        label = f"{badge.get(b.overall_confidence.value, '')} {b.company_name} — {b.overall_confidence.value}"
        with st.expander(label, expanded=True):
            st.markdown(render_brief_markdown(b))

    if not briefs:
        st.info("No briefs produced — try widening the thesis or raising the candidate count.")
