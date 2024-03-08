import requests

# Replace these variables with your GitLab details
GITLAB_URL = "https://gitlab.com"
PRIVATE_TOKEN = "YOUR_PERSONAL_ACCESS_TOKEN"

def get_all_projects():
    url = f"{GITLAB_URL}/api/v4/projects"
    params = {"private_token": PRIVATE_TOKEN}
    response = requests.get(url, params=params)
    return response.json()

def get_maintainers(project_id):
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/members"
    params = {"private_token": PRIVATE_TOKEN}
    response = requests.get(url, params=params)
    return response.json()

def main():
    projects = get_all_projects()

    for project in projects:
        project_id = project["id"]
        maintainers = get_maintainers(project_id)

        if not maintainers:
            print(f"Repository without maintainer: {project['name_with_namespace']}")

if __name__ == "__main__":
    main()
