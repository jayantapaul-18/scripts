#!/usr/bin/env python3

import sys
import re
import argparse

def parse_plan_output(plan_text):
    """
    Parses the text output of 'terraform plan' to extract changes.

    Args:
        plan_text (str): The multi-line string containing the plan output.

    Returns:
        dict: A dictionary containing lists of resources to be created,
              destroyed, updated, and replaced, plus the summary counts.
              Returns None if the essential summary line isn't found.
    """
    created = []
    destroyed = []
    updated = []
    replaced = [] # Resources that are destroyed and then created

    summary = {
        "add": 0,
        "change": 0,
        "destroy": 0,
        "found": False
    }

    # Regex patterns
    # Matches lines like: # aws_instance.example will be created
    # Matches lines like: # aws_instance.example will be destroyed
    # Matches lines like: # module.mymodule.aws_instance.example[0] will be created
    resource_change_pattern = re.compile(r"^\s*#\s+([\w\._\[\]\"-]+)\s+will\s+be\s+(created|destroyed)", re.MULTILINE)

    # Matches lines like: # aws_instance.example will be updated in-place
    resource_update_pattern = re.compile(r"^\s*#\s+([\w\._\[\]\"-]+)\s+will\s+be\s+updated\s+in-place", re.MULTILINE)

    # Matches lines indicating replacement (often involves +/- in the diff section)
    # This looks for the resource block line following a replacement indicator
    # Example line: -/+ resource "aws_instance" "example" { (known after change)
    resource_replace_pattern = re.compile(r"^\s*[-~]/\+\s+resource\s+\"([\w-]+)\"\s+\"([\w.-]+)\"", re.MULTILINE)

    # Matches the summary line: Plan: X to add, Y to change, Z to destroy.
    summary_pattern = re.compile(r"^Plan:\s+(\d+)\s+to\s+add,\s+(\d+)\s+to\s+change,\s+(\d+)\s+to\s+destroy\.", re.MULTILINE)

    # --- Pass 1: Find explicit create/destroy/update actions ---
    for match in resource_change_pattern.finditer(plan_text):
        resource_id = match.group(1)
        action = match.group(2)
        if action == "created":
            if resource_id not in created: # Avoid duplicates if format varies
                 created.append(resource_id)
        elif action == "destroyed":
            if resource_id not in destroyed:
                 destroyed.append(resource_id)

    for match in resource_update_pattern.finditer(plan_text):
        resource_id = match.group(1)
        if resource_id not in updated:
            updated.append(resource_id)

    # --- Pass 2: Find replacements ---
    # Note: Replacements are often counted in 'change' in the summary.
    # We identify them separately for more detail.
    for match in resource_replace_pattern.finditer(plan_text):
        resource_type = match.group(1)
        resource_name = match.group(2)
        resource_id = f"{resource_type}.{resource_name}"
        if resource_id not in replaced:
            replaced.append(resource_id)
        # A replaced resource might also appear in 'destroyed'. Remove it from there
        # if it's identified as a replacement for clarity.
        # It might also appear briefly in 'created' depending on output order - handle cautiously.
        if resource_id in destroyed:
            destroyed.remove(resource_id)
        # It's less common but possible for it to appear as 'created' before the -/+ line
        if resource_id in created:
             created.remove(resource_id)


    # --- Pass 3: Find the summary line ---
    summary_match = summary_pattern.search(plan_text)
    if summary_match:
        summary["add"] = int(summary_match.group(1))
        summary["change"] = int(summary_match.group(2))
        summary["destroy"] = int(summary_match.group(3))
        summary["found"] = True
    else:
        # If the summary line isn't found, the input might be invalid or incomplete
        print("WARNING: Could not find Terraform plan summary line.", file=sys.stderr)
        print("         Parsing might be inaccurate.", file=sys.stderr)
        # Attempt to derive counts from lists (less reliable)
        summary["add"] = len(created) + len(replaced) # Replacements involve an add
        summary["change"] = len(updated) + len(replaced) # Replacements are changes
        summary["destroy"] = len(destroyed) + len(replaced) # Replacements involve a destroy


    return {
        "created": sorted(created),
        "destroyed": sorted(destroyed),
        "updated": sorted(updated),
        "replaced": sorted(replaced),
        "summary": summary
    }

def generate_report(parsed_data):
    """
    Generates a formatted report string from the parsed plan data.

    Args:
        parsed_data (dict): The dictionary returned by parse_plan_output.

    Returns:
        str: A formatted report string.
    """
    if not parsed_data:
        return "Error: Failed to parse plan data."

    report = []
    summary = parsed_data["summary"]

    report.append("--- Terraform Plan Summary Report ---")
    report.append("")

    if summary["found"]:
        report.append(f"Summary: {summary['add']} to add, {summary['change']} to change, {summary['destroy']} to destroy.")
    else:
        report.append("Summary: Could not reliably detect summary counts from plan output.")
        report.append(f"         Detected approximately: {len(parsed_data['created'])} created, "
                      f"{len(parsed_data['destroyed'])} destroyed, {len(parsed_data['updated'])} updated, "
                      f"{len(parsed_data['replaced'])} replaced.")

    report.append("-" * 30) # Separator

    # --- Creations ---
    report.append(f"\nResources to Create ({len(parsed_data['created'])}):")
    if parsed_data["created"]:
        for resource in parsed_data["created"]:
            report.append(f"  + {resource}")
    else:
        report.append("  (None)")

    # --- Updates (In-Place) ---
    report.append(f"\nResources to Update In-Place ({len(parsed_data['updated'])}):")
    if parsed_data["updated"]:
        for resource in parsed_data["updated"]:
            report.append(f"  ~ {resource}")
    else:
        report.append("  (None)")

    # --- Replacements (Destroy then Create) ---
    report.append(f"\nResources to Replace (+/-) ({len(parsed_data['replaced'])}):")
    if parsed_data["replaced"]:
        for resource in parsed_data["replaced"]:
            report.append(f"  +/- {resource}")
    else:
        report.append("  (None)")

    # --- Destructions ---
    report.append(f"\nResources to Destroy ({len(parsed_data['destroyed'])}):")
    if parsed_data["destroyed"]:
        for resource in parsed_data["destroyed"]:
            report.append(f"  - {resource}")
    else:
        report.append("  (None)")

    report.append("\n--- End of Report ---")

    return "\n".join(report)

def main():
    """
    Main function to read input, parse, and print the report.
    """
    parser = argparse.ArgumentParser(
        description="Parses Terraform plan text output from stdin or a file and generates a summary report.",
        epilog="Example usage: terraform plan | python script_name.py\n"
               "               terraform plan -out=tfplan.txt; python script_name.py tfplan.txt"
    )
    parser.add_argument(
        'infile',
        nargs='?',
        type=argparse.FileType('r'),
        default=sys.stdin,
        help='Optional Terraform plan output file. Reads from stdin if not provided.'
    )

    args = parser.parse_args()

    # Check if input is coming from a pipe or a file
    if args.infile is sys.stdin and sys.stdin.isatty():
        print("Please pipe Terraform plan output to this script or provide a filename.", file=sys.stderr)
        print("Example: terraform plan | python", sys.argv[0], file=sys.stderr)
        sys.exit(1)

    try:
        plan_content = args.infile.read()
    finally:
        if args.infile is not sys.stdin:
            args.infile.close()

    if not plan_content:
        print("Error: Input is empty.", file=sys.stderr)
        sys.exit(1)

    parsed_results = parse_plan_output(plan_content)
    report = generate_report(parsed_results)
    print(report)

if __name__ == "__main__":
    main()
