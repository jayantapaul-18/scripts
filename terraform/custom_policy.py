import os
import json
import terraform_parser

def check_policy(tf_file, enforce_policy):
    try:
        parsed_tf = terraform_parser.parse(tf_file)
        results = []

        for resource_type, resources in parsed_tf.items():
            if resource_type == "resource" and "aws_instance" in resources:
                for resource_name, resource_data in resources["aws_instance"].items():
                    instance_type = resource_data.get("instance_type", "")
                    if "t2.micro" not in instance_type:
                        message = f"Resource {resource_name}: Instance type is not t2.micro, violating policy."
                        if enforce_policy.lower() == "true":
                            results.append(message + " Policy enforcement is active.")
                        else:
                            results.append(message)
        return results

    except Exception as e:
        return [f"Error parsing Terraform: {e}"]

if __name__ == "__main__":
    enforce_policy = os.environ.get("ENFORCE_POLICY", "true") #get from environment variable.
    if len(os.sys.argv) > 1:
        enforce_policy = os.sys.argv[1];

    tf_files = [f for f in os.listdir(".") if f.endswith(".tf")]
    all_results = []

    for tf_file in tf_files:
        results = check_policy(tf_file, enforce_policy)
        all_results.extend(results)

    for result in all_results:
        print(result)
