import requests
import json

# List of APIs to check
api_urls = [
    {"name": "API 1", "url": "https://api1.example.com/health"},
    {"name": "API 2", "url": "https://api2.example.com/health"},
    {"name": "API 3", "url": "https://api3.example.com/health"}
]

# Function to perform health check
def check_api(api):
    try:
        response = requests.get(api['url'])
        status = "up" if response.status_code == 200 else "down"
    except requests.RequestException:
        status = "down"
    return {"name": api['name'], "status": status}

# Perform health checks and collect results
results = [check_api(api) for api in api_urls]

# Convert results to JSON
results_json = json.dumps(results, indent=4)

# Print the JSON results
print(results_json)

# Optionally, write the results to a file
with open("health_check_results.json", "w") as f:
    f.write(results_json)
