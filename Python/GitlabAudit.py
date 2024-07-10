import gitlab
import datetime

# Configuration
GITLAB_URL = 'https://gitlab.com'  # Replace with your GitLab instance URL
PRIVATE_TOKEN = 'your_private_token'  # Replace with your private token
PROJECT_ID = 123456  # Replace with your project ID
DAYS_THRESHOLD = 30  # Define the threshold for recent activity (in days)

# Connect to GitLab
gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN)
project = gl.projects.get(PROJECT_ID)

# Helper function to check if activity is recent
def is_recent(activity_date, threshold_days):
    activity_datetime = datetime.datetime.strptime(activity_date, '%Y-%m-%dT%H:%M:%S.%fZ')
    return (datetime.datetime.utcnow() - activity_datetime).days <= threshold_days

# Check recent commits
commits = project.commits.list(all=True)
recent_commits = [commit for commit in commits if is_recent(commit.created_at, DAYS_THRESHOLD)]

# Check recent issues
issues = project.issues.list(all=True)
recent_issues = [issue for issue in issues if is_recent(issue.created_at, DAYS_THRESHOLD)]

# Check recent merge requests
merge_requests = project.mergerequests.list(all=True)
recent_mrs = [mr for mr in merge_requests if is_recent(mr.created_at, DAYS_THRESHOLD)]

# Output the results
print(f"Recent commits in the last {DAYS_THRESHOLD} days: {len(recent_commits)}")
print(f"Recent issues in the last {DAYS_THRESHOLD} days: {len(recent_issues)}")
print(f"Recent merge requests in the last {DAYS_THRESHOLD} days: {len(recent_mrs)}")

# Conclusion
if recent_commits or recent_issues or recent_mrs:
    print("The project is active.")
else:
    print("The project is inactive. Consider taking actions to prevent it from being archived.")
