#!/bin/bash

# Script to find GitLab users with inactive SAML links from Terraform plan.json
# and send notification via Teams webhook

# Check if input file is provided
if [ -z "$1" ]; then
  echo "Error: No input file provided"
  echo "Usage: $0 <terraform_plan.json>"
  exit 1
fi

PLAN_FILE="$1"
TEAMS_WEBHOOK_URL="${TEAMS_WEBHOOK_URL:-}" # Can be set as environment variable

# Check if jq is installed
if ! command -v jq &> /dev/null; then
  echo "Error: jq is not installed. Please install jq to proceed."
  exit 1
fi

# Check if curl is installed
if ! command -v curl &> /dev/null; then
  echo "Error: curl is not installed. Please install curl to proceed."
  exit 1
fi

# Extract GitLab users with provider = 'saml' and status indicating 400 error
echo "Processing Terraform plan file: $PLAN_FILE"

# Find users with inactive SAML links (assuming 400 response is indicated in the plan)
INACTIVE_USERS=$(jq -r '
  .resource_changes[] | 
  select(.type == "gitlab_user" and .change.after.provider == "saml") |
  select(.change.after.extern_uid == "400" or .change.after.extern_uid == null) |
  .change.after.username
' "$PLAN_FILE" 2>/dev/null)

if [ -z "$INACTIVE_USERS" ]; then
  echo "No users with inactive SAML links found."
  exit 0
fi

# Format the message
MESSAGE="## GitLab Users with Inactive SAML Links\n\n"
MESSAGE+="The following GitLab users have inactive SAML links (400 response):\n\n"
MESSAGE+="```\n"
MESSAGE+="$INACTIVE_USERS\n"
MESSAGE+="```\n\n"
MESSAGE+="Please investigate these user accounts."

echo -e "Found users with inactive SAML links:\n$INACTIVE_USERS"

# Send to Teams if webhook URL is provided
if [ -n "$TEAMS_WEBHOOK_URL" ]; then
  echo "Sending notification to Teams webhook..."
  
  # Create JSON payload for Teams
  JSON_PAYLOAD=$(jq -n \
    --arg msg "$MESSAGE" \
    '{
      "title": "GitLab SAML Link Alert",
      "text": $msg,
      "themeColor": "FF0000"
    }')
  
  # Send to Teams
  curl -X POST -H "Content-Type: application/json" \
    -d "$JSON_PAYLOAD" \
    "$TEAMS_WEBHOOK_URL"
  
  if [ $? -eq 0 ]; then
    echo "Notification sent successfully to Teams."
  else
    echo "Error sending notification to Teams."
    exit 1
  fi
else
  echo "TEAMS_WEBHOOK_URL not set. Skipping Teams notification."
fi

exit 0


# Run in GitLab CI/CD:
# Add this to your .gitlab-ci.yml file:
# check_saml_links:
#   stage: test
#   image: alpine:latest
#   before_script:
#     - apk add --no-cache jq curl
#   script:
#     - ./check_saml_users.sh plan.json
#   variables:
#     TEAMS_WEBHOOK_URL: "https://your-teams-webhook-url"
#   artifacts:
#     paths:
#       - plan.json
