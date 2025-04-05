#!/bin/bash

# --- Configuration ---
# Set to "short" for short SHA in link text, "full" for full SHA
LINK_TEXT_FORMAT="short"
# Set desired output format: "markdown", "html", or "text" (shows SHA and URL)
OUTPUT_FORMAT="markdown"
# Default remote name
REMOTE_NAME="origin"

# --- Function: get_commit_link ---
# Usage: get_commit_link <commit_sha_or_ref> [remote_name]
# Output: Formatted link or plain SHA if linking fails.
get_commit_link() {
    local ref="${1:-HEAD}" # Default to HEAD if no argument provided
    local remote_name="${2:-$REMOTE_NAME}"
    local full_sha
    local short_sha
    local remote_url
    local base_web_url
    local commit_url
    local link_text
    local output=""

    # Attempt to get SHAs
    full_sha=$(git rev-parse "$ref" 2>/dev/null)
    short_sha=$(git rev-parse --short "$ref" 2>/dev/null)

    if [ -z "$full_sha" ]; then
        echo "Error: Could not resolve ref '$ref'" >&2
        echo "$ref" # Output the original ref as fallback
        return 1
    fi

    # Determine link text
    if [ "$LINK_TEXT_FORMAT" = "short" ]; then
        link_text="$short_sha"
    else
        link_text="$full_sha"
    fi

    # Attempt to get remote URL
    remote_url=$(git remote get-url "$remote_name" 2>/dev/null)

    if [ -n "$remote_url" ]; then
        # Try to convert remote URL to base web URL for commits
        # This handles common GitHub, GitLab, Bitbucket formats (SSH and HTTPS)
        # Removes .git suffix, converts git@host:path -> https://host/path
        base_web_url=$(echo "$remote_url" | sed \
            -e 's|^git@\(.*\):|https://\1/|' \
            -e 's|\.git$||' \
            -e 's|/$||' # Remove trailing slash if any
        )

        # Determine commit path based on host (add more hosts as needed)
        if echo "$base_web_url" | grep -qE 'github\.com|gitlab\.com'; then
            commit_url="${base_web_url}/commit/${full_sha}"
        elif echo "$base_web_url" | grep -q 'bitbucket\.org'; then
             commit_url="${base_web_url}/commits/${full_sha}"
        # Add other platform handlers here if needed
        # elif echo "$base_web_url" | grep -q 'dev.azure.com'; then
        #     # Azure DevOps URL structure can be more complex, might need more parsing
        #     # Example: https://dev.azure.com/{org}/{project}/_git/{repo}/commit/{sha}
        #     # This simple sed won't be enough here usually.
        #     : # Placeholder - requires more specific logic
        else
             # Default or unknown provider - attempt a common path, might fail
             commit_url="${base_web_url}/commit/${full_sha}"
             # Or set commit_url="" to disable linking for unknown hosts
             # commit_url=""
        fi
    else
        # No remote URL found, cannot link
        commit_url=""
    fi

    # Format the output
    if [ -n "$commit_url" ]; then
        case "$OUTPUT_FORMAT" in
            markdown)
                output="[${link_text}](${commit_url})"
                ;;
            html)
                output="<a href=\"${commit_url}\">${link_text}</a>"
                ;;
            text)
                output="${link_text} (${commit_url})"
                ;;
            *) # Default to plain text if format unknown
                output="$link_text"
                ;;
        esac
    else
        # Fallback to plain SHA if URL couldn't be determined
        output="$link_text"
    fi

    echo "$output"
}

# --- Example Usage in your RC file generation ---

# Get the link for the current HEAD commit
current_commit_link=$(get_commit_link HEAD)

# Get the link for a specific tag
tag_commit_link=$(get_commit_link "v1.2.3")

# Get the link for a specific full SHA (useful if processing logs)
specific_sha="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
specific_commit_link=$(get_commit_link "$specific_sha")


# Example of generating a line in an RC file:
echo "##################################################"
echo "# Release Candidate Information"
echo "# Generated: $(date)"
echo "##################################################"
echo ""
echo "Version: 1.5.0-rc1"
echo "Commit: ${current_commit_link}"
echo "Based on tag: ${tag_commit_link}"
# Add other relevant information...
echo "Related commit: ${specific_commit_link}"

