import streamlit as st
import pandas as pd
import json

# Sample JSON data
json_data = '''
[
    {"id": 1, "name": "Alice", "status": "active"},
    {"id": 2, "name": "Bob", "status": "inactive"},
    {"id": 3, "name": "Charlie", "status": "active"}
]
'''

# Parse JSON data
data = json.loads(json_data)

# Convert JSON data to DataFrame
df = pd.DataFrame(data)

# Display title and description
st.title("JSON Data Dashboard")
st.write("This dashboard shows JSON data in a table with status indicators.")

# Function to set status indicators
def status_indicator(status):
    if status == "active":
        return "🟢 Active"
    elif status == "inactive":
        return "🔴 Inactive"
    else:
        return "⚪ Unknown"

# Apply status indicators to DataFrame
df['status_indicator'] = df['status'].apply(status_indicator)

# Display the DataFrame
st.dataframe(df)

# Display JSON data
st.subheader("Raw JSON Data")
st.json(data)
