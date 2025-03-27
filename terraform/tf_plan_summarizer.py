#!/usr/bin/env python3

import json
import argparse
import sys
import os
from collections import defaultdict

def summarize_tf_plan(plan_json_path, include_no_op=False):
    """
    Reads a Terraform JSON plan file and generates a summary report identifying
    creates, updates, destroys, and replacements.

    Args:
        plan_json_path (str): Path to the Terraform plan JSON file.
        include_no_op (bool): If True, include 'no-op' and 'read' resources
                              in the detailed lists.

    Returns:
        str: A formatted summary report string.
             Returns None if a critical error occurs during processing.
    """
    try:
        # Validate input file path
        if not os.path.exists(plan_json_path):
            raise FileNotFoundError(f"Error: Plan JSON file not found at '{plan_json_path}'")
        if not os.path.isfile(plan_json_path):
             raise IsADirectoryError(f"Error: '{plan_json_path}' is a directory, not a file.")

        # Read and parse the JSON file
        with open(plan_json_path, 'r', encoding='utf-8') as f:
            try:
                plan_data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error: Failed to parse JSON in '{plan_json_path}'. Invalid syntax.", file=sys.stderr)
                print(f"Details: {e}", file=sys.stderr)
                return None # Indicate failure

    except (FileNotFoundError, IsADirectoryError) as e:
        print(e, file=sys.stderr)
        return None
    except IOError as e:
        print(f"Error reading file '{plan_json_path}': {e}", file=sys.stderr)
        return None
    except Exception as e:
         print(f"An unexpected error occurred during file handling: {e}", file=sys.stderr)
         return None

    # --- Basic Plan Information ---
    tf_version = plan_data.get('terraform_version', 'N/A')
    format_version = plan_data.get('format_version', 'N/A')
    resource_changes = plan_data.get('resource_changes', []) # Gracefully handle if missing

    # --- Analyze Resource Changes ---
    # Use defaultdict for easy list appending and int counting
    changes_by_action = defaultdict(list)
    action_counts = defaultdict(int)

    if not resource_changes and 'resource_changes' in plan_data:
        # The key exists but the list is empty - genuine no changes plan
         pass # Continue to generate the report, which will show 0 changes
    elif 'resource_changes' not in plan_data:
        # Key might be missing in older formats or malformed JSON
        print("Warning: 'resource_changes' key not found in the JSON plan. Unable to analyze resources.", file=sys.stderr)
        # Still try to generate a minimal report
    else:
        # Process the resource changes
        for change in resource_changes:
            actions = change.get('change', {}).get('actions', ['unknown'])
            address = change.get('address', 'unknown_resource')

            # Determine the primary action category
            action_category = "unknown"
            if actions == ["no-op"]:
                action_category = "no-op"
            elif actions == ["read"]:
                 action_category = "read"
            elif actions == ["create"]:
                action_category = "create"
            elif actions == ["update"]:
                action_category = "update"
            elif actions == ["delete"]:
                action_category = "delete"
            # IMPORTANT: Check for replacement - often ["delete", "create"]
            elif "create" in actions and "delete" in actions:
                action_category = "replace"
             # Fallbacks (less common for standard resources)
            elif "create" in actions:
                 action_category = "create"
            elif "delete" in actions:
                action_category = "delete"


            action_counts[action_category] += 1
            changes_by_action[action_category].append(address)

    # --- Build the Report String ---
    report_lines = []
    report_lines.append(f"Terraform Plan Summary Report")
    report_lines.append(f"Plan File:         {os.path.abspath(plan_json_path)}")
    report_lines.append(f"Terraform Version: {tf_version}")
    report_lines.append(f"Plan Format Ver:   {format_version}")
    report_lines.append("=" * 60)

    # Overall summary line (like terraform plan's output)
    summary_parts = []
    if action_counts['create']:  summary_parts.append(f"{action_counts['create']} to create")
    if action_counts['update']:  summary_parts.append(f"{action_counts['update']} to update")
    if action_counts['replace']: summary_parts.append(f"{action_counts['replace']} to replace")
    if action_counts['delete']:  summary_parts.append(f"{action_counts['delete']} to destroy")

    # Optionally mention unchanged count
    no_op_read_count = action_counts['no-op'] + action_counts['read']
    if no_op_read_count > 0 and include_no_op:
         summary_parts.append(f"{no_op_read_count} unchanged/read")


    if summary_parts:
         report_lines.append(f"Resource Changes Summary: {', '.join(summary_parts)}.")
    elif 'resource_changes' in plan_data: # Only say 'no changes' if we are sure
         report_lines.append("Resource Changes Summary: No resource changes detected.")
    else:
         report_lines.append("Resource Changes Summary: Could not determine resource changes (check warnings).")


    # Detailed sections for each action type
    # Define order for consistent report structure
    action_order = ["create", "update", "replace", "delete"]
    if include_no_op:
         action_order.extend(["read", "no-op"]) # Add read/no-op if requested

    has_detailed_changes = False
    for action in action_order:
        if changes_by_action[action]:
            has_detailed_changes = True
            report_lines.append("-" * 60)
            # Use more descriptive titles
            title_map = {
                "create": "Create", "update": "Update", "replace": "Replace",
                "delete": "Destroy", "read": "Read (Data Sources)", "no-op": "Unchanged"
            }
            title = title_map.get(action, action.capitalize())
            report_lines.append(f"{title} ({action_counts[action]}):")
            for address in sorted(changes_by_action[action]):
                report_lines.append(f"  - {address}")

    if not has_detailed_changes and 'resource_changes' in plan_data and len(resource_changes) > 0 and not include_no_op:
        # Handles case where only no-op/read changes exist but weren't included
         if no_op_read_count > 0:
             report_lines.append("-" * 60)
             report_lines.append(f"Note: {no_op_read_count} resource(s) are unchanged or will be read.")
             report_lines.append("      (Use --include-no-op flag to list them)")


    # Add note about output changes if relevant
    output_changes = plan_data.get('output_changes', {})
    if output_changes:
         report_lines.append("-" * 60)
         report_lines.append(f"Output Changes: {len(output_changes)} output(s) will be created, updated, or destroyed.")

    report_lines.append("=" * 60)

    return "\n".join(report_lines)

