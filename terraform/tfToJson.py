import hcl2
import json

# Function to convert HCL to JSON
def convert_hcl_to_json(hcl_file_path, json_file_path):
    with open(hcl_file_path, 'r') as hcl_file:
        hcl_data = hcl2.load(hcl_file)

    with open(json_file_path, 'w') as json_file:
        json.dump(hcl_data, json_file, indent=4)

# Example usage
hcl_file_path = 'example.tf'
json_file_path = 'example.json'
convert_hcl_to_json(hcl_file_path, json_file_path)
