import json
import streamlit as st
from dispatch_engine import process_csv_to_json

st.set_page_config(page_title="Mars Colony Dispatch", page_icon="🚀", layout="wide")

st.title("🚀 Mars Colony Emergency Dispatch System")
st.caption("3 Response Crews Active: Crew Alpha | Crew Beta | Crew Gamma")

col1, col2 = st.columns(2)

# --- MODULE 1: CSV INPUT ---
with col1:
    st.header("1. Input Module (.CSV)")
    uploaded_file = st.file_uploader("Upload Colony Incident Log", type=["csv"])
    
    st.markdown("**Expected CSV Columns:**")
    st.code("incident_id,timestamp_mins,type,severity,duration_mins\nINC-001,10,Hull Crack,1,45", language="csv")

# --- MODULE 2: JSON OUTPUT ---
with col2:
    st.header("2. Output Module (.JSON)")
    
    if uploaded_file is not None:
        csv_content = uploaded_file.getvalue().decode("utf-8")
        
        result_data = process_csv_to_json(csv_content)
        json_string = json.dumps(result_data, indent=2)
        
        st.success(f"Dispatched {result_data['total_incidents_resolved']} incidents across 3 crews.")
        
        st.download_button(
            label="⬇️ Download Dispatch Schedule (.JSON)",
            data=json_string,
            file_name="mars_dispatch_output.json",
            mime="application/json"
        )
        
        st.json(result_data)
    else:
        st.info("Upload a CSV file on the left to generate the JSON dispatch log.")
