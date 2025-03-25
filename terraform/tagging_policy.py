import os
import terraform_parser

def check_tags(tf_file):
    try:
        parsed_tf = terraform_parser.parse(tf_file)
        results = []

        for resource_type, resources in parsed_tf.items():
            if resource_type == "resource" and resources:
                for resource_name, resource_data in resources.items():
                    for resource_instance_name, resource_instance_data in resource_data.items():
                        if "tags" not in resource_instance_data and "aws_" in resource_name:
                            results.append(f"Resource {resource_instance_name} of type {resource_name} is missing tags.")

        return results

    except Exception as e:
        return [f"Error parsing Terraform: {e}"]

if __name__ == "__main__":
    tf_files = [f for f in os.listdir(".") if f.endswith(".tf")]
    all_results = []

    for tf_file in tf_files:
        results = check_tags(tf_file)
        all_results.extend(results)

    for result in all_results:
        print(result)
