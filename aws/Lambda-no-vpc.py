import boto3

def list_lambda_functions_without_vpc_with_prefix(prefix):
    # Initialize a session using Boto3
    session = boto3.Session()
    lambda_client = session.client('lambda')

    # List all the Lambda functions
    paginator = lambda_client.get_paginator('list_functions')
    functions_without_vpc = []

    for page in paginator.paginate():
        for function in page['Functions']:
            function_name = function['FunctionName']

            # Check if the function name starts with the specified prefix
            if function_name.startswith(prefix):
                # Get the configuration for each function
                response = lambda_client.get_function_configuration(FunctionName=function_name)

                # Check if the function is associated with a VPC
                if 'VpcConfig' not in response or not response['VpcConfig'].get('VpcId'):
                    functions_without_vpc.append(function_name)

    return functions_without_vpc


if __name__ == '__main__':
    prefix = 'isp-'  # Specify the prefix to filter Lambda functions
    functions_without_vpc = list_lambda_functions_without_vpc_with_prefix(prefix)
    
    if functions_without_vpc:
        print(f"Lambda functions starting with '{prefix}' without VPC configuration:")
        for function in functions_without_vpc:
            print(f"- {function}")
    else:
        print(f"All Lambda functions starting with '{prefix}' have VPC configurations.")