def main():
    """Parses command-line arguments and runs the summarizer."""
    parser = argparse.ArgumentParser(
        description="Summarize a Terraform plan from its JSON output file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""How to Generate the Required JSON Input File:
  1. terraform plan -out=tfplan.binary   # Create binary plan
  2. terraform show -json tfplan.binary > tfplan.json  # Convert to JSON

Example Usage:
  # Summarize tfplan.json in the current directory
  python tf_plan_summarizer.py tfplan.json

  # Summarize a specific plan file and save to report.txt
  python tf_plan_summarizer.py /path/to/myplan.json -o report.txt

  # Include unchanged and read resources in the detailed list
  python tf_plan_summarizer.py tfplan.json --include-no-op
"""
    )
    parser.add_argument(
        "plan_json_file",
        help="Path to the Terraform plan JSON file (generated by 'terraform show -json <plan>').",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="OUTPUT_FILE",
        help="Optional path to write the summary report file. Prints to console if not specified."
    )
    parser.add_argument(
        "--include-no-op",
        action="store_true", # Sets the value to True if the flag is present
        help="Include details of resources with 'no-op' (unchanged) or 'read' actions in the report."
    )

    args = parser.parse_args()

    # --- Run Summarizer ---
    summary_report = summarize_tf_plan(args.plan_json_file, args.include_no_op)

    # --- Output Report ---
    if summary_report is None:
         sys.exit(1) # Exit with error code if summarization failed critically

    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(summary_report)
            print(f"Summary report successfully written to '{os.path.abspath(args.output)}'")
        except IOError as e:
            print(f"Error: Could not write report to file '{args.output}': {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred while writing the file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Print report to standard output
        print(summary_report)

if __name__ == "__main__":
    main()

# How to Use:
# Save: Save the code as tf_plan_summarizer.py.
# Generate Plan JSON: Make sure you have tfplan.json (or similar) generated as described in the prerequisites.
# Make Executable (Optional, Linux/macOS): chmod +x tf_plan_summarizer.py
# Run:
# Summarize tfplan.json and print to console:
# Bash

# python tf_plan_summarizer.py tfplan.json
# # or ./tf_plan_summarizer.py tfplan.json (if executable)
# Summarize a differently named JSON file:
# Bash

# python tf_plan_summarizer.py my_project_plan.json
# Summarize and save the report to a file:
# Bash

# python tf_plan_summarizer.py tfplan.json -o plan_summary.txt
# Summarize and include unchanged/read resources in the detail:
# Bash

# python tf_plan_summarizer.py tfplan.json --include-no-op
# This script gives you a quick, high-level overview of the impact of your Terraform plan, focusing on the resources being changed.
