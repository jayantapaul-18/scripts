import requests

# Replace with your GitLab personal access token
GITLAB_API_TOKEN = 'your_access_token_here'
# Replace with your GitLab project ID
PROJECT_ID = 'your_project_id_here'
# Replace with your GitLab instance URL
GITLAB_INSTANCE_URL = 'https://gitlab.example.com'

def get_last_activity(project_id, private_token, instance_url):
    url = f"{instance_url}/api/v4/projects/{project_id}/events"
    headers = {
        "PRIVATE-TOKEN": private_token
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        events = response.json()
        if events:
            # Assuming the first event is the most recent one
            last_event = events[0]
            return last_event
        else:
            return "No activity found for this project."
    else:
        return f"Failed to fetch data: {response.status_code}, {response.text}"

last_activity = get_last_activity(PROJECT_ID, GITLAB_API_TOKEN, GITLAB_INSTANCE_URL)
print(last_activity)
