#!/bin/bash

# Define the plan file name
PLAN_FILE="plan.tfplan"
PLAN_JSON="plan.json"

# Run terraform plan and output to a plan file
echo "Running Terraform plan..."
terraform plan -out=$PLAN_FILE -no-color

# Check if the plan command succeeded
if [ $? -ne 0 ]; then
    echo "Terraform plan failed."
    exit 1
fi

# Convert the plan file to JSON format for easier parsing
echo "Converting plan output to JSON..."
terraform show -json $PLAN_FILE > $PLAN_JSON

# Analyze the JSON output for resource changes
echo "Analyzing plan for resource changes..."
echo "------------------------------------"

# Count the number of each type of change
create_count=$(jq '[.resource_changes[] | select(.change.actions[0] == "create")] | length' $PLAN_JSON)
update_count=$(jq '[.resource_changes[] | select(.change.actions[0] == "update")] | length' $PLAN_JSON)
delete_count=$(jq '[.resource_changes[] | select(.change.actions[0] == "delete")] | length' $PLAN_JSON)

# List resources by type and action
echo "Summary of planned changes:"
echo "Resources to be created: $create_count"
echo "Resources to be updated: $update_count"
echo "Resources to be deleted: $delete_count"

echo
echo "Detailed list of resources by action type:"
echo "------------------------------------------"

echo "Resources to be created:"
jq -r '.resource_changes[] | select(.change.actions[0] == "create") | .address' $PLAN_JSON

echo
echo "Resources to be updated:"
jq -r '.resource_changes[] | select(.change.actions[0] == "update") | .address' $PLAN_JSON

echo
echo "Resources to be deleted:"
jq -r '.resource_changes[] | select(.change.actions[0] == "delete") | .address' $PLAN_JSON

# Clean up plan file and JSON output (optional)
rm -f $PLAN_FILE $PLAN_JSON
