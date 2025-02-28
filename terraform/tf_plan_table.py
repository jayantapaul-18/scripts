import json
import pandas as pd

# Load the Terraform plan JSON
with open("tfplan.json", "r") as file:
    tfplan = json.load(file)

# Initialize a list to store resource changes
resource_changes = []

# Parse resource changes
for change in tfplan.get("resource_changes", []):
    resource_address = change["address"]
    action = "".join(change["change"]["actions"])  # Combine actions (e.g., "create", "delete", "update")
    resource_type = change["type"]
    provider_name = change["provider_name"]
    
    # Append the resource change to the list
    resource_changes.append({
        "Resource Address": resource_address,
        "Resource Type": resource_type,
        "Provider": provider_name,
        "Action": action
    })

# Create a DataFrame from the list of resource changes
df = pd.DataFrame(resource_changes)

# Print the table
print("Terraform Plan Changes:")
print(df.to_string(index=False))
df.to_csv("terraform_changes.csv", index=False)
from tabulate import tabulate

# Print the table using tabulate
print("Terraform Plan Changes:")
print(tabulate(df, headers="keys", tablefmt="pretty"))


