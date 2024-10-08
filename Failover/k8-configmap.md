To create an automated script that updates a Kubernetes ConfigMap, performs a rolling restart of the relevant deployment, and validates the change, you can use Python’s subprocess module or a Kubernetes client library to interact with the Kubernetes API.

Here’s an outline of what the script will do:

	1.	Update the ConfigMap: Modify the ConfigMap with the required changes.
	2.	Perform a rolling restart: Trigger a rolling restart of the pods by updating an annotation or using kubectl rollout.
	3.	Validate the changes: Ensure that the new pods are up and running and that the ConfigMap has been updated successfully in the running pods.

Script using kubectl and Python

This script assumes that kubectl is installed and configured on the machine where the script runs. The script will:

	•	Update the ConfigMap using kubectl apply.
	•	Trigger a rolling restart of the deployment.
	•	Check the rollout status and validate if the new pods are using the updated ConfigMap.

Python Script:

import subprocess
import time
import sys

def run_command(command):
    """ Run shell command and capture output """
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return output.decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e.output.decode('utf-8').strip()}")
        sys.exit(1)

def update_configmap(namespace, configmap_name, configmap_file):
    """ Update the Kubernetes ConfigMap """
    print(f"Updating ConfigMap {configmap_name} in namespace {namespace}...")
    command = f"kubectl apply -f {configmap_file} -n {namespace}"
    run_command(command)
    print("ConfigMap updated successfully.")

def rolling_restart(namespace, deployment_name):
    """ Trigger a rolling restart of a Kubernetes deployment """
    print(f"Rolling restart of deployment {deployment_name} in namespace {namespace}...")
    # Trigger restart by patching the deployment's annotation
    command = f"kubectl rollout restart deployment/{deployment_name} -n {namespace}"
    run_command(command)
    print(f"Rolling restart triggered for deployment {deployment_name}.")

def check_rollout_status(namespace, deployment_name):
    """ Check the status of the rollout """
    print(f"Checking rollout status for deployment {deployment_name}...")
    command = f"kubectl rollout status deployment/{deployment_name} -n {namespace}"
    output = run_command(command)
    print(output)
    if "successfully" in output.lower():
        print("Rollout completed successfully.")
    else:
        print("Rollout failed.")
        sys.exit(1)

def validate_configmap_in_pods(namespace, configmap_name, configmap_key, expected_value):
    """ Validate that the ConfigMap update has been applied to all running pods """
    print("Validating ConfigMap updates in running pods...")
    command = f"kubectl get pods -n {namespace} -o jsonpath='{{.items[*].metadata.name}}'"
    pod_names = run_command(command).split()

    for pod_name in pod_names:
        command = f"kubectl exec {pod_name} -n {namespace} -- cat /etc/config/{configmap_key}"
        pod_config_value = run_command(command)
        if pod_config_value == expected_value:
            print(f"Pod {pod_name} is using the updated ConfigMap value.")
        else:
            print(f"Pod {pod_name} does NOT have the updated ConfigMap value. Found: {pod_config_value}")
            sys.exit(1)

def main():
    # Define variables (edit these according to your environment)
    namespace = "default"
    configmap_name = "my-configmap"
    configmap_file = "./configmap.yaml"
    deployment_name = "my-deployment"
    configmap_key = "my-key"
    expected_value = "new-value"

    # Step 1: Update the ConfigMap
    update_configmap(namespace, configmap_name, configmap_file)

    # Step 2: Trigger a rolling restart of the deployment
    rolling_restart(namespace, deployment_name)

    # Step 3: Validate the rollout status
    check_rollout_status(namespace, deployment_name)

    # Step 4: Validate that the ConfigMap change has been applied to the pods
    validate_configmap_in_pods(namespace, configmap_name, configmap_key, expected_value)

if __name__ == "__main__":
    main()

Explanation:

	1.	run_command: Executes shell commands and handles errors.
	2.	update_configmap: Uses kubectl apply to update the ConfigMap with the changes from a file (configmap.yaml).
	3.	rolling_restart: Triggers a rolling restart of the deployment by updating its annotations using kubectl rollout restart.
	4.	check_rollout_status: Uses kubectl rollout status to check the progress of the rolling restart.
	5.	validate_configmap_in_pods: Checks if the updated ConfigMap is applied to the running pods by comparing the value in the pods with the expected value.

Sample configmap.yaml file:

apiVersion: v1
kind: ConfigMap
metadata:
  name: my-configmap
  namespace: default
data:
  my-key: "new-value"

Running the Script:

	1.	Ensure that you have kubectl installed and configured to access your Kubernetes cluster.
	2.	Modify the namespace, configmap_name, deployment_name, and other parameters in the script to match your setup.
	3.	Save the script as update_configmap.py.
	4.	Run the script:

python update_configmap.py



Key Points:

	•	Automation: The script automates the update, rolling restart, and validation process.
	•	Validation: It validates the rollout success and checks whether the new ConfigMap values are being used by all the pods.
	•	Customizable: You can modify this script to add more validation checks or modify the way ConfigMap updates are handled.

Let me know if you’d like to customize this script further!