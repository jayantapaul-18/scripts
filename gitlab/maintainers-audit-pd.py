import pandas as pd
import requests

# Replace 'YOUR_ACCESS_TOKEN' with your GitLab personal access token
access_token = 'YOUR_ACCESS_TOKEN'

# Function to get project information
def get_project_info(project_id):
    url = f'https://gitlab.com/api/v4/projects/{project_id}'
    headers = {'PRIVATE-TOKEN': access_token}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        project_info = response.json()
        return {
            "Project ID": project_info['id'],
            "Project Name": project_info['name'],
            "Project Description": project_info['description'],
            # Add more project details as needed
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching project info for Project ID {project_id}: {e}")
        return None

# Function to get maintainers information for a project
def get_maintainers_info(project_id):
    url = f'https://gitlab.com/api/v4/projects/{project_id}/maintainers'
    headers = {'PRIVATE-TOKEN': access_token}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        maintainers = response.json()
        maintainers_data = [{
            "Maintainer ID": m['id'],
            "Maintainer Name": m['name'],
            "Maintainer Username": m['username'],
            # Add more maintainer details as needed
        } for m in maintainers]
        return maintainers_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching maintainers info for Project ID {project_id}: {e}")
        return []

# List of GitLab project IDs
gitlab_projects = [1, 2, 3]  # Replace with your actual project IDs

# Initialize empty lists for project and maintainers data
project_data_list = []
maintainers_data_list = []

# Loop through GitLab projects
for project_id in gitlab_projects:
    project_info = get_project_info(project_id)
    maintainers_info = get_maintainers_info(project_id)

    # Append project info to project data list
    if project_info:
        project_data_list.append(project_info)

    # Append maintainers info to maintainers data list
    maintainers_data_list.extend(maintainers_info)

# Create DataFrames from the lists
project_df = pd.DataFrame(project_data_list)
maintainers_df = pd.DataFrame(maintainers_data_list)

# Print the DataFrames
print("GitLab Projects Information:")
print(project_df)

print("\nGitLab Maintainers Information:")
print(maintainers_df)
