To build a Python script that reads the NCLM certificate rotation Terraform state file, extracts all the fields, and generates dashboards using Streamlit, you can follow these steps:

Steps:

	1.	Read the Terraform state file: Terraform stores its state in JSON format, so we can parse it using Python’s json module.
	2.	Extract the necessary fields: Once we load the state file, we’ll extract the fields related to the NCOM certificate rotation.
	3.	Display the data in a dashboard using Streamlit: Streamlit can help us build interactive dashboards where we visualize the relevant data.

Python Script:

import json
import streamlit as st
import pandas as pd

# Function to read the Terraform state file
def read_terraform_state(file_path):
    try:
        with open(file_path, 'r') as file:
            state_data = json.load(file)
        return state_data
    except Exception as e:
        st.error(f"Error reading Terraform state file: {e}")
        return None

# Function to extract relevant certificate rotation data
def extract_certificate_data(state_data):
    resources = state_data.get('resources', [])
    cert_data = []

    for resource in resources:
        # Filter by the resource type related to certificate rotation (adjust based on your Terraform state structure)
        if resource['type'] == 'aws_acm_certificate':  # Example: AWS ACM certificate
            for instance in resource['instances']:
                cert_info = {
                    'id': instance.get('attributes', {}).get('id'),
                    'domain_name': instance.get('attributes', {}).get('domain_name'),
                    'status': instance.get('attributes', {}).get('status'),
                    'not_before': instance.get('attributes', {}).get('not_before'),
                    'not_after': instance.get('attributes', {}).get('not_after'),
                    'renewal_eligibility': instance.get('attributes', {}).get('renewal_eligibility'),
                }
                cert_data.append(cert_info)
    
    return cert_data

# Function to create a Streamlit dashboard
def create_dashboard(cert_data):
    if cert_data:
        # Convert the certificate data to a Pandas DataFrame for easy manipulation
        df = pd.DataFrame(cert_data)

        # Create a dashboard in Streamlit
        st.title("NCOM Certificate Rotation Dashboard")

        # Display data table
        st.subheader("Certificate Data Table")
        st.dataframe(df)

        # Example: Add a status filter
        status_filter = st.selectbox("Filter by Certificate Status", options=['All'] + df['status'].unique().tolist())
        if status_filter != 'All':
            df_filtered = df[df['status'] == status_filter]
        else:
            df_filtered = df

        st.subheader(f"Filtered Certificates by Status: {status_filter}")
        st.dataframe(df_filtered)

        # Additional visualizations (if needed)
        st.subheader("Certificates Expiration Overview")
        st.bar_chart(df_filtered.set_index('domain_name')['not_after'].astype('datetime64[ns]'])

    else:
        st.write("No certificate data available to display.")

# Main function to run the Streamlit app
def main():
    st.sidebar.title("Terraform State File Reader")
    
    # Upload Terraform state file
    file_upload = st.sidebar.file_uploader("Upload Terraform State File (.json)", type="json")
    
    if file_upload:
        state_data = read_terraform_state(file_upload)

        if state_data:
            cert_data = extract_certificate_data(state_data)
            create_dashboard(cert_data)

if __name__ == "__main__":
    main()

Explanation:

	1.	read_terraform_state: Reads the Terraform state file from JSON format.
	2.	extract_certificate_data: Extracts certificate-specific data (such as domain name, certificate status, expiration dates, etc.). This is tailored based on how AWS ACM certificates are stored in the Terraform state file.
	3.	create_dashboard: Generates the Streamlit dashboard, displaying a table with the certificate data and providing filtering options for certificate status. There’s also an expiration overview using a bar chart.
	4.	Streamlit Interface: Users can upload the state file directly via Streamlit’s file uploader.

How to run:

	1.	Save this script as app.py.
	2.	Install the required libraries:

pip install streamlit pandas


	3.	Run the Streamlit app:

streamlit run app.py



This script will display a dashboard with all certificate data, allow you to filter by status, and provide a bar chart for certificate expiration dates. You can expand the dashboard by adding more visualizations and data points depending on the fields in your Terraform state file.