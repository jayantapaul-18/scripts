from hcl2 import loads

# Specify the path to your Terraform file
terraform_file_path = 'path/to/your/terraform/file.tf'

# Read and parse the Terraform file
with open(terraform_file_path, 'r') as file:
    terraform_data = loads(file.read())

# Access the data values
data_values = terraform_data.get('data', {})

# Iterate through the data values
for data_block_name, data_block in data_values.items():
    print(f"Data Block: {data_block_name}")
    
    if isinstance(data_block, dict):
        for data_name, data_value in data_block.items():
            print(f"  Data Name: {data_name}, Data Value: {data_value}")
    else:
        print(f"  Data Value: {data_block}")
