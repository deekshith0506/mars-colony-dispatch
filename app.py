import json
import streamlit as st
from dispatch_engine import solve_dispatch

st.set_page_config(page_title="AlgoX Mars Colony Dispatch", page_icon="🚀", layout="wide")

st.title("🚀 AlgoX: Mars Colony Emergency Response")
st.caption("Crews: E (STRUCTURAL) | M (MEDICAL) | L (LIFE_SUPPORT) — Non-matching crews take 2× duration")

col1, col2 = st.columns(2)

with col1:
    st.header("1. Input Module (.CSV)")
    uploaded_file = st.file_uploader("Upload AlgoX Incident CSV", type=["csv"])

    st.markdown("**Expected AlgoX CSV Format:**")
    st.code("id,arrival,category,severity,duration\n1,0,STRUCTURAL,6,4\n2,1,MEDICAL,9,3\n3,2,STRUCTURAL,3,5", language="csv")

with col2:
    st.header("2. Output Module (submission.json)")

    if uploaded_file is not None:
        csv_content = uploaded_file.getvalue().decode("utf-8")

        submission_data, safety_score, validation_errors = solve_dispatch(csv_content)
        json_string = json.dumps(submission_data, indent=2)

        if not validation_errors:
            st.success(f"✅ Judge Validation Passed (All 7 Rules) | Colony Safety Score: **{safety_score}**")
        else:
            st.error("❌ Validation Errors Detected:")
            for err in validation_errors:
                st.write(f"- {err}")

        st.download_button(
            label="⬇️ Download submission.json",
            data=json_string,
            file_name="submission.json",
            mime="application/json"
        )

        st.json(submission_data)
    else:
        st.info("Upload sample1.csv, sample2.csv, sample3.csv, or the final dataset on the left.")
