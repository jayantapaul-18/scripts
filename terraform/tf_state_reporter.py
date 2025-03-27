#!/usr/bin/env python3

import json
import argparse
import sys
import os

def analyze_tfstate(state_file_path):
    """
    Reads and analyzes a Terraform state file to report on resources,
    configuration, and tags.

    Args:
        state_file_path (str): Path to the terraform.tfstate file.

    Returns:
        str: A formatted report string.
    """
    try:
        # Check if file exists before attempting to open
        if not os.path.exists(state_file_path):
            raise FileNotFoundError(f"Error: State file not found at '{state_file_path}'")
        if not os.path.isfile(state_file_path):
             raise IsADirectoryError(f"Error: '{state_file_path}' is a directory, not a file.")


        with open(state_file_path, 'r', encoding='utf-8') as f:
            try:
                state_data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error: Failed to parse JSON in '{state_file_path}'. Invalid syntax.", file=sys.stderr)
                print(f"Details: {e}", file=sys.stderr)
                sys.exit(1)

    except (FileNotFoundError, IsADirectoryError) as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading file '{state_file_path}': {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
         print(f"An unexpected error occurred: {e}", file=sys.stderr)
         sys.exit(1)


    report_lines = []
    report_lines.append(f"Terraform State Analysis Report")
    report_lines.append(f"State File: {os.path.abspath(state_file_path)}")
    report_lines.append(f"Format Version: {state_data.get('version', 'N/A')}")
    report_lines.append(f"Terraform Version Used: {state_data.get('terraform_version', 'N/A')}")
    report_lines.append("=" * 60)

    resources = state_data.get('resources', [])
    if not resources:
        report_lines.append("No managed resources found in the state file.")
        return "\n".join(report_lines)

    report_lines.append(f"Found {len(resources)} resource configurations managed in this state.")
    report_lines.append("-" * 60)

    for i, resource in enumerate(resources):
        resource_type = resource.get('type', 'N/A')
        resource_name = resource.get('name', 'N/A')
        provider = resource.get('provider', 'N/A')
        instances = resource.get('instances', [])

        report_lines.append(f"\nResource #{i+1}:")
        report_lines.append(f"  Type:     {resource_type}")
        report_lines.append(f"  Name:     {resource_name}")
        report_lines.append(f"  Provider: {provider}")

        if not instances:
            report_lines.append("  Instances: None (Resource may be tainted or incompletely created)")
            report_lines.append("-" * 60)
            continue

        for j, instance in enumerate(instances):
            instance_id_str = ""
            # Check for index key (from for_each) or count index
            if 'index_key' in instance and instance['index_key'] is not None:
                instance_id_str = f" [Key: {instance['index_key']}]"
            elif 'index_key' in instance and instance['index_key'] is None and len(instances) > 1:
                 # This might happen with count in older versions or certain scenarios
                 instance_id_str = f" [Index: {j}]"
            elif len(instances) > 1:
                # Default to index if multiple instances and no clear key
                 instance_id_str = f" [Index: {j}]"

            report_lines.append(f"\n  Instance {j+1}{instance_id_str}:")

            attributes = instance.get('attributes', {})
            schema_version = instance.get('schema_version', 'N/A')
            report_lines.append(f"    Schema Version: {schema_version}")

            # --- Extract Tags ---
            # Prioritize 'tags_all' as it includes provider-default tags
            tags = attributes.get('tags_all', attributes.get('tags'))

            report_lines.append("    Tags:")
            if isinstance(tags, dict) and tags:
                for key, value in sorted(tags.items()):
                    report_lines.append(f"      - {key}: {value}")
            elif tags is None:
                report_lines.append("      (No tags found)")
            else: # Handle empty dict or unexpected format
                report_lines.append(f"      {tags if tags else '(No tags found or empty map)'}")

            # --- Extract Other Configuration Attributes ---
            report_lines.append("\n    Configuration Attributes (State):")
            if attributes:
                for key, value in sorted(attributes.items()):
                    # Avoid duplicating tags list
                    if key == 'tags' or key == 'tags_all':
                        continue
                    # Simple heuristic to shorten potentially very long values for readability
                    value_str = str(value)
                    max_len = 150
                    if len(value_str) > max_len:
                        value_str = value_str[:max_len] + f"... (truncated, original length {len(value_str)})"

                    # Indent multi-line values for clarity
                    value_lines = value_str.splitlines()
                    if len(value_lines) > 1:
                        report_lines.append(f"      - {key}:")
                        for line in value_lines:
                            report_lines.append(f"          {line}")
                    else:
                         report_lines.append(f"      - {key}: {value_str}")

            else:
                report_lines.append("      (No attributes found in this instance)")

        report_lines.append("-" * 60) # Separator after all instances of a resource

    return "\n".join(report_lines)

def main():
    """Parses command-line arguments and runs the analysis."""
    parser = argparse.ArgumentParser(
        description="Read a Terraform state file (terraform.tfstate) and generate a report on resources, configuration, and tags.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Example Usage:
  python tf_state_reporter.py                 # Reads ./terraform.tfstate
  python tf_state_reporter.py path/to/my.tfstate
  python tf_state_reporter.py state.json -o report.txt
"""
    )
    parser.add_argument(
        "state_file",
        help="Path to the terraform.tfstate file (default: terraform.tfstate in current directory).",
        default="terraform.tfstate", # Default to standard name in CWD
        nargs='?' # Makes the argument optional, uses default if not provided
    )
    parser.add_argument(
        "-o", "--output",
        metavar="OUTPUT_FILE",
        help="Optional path to write the report file. If not specified, prints to standard output."
    )

    args = parser.parse_args()

    # --- Run Analysis ---
    report = analyze_tfstate(args.state_file)

    # --- Output Report ---
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"Report successfully written to '{os.path.abspath(args.output)}'")
        except IOError as e:
            print(f"Error: Could not write report to file '{args.output}': {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
             print(f"An unexpected error occurred while writing the file: {e}", file=sys.stderr)
             sys.exit(1)
    else:
        # Print report to standard output
        print(report)

if __name__ == "__main__":
    main()
