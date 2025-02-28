import streamlit as st
import requests
import time

# Define the APIs to monitor
APIS = {
    "Region 1 - API 1": {
        "url": "https://api.region1.example.com/health",
        "short_name": "R1-API1",
    },
    "Region 1 - API 2": {
        "url": "https://api.region1.example.com/health",
        "short_name": "R1-API2",
    },
    "Region 2 - API 1": {
        "url": "https://api.region2.example.com/health",
        "short_name": "R2-API1",
    },
    "Region 2 - API 2": {
        "url": "https://api.region2.example.com/health",
        "short_name": "R2-API2",
    },
}

# Function to check API health
def check_api_health(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return "Healthy", None
        else:
            return "Unhealthy", f"Status Code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return "Error", str(e)

# Function to display logs
def display_logs(logs):
    st.write("### Logs")
    for log in logs:
        st.write(log)

# Main Streamlit app
def main():
    st.title("API Health Check Dashboard")

    # Initialize session state for logs
    if "logs" not in st.session_state:
        st.session_state.logs = []

    # Check API health
    for api_name, api_info in APIS.items():
        status, error = check_api_health(api_info["url"])
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "api_name": api_name,
            "short_name": api_info["short_name"],
            "url": api_info["url"],
            "status": status,
            "error": error,
        }
        st.session_state.logs.append(log_entry)

    # Display report
    st.write("### API Health Report")
    report_data = []
    for log in st.session_state.logs[-len(APIS):]:  # Show only the latest check
        report_data.append([
            log["short_name"],
            log["url"],
            log["status"],
            log["error"] if log["error"] else "No Error",
        ])
    st.table(report_data)

    # Dropdown to view logs
    st.write("### View Logs")
    log_options = [log["timestamp"] for log in st.session_state.logs]
    selected_log = st.selectbox("Select a log entry", log_options)

    # Display selected log
    if selected_log:
        selected_log_entry = next(log for log in st.session_state.logs if log["timestamp"] == selected_log)
        st.write(f"**API Name:** {selected_log_entry['api_name']}")
        st.write(f"**Short Name:** {selected_log_entry['short_name']}")
        st.write(f"**URL:** {selected_log_entry['url']}")
        st.write(f"**Status:** {selected_log_entry['status']}")
        st.write(f"**Error:** {selected_log_entry['error']}")

# Run the app
if __name__ == "__main__":
    main()