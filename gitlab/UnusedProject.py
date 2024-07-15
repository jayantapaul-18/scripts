import json
import requests
from datetime import datetime, timedelta

GITLAB_API_TOKEN = "your_gitlab_personal_access_token"
GITLAB_API_URL = "https://gitlab.example.com/api/v4"
UNUSED_PERIOD_DAYS = 180

def get_last_commit_date(project_id):
    url = f"{GITLAB_API_URL}/projects/{project_id}/repository/commits"
    headers = {"PRIVATE-TOKEN": GITLAB_API_TOKEN}
    response = requests.get(url, headers=headers)
    commits = response.json()
    if commits:
        return datetime.strptime(commits[0]['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
    return None

def main():
    with open('projects.json', 'r') as f:
        projects = json.load(f)

    unused_projects = []
    cutoff_date = datetime.now() - timedelta(days=UNUSED_PERIOD_DAYS)
    
    for project in projects:
        last_commit_date = get_last_commit_date(project['id'])
        if last_commit_date is None or last_commit_date < cutoff_date:
            unused_projects.append(project)

    with open('unused_projects.json', 'w') as f:
        json.dump(unused_projects, f, indent=2)

if __name__ == "__main__":
    main()
