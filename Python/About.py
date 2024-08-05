import streamlit as st
import pandas as pd
import calendar
from datetime import datetime

# Set page configuration
st.set_page_config(page_title="SRE Runbook and On-Call Calendar", layout="wide")

# Title
st.title("SRE Runbook and On-Call Calendar")

# Tabs
tab1, tab2, tab3 = st.tabs(["Runbook", "On-Call Calendar", "About"])

# Runbook Section
with tab1:
    st.header("SRE Runbook")
    
    runbook_data = {
        "Incident": ["Service Down", "High Latency", "Error Rate Increase"],
        "Procedure": [
            "1. Check logs\n2. Restart service\n3. Notify stakeholders",
            "1. Investigate network issues\n2. Check service health\n3. Optimize database queries",
            "1. Check error logs\n2. Identify root cause\n3. Deploy fix"
        ],
        "Contact": ["John Doe", "Jane Smith", "Alice Johnson"]
    }

    df_runbook = pd.DataFrame(runbook_data)
    st.table(df_runbook)

    # Add a new runbook entry
    st.subheader("Add New Runbook Entry")
    incident = st.text_input("Incident")
    procedure = st.text_area("Procedure")
    contact = st.text_input("Contact")

    if st.button("Add Entry"):
        new_entry = {"Incident": incident, "Procedure": procedure, "Contact": contact}
        df_runbook = df_runbook.append(new_entry, ignore_index=True)
        st.success("New runbook entry added successfully!")
        st.table(df_runbook)

# On-Call Calendar Section
with tab2:
    st.header("On-Call Calendar")

    # Display current month calendar with on-call schedule
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    cal = calendar.HTMLCalendar(calendar.SUNDAY)
    on_call_schedule = {
        "1": "John Doe",
        "2": "Jane Smith",
        "3": "Alice Johnson",
        "4": "Bob Brown"
    }

    st.markdown(f"### {calendar.month_name[current_month]} {current_year}")
    cal_html = cal.formatmonth(current_year, current_month)
    for day, user in on_call_schedule.items():
        cal_html = cal_html.replace(f'>{day}<', f'>{day} ({user})<')
    
    st.markdown(cal_html, unsafe_allow_html=True)

    # Add a new on-call schedule
    st.subheader("Add On-Call Schedule")
    day = st.selectbox("Day", range(1, 32))
    user = st.selectbox("User", ["John Doe", "Jane Smith", "Alice Johnson", "Bob Brown"])

    if st.button("Add Schedule"):
        on_call_schedule[str(day)] = user
        st.success("On-call schedule updated successfully!")
        cal_html = cal.formatmonth(current_year, current_month)
        for day, user in on_call_schedule.items():
            cal_html = cal_html.replace(f'>{day}<', f'>{day} ({user})<')
        st.markdown(cal_html, unsafe_allow_html=True)

# About Section
with tab3:
    st.header("About")

    about_html = """
    <div style="text-align: center;">
        <h2>About This Application</h2>
        <p>This application is designed to help SRE teams manage their runbooks and on-call schedules effectively.</p>
        <h3>Features</h3>
        <ul style="text-align: left;">
            <li>Document and manage SRE runbook procedures</li>
            <li>Track and update on-call schedules</li>
            <li>Interactive and user-friendly interface</li>
        </ul>
        <h3>Contact</h3>
        <p>For more information, contact us at <a href="mailto:support@example.com">support@example.com</a>.</p>
    </div>
    """

    st.markdown(about_html, unsafe_allow_html=True)
