Implementing a feature flag solution using GitLab for controlling a Node.js application’s environment configuration in Kubernetes via ConfigMap can be accomplished by setting up a feature flagging strategy in GitLab CI/CD. This would involve creating feature flags in GitLab, using them to manage configuration in the Kubernetes ConfigMap, and triggering updates based on the flag values.

Here’s how to build this solution step-by-step:

Step 1: Create Feature Flags in GitLab

	1.	Navigate to your GitLab project.
	2.	Go to Settings -> Operations -> Feature Flags.
	3.	Create a new feature flag for your environment configurations (e.g., NEW_ENV_FEATURE).

The feature flag values (enabled/disabled) will determine whether new environment variables are used or old ones are kept.

Step 2: Modify Node.js Application to Use Environment Variables

In your Node.js application, read environment variables from the Kubernetes ConfigMap. For instance, you can use process.env to access the variables:

const myFeatureFlag = process.env.NEW_ENV_FEATURE === 'true';

if (myFeatureFlag) {
  // Use new environment variables or logic
  console.log('New environment settings enabled');
} else {
  // Use old environment variables or logic
  console.log('Old environment settings in use');
}

Step 3: Configure Kubernetes ConfigMap for Environment Variables

The ConfigMap will contain environment variables that the Node.js application reads at runtime. You’ll need to update the ConfigMap dynamically based on the feature flag value in GitLab.

Example ConfigMap YAML (configmap.yaml):

apiVersion: v1
kind: ConfigMap
metadata:
  name: nodejs-config
  namespace: default
data:
  NODE_ENV: "production"
  NEW_ENV_FEATURE: "{{NEW_ENV_FEATURE}}"  # Placeholder for feature flag value
  OLD_API_URL: "https://old-api.example.com"
  NEW_API_URL: "https://new-api.example.com"

Step 4: Automate Updates with GitLab CI/CD

In GitLab CI/CD, automate the process of updating the ConfigMap based on the status of the feature flag.

GitLab CI/CD Pipeline (.gitlab-ci.yml):

stages:
  - validate
  - deploy

variables:
  KUBECONFIG: "/path/to/kubeconfig"  # Update path to your kubeconfig file

before_script:
  - kubectl version --client
  - echo $KUBECONFIG > kubeconfig  # Load the kubeconfig file
  - export KUBECONFIG=$(pwd)/kubeconfig

validate_feature_flag:
  stage: validate
  script:
    # Check if the feature flag is enabled in GitLab
    - 'curl --header "PRIVATE-TOKEN: ${CI_JOB_TOKEN}" https://gitlab.com/api/v4/projects/${CI_PROJECT_ID}/features_flags | jq ".[] | select(.name==\"NEW_ENV_FEATURE\").active"'
  only:
    - master  # Only run on master/main branch

update_configmap:
  stage: deploy
  script:
    # Fetch the value of the feature flag from GitLab API
    - FEATURE_FLAG=$(curl --header "PRIVATE-TOKEN: ${CI_JOB_TOKEN}" https://gitlab.com/api/v4/projects/${CI_PROJECT_ID}/feature_flags | jq ".[] | select(.name==\"NEW_ENV_FEATURE\").active")

    # Replace the placeholder in the ConfigMap template with the feature flag value
    - sed -i "s/{{NEW_ENV_FEATURE}}/${FEATURE_FLAG}/g" configmap.yaml

    # Apply the updated ConfigMap to the Kubernetes cluster
    - kubectl apply -f configmap.yaml
    - echo "ConfigMap updated successfully based on feature flag"

  only:
    - master  # Deploy on master/main branch

Step 5: Ensure Kubernetes Pod Uses Updated ConfigMap

Your Kubernetes Deployment should use the ConfigMap to inject environment variables into the Node.js application.

Example Deployment.yaml:

apiVersion: apps/v1
kind: Deployment
metadata:
  name: nodejs-app
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nodejs-app
  template:
    metadata:
      labels:
        app: nodejs-app
    spec:
      containers:
      - name: nodejs-container
        image: nodejs-app-image:latest
        envFrom:
        - configMapRef:
            name: nodejs-config
        ports:
        - containerPort: 8080

Step 6: Deploy and Validate

Once the GitLab pipeline runs:

	1.	It fetches the feature flag value from GitLab’s API.
	2.	It dynamically replaces the NEW_ENV_FEATURE placeholder in the ConfigMap with the current feature flag value.
	3.	It applies the updated ConfigMap to Kubernetes.
	4.	The Node.js app reads the updated environment variable (NEW_ENV_FEATURE) and switches between old/new configurations based on the flag.

Step 7: Logging and Monitoring

You can add logging to your Node.js application to track which configuration is in use. You can also monitor GitLab pipeline logs to verify that the feature flag logic is working as expected.

if (myFeatureFlag) {
  console.log('New environment is active');
} else {
  console.log('Old environment is active');
}

For deeper monitoring, consider adding Prometheus metrics to your Node.js app to track which environment is in use, and push them to your monitoring stack (Prometheus/Grafana, Datadog, etc.).

Step 8: Rollback or Adjust

If there’s an issue with the feature flag configuration, simply toggle the flag in GitLab’s Feature Flags settings, and re-run the pipeline to apply the updated configuration.

This approach lets you dynamically control your Node.js application’s environment settings using GitLab feature flags, Kubernetes ConfigMap, and GitLab CI/CD pipelines.